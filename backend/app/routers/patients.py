from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/patients", tags=["patients"])


def _require_institution(user: models.User):
    if user.institution_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your account is not linked to an institution",
        )


@router.post("", response_model=schemas.PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(
    payload: schemas.PatientCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _require_institution(current_user)
    patient = models.Patient(
        institution_id=current_user.institution_id,
        created_by_id=current_user.id,
        **payload.model_dump(),
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("", response_model=List[schemas.PatientOut])
def list_patients(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Data isolation: a clinician only ever sees patients belonging to their
    own institution. Admins may pass no filter and still only see their own
    institution's data through this endpoint - cross-institution raw data
    access is intentionally not exposed anywhere in this API.
    """
    _require_institution(current_user)
    return (
        db.query(models.Patient)
        .filter(models.Patient.institution_id == current_user.institution_id)
        .order_by(models.Patient.created_at.desc())
        .all()
    )


@router.get("/{patient_id}", response_model=schemas.PatientOut)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    patient = db.query(models.Patient).get(patient_id)
    if not patient or patient.institution_id != current_user.institution_id:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient
