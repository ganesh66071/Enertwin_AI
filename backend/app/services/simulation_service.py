"""What-if simulation engine."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.services.dataset_service import get_campus_records
from app.utils.data_cleaning import json_safe


def run_simulation(
    db: Session,
    campus_id: str,
    hvac_reduction_percent: float = 0,
    lighting_reduction_percent: float = 0,
    equipment_reduction_percent: float = 0,
    occupancy_change_percent: float = 0,
    peak_shift: bool = False,
) -> dict[str, Any]:
    """
    Simulate energy impact of parameter changes on campus baseline data.
    All calculations derive from actual campus records.
    """
    records = get_campus_records(db, campus_id)
    if not records:
        return json_safe(
            {
                "success": False,
                "message": "No data available for simulation",
                "campus_id": campus_id,
                "baseline": {"energy": 0, "cost": 0, "co2": 0, "peak_demand": 0},
                "projected": {"energy": 0, "cost": 0, "co2": 0, "peak_demand": 0},
                "savings": {"energy": 0, "cost": 0, "co2": 0, "peak_demand": 0},
            }
        )

    baseline_energy = sum(r.energy_consumption_kwh for r in records)
    baseline_cost = sum(r.energy_consumption_kwh * r.electricity_tariff for r in records)
    baseline_co2 = sum(r.co2_emission_kg for r in records)
    baseline_peak = max(r.peak_demand_kw for r in records)

    hvac_total = sum(r.hvac_energy_kwh for r in records)
    lighting_total = sum(r.lighting_energy_kwh for r in records)
    equipment_total = sum(r.equipment_energy_kwh for r in records)

    hvac_saved = hvac_total * (hvac_reduction_percent / 100)
    lighting_saved = lighting_total * (lighting_reduction_percent / 100)
    equipment_saved = equipment_total * (equipment_reduction_percent / 100)

    # Occupancy increase may increase HVAC slightly
    occ_factor = 1 + (occupancy_change_percent / 100) * 0.15
    direct_savings = hvac_saved + lighting_saved + equipment_saved
    occupancy_penalty = max(0, (occupancy_change_percent / 100) * hvac_total * 0.3) if occupancy_change_percent > 0 else 0

    projected_energy = baseline_energy - direct_savings + occupancy_penalty
    projected_energy *= occ_factor if occupancy_change_percent != 0 else 1
    projected_energy = max(projected_energy, baseline_energy * 0.5)

    cost_ratio = projected_energy / baseline_energy if baseline_energy else 1
    projected_cost = baseline_cost * cost_ratio
    projected_co2 = baseline_co2 * cost_ratio

    peak_reduction_factor = 1.0
    if peak_shift:
        peak_reduction_factor = 0.92
    peak_component_saving = baseline_peak * (
        (hvac_reduction_percent + equipment_reduction_percent) / 200
    )
    if peak_shift:
        peak_component_saving += baseline_peak * 0.05
    projected_peak = max(baseline_peak - peak_component_saving, baseline_peak * 0.7) * peak_reduction_factor

    return json_safe(
        {
            "success": True,
            "campus_id": campus_id,
            "baseline": {
                "energy": round(baseline_energy, 2),
                "cost": round(baseline_cost, 2),
                "co2": round(baseline_co2, 2),
                "peak_demand": round(baseline_peak, 2),
            },
            "projected": {
                "energy": round(projected_energy, 2),
                "cost": round(projected_cost, 2),
                "co2": round(projected_co2, 2),
                "peak_demand": round(projected_peak, 2),
            },
            "savings": {
                "energy": round(baseline_energy - projected_energy, 2),
                "cost": round(baseline_cost - projected_cost, 2),
                "co2": round(baseline_co2 - projected_co2, 2),
                "peak_demand": round(baseline_peak - projected_peak, 2),
            },
        }
    )
