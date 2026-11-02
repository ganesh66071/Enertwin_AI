"""Analytics endpoints."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.campus import Campus
from app.schemas.analytics import BuildingAnalyticsResponse, CampusOverviewResponse
from app.schemas.energy import EnergyTrendResponse
from app.services.analytics_service import (
    calculate_campus_analytics,
    get_building_analytics,
    get_campus_overview,
    get_energy_trend,
)
from app.services.static_demo_campuses import get_static_overview_payload

router = APIRouter(prefix="/campuses", tags=["Analytics"])


def _ensure_campus(db: Session, campus_id: str) -> Campus:
    campus = db.query(Campus).filter(Campus.id == campus_id).first()
    if not campus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": "Campus not found", "code": "CAMPUS_NOT_FOUND"},
        )
    return campus


@router.get("/{campus_id}/overview", response_model=CampusOverviewResponse)
def campus_overview(campus_id: str, db: Session = Depends(get_db)):
    """Get campus dashboard overview with KPIs, breakdown, and building summary."""
    static_payload = get_static_overview_payload(campus_id)
    if static_payload:
        return static_payload
    _ensure_campus(db, campus_id)
    try:
        return get_campus_overview(db, campus_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": "Campus not found", "code": "CAMPUS_NOT_FOUND"},
        )


@router.get("/{campus_id}/analytics")
def campus_analytics(campus_id: str, db: Session = Depends(get_db)):
    """Get computed KPIs for a campus."""
    static_payload = get_static_overview_payload(campus_id)
    if static_payload:
        return {"success": True, "campus_id": campus_id, "kpis": static_payload["kpis"]}
    _ensure_campus(db, campus_id)
    return {"success": True, "campus_id": campus_id, "kpis": calculate_campus_analytics(db, campus_id)}


@router.get("/{campus_id}/energy-trend", response_model=EnergyTrendResponse)
def campus_energy_trend(
    campus_id: str,
    aggregation: Literal["hourly", "daily", "weekly", "monthly"] = Query(default="daily"),
    db: Session = Depends(get_db),
):
    """Get time-series energy trend for a campus."""
    static_payload = get_static_overview_payload(campus_id)
    if static_payload:
        trend = static_payload.get("energy_trend", [])
        return EnergyTrendResponse(campus_id=campus_id, aggregation=aggregation, data=trend)
    _ensure_campus(db, campus_id)
    data = get_energy_trend(db, campus_id, aggregation)
    return EnergyTrendResponse(campus_id=campus_id, aggregation=aggregation, data=data)


@router.get("/{campus_id}/buildings", response_model=BuildingAnalyticsResponse)
def campus_buildings(campus_id: str, db: Session = Depends(get_db)):
    """Get per-building analytics for a campus."""
    static_payload = get_static_overview_payload(campus_id)
    if static_payload:
        return BuildingAnalyticsResponse(campus_id=campus_id, buildings=static_payload["building_summary"])
    _ensure_campus(db, campus_id)
    return BuildingAnalyticsResponse(campus_id=campus_id, buildings=get_building_analytics(db, campus_id))
