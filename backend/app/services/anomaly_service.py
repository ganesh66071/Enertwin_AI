"""Anomaly detection service wrapper."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.ml.anomaly_detector import detect_anomalies
from app.services.dataset_service import get_campus_records
from app.utils.data_cleaning import json_safe


def get_campus_anomalies(db: Session, campus_id: str) -> dict:
    records = get_campus_records(db, campus_id)
    result = detect_anomalies(records)
    return json_safe({"success": True, "campus_id": campus_id, **result})
