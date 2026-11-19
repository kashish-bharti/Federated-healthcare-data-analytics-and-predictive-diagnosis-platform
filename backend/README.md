# Backend — Federated Healthcare Analytics Platform

FastAPI + SQLAlchemy + PyTorch backend implementing:

- **Auth**: JWT-based login/register, bcrypt password hashing, role-based access (`admin` vs `clinician`).
- **Database**: SQLite by default (swap `DATABASE_URL` for Postgres/MySQL in production) with models for
  Institutions (federated nodes), Users, Patients, Predictions, and FederatedRound history.
- **Federated learning**: a from-scratch FedAvg implementation (`app/ml/federated_trainer.py`). Each
  institution's patient data never leaves its own row-filtered query — only PyTorch model weights are
  centrally averaged.
- **Predictive diagnosis**: a small PyTorch MLP (`app/ml/model.py`) trained via the federated rounds and
  served through `/predictions/predict`.

## Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Seed demo institutions, users, and synthetic labeled patients
python seed.py

# Run the API
uvicorn app.main:app --reload --port 8000
```

API docs (Swagger UI) will be at http://localhost:8000/docs

## Demo accounts (created by seed.py)

| Role      | Email                        | Password           |
|-----------|-------------------------------|---------------------|
| Admin     | admin@fedhealth.demo          | AdminPass123!       |
| Clinician | clinician1@fedhealth.demo     | ClinicianPass123!   |
| Clinician | clinician2@fedhealth.demo     | ClinicianPass123!   |
| Clinician | clinician3@fedhealth.demo     | ClinicianPass123!   |

## Trying the federated training loop

1. Log in as `admin@fedhealth.demo`.
2. Call `POST /federated/train` with `{"rounds": 5}` (or use the frontend's "Federated Training" tab).
3. Each seeded institution has 40 synthetic labeled patients (above the `FL_MIN_CLIENT_SAMPLES`
   threshold in `app/config.py`), so all three participate as clients in every round.
4. Watch `global_val_accuracy` in `GET /federated/rounds` improve round over round.
5. Use `POST /predictions/predict` (as any clinician) to run inference with the newest global model.

## Notes on the "federated" design

- Raw patient rows are always filtered by `institution_id` — no endpoint in this API ever returns another
  institution's patient records.
- Local training (`_local_train` in `federated_trainer.py`) only ever sees one institution's `Patient` rows
  at a time; the function returns weight tensors, never data.
- Aggregation (`_fed_average`) is a pure weight-averaging step over those returned tensors.
- Global model quality is monitored using a fixed, synthetic server-side validation set
  (`ml/data.py`) — never real patient data — which is standard practice for tracking a federated model
  without needing access to any client's raw records.

This is a teaching/demo-scale implementation (single process, sequential "clients") — for true
multi-machine federation you'd swap the in-process loop in `run_federated_rounds` for a framework like
Flower or NVIDIA FLARE, but the data-isolation and FedAvg logic here would stay conceptually the same.
