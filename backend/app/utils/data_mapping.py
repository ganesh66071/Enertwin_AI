"""
Centralized column name mapping for uploaded datasets.

All column normalization logic lives here — do not scatter elsewhere.
"""

from __future__ import annotations

import re
from typing import Optional

# Canonical field -> list of acceptable source column patterns (lowercase)
COLUMN_ALIASES: dict[str, list[str]] = {
    "timestamp": [
        "timestamp", "datetime", "date_time", "date time", "recorded_at",
        "recordedat", "time", "date", "reading_time", "meter_reading_time",
    ],
    "building_name": [
        "building", "building_name", "building name", "block", "facility",
        "site", "location_name", "premises",
    ],
    "floor": ["floor", "level", "storey", "story"],
    "zone": ["zone", "area", "section", "wing", "department"],
    "energy_consumption_kwh": [
        "energy_consumption_kwh", "energy consumption", "energy_consumption",
        "energy_kwh", "energy", "total_energy", "total energy", "kwh",
        "consumption", "energy consumption kwh", "energy_consumption_kwh",
    ],
    "hvac_energy_kwh": [
        "hvac_energy_kwh", "hvac", "hvac energy", "hvac_kwh", "hvac consumption",
        "cooling", "heating", "air_conditioning", "ac_energy",
    ],
    "lighting_energy_kwh": [
        "lighting_energy_kwh", "lighting", "lighting energy", "lighting_kwh",
        "lights", "illumination",
    ],
    "equipment_energy_kwh": [
        "equipment_energy_kwh", "equipment", "equipment energy", "equipment_kwh",
        "plug_load", "machinery", "it_load", "server",
    ],
    "peak_demand_kw": [
        "peak_demand_kw", "peak demand", "peak_demand", "demand_kw", "max_demand",
        "peak_kw", "demand",
    ],
    "occupancy_count": [
        "occupancy_count", "occupancy count", "occupants", "people_count",
        "headcount", "person_count",
    ],
    "occupancy_percent": [
        "occupancy_percent", "occupancy percent", "occupancy", "occupancy_pct",
        "occupancy_rate", "utilization",
    ],
    "indoor_temperature_c": [
        "indoor_temperature_c", "indoor temperature", "indoor_temp",
        "temperature", "temp", "inside_temp", "room_temperature",
    ],
    "outdoor_temperature_c": [
        "outdoor_temperature_c", "outdoor temperature", "outdoor_temp",
        "ambient_temp", "outside_temp", "external_temperature",
    ],
    "humidity_percent": [
        "humidity_percent", "humidity", "relative_humidity", "rh",
    ],
    "hvac_runtime_hours": [
        "hvac_runtime_hours", "hvac runtime", "hvac_hours", "ac_runtime",
        "cooling_hours",
    ],
    "hvac_setpoint_c": [
        "hvac_setpoint_c", "hvac setpoint", "setpoint", "thermostat",
        "target_temperature",
    ],
    "equipment_runtime_hours": [
        "equipment_runtime_hours", "equipment runtime", "equipment_hours",
        "runtime_hours",
    ],
    "electricity_tariff": [
        "electricity_tariff", "tariff", "rate", "unit_rate", "price_per_kwh",
        "energy_rate", "cost_per_kwh",
    ],
    "co2_emission_kg": [
        "co2_emission_kg", "co2", "carbon", "carbon_kg", "carbonkg",
        "emissions", "co2_kg", "carbon_emission",
    ],
}


def _normalize_header(name: str) -> str:
    """Normalize a column header for matching."""
    s = str(name).strip().lower()
    s = re.sub(r"[\s\-/]+", "_", s)
    s = re.sub(r"[^a-z0-9_%]", "", s.replace("%", "percent"))
    s = re.sub(r"_+", "_", s).strip("_")
    return s


def _alias_lookup() -> dict[str, str]:
    """Build normalized alias -> canonical field map."""
    lookup: dict[str, str] = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        lookup[_normalize_header(canonical)] = canonical
        for alias in aliases:
            lookup[_normalize_header(alias)] = canonical
    return lookup


_ALIAS_LOOKUP = _alias_lookup()


def map_columns(raw_columns: list[str]) -> dict[str, str]:
    """
    Map raw DataFrame columns to canonical field names.

    Returns dict: canonical_field -> original_column_name
    """
    mapped: dict[str, str] = {}
    used_originals: set[str] = set()

    for col in raw_columns:
        norm = _normalize_header(col)
        canonical = _ALIAS_LOOKUP.get(norm)
        if canonical and canonical not in mapped:
            mapped[canonical] = col
            used_originals.add(col)

    # Fuzzy partial match for remaining columns
    for col in raw_columns:
        if col in used_originals:
            continue
        norm = _normalize_header(col)
        for alias_norm, canonical in _ALIAS_LOOKUP.items():
            if canonical in mapped:
                continue
            if alias_norm in norm or norm in alias_norm:
                mapped[canonical] = col
                used_originals.add(col)
                break

    return mapped


def get_required_fields() -> list[str]:
    return ["timestamp", "building_name", "energy_consumption_kwh"]


def validate_mapped_columns(mapped: dict[str, str]) -> list[str]:
    """Return list of missing required canonical fields."""
    missing = []
    for field in get_required_fields():
        if field not in mapped:
            missing.append(field)
    return missing
