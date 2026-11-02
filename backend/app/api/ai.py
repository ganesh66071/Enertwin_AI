"""AI endpoints for campus-specific analytics and agentic insights."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.campus import Campus
from ai.services.ai_service import (
    chat_with_ai,
    get_ai_status,
    get_building_intelligence,
    get_campus_ai_anomalies,
    get_campus_ai_forecast,
    get_campus_ai_optimization,
    get_campus_comparison,
    get_energy_score,
    get_executive_report,
)

router = APIRouter(prefix="/ai", tags=["AI"])


class ChatRequest(BaseModel):
    message: str


def _ensure_campus(db: Session, campus_id: str) -> Campus:
    campus = db.query(Campus).filter(Campus.id == campus_id).first()
    if not campus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": "Campus not found", "code": "CAMPUS_NOT_FOUND"},
        )
    return campus


@router.get("/{campus_id}/status")
def campus_ai_status(campus_id: str, db: Session = Depends(get_db)):
    _ensure_campus(db, campus_id)
    return get_ai_status(campus_id, db)


@router.get("/{campus_id}/anomalies")
def campus_ai_anomalies(campus_id: str, db: Session = Depends(get_db)):
    _ensure_campus(db, campus_id)
    return get_campus_ai_anomalies(db, campus_id)


@router.get("/{campus_id}/forecast")
def campus_ai_forecast(campus_id: str, db: Session = Depends(get_db)):
    _ensure_campus(db, campus_id)
    return get_campus_ai_forecast(db, campus_id)


@router.get("/{campus_id}/optimization")
def campus_ai_optimization(campus_id: str, db: Session = Depends(get_db)):
    _ensure_campus(db, campus_id)
    return get_campus_ai_optimization(db, campus_id)


@router.get("/{campus_id}/energy-score")
def campus_energy_score(campus_id: str, db: Session = Depends(get_db)):
    _ensure_campus(db, campus_id)
    return get_energy_score(db, campus_id)


@router.get("/{campus_id}/building-intelligence")
def campus_building_intelligence(campus_id: str, db: Session = Depends(get_db)):
    _ensure_campus(db, campus_id)
    return get_building_intelligence(db, campus_id)


@router.get("/campus-comparison")
def campus_comparison(db: Session = Depends(get_db)):
    return get_campus_comparison(db)


@router.get("/{campus_id}/executive-report")
def campus_executive_report(campus_id: str, db: Session = Depends(get_db)):
    _ensure_campus(db, campus_id)
    return get_executive_report(db, campus_id)


@router.post("/{campus_id}/chat")
def campus_ai_chat(campus_id: str, payload: ChatRequest, db: Session = Depends(get_db)):
    _ensure_campus(db, campus_id)
    return chat_with_ai(db, campus_id, payload.message)
