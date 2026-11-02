"""Campus analytics engine — all queries scoped to campus_id."""

from __future__ import annotations

from typing import Any, Optional

import pandas as pd
from sqlalchemy.orm import Session

from app.models.campus import Campus
from app.models.energy_record import EnergyRecord
from app.services.dataset_service import get_campus_records
from app.utils.calculations import compute_efficiency_score, energy_intensity
from app.utils.data_cleaning import json_safe


def _get_campus_or_raise(db: Session, campus_id: str) -> Campus:
    campus = db.query(Campus).filter(Campus.id == campus_id).first()
    if not campus:
        raise ValueError("Campus not found")
    return campus


def calculate_campus_analytics(db: Session, campus_id: str) -> dict[str, Any]:
    """Calculate KPIs for a single campus."""
    records = get_campus_records(db, campus_id)
    if not records:
        return {
            "total_energy_kwh": 0,
            "average_energy_kwh": 0,
            "minimum_energy_kwh": 0,
            "maximum_energy_kwh": 0,
            "peak_demand_kw": 0,
            "average_occupancy": 0,
            "hvac_energy_kwh": 0,
            "lighting_energy_kwh": 0,
            "equipment_energy_kwh": 0,
            "hvac_percentage": 0,
            "lighting_percentage": 0,
            "equipment_percentage": 0,
            "other_percentage": 0,
            "total_cost": 0,
            "total_co2": 0,
            "energy_intensity": 0,
            "efficiency_score": 50,
            "record_count": 0,
        }

    energies = [r.energy_consumption_kwh for r in records]
    total_energy = sum(energies)
    hvac_total = sum(r.hvac_energy_kwh for r in records)
    lighting_total = sum(r.lighting_energy_kwh for r in records)
    equipment_total = sum(r.equipment_energy_kwh for r in records)
    total_cost = sum(r.energy_consumption_kwh * r.electricity_tariff for r in records)
    total_co2 = sum(r.co2_emission_kg for r in records)
    avg_occ = sum(r.occupancy_percent for r in records) / len(records)
    peak_demand = max(r.peak_demand_kw for r in records)

    hvac_pct = (hvac_total / total_energy * 100) if total_energy else 0
    light_pct = (lighting_total / total_energy * 100) if total_energy else 0
    equip_pct = (equipment_total / total_energy * 100) if total_energy else 0
    other_pct = max(0, 100 - hvac_pct - light_pct - equip_pct)

    buildings = {r.building_name for r in records}
    intensity = energy_intensity(total_energy, len(records), len(buildings))

    avg_energy = total_energy / len(records)
    efficiency = compute_efficiency_score(avg_energy, avg_occ, hvac_pct, peak_demand)

    return json_safe(
        {
            "total_energy_kwh": round(total_energy, 2),
            "average_energy_kwh": round(avg_energy, 2),
            "minimum_energy_kwh": round(min(energies), 2),
            "maximum_energy_kwh": round(max(energies), 2),
            "peak_demand_kw": round(peak_demand, 2),
            "average_occupancy": round(avg_occ, 2),
            "hvac_energy_kwh": round(hvac_total, 2),
            "lighting_energy_kwh": round(lighting_total, 2),
            "equipment_energy_kwh": round(equipment_total, 2),
            "hvac_percentage": round(hvac_pct, 2),
            "lighting_percentage": round(light_pct, 2),
            "equipment_percentage": round(equip_pct, 2),
            "other_percentage": round(other_pct, 2),
            "total_cost": round(total_cost, 2),
            "total_co2": round(total_co2, 2),
            "energy_intensity": intensity,
            "efficiency_score": efficiency,
            "record_count": len(records),
        }
    )


def get_energy_trend(
    db: Session,
    campus_id: str,
    aggregation: str = "daily",
) -> list[dict[str, Any]]:
    """Return time-series energy trend for campus."""
    records = get_campus_records(db, campus_id)
    if not records:
        return []

    rows = [{"timestamp": r.timestamp, "energy_kwh": r.energy_consumption_kwh} for r in records]
    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    freq_map = {
        "hourly": "h",
        "daily": "D",
        "weekly": "W",
        "monthly": "ME",
    }
    freq = freq_map.get(aggregation, "D")

    grouped = (
        df.groupby(pd.Grouper(key="timestamp", freq=freq))["energy_kwh"]
        .sum()
        .reset_index()
        .dropna()
    )

    return [
        {"timestamp": row["timestamp"].isoformat(), "energy_kwh": round(float(row["energy_kwh"]), 2)}
        for _, row in grouped.iterrows()
    ]


def get_building_analytics(db: Session, campus_id: str) -> list[dict[str, Any]]:
    """Group analytics by building for a campus."""
    records = get_campus_records(db, campus_id)
    if not records:
        return []

    from app.ml.anomaly_detector import detect_anomalies

    anomaly_report = detect_anomalies(records)
    anomaly_by_building: dict[str, int] = {}
    for a in anomaly_report.get("anomalies", []):
        b = a["building"]
        anomaly_by_building[b] = anomaly_by_building.get(b, 0) + 1

    by_building: dict[str, list[EnergyRecord]] = {}
    for r in records:
        by_building.setdefault(r.building_name, []).append(r)

    results = []
    for name, brecords in by_building.items():
        total = sum(r.energy_consumption_kwh for r in brecords)
        avg = total / len(brecords)
        hvac = sum(r.hvac_energy_kwh for r in brecords)
        lighting = sum(r.lighting_energy_kwh for r in brecords)
        equipment = sum(r.equipment_energy_kwh for r in brecords)
        co2 = sum(r.co2_emission_kg for r in brecords)
        occ = sum(r.occupancy_percent for r in brecords) / len(brecords)
        peak = max(r.peak_demand_kw for r in brecords)
        hvac_pct = (hvac / total * 100) if total else 0
        eff = compute_efficiency_score(avg, occ, hvac_pct, peak)

        results.append(
            json_safe(
                {
                    "building_name": name,
                    "total_energy": round(total, 2),
                    "average_energy": round(avg, 2),
                    "peak_demand": round(peak, 2),
                    "occupancy": round(occ, 2),
                    "hvac": round(hvac, 2),
                    "lighting": round(lighting, 2),
                    "equipment": round(equipment, 2),
                    "co2": round(co2, 2),
                    "anomaly_count": anomaly_by_building.get(name, 0),
                    "efficiency_score": eff,
                }
            )
        )

    results.sort(key=lambda x: x["total_energy"], reverse=True)
    return results


def get_campus_overview(db: Session, campus_id: str) -> dict[str, Any]:
    """Full overview payload for dashboard."""
    campus = _get_campus_or_raise(db, campus_id)
    kpis = calculate_campus_analytics(db, campus_id)
    records = get_campus_records(db, campus_id)

    derived_count = sum(1 for r in records if r.data_source == "derived")
    total = len(records)

    return json_safe(
        {
            "success": True,
            "campus": {
                "id": campus.id,
                "name": campus.name,
                "location": campus.location,
                "campus_type": campus.campus_type,
                "description": campus.description,
            },
            "kpis": kpis,
            "energy_breakdown": {
                "hvac": kpis["hvac_energy_kwh"],
                "lighting": kpis["lighting_energy_kwh"],
                "equipment": kpis["equipment_energy_kwh"],
                "other": round(kpis["total_energy_kwh"] - kpis["hvac_energy_kwh"] - kpis["lighting_energy_kwh"] - kpis["equipment_energy_kwh"], 2),
            },
            "building_summary": get_building_analytics(db, campus_id),
            "data_quality": {
                "total_records": total,
                "valid_records": total,
                "derived_records": derived_count,
                "duplicate_records_removed": 0,
                "completeness_score": round((1 - derived_count / max(total, 1)) * 100, 1),
            },
        }
    )
