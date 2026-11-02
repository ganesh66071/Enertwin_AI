"""Static demo campus data used for hackathon-ready campus switching."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

_STATIC_CAMPUS_DATA: dict[str, dict[str, Any]] = {
    "CAMP001": {
        "id": "CAMP001",
        "name": "Vignan University",
        "location": "Vadlamudi, Guntur",
        "campus_type": "University Campus",
        "description": "Large multi-disciplinary campus with high academic, hostel, and sports loads.",
        "created_at": datetime.now(timezone.utc),
        "kpis": {
            "total_energy_kwh": 1465000.0,
            "average_energy_kwh": 18500.0,
            "minimum_energy_kwh": 4800.0,
            "maximum_energy_kwh": 34200.0,
            "peak_demand_kw": 1380.0,
            "average_occupancy": 72.4,
            "hvac_energy_kwh": 431000.0,
            "lighting_energy_kwh": 208000.0,
            "equipment_energy_kwh": 342000.0,
            "hvac_percentage": 29.4,
            "lighting_percentage": 14.2,
            "equipment_percentage": 23.3,
            "other_percentage": 33.1,
            "total_cost": 1201000.0,
            "total_co2": 996200.0,
            "energy_intensity": 292.0,
            "efficiency_score": 87,
            "record_count": 720,
        },
        "energy_breakdown": {
            "hvac": 431000.0,
            "lighting": 208000.0,
            "equipment": 342000.0,
            "other": 480000.0,
        },
        "building_summary": [
            {"building_name": "Academic Block", "total_energy": 328000.0, "average_energy": 18200.0, "peak_demand": 420.0, "occupancy": 78.0, "hvac": 112000.0, "lighting": 47000.0, "equipment": 88000.0, "co2": 222000.0, "anomaly_count": 2, "efficiency_score": 88},
            {"building_name": "Engineering Block", "total_energy": 294000.0, "average_energy": 16800.0, "peak_demand": 390.0, "occupancy": 74.0, "hvac": 98000.0, "lighting": 42000.0, "equipment": 76000.0, "co2": 199000.0, "anomaly_count": 1, "efficiency_score": 84},
            {"building_name": "Research Center", "total_energy": 236000.0, "average_energy": 14500.0, "peak_demand": 310.0, "occupancy": 68.0, "hvac": 76000.0, "lighting": 32000.0, "equipment": 79000.0, "co2": 160000.0, "anomaly_count": 1, "efficiency_score": 82},
            {"building_name": "Hostel Blocks", "total_energy": 286000.0, "average_energy": 17800.0, "peak_demand": 360.0, "occupancy": 81.0, "hvac": 104000.0, "lighting": 36000.0, "equipment": 54000.0, "co2": 194000.0, "anomaly_count": 3, "efficiency_score": 78},
            {"building_name": "Sports Complex", "total_energy": 194000.0, "average_energy": 12100.0, "peak_demand": 260.0, "occupancy": 59.0, "hvac": 51000.0, "lighting": 31000.0, "equipment": 71000.0, "co2": 132000.0, "anomaly_count": 1, "efficiency_score": 80},
        ],
        "energy_trend": [
            {"timestamp": "2026-08-01T00:00:00+05:30", "energy_kwh": 24600},
            {"timestamp": "2026-08-02T00:00:00+05:30", "energy_kwh": 25200},
            {"timestamp": "2026-08-03T00:00:00+05:30", "energy_kwh": 27100},
            {"timestamp": "2026-08-04T00:00:00+05:30", "energy_kwh": 28900},
            {"timestamp": "2026-08-05T00:00:00+05:30", "energy_kwh": 30550},
            {"timestamp": "2026-08-06T00:00:00+05:30", "energy_kwh": 31000},
            {"timestamp": "2026-08-07T00:00:00+05:30", "energy_kwh": 32500},
        ],
    },
    "CAMP002": {
        "id": "CAMP002",
        "name": "VIIT",
        "location": "Visakhapatnam",
        "campus_type": "Engineering Campus",
        "description": "Technology-first campus with heavy computing and academic block loads.",
        "created_at": datetime.now(timezone.utc),
        "kpis": {
            "total_energy_kwh": 1128000.0,
            "average_energy_kwh": 14950.0,
            "minimum_energy_kwh": 4100.0,
            "maximum_energy_kwh": 26700.0,
            "peak_demand_kw": 980.0,
            "average_occupancy": 68.1,
            "hvac_energy_kwh": 295000.0,
            "lighting_energy_kwh": 182000.0,
            "equipment_energy_kwh": 358000.0,
            "hvac_percentage": 26.1,
            "lighting_percentage": 16.1,
            "equipment_percentage": 31.7,
            "other_percentage": 26.1,
            "total_cost": 924000.0,
            "total_co2": 767000.0,
            "energy_intensity": 264.0,
            "efficiency_score": 90,
            "record_count": 640,
        },
        "energy_breakdown": {
            "hvac": 295000.0,
            "lighting": 182000.0,
            "equipment": 358000.0,
            "other": 298000.0,
        },
        "building_summary": [
            {"building_name": "CSE Block", "total_energy": 264000.0, "average_energy": 15600.0, "peak_demand": 340.0, "occupancy": 74.0, "hvac": 62000.0, "lighting": 38000.0, "equipment": 125000.0, "co2": 180000.0, "anomaly_count": 2, "efficiency_score": 89},
            {"building_name": "AI & DS Block", "total_energy": 242000.0, "average_energy": 14700.0, "peak_demand": 330.0, "occupancy": 71.0, "hvac": 59000.0, "lighting": 34000.0, "equipment": 113000.0, "co2": 164000.0, "anomaly_count": 1, "efficiency_score": 88},
            {"building_name": "ECE Block", "total_energy": 214000.0, "average_energy": 13950.0, "peak_demand": 290.0, "occupancy": 69.0, "hvac": 53000.0, "lighting": 30000.0, "equipment": 89000.0, "co2": 145000.0, "anomaly_count": 1, "efficiency_score": 86},
            {"building_name": "Central Library", "total_energy": 186000.0, "average_energy": 11700.0, "peak_demand": 240.0, "occupancy": 67.0, "hvac": 48000.0, "lighting": 34000.0, "equipment": 72000.0, "co2": 126000.0, "anomaly_count": 1, "efficiency_score": 85},
            {"building_name": "Computer Center", "total_energy": 208000.0, "average_energy": 12500.0, "peak_demand": 280.0, "occupancy": 61.0, "hvac": 47000.0, "lighting": 27000.0, "equipment": 104000.0, "co2": 141000.0, "anomaly_count": 3, "efficiency_score": 80},
        ],
        "energy_trend": [
            {"timestamp": "2026-08-01T00:00:00+05:30", "energy_kwh": 21300},
            {"timestamp": "2026-08-02T00:00:00+05:30", "energy_kwh": 21900},
            {"timestamp": "2026-08-03T00:00:00+05:30", "energy_kwh": 22400},
            {"timestamp": "2026-08-04T00:00:00+05:30", "energy_kwh": 24300},
            {"timestamp": "2026-08-05T00:00:00+05:30", "energy_kwh": 26600},
            {"timestamp": "2026-08-06T00:00:00+05:30", "energy_kwh": 25900},
            {"timestamp": "2026-08-07T00:00:00+05:30", "energy_kwh": 27100},
        ],
    },
    "CAMP003": {
        "id": "CAMP003",
        "name": "Vignan Pharma",
        "location": "Guntur, Andhra Pradesh",
        "campus_type": "Pharma Campus",
        "description": "Manufacturing and lab-intensive campus with process heating and cleanroom loads.",
        "created_at": datetime.now(timezone.utc),
        "kpis": {
            "total_energy_kwh": 983000.0,
            "average_energy_kwh": 13200.0,
            "minimum_energy_kwh": 3600.0,
            "maximum_energy_kwh": 23500.0,
            "peak_demand_kw": 1160.0,
            "average_occupancy": 63.4,
            "hvac_energy_kwh": 268000.0,
            "lighting_energy_kwh": 140000.0,
            "equipment_energy_kwh": 373000.0,
            "hvac_percentage": 27.3,
            "lighting_percentage": 14.2,
            "equipment_percentage": 37.9,
            "other_percentage": 20.6,
            "total_cost": 806000.0,
            "total_co2": 668000.0,
            "energy_intensity": 318.0,
            "efficiency_score": 84,
            "record_count": 560,
        },
        "energy_breakdown": {
            "hvac": 268000.0,
            "lighting": 140000.0,
            "equipment": 373000.0,
            "other": 202000.0,
        },
        "building_summary": [
            {"building_name": "Formulation Block", "total_energy": 244000.0, "average_energy": 14400.0, "peak_demand": 320.0, "occupancy": 66.0, "hvac": 60000.0, "lighting": 25000.0, "equipment": 111000.0, "co2": 166000.0, "anomaly_count": 2, "efficiency_score": 85},
            {"building_name": "Quality Control Lab", "total_energy": 212000.0, "average_energy": 13800.0, "peak_demand": 300.0, "occupancy": 62.0, "hvac": 52000.0, "lighting": 22000.0, "equipment": 98000.0, "co2": 144000.0, "anomaly_count": 1, "efficiency_score": 82},
            {"building_name": "Utilities Plant", "total_energy": 254000.0, "average_energy": 15200.0, "peak_demand": 360.0, "occupancy": 58.0, "hvac": 71000.0, "lighting": 28000.0, "equipment": 118000.0, "co2": 172000.0, "anomaly_count": 3, "efficiency_score": 79},
            {"building_name": "Warehouse & Cold Storage", "total_energy": 178000.0, "average_energy": 11900.0, "peak_demand": 240.0, "occupancy": 54.0, "hvac": 43000.0, "lighting": 20000.0, "equipment": 82000.0, "co2": 121000.0, "anomaly_count": 1, "efficiency_score": 81},
            {"building_name": "Research & Pilot Plant", "total_energy": 195000.0, "average_energy": 12800.0, "peak_demand": 290.0, "occupancy": 60.0, "hvac": 47000.0, "lighting": 23000.0, "equipment": 93000.0, "co2": 132000.0, "anomaly_count": 2, "efficiency_score": 80},
        ],
        "energy_trend": [
            {"timestamp": "2026-08-01T00:00:00+05:30", "energy_kwh": 18400},
            {"timestamp": "2026-08-02T00:00:00+05:30", "energy_kwh": 19100},
            {"timestamp": "2026-08-03T00:00:00+05:30", "energy_kwh": 19700},
            {"timestamp": "2026-08-04T00:00:00+05:30", "energy_kwh": 20800},
            {"timestamp": "2026-08-05T00:00:00+05:30", "energy_kwh": 21500},
            {"timestamp": "2026-08-06T00:00:00+05:30", "energy_kwh": 22200},
            {"timestamp": "2026-08-07T00:00:00+05:30", "energy_kwh": 23800},
        ],
    },
}


def get_static_demo_campuses() -> list[dict[str, Any]]:
    return [deepcopy(campus) for campus in _STATIC_CAMPUS_DATA.values()]


def get_static_demo_campus(campus_id: str) -> dict[str, Any] | None:
    campus = _STATIC_CAMPUS_DATA.get(campus_id)
    if campus is None:
        return None
    return deepcopy(campus)


def get_static_overview_payload(campus_id: str) -> dict[str, Any] | None:
    campus = get_static_demo_campus(campus_id)
    if campus is None:
        return None
    return {
        "success": True,
        "campus": {
            "id": campus["id"],
            "name": campus["name"],
            "location": campus["location"],
            "campus_type": campus["campus_type"],
            "description": campus["description"],
        },
        "kpis": campus["kpis"],
        "energy_breakdown": campus["energy_breakdown"],
        "building_summary": campus["building_summary"],
        "data_quality": {
            "total_records": campus["kpis"]["record_count"],
            "valid_records": campus["kpis"]["record_count"],
            "derived_records": 0,
            "duplicate_records_removed": 0,
            "completeness_score": 100.0,
        },
        "energy_trend": campus["energy_trend"],
    }
