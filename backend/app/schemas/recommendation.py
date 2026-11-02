"""Pydantic schemas for recommendation endpoints."""

from typing import Optional

from pydantic import BaseModel, Field


class RecommendationItem(BaseModel):
    title: str
    priority: str
    problem: str
    recommendation: str
    expected_energy_saving: float
    expected_cost_saving: float
    expected_co2_reduction: float
    expected_monthly_saving: Optional[float] = None


class RecommendationsResponse(BaseModel):
    success: bool = True
    campus_id: str
    recommendations: list[RecommendationItem]
    llm_enhanced: bool = False


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)


class AskResponse(BaseModel):
    success: bool = True
    campus_id: str
    question: str
    answer: str
    sources: list[str] = Field(default_factory=list)
    llm_enhanced: bool = False
