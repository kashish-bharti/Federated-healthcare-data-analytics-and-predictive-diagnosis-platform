"""
Synthetic clinical-risk data generator.

Used for:
  1. Seeding demo institutions with plausible patient records so the
     federated training pipeline has something to train on out of the box.
  2. Building a fixed, server-side validation set used only to *evaluate*
     global model quality after each federated round (the server never
     trains on this data, and it is not any institution's real patient data).

The "ground truth" label is generated from a clinically-inspired logistic
combination of risk factors plus noise - a reasonable stand-in for a real
diagnosis outcome in a demo/teaching context.
"""
import random
import math


def _risk_probability(age, bmi, systolic_bp, glucose, cholesterol, smoker):
    z = (
        -8.0
        + 0.045 * age
        + 0.09 * bmi
        + 0.02 * systolic_bp
        + 0.018 * glucose
        + 0.01 * cholesterol
        + (1.1 if smoker else 0.0)
    )
    return 1.0 / (1.0 + math.exp(-z))


def generate_patient_row(rng: random.Random) -> dict:
    age = rng.uniform(18, 90)
    bmi = rng.uniform(16, 45)
    systolic_bp = rng.uniform(95, 190)
    glucose = rng.uniform(70, 260)
    cholesterol = rng.uniform(120, 320)
    smoker = rng.random() < 0.22

    p = _risk_probability(age, bmi, systolic_bp, glucose, cholesterol, smoker)
    label = 1 if rng.random() < p else 0

    return {
        "age": round(age, 1),
        "bmi": round(bmi, 1),
        "systolic_bp": round(systolic_bp, 1),
        "glucose": round(glucose, 1),
        "cholesterol": round(cholesterol, 1),
        "smoker": smoker,
        "diagnosis_label": label,
    }


def generate_dataset(n_rows: int, seed: int) -> list:
    rng = random.Random(seed)
    return [generate_patient_row(rng) for _ in range(n_rows)]
