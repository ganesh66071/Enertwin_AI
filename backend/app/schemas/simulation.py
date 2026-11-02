"""Pydantic schemas for simulation endpoints."""

from pydantic import BaseModel, Field


class SimulationRequest(BaseModel):
    hvac_reduction_percent: float = Field(default=0, ge=0, le=100)
    lighting_reduction_percent: float = Field(default=0, ge=0, le=100)
    equipment_reduction_percent: float = Field(default=0, ge=0, le=100)
    occupancy_change_percent: float = Field(default=0, ge=-100, le=100)
    peak_shift: bool = Field(default=False, description="Attempt to shift peak demand")


class SimulationMetrics(BaseModel):
    energy: float
    cost: float
    co2: float
    peak_demand: float


class SimulationResponse(BaseModel):
    success: bool = True
    campus_id: str
    baseline: SimulationMetrics
    projected: SimulationMetrics
    savings: SimulationMetrics
