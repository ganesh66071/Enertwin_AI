"""AI recommendations and analyst endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.campus import Campus
from app.schemas.recommendation import AskRequest, AskResponse, RecommendationsResponse
from app.services.recommendation_service import answer_campus_question, get_recommendations

router = APIRouter(prefix="/campuses", tags=["Recommendations & AI Analyst"])


@router.get("/{campus_id}/recommendations", response_model=RecommendationsResponse)
def campus_recommendations(campus_id: str, db: Session = Depends(get_db)):
    """Get AI-powered energy optimization recommendations grounded in campus analytics."""
    campus = db.query(Campus).filter(Campus.id == campus_id).first()
    if not campus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": "Campus not found", "code": "CAMPUS_NOT_FOUND"},
        )
    return get_recommendations(db, campus_id)


@router.post("/{campus_id}/ask", response_model=AskResponse)
def campus_ask(
    campus_id: str,
    payload: AskRequest,
    db: Session = Depends(get_db),
):
    """Ask the AI analyst a question about campus energy data."""
    campus = db.query(Campus).filter(Campus.id == campus_id).first()
    if not campus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": "Campus not found", "code": "CAMPUS_NOT_FOUND"},
        )
    return answer_campus_question(db, campus_id, payload.question)
