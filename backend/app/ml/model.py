"""
Small feed-forward network used as the *global* federated model.
Kept intentionally simple (single hidden-layer MLP) so that FedAvg
(weight averaging across institutions) is easy to reason about.
"""
import os
import torch
import torch.nn as nn

FEATURE_ORDER = ["age", "bmi", "systolic_bp", "glucose", "cholesterol", "smoker"]

# Fixed clinical reference ranges used for min-max normalization.
# Using fixed ranges (rather than a mean/std fit on pooled data) means no
# institution ever needs to share raw statistics with the server - each
# client can normalize locally and independently.
FEATURE_RANGES = {
    "age": (0.0, 120.0),
    "bmi": (10.0, 80.0),
    "systolic_bp": (70.0, 260.0),
    "glucose": (40.0, 500.0),
    "cholesterol": (80.0, 500.0),
    "smoker": (0.0, 1.0),
}

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "storage")
os.makedirs(MODEL_DIR, exist_ok=True)
GLOBAL_MODEL_PATH = os.path.join(MODEL_DIR, "global_model.pt")


def normalize_features(feature_dict: dict) -> list:
    row = []
    for name in FEATURE_ORDER:
        value = float(feature_dict[name])
        lo, hi = FEATURE_RANGES[name]
        row.append((value - lo) / (hi - lo))
    return row


class RiskNet(nn.Module):
    def __init__(self, in_features: int = len(FEATURE_ORDER)):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_features, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Linear(8, 1),
        )

    def forward(self, x):
        return self.net(x)  # raw logits; apply sigmoid outside for probability


def new_model() -> RiskNet:
    torch.manual_seed(42)
    return RiskNet()


def save_global_model(model: RiskNet, version: int):
    torch.save({"state_dict": model.state_dict(), "version": version}, GLOBAL_MODEL_PATH)


def load_global_model() -> tuple:
    """Returns (model, version). Creates a fresh model if none has been trained yet."""
    model = new_model()
    if os.path.exists(GLOBAL_MODEL_PATH):
        checkpoint = torch.load(GLOBAL_MODEL_PATH, map_location="cpu")
        model.load_state_dict(checkpoint["state_dict"])
        version = checkpoint["version"]
    else:
        version = 0
        save_global_model(model, version)
    model.eval()
    return model, version
