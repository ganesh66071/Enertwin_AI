"""Optimization scenario and score helpers."""

from __future__ import annotations

from typing import Any


def optimization_score(energy_saving_score: float, cost_saving_score: float, carbon_score: float, comfort_penalty: float, weights: dict[str, float] | None = None) -> float:
    weights = weights or {"energy_weight": 0.4, "cost_weight": 0.3, "carbon_weight": 0.2, "comfort_weight": 0.1}
    return (
        energy_saving_score * weights.get("energy_weight", 0.4)
        + cost_saving_score * weights.get("cost_weight", 0.3)
        + carbon_score * weights.get("carbon_weight", 0.2)
        - comfort_penalty * weights.get("comfort_weight", 0.1)
    )


def build_scenario_summary(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "optimization_score": round(float(optimization_score(metrics.get("energy_score", 0), metrics.get("cost_score", 0), metrics.get("carbon_score", 0), metrics.get("comfort_penalty", 0))), 2),
        "energy_saved": metrics.get("energy_saved", 0),
        "cost_saved": metrics.get("cost_saved", 0),
        "co2_saved": metrics.get("co2_saved", 0),
        "peak_reduction": metrics.get("peak_reduction", 0),
    }
