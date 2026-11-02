"""Energy optimization opportunity analysis."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.services.analytics_service import calculate_campus_analytics, get_building_analytics
from app.utils.data_cleaning import json_safe


def calculate_optimization_opportunities(db: Session, campus_id: str) -> dict[str, Any]:
    """Identify energy-saving opportunities from campus data."""
    kpis = calculate_campus_analytics(db, campus_id)
    buildings = get_building_analytics(db, campus_id)

    if kpis["record_count"] == 0:
        return json_safe(
            {
                "success": False,
                "message": "No data available for optimization analysis",
                "current_energy": 0,
                "optimized_energy": 0,
                "energy_saved": 0,
                "cost_saved": 0,
                "co2_saved": 0,
                "peak_reduction": 0,
                "opportunities": [],
            }
        )

    current_energy = kpis["total_energy_kwh"]
    current_cost = kpis["total_cost"]
    current_co2 = kpis["total_co2"]
    current_peak = kpis["peak_demand_kw"]

    # Opportunity weights based on actual breakdown
    hvac_saving_pct = min(20, max(5, (kpis["hvac_percentage"] - 35) * 0.4))
    lighting_saving_pct = min(15, max(3, (kpis["lighting_percentage"] - 15) * 0.5))
    equipment_saving_pct = min(12, max(2, (kpis["equipment_percentage"] - 20) * 0.4))
    peak_saving_pct = 8 if current_peak > kpis["average_energy_kwh"] * 1.5 else 4

    total_saving_pct = hvac_saving_pct + lighting_saving_pct + equipment_saving_pct + peak_saving_pct
    total_saving_pct = min(total_saving_pct, 35)

    energy_saved = current_energy * (total_saving_pct / 100)
    optimized_energy = current_energy - energy_saved
    cost_saved = current_cost * (total_saving_pct / 100)
    co2_saved = current_co2 * (total_saving_pct / 100)
    peak_reduction = current_peak * (peak_saving_pct / 100)

    opportunities = []
    if hvac_saving_pct > 3:
        opportunities.append(
            {
                "category": "HVAC reduction",
                "potential_saving_pct": round(hvac_saving_pct, 1),
                "energy_kwh": round(current_energy * hvac_saving_pct / 100, 2),
                "description": f"HVAC accounts for {kpis['hvac_percentage']:.1f}% of total energy",
            }
        )
    if lighting_saving_pct > 2:
        opportunities.append(
            {
                "category": "Lighting reduction",
                "potential_saving_pct": round(lighting_saving_pct, 1),
                "energy_kwh": round(current_energy * lighting_saving_pct / 100, 2),
                "description": "Optimize lighting schedules based on occupancy patterns",
            }
        )
    if equipment_saving_pct > 2:
        opportunities.append(
            {
                "category": "Equipment optimization",
                "potential_saving_pct": round(equipment_saving_pct, 1),
                "energy_kwh": round(current_energy * equipment_saving_pct / 100, 2),
                "description": "Reduce idle equipment loads during off-peak hours",
            }
        )

    # Building-specific opportunities
    for b in buildings[:3]:
        if b["anomaly_count"] > 0:
            opportunities.append(
                {
                    "category": f"Building: {b['building_name']}",
                    "potential_saving_pct": round(min(10, b["anomaly_count"] * 2), 1),
                    "energy_kwh": round(b["total_energy"] * 0.08, 2),
                    "description": f"{b['anomaly_count']} anomalies detected; efficiency score {b['efficiency_score']}",
                }
            )

    return json_safe(
        {
            "success": True,
            "campus_id": campus_id,
            "current_energy": round(current_energy, 2),
            "optimized_energy": round(optimized_energy, 2),
            "energy_saved": round(energy_saved, 2),
            "cost_saved": round(cost_saved, 2),
            "co2_saved": round(co2_saved, 2),
            "peak_reduction": round(peak_reduction, 2),
            "opportunities": opportunities,
        }
    )
