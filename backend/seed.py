"""
Seeds the database with demo data so the platform is usable immediately:
  - 1 admin account
  - 3 institutions ("hospitals"), each with a clinician account
  - ~40 synthetic, labeled patients per institution (enough to satisfy
    FL_MIN_CLIENT_SAMPLES and produce a meaningful federated training demo)

Run with:  python seed.py
"""
from app.database import SessionLocal, init_db
from app import models
from app.security import hash_password
from app.ml.data import generate_dataset

ADMIN_EMAIL = "admin@fedhealth.demo"
ADMIN_PASSWORD = "AdminPass123!"

INSTITUTIONS = [
    {"name": "Riverside General Hospital", "location": "Chicago, IL", "clinician": "clinician1@fedhealth.demo"},
    {"name": "Lakeside Medical Center", "location": "Austin, TX", "clinician": "clinician2@fedhealth.demo"},
    {"name": "Summit Regional Clinic", "location": "Denver, CO", "clinician": "clinician3@fedhealth.demo"},
]
CLINICIAN_PASSWORD = "ClinicianPass123!"


def run():
    init_db()
    db = SessionLocal()
    try:
        if not db.query(models.User).filter(models.User.email == ADMIN_EMAIL).first():
            admin = models.User(
                email=ADMIN_EMAIL,
                hashed_password=hash_password(ADMIN_PASSWORD),
                full_name="Platform Administrator",
                role=models.UserRole.admin,
            )
            db.add(admin)
            print(f"Created admin: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")

        for idx, spec in enumerate(INSTITUTIONS):
            inst = db.query(models.Institution).filter(models.Institution.name == spec["name"]).first()
            if not inst:
                inst = models.Institution(name=spec["name"], location=spec["location"])
                db.add(inst)
                db.commit()
                db.refresh(inst)
                print(f"Created institution: {inst.name}")

            if not db.query(models.User).filter(models.User.email == spec["clinician"]).first():
                clinician = models.User(
                    email=spec["clinician"],
                    hashed_password=hash_password(CLINICIAN_PASSWORD),
                    full_name=f"Dr. Demo {idx + 1}",
                    role=models.UserRole.clinician,
                    institution_id=inst.id,
                )
                db.add(clinician)
                print(f"Created clinician: {spec['clinician']} / {CLINICIAN_PASSWORD}")

            existing_count = db.query(models.Patient).filter(models.Patient.institution_id == inst.id).count()
            if existing_count == 0:
                rows = generate_dataset(n_rows=40, seed=100 + idx)
                for row in rows:
                    db.add(models.Patient(institution_id=inst.id, **row))
                print(f"Seeded 40 synthetic patients for {inst.name}")

        db.commit()
        print("\nSeed complete. You can now log in with the accounts above.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
