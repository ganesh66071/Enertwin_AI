"""Feature engineering for campus energy analytics."""

from __future__ import annotations

from typing import Any

import pandas as pd


def engineer_features(campus_id: str, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create campus-specific engineered features from the preprocessed dataset."""
    if not records:
        return []

    df = pd.DataFrame(records)
    if df.empty:
        return []

    df["timestamp"] = pd.to_datetime(df.get("timestamp"), errors="coerce")
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)

    energy = df["energy_consumption_kwh"].astype(float) if "energy_consumption_kwh" in df.columns else pd.Series([0.0] * len(df))
    occupancy = df["occupancy_percent"].astype(float) if "occupancy_percent" in df.columns else pd.Series([0.0] * len(df))
    peak = df["peak_demand_kw"].astype(float) if "peak_demand_kw" in df.columns else pd.Series([0.0] * len(df))
    hvac = df["hvac_energy_kwh"].astype(float) if "hvac_energy_kwh" in df.columns else pd.Series([0.0] * len(df))
    lighting = df["lighting_energy_kwh"].astype(float) if "lighting_energy_kwh" in df.columns else pd.Series([0.0] * len(df))
    equipment = df["equipment_energy_kwh"].astype(float) if "equipment_energy_kwh" in df.columns else pd.Series([0.0] * len(df))
    humidity = df["humidity_percent"].astype(float) if "humidity_percent" in df.columns else pd.Series([55.0] * len(df))

    df["energy_per_person"] = (energy / (occupancy.replace(0, 1))).fillna(0)
    df["hvac_percentage"] = (hvac / energy.replace(0, 1) * 100).fillna(0)
    df["lighting_percentage"] = (lighting / energy.replace(0, 1) * 100).fillna(0)
    df["equipment_percentage"] = (equipment / energy.replace(0, 1) * 100).fillna(0)
    df["rolling_energy_mean"] = energy.rolling(window=3, min_periods=1).mean()
    df["rolling_energy_std"] = energy.rolling(window=3, min_periods=1).std().fillna(0)
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["is_peak_hour"] = ((df["hour"] >= 14) & (df["hour"] <= 18)).astype(int)

    if "outdoor_temperature_c" in df.columns:
        outdoor = df["outdoor_temperature_c"].astype(float)
    else:
        outdoor = pd.Series([28.0] * len(df))

    df["temperature"] = outdoor
    df["humidity"] = humidity
    df["peak_demand_kw"] = peak
    df["occupancy"] = occupancy

    return df.where(pd.notna(df), 0).to_dict("records")
