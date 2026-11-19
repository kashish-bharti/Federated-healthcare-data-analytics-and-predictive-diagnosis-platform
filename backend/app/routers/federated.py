from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user, require_admin
from ..ml.federated_trainer import run_federated_rounds, get_eligible_clients
from ..ml.model import load_global_model

router = APIRouter(prefix="/federated", tags=["federated learning"])


@router.post("/train", response_model=List[schemas.FederatedRoundOut], dependencies=[Depends(require_admin)])
def train(payload: schemas.FederatedTrainRequest, db: Session = Depends(get_db)):
    try:
        rounds = run_federated_rounds(db, payload.rounds)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return rounds


@router.get("/rounds", response_model=List[schemas.FederatedRoundOut])
def rounds(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return (
        db.query(models.FederatedRound)
        .order_by(models.FederatedRound.round_number.desc())
        .all()
    )


@router.get("/status", response_model=schemas.FederatedStatus)
def status(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    _, version = load_global_model()
    total_rounds = db.query(models.FederatedRound).count()
    last = (
        db.query(models.FederatedRound)
        .order_by(models.FederatedRound.round_number.desc())
        .first()
    )
    eligible = [inst.name for inst, _ in get_eligible_clients(db)]
    return schemas.FederatedStatus(
        current_model_version=version,
        total_rounds_completed=total_rounds,
        last_round=last,
        eligible_institutions=eligible,
    )
