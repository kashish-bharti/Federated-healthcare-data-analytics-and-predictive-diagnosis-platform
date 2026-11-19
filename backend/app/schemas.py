from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

from .models import UserRole


# ---------- Auth ----------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: Optional[str] = None
    institution_id: Optional[int] = None
    role: UserRole = UserRole.clinician


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str]
    role: UserRole
    institution_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Institutions ----------
class InstitutionCreate(BaseModel):
    name: str
    location: Optional[str] = None


class InstitutionOut(BaseModel):
    id: int
    name: str
    location: Optional[str]
    created_at: datetime
    patient_count: int = 0

    class Config:
        from_attributes = True


# ---------- Patients ----------
class PatientCreate(BaseModel):
    age: float = Field(ge=0, le=120)
    bmi: float = Field(ge=10, le=80)
    systolic_bp: float = Field(ge=70, le=260)
    glucose: float = Field(ge=40, le=500)
    cholesterol: float = Field(ge=80, le=500)
    smoker: bool = False
    diagnosis_label: Optional[int] = Field(default=None, ge=0, le=1)
    notes: Optional[str] = None


class PatientOut(BaseModel):
    id: int
    institution_id: int
    age: float
    bmi: float
    systolic_bp: float
    glucose: float
    cholesterol: float
    smoker: bool
    diagnosis_label: Optional[int]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Predictions ----------
class PredictionRequest(BaseModel):
    patient_id: Optional[int] = None
    age: float
    bmi: float
    systolic_bp: float
    glucose: float
    cholesterol: float
    smoker: bool = False


class PredictionOut(BaseModel):
    id: int
    patient_id: Optional[int]
    model_version: int
    risk_score: float
    predicted_label: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Federated learning ----------
class FederatedRoundOut(BaseModel):
    id: int
    round_number: int
    num_clients: int
    total_samples: int
    avg_train_loss: float
    global_val_loss: float
    global_val_accuracy: float
    model_version: int
    created_at: datetime

    class Config:
        from_attributes = True


class FederatedTrainRequest(BaseModel):
    rounds: int = Field(default=3, ge=1, le=50)


class FederatedStatus(BaseModel):
    current_model_version: int
    total_rounds_completed: int
    last_round: Optional[FederatedRoundOut]
    eligible_institutions: List[str]
