"""
FedAvg orchestration.

Design (mirrors real federated learning, simplified for a single-process demo):

  1. The server holds only the *global model weights* - never raw patient data.
  2. For each round, every eligible institution ("client") receives a copy of
     the current global weights.
  3. Each client trains locally for a few epochs on its own patients only
     (data never leaves the institution's boundary in this function).
  4. Clients return their *updated weights* (not their data) to the server.
  5. The server aggregates client weights with FedAvg: a weighted average by
     each client's local sample count.
  6. The new global model is evaluated on a fixed, server-held validation
     set (synthetic - see ml/data.py) purely to monitor quality over rounds.
"""
import copy
from typing import List, Tuple

import torch
import torch.nn as nn
from sqlalchemy.orm import Session

from .. import models
from ..config import settings
from .model import RiskNet, load_global_model, save_global_model, normalize_features
from .data import generate_dataset


def _patients_to_tensors(patients: List["models.Patient"]) -> Tuple[torch.Tensor, torch.Tensor]:
    X, y = [], []
    for p in patients:
        if p.diagnosis_label is None:
            continue
        X.append(normalize_features({
            "age": p.age, "bmi": p.bmi, "systolic_bp": p.systolic_bp,
            "glucose": p.glucose, "cholesterol": p.cholesterol, "smoker": p.smoker,
        }))
        y.append(float(p.diagnosis_label))
    if not X:
        return torch.empty(0, 6), torch.empty(0, 1)
    return torch.tensor(X, dtype=torch.float32), torch.tensor(y, dtype=torch.float32).unsqueeze(1)


def _rows_to_tensors(rows: List[dict]) -> Tuple[torch.Tensor, torch.Tensor]:
    X = [normalize_features(r) for r in rows]
    y = [[float(r["diagnosis_label"])] for r in rows]
    return torch.tensor(X, dtype=torch.float32), torch.tensor(y, dtype=torch.float32)


def _local_train(global_state_dict, X: torch.Tensor, y: torch.Tensor, epochs: int, lr: float):
    """Simulates one institution's local training step. Never sees other clients' data."""
    model = RiskNet()
    model.load_state_dict(copy.deepcopy(global_state_dict))
    model.train()

    optimizer = torch.optim.SGD(model.parameters(), lr=lr, momentum=0.9)
    loss_fn = nn.BCEWithLogitsLoss()

    batch_size = min(settings.FL_BATCH_SIZE, len(X))
    final_loss = 0.0
    n = len(X)
    for _ in range(epochs):
        perm = torch.randperm(n)
        epoch_loss = 0.0
        batches = 0
        for start in range(0, n, batch_size):
            idx = perm[start:start + batch_size]
            xb, yb = X[idx], y[idx]
            optimizer.zero_grad()
            logits = model(xb)
            loss = loss_fn(logits, yb)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
            batches += 1
        final_loss = epoch_loss / max(batches, 1)

    return model.state_dict(), final_loss, n


def _fed_average(client_states: List[dict], client_weights: List[int]) -> dict:
    total = sum(client_weights)
    avg_state = copy.deepcopy(client_states[0])
    for key in avg_state.keys():
        avg_state[key] = sum(
            state[key] * (w / total) for state, w in zip(client_states, client_weights)
        )
    return avg_state


def _evaluate(model: RiskNet, X_val: torch.Tensor, y_val: torch.Tensor):
    model.eval()
    loss_fn = nn.BCEWithLogitsLoss()
    with torch.no_grad():
        logits = model(X_val)
        loss = loss_fn(logits, y_val).item()
        preds = (torch.sigmoid(logits) >= 0.5).float()
        accuracy = (preds == y_val).float().mean().item()
    return loss, accuracy


def get_eligible_clients(db: Session):
    """Institutions with enough labeled patients to participate in a round."""
    eligible = []
    for inst in db.query(models.Institution).all():
        patients = db.query(models.Patient).filter(
            models.Patient.institution_id == inst.id,
            models.Patient.diagnosis_label.isnot(None),
        ).all()
        if len(patients) >= settings.FL_MIN_CLIENT_SAMPLES:
            eligible.append((inst, patients))
    return eligible


_VALIDATION_ROWS = generate_dataset(n_rows=300, seed=999)  # fixed server-side benchmark set
_X_VAL, _Y_VAL = _rows_to_tensors(_VALIDATION_ROWS)


def run_federated_rounds(db: Session, num_rounds: int) -> List["models.FederatedRound"]:
    global_model, version = load_global_model()
    eligible = get_eligible_clients(db)

    if not eligible:
        raise ValueError(
            "No institution currently has enough labeled patients "
            f"(minimum {settings.FL_MIN_CLIENT_SAMPLES}) to participate in a training round."
        )

    completed_rounds = []
    last_round_number = db.query(models.FederatedRound).count()

    for r in range(1, num_rounds + 1):
        client_states, client_weights, client_losses = [], [], []

        for inst, patients in eligible:
            X, y = _patients_to_tensors(patients)
            if len(X) == 0:
                continue
            state, loss, n = _local_train(
                global_model.state_dict(), X, y,
                epochs=settings.FL_LOCAL_EPOCHS, lr=settings.FL_LEARNING_RATE,
            )
            client_states.append(state)
            client_weights.append(n)
            client_losses.append(loss)

        if not client_states:
            raise ValueError("No client produced a valid local update for this round.")

        new_state = _fed_average(client_states, client_weights)
        global_model.load_state_dict(new_state)
        version += 1
        save_global_model(global_model, version)

        val_loss, val_acc = _evaluate(global_model, _X_VAL, _Y_VAL)
        avg_train_loss = sum(client_losses) / len(client_losses)

        round_record = models.FederatedRound(
            round_number=last_round_number + r,
            num_clients=len(client_states),
            total_samples=sum(client_weights),
            avg_train_loss=avg_train_loss,
            global_val_loss=val_loss,
            global_val_accuracy=val_acc,
            model_version=version,
        )
        db.add(round_record)
        db.commit()
        db.refresh(round_record)
        completed_rounds.append(round_record)

    return completed_rounds
