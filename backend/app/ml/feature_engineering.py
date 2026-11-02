"""Feature engineering for ML pipelines."""

from __future__ import annotations

import pandas as pd


FEATURE_COLUMNS = [
    "energy_consumption_kwh",
    "occupancy_percent",
    "hvac_energy_kwh",
    "lighting_energy_kwh",
    "equipment_energy_kwh",
    "outdoor_temperature_c",
    "hvac_runtime_hours",
]


def records_to_dataframe(records: list) -> pd.DataFrame:
    """Convert SQLAlchemy energy records to DataFrame."""
    rows = []
    for r in records:
        rows.append(
            {
                "timestamp": r.timestamp,
                "energy_consumption_kwh": r.energy_consumption_kwh,
                "occupancy_percent": r.occupancy_percent,
                "hvac_energy_kwh": r.hvac_energy_kwh,
                "lighting_energy_kwh": r.lighting_energy_kwh,
                "equipment_energy_kwh": r.equipment_energy_kwh,
                "outdoor_temperature_c": r.outdoor_temperature_c,
                "hvac_runtime_hours": r.hvac_runtime_hours,
                "building_name": r.building_name,
                "indoor_temperature_c": r.indoor_temperature_c,
                "peak_demand_kw": r.peak_demand_kw,
            }
        )
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


def build_forecast_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add time-based and lag features for forecasting."""
    if df.empty:
        return df

    out = df.copy()
    ts = out["timestamp"]
    out["hour"] = ts.dt.hour
    out["day_of_week"] = ts.dt.dayofweek
    out["day_of_month"] = ts.dt.day
    out["month"] = ts.dt.month

    if "occupancy_percent" not in out.columns:
        out["occupancy_percent"] = 50.0
    if "outdoor_temperature_c" not in out.columns:
        out["outdoor_temperature_c"] = 28.0

    energy = out["energy_consumption_kwh"]
    out["lag_1"] = energy.shift(1).fillna(energy.mean())
    out["lag_2"] = energy.shift(2).fillna(energy.mean())
    out["rolling_mean"] = energy.rolling(window=3, min_periods=1).mean()
    out["rolling_std"] = energy.rolling(window=3, min_periods=1).std().fillna(0)

    return out


def aggregate_hourly(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate records to hourly campus-level totals."""
    if df.empty:
        return df
    agg = (
        df.groupby(pd.Grouper(key="timestamp", freq="h"))
        .agg(
            {
                "energy_consumption_kwh": "sum",
                "occupancy_percent": "mean",
                "outdoor_temperature_c": "mean",
            }
        )
        .reset_index()
    )
    return agg.dropna(subset=["energy_consumption_kwh"])
