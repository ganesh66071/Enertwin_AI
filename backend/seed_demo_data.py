"""
Seed demo data for three campuses with distinct energy profiles.

Usage:
    python seed_demo_data.py
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta

from app.core.database import SessionLocal, init_db
from app.models.campus import Campus
from app.models.energy_record import EnergyRecord
from app.utils.calculations import (
    derive_co2,
    derive_peak_demand_kwh,
    deterministic_seed,
    estimate_equipment_energy,
    estimate_hvac_energy,
    estimate_lighting_energy,
    pseudo_random,
)

DEMO_CAMPUSES = [
    {
        "id": "viit",
        "name": "VIIT",
        "location": "Visakhapatnam",
        "campus_type": "Engineering / Technology Campus",
        "description": "Engineering campus with computer labs and high daytime equipment load",
        "buildings": [
            "CSE Block", "AI & DS Block", "ECE Block", "Mechanical Block",
            "Central Library", "Administration Block", "Computer Center", "Auditorium",
        ],
        "base_energy": 118,
        "pattern": "academic",
    },
    {
        "id": "vignan-university",
        "name": "Vignan University",
        "location": "Guntur",
        "campus_type": "Large University Campus",
        "description": "Large university with academic blocks and evening hostel consumption",
        "buildings": [
            "Academic Block", "Engineering Block", "Science Block", "Library",
            "Administration", "Research Center", "Student Center", "Hostel Blocks",
            "Auditorium", "Sports Complex",
        ],
        "base_energy": 142,
        "pattern": "university",
    },
    {
        "id": "mvv-mk-park",
        "name": "MVV & MK Park",
        "location": "Gated Residential Community",
        "campus_type": "Smart Gated Residential Community",
        "description": "Residential towers with morning/evening peaks and EV charging",
        "buildings": [
            "Tower A", "Tower B", "Tower C", "Tower D", "Clubhouse",
            "Swimming Pool", "Gym", "Security Block", "Parking Area", "EV Charging Zone",
        ],
        "base_energy": 52,
        "pattern": "residential",
    },
]


def _pattern_factor(pattern: str, hour: int, building_index: int, building_name: str) -> float:
    if pattern == "academic":
        if 8 <= hour <= 17:
            bonus = 0.45 if "Computer" in building_name else 0
            return 1.5 + bonus + math.sin(hour) * 0.12
        if 18 <= hour <= 21:
            return 0.65
        return 0.25
    if pattern == "university":
        if 8 <= hour <= 16:
            return 1.45
        if 18 <= hour <= 23:
            return 1.45 if "Hostel" in building_name else 0.82
        return 0.42
    # residential
    if 6 <= hour <= 9:
        return 1.28
    if 18 <= hour <= 22:
        return 1.85 if "EV" in building_name else 1.55
    if hour >= 23 or hour < 5:
        return 0.56
    return 0.82


def _inject_anomaly(energy: float, campus_id: str, building: str, hour: int) -> float:
    """Inject deterministic anomalies for demo."""
    if campus_id == "viit" and building == "Computer Center" and 14 <= hour <= 16:
        return energy * 1.34
    if campus_id == "vignan-university" and building == "Hostel Blocks" and 20 <= hour <= 23:
        return energy * 1.28
    if campus_id == "mvv-mk-park" and building == "EV Charging Zone" and 18 <= hour <= 21:
        return energy * 1.42
    return energy


def generate_records(campus_cfg: dict, days: int = 30) -> list[EnergyRecord]:
    records = []
    campus_id = campus_cfg["id"]
    base = campus_cfg["base_energy"]
    pattern = campus_cfg["pattern"]
    start = datetime(2026, 7, 1, 0, 0, 0)

    for day in range(days):
        for hour in range(24):
            for idx, building in enumerate(campus_cfg["buildings"]):
                ts = start + timedelta(days=day, hours=hour)
                seed = deterministic_seed(campus_id, building)
                factor = _pattern_factor(pattern, hour, idx, building)
                energy = round(base * (1 + idx * 0.035) * factor, 2)
                energy = _inject_anomaly(energy, campus_id, building, hour)

                occ_base = 22 + (48 if 8 <= hour <= 17 else 28 if 18 <= hour <= 22 else 8)
                occ_pct = max(8, min(96, occ_base + idx * 1.5))
                outdoor = round(24 + math.sin(hour / 3) * 4 + pseudo_random(seed, day, -2, 2), 1)
                indoor = 24.0

                hvac = estimate_hvac_energy(energy, occ_pct, outdoor, indoor, hour, seed)
                lighting = estimate_lighting_energy(energy, occ_pct, hour, seed)
                equipment = estimate_equipment_energy(energy, building, occ_pct, hour, seed)

                records.append(
                    EnergyRecord(
                        campus_id=campus_id,
                        timestamp=ts,
                        building_name=building,
                        floor=str((idx % 4) + 1),
                        zone="Main",
                        energy_consumption_kwh=energy,
                        hvac_energy_kwh=hvac,
                        lighting_energy_kwh=lighting,
                        equipment_energy_kwh=equipment,
                        peak_demand_kw=derive_peak_demand_kwh(energy),
                        occupancy_count=int(occ_pct * pseudo_random(seed, hour, 1.5, 3.5)),
                        occupancy_percent=occ_pct,
                        indoor_temperature_c=indoor,
                        outdoor_temperature_c=outdoor,
                        humidity_percent=round(50 + pseudo_random(seed, day, -10, 10), 1),
                        hvac_runtime_hours=round(max(0, hour % 12) * pseudo_random(seed, hour, 0.8, 1.2), 2),
                        hvac_setpoint_c=24.0,
                        equipment_runtime_hours=round(max(0, hour % 10) * pseudo_random(seed, hour + 50, 0.7, 1.1), 2),
                        electricity_tariff=8.2,
                        co2_emission_kg=derive_co2(energy),
                        data_source="dataset",
                    )
                )
    return records


def seed():
    init_db()
    db = SessionLocal()
    try:
        for cfg in DEMO_CAMPUSES:
            existing = db.query(Campus).filter(Campus.id == cfg["id"]).first()
            if existing:
                db.query(EnergyRecord).filter(EnergyRecord.campus_id == cfg["id"]).delete()
                db.delete(existing)
                db.commit()

            campus = Campus(
                id=cfg["id"],
                name=cfg["name"],
                location=cfg["location"],
                campus_type=cfg["campus_type"],
                description=cfg["description"],
            )
            db.add(campus)
            db.flush()

            records = generate_records(cfg, days=30)
            db.add_all(records)
            db.commit()
            print(f"Seeded {cfg['name']}: {len(records)} records")

        print("\nDemo data seeding complete!")
        print("Campus IDs: viit, vignan-university, mvv-mk-park")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
