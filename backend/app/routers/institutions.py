from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user, require_admin

router = APIRouter(prefix="/institutions", tags=["institutions"])


@router.post("", response_model=schemas.InstitutionOut, dependencies=[Depends(require_admin)])
def create_institution(payload: schemas.InstitutionCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Institution).filter(models.Institution.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Institution already exists")
    inst = models.Institution(name=payload.name, location=payload.location)
    db.add(inst)
    db.commit()
    db.refresh(inst)
    out = schemas.InstitutionOut.model_validate(inst)
    out.patient_count = 0
    return out


@router.get("", response_model=List[schemas.InstitutionOut])
def list_institutions(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    institutions = db.query(models.Institution).all()
    results = []
    for inst in institutions:
        out = schemas.InstitutionOut.model_validate(inst)
        out.patient_count = db.query(models.Patient).filter(models.Patient.institution_id == inst.id).count()
        results.append(out)
    return results
