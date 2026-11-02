"""Pydantic schemas for analytics endpoints."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class CampusKPIs(BaseModel):
    total_energy_kwh: float
    average_energy_kwh: float
    minimum_energy_kwh: float
    maximum_energy_kwh: float
    peak_demand_kw: float
    average_occupancy: float
    hvac_energy_kwh: float
    lighting_energy_kwh: float
    equipment_energy_kwh: float
    hvac_percentage: float
    lighting_percentage: float
    equipment_percentage: float
    other_percentage: float
    total_cost: float
    total_co2: float
    energy_intensity: float
    efficiency_score: float


class EnergyBreakdown(BaseModel):
    hvac: float
    lighting: float
    equipment: float
    other: float


class BuildingSummary(BaseModel):
    building_name: str
    total_energy: float
    average_energy: float
    peak_demand: float
    occupancy: float
    hvac: float
    lighting: float
    equipment: float
    co2: float
    anomaly_count: int = 0
    efficiency_score: float


class DataQuality(BaseModel):
    total_records: int
    valid_records: int
    derived_records: int
    duplicate_records_removed: int
    completeness_score: float


class CampusOverviewResponse(BaseModel):
    success: bool = True
    campus: dict[str, Any]
    kpis: CampusKPIs
    energy_breakdown: EnergyBreakdown
    building_summary: list[BuildingSummary]
    data_quality: DataQuality


class BuildingAnalyticsResponse(BaseModel):
    success: bool = True
    campus_id: str
    buildings: list[BuildingSummary]
