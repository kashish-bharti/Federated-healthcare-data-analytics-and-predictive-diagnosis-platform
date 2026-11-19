from typing import List

import torch
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user
from ..ml.model import load_global_model, normalize_features

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.post("/predict", response_model=schemas.PredictionOut)
def predict(
    payload: schemas.PredictionRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.institution_id is None:
        raise HTTPException(status_code=400, detail="Your account is not linked to an institution")

    if payload.patient_id is not None:
        patient = db.query(models.Patient).get(payload.patient_id)
        if not patient or patient.institution_id != current_user.institution_id:
            raise HTTPException(status_code=404, detail="Patient not found")

    model, version = load_global_model()
    features = normalize_features({
        "age": payload.age, "bmi": payload.bmi, "systolic_bp": payload.systolic_bp,
        "glucose": payload.glucose, "cholesterol": payload.cholesterol,
        "smoker": payload.smoker,
    })
    with torch.no_grad():
        logit = model(torch.tensor([features], dtype=torch.float32))
        risk_score = torch.sigmoid(logit).item()
    predicted_label = 1 if risk_score >= 0.5 else 0

    record = models.PredictionRecord(
        patient_id=payload.patient_id,
        institution_id=current_user.institution_id,
        requested_by_id=current_user.id,
        model_version=version,
        risk_score=risk_score,
        predicted_label=predicted_label,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/history", response_model=List[schemas.PredictionOut])
def prediction_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.PredictionRecord)
        .filter(models.PredictionRecord.institution_id == current_user.institution_id)
        .order_by(models.PredictionRecord.created_at.desc())
        .limit(100)
        .all()
    )
