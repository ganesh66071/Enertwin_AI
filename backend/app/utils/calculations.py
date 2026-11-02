"""Energy and efficiency calculation utilities."""

from __future__ import annotations

import hashlib
import math
from datetime import datetime
from typing import Optional

from app.core.config import get_settings

settings = get_settings()


def deterministic_seed(*parts: str) -> int:
    """Generate deterministic integer seed from string parts."""
    raw = "|".join(str(p) for p in parts)
    return int(hashlib.md5(raw.encode()).hexdigest()[:8], 16)


def pseudo_random(seed: int, index: int, low: float = 0.0, high: float = 1.0) -> float:
    """Deterministic pseudo-random in [low, high)."""
    h = hashlib.sha256(f"{seed}:{index}".encode()).hexdigest()
    val = int(h[:8], 16) / 0xFFFFFFFF
    return low + val * (high - low)


def derive_peak_demand_kwh(energy_kwh: float, interval_hours: float = 1.0) -> float:
    """Derive peak demand from energy and interval."""
    if interval_hours <= 0:
        interval_hours = 1.0
    return round(energy_kwh / interval_hours, 2)


def derive_co2(energy_kwh: float, factor: Optional[float] = None) -> float:
    factor = factor or settings.co2_emission_factor_kg_per_kwh
    return round(energy_kwh * factor, 4)


def derive_cost(energy_kwh: float, tariff: Optional[float] = None) -> float:
    tariff = tariff or settings.default_electricity_tariff
    return round(energy_kwh * tariff, 2)


def estimate_hvac_energy(
    total_kwh: float,
    occupancy_pct: float,
    outdoor_temp: float,
    indoor_temp: float,
    hour: int,
    seed: int,
) -> float:
    """Estimate HVAC share deterministically."""
    temp_delta = abs(outdoor_temp - indoor_temp)
    base_ratio = 0.25 + min(temp_delta / 20.0, 0.35)
    occ_factor = 0.5 + (occupancy_pct / 100.0) * 0.5
    hour_factor = 1.1 if 10 <= hour <= 16 else 0.85
    jitter = pseudo_random(seed, hour, 0.95, 1.05)
    hvac = total_kwh * base_ratio * occ_factor * hour_factor * jitter
    return round(min(hvac, total_kwh * 0.65), 4)


def estimate_lighting_energy(
    total_kwh: float,
    occupancy_pct: float,
    hour: int,
    seed: int,
) -> float:
    """Estimate lighting share deterministically."""
    if 6 <= hour <= 20:
        light_ratio = 0.12 + (occupancy_pct / 100.0) * 0.18
    else:
        light_ratio = 0.04 + (occupancy_pct / 100.0) * 0.06
    jitter = pseudo_random(seed, hour + 100, 0.92, 1.08)
    lighting = total_kwh * light_ratio * jitter
    return round(min(lighting, total_kwh * 0.35), 4)


def estimate_equipment_energy(
    total_kwh: float,
    building_name: str,
    occupancy_pct: float,
    hour: int,
    seed: int,
) -> float:
    """Estimate equipment share deterministically."""
    building_lower = building_name.lower()
    if any(k in building_lower for k in ["computer", "lab", "server", "engineering", "ev"]):
        base_ratio = 0.35
    elif any(k in building_lower for k in ["hostel", "residence", "tower"]):
        base_ratio = 0.22
    else:
        base_ratio = 0.18

    if 8 <= hour <= 18:
        hour_factor = 1.15
    else:
        hour_factor = 0.75

    occ_factor = 0.6 + (occupancy_pct / 100.0) * 0.4
    jitter = pseudo_random(seed, hour + 200, 0.9, 1.1)
    equipment = total_kwh * base_ratio * hour_factor * occ_factor * jitter
    return round(min(equipment, total_kwh * 0.55), 4)


def estimate_occupancy_profile(
    building_name: str,
    campus_type: str,
    hour: int,
    day_of_week: int,
    seed: int,
) -> tuple[int, float]:
    """Deterministic occupancy estimate from building type and time."""
    building_lower = building_name.lower()
    campus_lower = campus_type.lower()

    if "hostel" in building_lower or "residential" in campus_lower or "tower" in building_lower:
        if 18 <= hour <= 23:
            base_pct = 78
        elif 0 <= hour <= 5:
            base_pct = 55
        else:
            base_pct = 35
    elif "computer" in building_lower or "lab" in building_lower:
        base_pct = 72 if 9 <= hour <= 17 else 18
    elif "ev" in building_lower:
        base_pct = 40 if 17 <= hour <= 21 else 12
    else:
        if 8 <= hour <= 17 and day_of_week < 5:
            base_pct = 68
        elif 18 <= hour <= 21:
            base_pct = 42
        else:
            base_pct = 15

    jitter = pseudo_random(seed, hour + day_of_week, -5, 5)
    pct = max(5.0, min(98.0, base_pct + jitter))
    count = int(pct * pseudo_random(seed, hour, 1.5, 3.5))
    return count, round(pct, 2)


def compute_efficiency_score(
    energy_kwh: float,
    occupancy_pct: float,
    hvac_pct: float,
    peak_demand: float,
) -> float:
    """Score 0-100; higher is better."""
    if energy_kwh <= 0:
        return 50.0
    intensity = energy_kwh / max(occupancy_pct, 1.0)
    hvac_penalty = max(0, hvac_pct - 45) * 0.5
    peak_penalty = min(peak_demand / max(energy_kwh, 1), 2) * 5
    score = 100 - intensity * 0.15 - hvac_penalty - peak_penalty
    return round(max(10.0, min(98.0, score)), 2)


def energy_intensity(total_energy: float, record_count: int, building_count: int) -> float:
    if record_count == 0 or building_count == 0:
        return 0.0
    return round(total_energy / (record_count * building_count), 4)
