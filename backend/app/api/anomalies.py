"""Anomaly detection endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.campus import Campus
from app.services.anomaly_service import get_campus_anomalies

router = APIRouter(prefix="/campuses", tags=["Anomalies"])


@router.get("/{campus_id}/anomalies")
def campus_anomalies(campus_id: str, db: Session = Depends(get_db)):
    """Detect energy anomalies for a campus using Isolation Forest + Z-score."""
    campus = db.query(Campus).filter(Campus.id == campus_id).first()
    if not campus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": "Campus not found", "code": "CAMPUS_NOT_FOUND"},
        )
    return get_campus_anomalies(db, campus_id)
