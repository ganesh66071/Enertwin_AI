"""Pydantic schemas for energy data."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class EnergyRecordResponse(BaseModel):
    id: str
    campus_id: str
    timestamp: datetime
    building_name: str
    energy_consumption_kwh: float
    hvac_energy_kwh: float
    lighting_energy_kwh: float
    equipment_energy_kwh: float
    peak_demand_kw: float
    occupancy_percent: float
    co2_emission_kg: float
    data_source: str

    model_config = {"from_attributes": True}


class DatasetUploadResponse(BaseModel):
    success: bool = True
    campus_id: str
    filename: str
    records_processed: int
    records_rejected: int
    warnings: list[str] = Field(default_factory=list)
    mapped_columns: dict[str, str] = Field(default_factory=dict)


class EnergyTrendPoint(BaseModel):
    timestamp: str
    energy_kwh: float


class EnergyTrendResponse(BaseModel):
    success: bool = True
    campus_id: str
    aggregation: str
    data: list[EnergyTrendPoint]
