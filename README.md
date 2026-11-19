# Federated Healthcare Data Analytics & Predictive Diagnosis Platform

A full-stack demo platform combining:

- **Backend** — FastAPI (Python)
- **ML** — PyTorch model trained via a hand-rolled FedAvg federated-learning loop
- **Authentication** — JWT + bcrypt, role-based (admin / clinician)
- **UI** — vanilla-JS single-page frontend (no build step required)
- **Database** — SQLite via SQLAlchemy (swappable for Postgres/MySQL)

## Architecture

```
Institution A patients ──┐
Institution B patients ──┼──► local training (per-institution) ──► weight updates only
Institution C patients ──┘                                              │
                                                                          ▼
                                                        Central server: FedAvg aggregation
                                                                          │
                                                                          ▼
                                                        Updated global diagnosis model
                                                                          │
                                                                          ▼
                                                      /predictions/predict (any clinician)
```

Raw patient data is queried strictly per-institution and is never pooled or transmitted; only
PyTorch weight tensors move between the simulated "clients" and the server.

## Quick start

**1. Backend**
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python seed.py                 # creates demo institutions, users, and synthetic patients
uvicorn app.main:app --reload --port 8000
```

**2. Frontend**

Just open `frontend/index.html` directly in a browser, or serve it statically:
```bash
cd frontend
python3 -m http.server 5500
# then visit http://localhost:5500
```
The frontend talks to `http://localhost:8000` by default — edit the `API_BASE_URL` line at the
top of `frontend/index.html` if your backend runs elsewhere.

**3. Log in** with a seeded demo account (see `backend/README.md` for the full list), add a few
patients, run a federated training round as the admin account, then try a prediction.

## Project layout

```
backend/
  app/
    main.py              FastAPI app + router registration
    config.py            Settings (DB URL, JWT secret, FL hyperparameters)
    database.py           SQLAlchemy engine/session
    models.py             ORM models: Institution, User, Patient, PredictionRecord, FederatedRound
    schemas.py             Pydantic request/response schemas
    security.py           Password hashing + JWT
    deps.py                Auth dependencies (current user, admin guard)
    routers/               auth, institutions, patients, predictions, federated
    ml/
      model.py             PyTorch RiskNet + feature normalization
      data.py               Synthetic data generator (seeding + server-side validation set)
      federated_trainer.py  FedAvg: local training, aggregation, evaluation
  seed.py                  Demo data seeding script
  requirements.txt
frontend/
  index.html
  css/style.css
  js/api.js               Fetch wrapper for the backend API
  js/views.js              HTML templates per page
  js/app.js                Router/state + event wiring
```

## Extending this further

- Swap the in-process FedAvg loop for [Flower](https://flower.ai/) or NVIDIA FLARE for true
  multi-machine federation across real hospital networks.
- Add differential privacy noise to local weight updates before aggregation (e.g. Opacus) for a
  stronger formal privacy guarantee than data-isolation alone.
- Replace the tabular MLP with a model suited to your actual data modality (e.g. a CNN for imaging,
  a transformer for clinical notes).
- Add audit logging and consent tracking tables — expected in most real healthcare-data platforms.
