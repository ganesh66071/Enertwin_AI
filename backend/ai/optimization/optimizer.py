"""Energy optimization engine with scenario comparison."""

from __future__ import annotations

from typing import Any


def calculate_scenario(baseline_energy: float, baseline_peak: float, tariff: float = 8.2, emission_factor: float = 0.68, hvac_reduction: float = 0.0, lighting_reduction: float = 0.0, equipment_reduction: float = 0.0) -> dict[str, Any]:
    """Calculate projected metrics for a weighted reduction scenario."""
    weighted_reduction = min(0.45, max(0.0, hvac_reduction * 0.45 + lighting_reduction * 0.35 + equipment_reduction * 0.20))
    new_energy = baseline_energy * (1 - weighted_reduction)
    energy_saved = baseline_energy - new_energy
    cost_saved = energy_saved * tariff
    co2_saved = energy_saved * emission_factor
    peak_demand_reduction = baseline_peak * min(0.35, weighted_reduction * 0.8)
    roi = (cost_saved / max(baseline_energy * tariff, 1.0)) * 100.0
    return {
        "new_energy": round(float(new_energy), 2),
        "energy_saved": round(float(energy_saved), 2),
        "cost_saved": round(float(cost_saved), 2),
        "co2_saved": round(float(co2_saved), 2),
        "peak_demand_reduction": round(float(peak_demand_reduction), 2),
        "roi": round(float(roi), 2),
        "weighted_reduction": round(float(weighted_reduction), 4),
    }


def generate_scenarios(baseline_energy: float, baseline_peak: float, tariff: float = 8.2, emission_factor: float = 0.68) -> list[dict[str, Any]]:
    """Generate candidate optimization strategies based on campus usage profile."""
    scenarios = [
        {"name": "Scenario A", "hvac": 10, "lighting": 8, "equipment": 4},
        {"name": "Scenario B", "hvac": 15, "lighting": 10, "equipment": 5},
        {"name": "Scenario C", "hvac": 20, "lighting": 12, "equipment": 7},
    ]
    results = []
    for scenario in scenarios:
        metrics = calculate_scenario(
            baseline_energy=baseline_energy,
            baseline_peak=baseline_peak,
            tariff=tariff,
            emission_factor=emission_factor,
            hvac_reduction=scenario["hvac"] / 100.0,
            lighting_reduction=scenario["lighting"] / 100.0,
            equipment_reduction=scenario["equipment"] / 100.0,
        )
        metrics["scenario"] = scenario["name"]
        metrics["hvac_reduction_pct"] = scenario["hvac"]
        metrics["lighting_reduction_pct"] = scenario["lighting"]
        metrics["equipment_reduction_pct"] = scenario["equipment"]
        results.append(metrics)
    return results


def choose_best_scenario(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    """Choose the scenario with the best balanced ROI and savings profile."""
    if not scenarios:
        return {"recommended_action": "No feasible scenario", "expected_savings": 0, "expected_cost_savings": 0, "expected_co2_reduction": 0, "roi": 0}
    best = max(scenarios, key=lambda item: item["energy_saved"] * 0.55 + item["cost_saved"] * 0.3 + item["co2_saved"] * 0.15 - max(0, item["weighted_reduction"]) * 20)
    return {
        "recommended_action": best["scenario"],
        "expected_savings": round(float(best["energy_saved"]), 2),
        "expected_cost_savings": round(float(best["cost_saved"]), 2),
        "expected_co2_reduction": round(float(best["co2_saved"]), 2),
        "roi": round(float(best["roi"]), 2),
    }
