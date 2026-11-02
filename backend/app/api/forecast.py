"""Forecasting endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.campus import Campus
from app.services.forecast_service import get_campus_forecast

router = APIRouter(prefix="/campuses", tags=["Forecast"])


@router.get("/{campus_id}/forecast")
def campus_forecast(campus_id: str, db: Session = Depends(get_db)):
    """Generate energy consumption forecast for a campus."""
    campus = db.query(Campus).filter(Campus.id == campus_id).first()
    if not campus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": "Campus not found", "code": "CAMPUS_NOT_FOUND"},
        )
    return get_campus_forecast(db, campus_id)
