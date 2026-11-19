import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum, Text
)
from sqlalchemy.orm import relationship

from .database import Base


class UserRole(str, enum.Enum):
    admin = "admin"          # platform-wide administrator
    clinician = "clinician"  # institution-scoped user who manages patients / runs predictions


class Institution(Base):
    """
    Represents one federated node (e.g. a hospital or clinic).
    Raw patient data never leaves its owning institution - only model
    weight updates are shared with the central server during training.
    """
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False)
    location = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="institution")
    patients = relationship("Patient", back_populates="institution")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    hashed_password = Column(String(200), nullable=False)
    full_name = Column(String(200), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.clinician, nullable=False)
    is_active = Column(Boolean, default=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    institution = relationship("Institution", back_populates="users")


class Patient(Base):
    """
    A patient record, scoped to a single institution. Clinicians can only
    read/write patients belonging to their own institution (enforced in
    the routers/deps layer), which is what makes the "federation" real:
    the platform never returns another institution's raw records.
    """
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # De-identified clinical features used by the risk model
    age = Column(Float, nullable=False)
    bmi = Column(Float, nullable=False)
    systolic_bp = Column(Float, nullable=False)
    glucose = Column(Float, nullable=False)
    cholesterol = Column(Float, nullable=False)
    smoker = Column(Boolean, default=False)

    # Ground-truth label if known (used only locally for federated training,
    # never transmitted to the server - only gradient/weight updates are).
    diagnosis_label = Column(Integer, nullable=True)  # 0 = low risk, 1 = high risk

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    institution = relationship("Institution", back_populates="patients")


class PredictionRecord(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False)
    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    model_version = Column(Integer, nullable=False)
    risk_score = Column(Float, nullable=False)       # 0.0 - 1.0
    predicted_label = Column(Integer, nullable=False)  # 0 / 1
    created_at = Column(DateTime, default=datetime.utcnow)


class FederatedRound(Base):
    """
    One completed round of federated averaging (FedAvg) across
    participating institutions.
    """
    __tablename__ = "federated_rounds"

    id = Column(Integer, primary_key=True, index=True)
    round_number = Column(Integer, nullable=False)
    num_clients = Column(Integer, nullable=False)
    total_samples = Column(Integer, nullable=False)
    avg_train_loss = Column(Float, nullable=False)
    global_val_loss = Column(Float, nullable=False)
    global_val_accuracy = Column(Float, nullable=False)
    model_version = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
