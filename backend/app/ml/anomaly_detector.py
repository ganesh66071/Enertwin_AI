"""Combined Isolation Forest + Z-score anomaly detection."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from app.ml.feature_engineering import FEATURE_COLUMNS, records_to_dataframe


def _severity_from_deviation(deviation_pct: float) -> str:
    abs_dev = abs(deviation_pct)
    if abs_dev >= 25:
        return "critical"
    if abs_dev >= 15:
        return "warning"
    return "minor"


def _root_causes(row: pd.Series, baseline: pd.Series) -> list[str]:
    causes: list[str] = []
    if row.get("hvac_energy_kwh", 0) > baseline.get("hvac_energy_kwh", 0) * 1.2:
        causes.append(
            f"HVAC energy ({row['hvac_energy_kwh']:.1f} kWh) significantly above baseline "
            f"({baseline.get('hvac_energy_kwh', 0):.1f} kWh)"
        )
    if row.get("lighting_energy_kwh", 0) > baseline.get("lighting_energy_kwh", 0) * 1.2:
        causes.append(
            f"Lighting load ({row['lighting_energy_kwh']:.1f} kWh) elevated vs baseline"
        )
    if row.get("equipment_energy_kwh", 0) > baseline.get("equipment_energy_kwh", 0) * 1.2:
        causes.append(
            f"Equipment load ({row['equipment_energy_kwh']:.1f} kWh) above expected levels"
        )
    if row.get("occupancy_percent", 0) < baseline.get("occupancy_percent", 50) * 0.7:
        causes.append(
            f"High energy during low occupancy ({row['occupancy_percent']:.1f}% vs "
            f"baseline {baseline.get('occupancy_percent', 0):.1f}%)"
        )
    if row.get("hvac_runtime_hours", 0) > baseline.get("hvac_runtime_hours", 0) * 1.25:
        causes.append(
            f"HVAC runtime ({row['hvac_runtime_hours']:.1f}h) exceeds baseline "
            f"({baseline.get('hvac_runtime_hours', 0):.1f}h)"
        )
    if row.get("outdoor_temperature_c", 28) > baseline.get("outdoor_temperature_c", 28) + 3:
        causes.append(
            f"Elevated outdoor temperature ({row['outdoor_temperature_c']:.1f}°C) increasing HVAC load"
        )
    if not causes:
        causes.append("Unusual energy pattern detected relative to campus baseline")
    return causes


def detect_anomalies(records: list) -> dict[str, Any]:
    """
    Detect anomalies using Isolation Forest + Z-score on campus records.
    Returns structured anomaly report.
    """
    df = records_to_dataframe(records)
    if df.empty or len(df) < 5:
        return {
            "total": 0,
            "critical": 0,
            "warning": 0,
            "minor": 0,
            "anomalies": [],
            "message": "Insufficient data for anomaly detection (minimum 5 records required)",
        }

    feature_df = df[FEATURE_COLUMNS].fillna(0).replace([np.inf, -np.inf], 0)
    baseline = feature_df.mean()

    # Isolation Forest
    scaler = StandardScaler()
    scaled = scaler.fit_transform(feature_df)
    iso = IsolationForest(contamination=0.08, random_state=42, n_estimators=100)
    iso_labels = iso.fit_predict(scaled)

    # Z-score on energy
    energy_mean = df["energy_consumption_kwh"].mean()
    energy_std = max(df["energy_consumption_kwh"].std(), 0.01)
    z_scores = (df["energy_consumption_kwh"] - energy_mean) / energy_std

    anomalies: list[dict] = []
    for idx, row in df.iterrows():
        is_iso = iso_labels[idx] == -1
        is_z = abs(z_scores.iloc[idx]) >= 2.0
        if not (is_iso or is_z):
            continue

        actual = float(row["energy_consumption_kwh"])
        expected = float(energy_mean)
        deviation_pct = round(((actual - expected) / max(expected, 0.01)) * 100, 1)
        severity = _severity_from_deviation(deviation_pct)

        anomalies.append(
            {
                "building": row["building_name"],
                "timestamp": row["timestamp"].isoformat(),
                "actual_energy": round(actual, 2),
                "expected_energy": round(expected, 2),
                "deviation_percent": deviation_pct,
                "severity": severity,
                "possible_causes": _root_causes(row, baseline),
            }
        )

    # Sort by severity
    severity_order = {"critical": 0, "warning": 1, "minor": 2}
    anomalies.sort(key=lambda a: (severity_order.get(a["severity"], 3), -abs(a["deviation_percent"])))

    counts = {"critical": 0, "warning": 0, "minor": 0}
    for a in anomalies:
        counts[a["severity"]] = counts.get(a["severity"], 0) + 1

    return {
        "total": len(anomalies),
        "critical": counts["critical"],
        "warning": counts["warning"],
        "minor": counts["minor"],
        "anomalies": anomalies[:50],
    }
