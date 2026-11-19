from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db
from .routers import auth, institutions, patients, predictions, federated

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Backend for a federated healthcare data analytics platform. "
        "Each institution's raw patient data stays local; only model weight "
        "updates are aggregated centrally via FedAvg to produce a shared "
        "predictive-diagnosis model."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "app": settings.APP_NAME}


app.include_router(auth.router)
app.include_router(institutions.router)
app.include_router(patients.router)
app.include_router(predictions.router)
app.include_router(federated.router)
