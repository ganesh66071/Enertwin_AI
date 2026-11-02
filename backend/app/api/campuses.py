"""Campus CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.campus import Campus
from app.schemas.campus import CampusCreate, CampusListResponse, CampusResponse
from app.services.static_demo_campuses import get_static_demo_campuses

router = APIRouter(prefix="/campuses", tags=["Campuses"])


@router.post("", response_model=CampusResponse, status_code=status.HTTP_201_CREATED)
def create_campus(payload: CampusCreate, db: Session = Depends(get_db)):
    """Create a new campus."""
    campus = Campus(
        name=payload.name,
        location=payload.location,
        campus_type=payload.campus_type,
        description=payload.description,
    )
    db.add(campus)
    db.commit()
    db.refresh(campus)
    return campus


@router.get("", response_model=CampusListResponse)
def list_campuses(db: Session = Depends(get_db)):
    """List all campuses."""
    static_campuses = get_static_demo_campuses()
    if static_campuses:
        return CampusListResponse(
            campuses=[
                CampusResponse(
                    id=campus["id"],
                    name=campus["name"],
                    location=campus["location"],
                    campus_type=campus["campus_type"],
                    description=campus.get("description"),
                    created_at=campus["created_at"],
                )
                for campus in static_campuses
            ],
            total=len(static_campuses),
        )
    campuses = db.query(Campus).order_by(Campus.created_at.desc()).all()
    return CampusListResponse(campuses=campuses, total=len(campuses))


@router.get("/{campus_id}", response_model=CampusResponse)
def get_campus(campus_id: str, db: Session = Depends(get_db)):
    """Get a campus by ID."""
    static_campus = next((campus for campus in get_static_demo_campuses() if campus["id"] == campus_id), None)
    if static_campus:
        return CampusResponse(
            id=static_campus["id"],
            name=static_campus["name"],
            location=static_campus["location"],
            campus_type=static_campus["campus_type"],
            description=static_campus.get("description"),
            created_at=static_campus["created_at"],
        )
    campus = db.query(Campus).filter(Campus.id == campus_id).first()
    if not campus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": "Campus not found", "code": "CAMPUS_NOT_FOUND"},
        )
    return campus


@router.delete("/{campus_id}", status_code=status.HTTP_200_OK)
def delete_campus(campus_id: str, db: Session = Depends(get_db)):
    """Delete a campus and all associated energy records."""
    campus = db.query(Campus).filter(Campus.id == campus_id).first()
    if not campus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": "Campus not found", "code": "CAMPUS_NOT_FOUND"},
        )
    db.delete(campus)
    db.commit()
    return {"success": True, "message": f"Campus {campus_id} deleted"}
