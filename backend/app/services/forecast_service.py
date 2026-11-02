"""Forecast service wrapper."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.ml.forecaster import forecast_energy
from app.services.dataset_service import get_campus_records
from app.utils.data_cleaning import json_safe


def get_campus_forecast(db: Session, campus_id: str) -> dict:
    records = get_campus_records(db, campus_id)
    result = forecast_energy(records)
    return json_safe({"campus_id": campus_id, **result})
