"""Campus-specific anomaly analysis helpers."""

from __future__ import annotations

from typing import Any


def summarize_root_cause(values: dict[str, Any]) -> str:
    energy_increase = float(values.get("energy_increase", 0.0))
    hvac_increase = float(values.get("hvac_increase", 0.0))
    lighting_increase = float(values.get("lighting_increase", 0.0))
    equipment_increase = float(values.get("equipment_increase", 0.0))
    occupancy_drop = float(values.get("occupancy_drop", 0.0))

    if hvac_increase > lighting_increase and hvac_increase > equipment_increase and occupancy_drop > 0:
        return (
            "HVAC consumption increased significantly while occupancy decreased, indicating "
            "inefficient HVAC operation during low-occupancy periods."
        )
    if equipment_increase > hvac_increase and equipment_increase > lighting_increase:
        return "Equipment load is the dominant contributor to the observed energy anomaly."
    if lighting_increase > hvac_increase and lighting_increase > equipment_increase:
        return "Lighting demand is materially above baseline and is contributing to the campus energy spike."
    return "The campus anomaly is driven by a combination of load growth and schedule inefficiency."
