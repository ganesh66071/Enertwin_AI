"""Dataset upload endpoints."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.campus import Campus
from app.schemas.energy import DatasetUploadResponse
from app.services.analytics_service import calculate_campus_analytics
from app.services.dataset_service import process_dataset_upload

router = APIRouter(prefix="/datasets", tags=["Datasets"])

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


@router.post("/upload/{campus_id}", response_model=DatasetUploadResponse)
async def upload_dataset(
    campus_id: str,
    file: UploadFile = File(..., description="CSV or Excel energy dataset"),
    db: Session = Depends(get_db),
):
    """
    Upload and process an energy dataset for a specific campus.

    Pipeline: read → validate → normalize columns → derive missing values → store.
    """
    campus = db.query(Campus).filter(Campus.id == campus_id).first()
    if not campus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": "Campus not found", "code": "CAMPUS_NOT_FOUND"},
        )

    filename = file.filename or "upload.csv"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "error": f"Unsupported file type: {ext}", "code": "INVALID_FILE_TYPE"},
        )

    content = await file.read()
    try:
        result = process_dataset_upload(db, campus_id, campus.campus_type, content, filename)
        # Trigger analytics refresh (computed on demand)
        calculate_campus_analytics(db, campus_id)
        return DatasetUploadResponse(**result)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "error": str(exc), "code": "DATASET_PROCESSING_ERROR"},
        )
