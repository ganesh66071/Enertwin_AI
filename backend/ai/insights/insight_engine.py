"""Convert raw analytics into structured AI insights."""

from __future__ import annotations

from typing import Any


def build_insights(campus_name: str, kpis: dict[str, Any], anomalies: dict[str, Any], forecast: dict[str, Any], optimization: dict[str, Any]) -> dict[str, Any]:
    findings = []
    if kpis.get("hvac_percentage", 0) > 0:
        findings.append(f"HVAC contributes {kpis.get('hvac_percentage', 0):.1f}% of campus energy consumption.")
    if forecast.get("predicted_peak"):
        findings.append(f"Peak demand is expected at {forecast.get('peak_time', 'a future period')}.")
    if anomalies.get("anomalies"):
        top = anomalies["anomalies"][0]
        findings.append(f"{top['building']} has the highest anomaly severity with a {top['deviation_percentage']}% deviation from expected energy.")
    if optimization.get("expected_savings"):
        findings.append(f"The current optimization scenario can save {optimization.get('expected_savings', 0):.0f} kWh across the campus.")
    return {
        "campus": campus_name,
        "key_findings": findings,
        "anomalies": anomalies,
        "forecast": forecast,
        "optimization": optimization,
    }
