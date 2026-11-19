import os
from datetime import timedelta

class Settings:
    # --- General ---
    APP_NAME: str = "Federated Healthcare Data Analytics & Predictive Diagnosis Platform"

    # --- Database ---
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./fedhealth.db")

    # --- Auth / JWT ---
    SECRET_KEY: str = os.getenv("SECRET_KEY", "CHANGE_ME_IN_PRODUCTION_" + os.urandom(8).hex())
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours

    # --- Federated Learning ---
    FL_LOCAL_EPOCHS: int = 3
    FL_LEARNING_RATE: float = 0.05
    FL_BATCH_SIZE: int = 16
    FL_MIN_CLIENT_SAMPLES: int = 5  # institutions with fewer patients than this are skipped in a round

settings = Settings()
