"""Optimization endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.campus import Campus
from app.services.optimization_service import calculate_optimization_opportunities

router = APIRouter(prefix="/campuses", tags=["Optimization"])


@router.get("/{campus_id}/optimization")
def campus_optimization(campus_id: str, db: Session = Depends(get_db)):
    """Identify energy optimization opportunities for a campus."""
    campus = db.query(Campus).filter(Campus.id == campus_id).first()
    if not campus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": "Campus not found", "code": "CAMPUS_NOT_FOUND"},
        )
    return calculate_optimization_opportunities(db, campus_id)
