"""Model persistence and training coordination for campus models."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib

BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_ROOT = BASE_DIR / "models"


def ensure_model_dir(campus_id: str) -> Path:
    campus_dir = MODEL_ROOT / campus_id
    campus_dir.mkdir(parents=True, exist_ok=True)
    return campus_dir


def train_models_for_campus(campus_id: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    campus_dir = ensure_model_dir(campus_id)
    anomaly_model = {"model_type": "anomaly", "campus_id": campus_id, "trained_at": "now", "training_records": len(records), "feature_names": ["energy_consumption_kwh", "peak_demand_kw", "occupancy_percent"], "model_version": "v1.0"}
    forecast_model = {"model_type": "forecast", "campus_id": campus_id, "trained_at": "now", "training_records": len(records), "feature_names": ["hour", "day_of_week", "lag_1", "rolling_12"], "model_version": "v1.0"}
    anomaly_path = campus_dir / "anomaly_model.pkl"
    forecast_path = campus_dir / "forecast_model.pkl"
    joblib.dump(anomaly_model, anomaly_path)
    joblib.dump(forecast_model, forecast_path)
    metadata = {
        "campus_id": campus_id,
        "anomaly_model": str(anomaly_path),
        "forecast_model": str(forecast_path),
        "training_records": len(records),
    }
    (campus_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    return metadata


def get_or_train_model(campus_id: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    campus_dir = ensure_model_dir(campus_id)
    anomaly_path = campus_dir / "anomaly_model.pkl"
    forecast_path = campus_dir / "forecast_model.pkl"
    if anomaly_path.exists() and forecast_path.exists():
        return {"campus_id": campus_id, "status": "ready", "models": {"anomaly": str(anomaly_path), "forecast": str(forecast_path)}}
    return train_models_for_campus(campus_id, records)
