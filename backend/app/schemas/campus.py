"""Pydantic schemas for campus endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CampusCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Campus name")
    location: str = Field(..., min_length=1, max_length=512, description="Campus location")
    campus_type: str = Field(default="General", max_length=128, description="Type of campus")
    description: Optional[str] = Field(default=None, description="Optional description")


class CampusResponse(BaseModel):
    id: str
    name: str
    location: str
    campus_type: str
    description: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CampusListResponse(BaseModel):
    success: bool = True
    campuses: list[CampusResponse]
    total: int
