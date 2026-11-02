"""What-if simulation endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.campus import Campus
from app.schemas.simulation import SimulationRequest, SimulationResponse
from app.services.simulation_service import run_simulation

router = APIRouter(prefix="/campuses", tags=["Simulation"])


@router.post("/{campus_id}/simulate", response_model=SimulationResponse)
def campus_simulate(
    campus_id: str,
    payload: SimulationRequest,
    db: Session = Depends(get_db),
):
    """Run a what-if energy simulation for a campus."""
    campus = db.query(Campus).filter(Campus.id == campus_id).first()
    if not campus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": "Campus not found", "code": "CAMPUS_NOT_FOUND"},
        )
    result = run_simulation(
        db,
        campus_id,
        hvac_reduction_percent=payload.hvac_reduction_percent,
        lighting_reduction_percent=payload.lighting_reduction_percent,
        equipment_reduction_percent=payload.equipment_reduction_percent,
        occupancy_change_percent=payload.occupancy_change_percent,
        peak_shift=payload.peak_shift,
    )
    return SimulationResponse(**result)
