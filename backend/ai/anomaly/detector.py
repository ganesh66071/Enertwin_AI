"""Isolation Forest + rolling baseline anomaly detector."""

from __future__ import annotations

from typing import Any, Iterable

import numpy as np
import pandas as pd

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
except Exception:  # pragma: no cover
    IsolationForest = None
    StandardScaler = None


def _severity_from_deviation(deviation_pct: float) -> str:
    abs_dev = abs(float(deviation_pct))
    if abs_dev >= 30:
        return "CRITICAL"
    if abs_dev >= 18:
        return "HIGH"
    if abs_dev >= 8:
        return "MEDIUM"
    return "LOW"


def detect_anomalies_for_campus(campus_id: str, records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Detect campus-specific anomalies based on real campus data."""
    items = list(records)
    if not items:
        return {"campus_id": campus_id, "total_records": 0, "anomalies_detected": 0, "critical": 0, "high": 0, "medium": 0, "low": 0, "anomalies": []}

    df = pd.DataFrame(items)
    df["timestamp"] = pd.to_datetime(df.get("timestamp"), errors="coerce")
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    if df.empty:
        return {"campus_id": campus_id, "total_records": 0, "anomalies_detected": 0, "critical": 0, "high": 0, "medium": 0, "low": 0, "anomalies": []}

    energy = df.get("energy_consumption_kwh", pd.Series([0.0] * len(df)))
    energy = pd.to_numeric(energy, errors="coerce").fillna(0.0)
    baseline = energy.rolling(window=12, min_periods=3).mean().fillna(energy.mean())
    deviation = (energy - baseline) / baseline.replace(0, 1) * 100
    z_score = ((energy - energy.mean()) / max(energy.std(ddof=0), 1e-6))

    features = df[[col for col in [
        "energy_consumption_kwh", "peak_demand_kw", "occupancy_percent", "hvac_energy_kwh",
        "lighting_energy_kwh", "equipment_energy_kwh", "outdoor_temperature_c", "humidity_percent"
    ] if col in df.columns]].copy()
    for col in features.columns:
        features[col] = pd.to_numeric(features[col], errors="coerce").fillna(0)

    iso_scores = np.zeros(len(df))
    if IsolationForest is not None and len(features) >= 5:
        scaler = StandardScaler()
        scaled = scaler.fit_transform(features)
        model = IsolationForest(contamination=0.1, random_state=42, n_estimators=200)
        pred = model.fit_predict(scaled)
        iso_scores = np.where(pred == -1, 1.0, 0.2)

    anomaly_mask = (np.abs(z_score.to_numpy()) >= 1.9) | (iso_scores >= 0.7) | (np.abs(deviation.to_numpy()) >= 12)
    anomalies = []
    for idx, row in df.iterrows():
        if not anomaly_mask[idx]:
            continue
        actual = float(pd.to_numeric(row.get("energy_consumption_kwh", 0), errors="coerce") or 0.0)
        expected = float(baseline.iloc[idx])
        diff = actual - expected
        pct = float((diff / expected) * 100) if expected else 0.0
        score = min(1.0, max(0.0, 0.5 * min(1.0, abs(z_score.iloc[idx]) / 4.0) + 0.5 * float(iso_scores[idx])))
        severity = _severity_from_deviation(pct)
        anomalies.append({
            "timestamp": pd.Timestamp(row["timestamp"]).isoformat(),
            "building": str(row.get("building_name", "Unknown Building")),
            "actual_energy": round(actual, 2),
            "expected_energy": round(expected, 2),
            "deviation": round(diff, 2),
            "deviation_percentage": round(pct, 2),
            "anomaly_score": round(float(score), 3),
            "severity": severity,
            "root_cause": _root_cause_text(campus_id, row),
            "contributing_factors": _contributing_factors(row),
        })

    counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for item in anomalies:
        counts[item["severity"]] = counts.get(item["severity"], 0) + 1

    return {
        "campus_id": campus_id,
        "total_records": int(len(df)),
        "anomalies_detected": len(anomalies),
        "critical": counts["CRITICAL"],
        "high": counts["HIGH"],
        "medium": counts["MEDIUM"],
        "low": counts["LOW"],
        "anomalies": sorted(anomalies, key=lambda x: ({"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}[x["severity"]], -abs(float(x["deviation_percentage"])))),
    }


def _contributing_factors(row: pd.Series) -> list[str]:
    factors = []
    for key, label in [
        ("hvac_energy_kwh", "HVAC"),
        ("lighting_energy_kwh", "Lighting"),
        ("equipment_energy_kwh", "Equipment"),
        ("occupancy_percent", "Occupancy"),
    ]:
        value = pd.to_numeric(row.get(key, 0), errors="coerce") or 0.0
        if value and key != "occupancy_percent":
            factors.append(f"{label} energy: {float(value):.0f} kWh")
        elif key == "occupancy_percent":
            factors.append(f"Occupancy: {float(value):.1f}%")
    return factors[:5]


def _root_cause_text(campus_id: str, row: pd.Series) -> str:
    hvac = float(pd.to_numeric(row.get("hvac_energy_kwh", 0), errors="coerce") or 0.0)
    lighting = float(pd.to_numeric(row.get("lighting_energy_kwh", 0), errors="coerce") or 0.0)
    equipment = float(pd.to_numeric(row.get("equipment_energy_kwh", 0), errors="coerce") or 0.0)
    occupancy = float(pd.to_numeric(row.get("occupancy_percent", 0), errors="coerce") or 0.0)
    building = str(row.get("building_name", "building"))
    if hvac > max((lighting, equipment), default=0) and occupancy < 70:
        return f"HVAC consumption increased strongly while occupancy was low, indicating inefficient HVAC operation in {building}."
    if equipment > max((hvac, lighting), default=0):
        return f"Equipment load is the dominant contributor to the observed energy anomaly in {building}."
    if hvac > max((lighting, equipment), default=0):
        return f"HVAC remained the largest contributor to the anomaly, with elevated runtimes and low occupancy conditions."
    return f"Energy demand exceeded baseline expectations due to a combination of load drivers in {building}."
