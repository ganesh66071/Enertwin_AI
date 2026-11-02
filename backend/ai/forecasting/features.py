"""Time-series feature engineering for energy forecasting."""

from __future__ import annotations

from typing import Any

import pandas as pd

FEATURE_COLUMNS = [
    "hour", "day_of_week", "day_of_month", "month", "is_weekend",
    "occupancy_percent", "outdoor_temperature_c", "lag_1", "lag_2", "lag_3",
    "lag_6", "lag_12", "lag_24", "rolling_6", "rolling_12", "rolling_24",
]


def build_forecast_features(records: list[dict[str, Any]]) -> pd.DataFrame:
    """Create time series and lag features for campus energy forecasting."""
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    df["timestamp"] = pd.to_datetime(df.get("timestamp"), errors="coerce")
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    if df.empty:
        return df

    energy = pd.to_numeric(df.get("energy_consumption_kwh", pd.Series([0.0] * len(df))), errors="coerce").fillna(0.0)
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["day_of_month"] = df["timestamp"].dt.day
    df["month"] = df["timestamp"].dt.month
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["occupancy_percent"] = pd.to_numeric(df.get("occupancy_percent", 0), errors="coerce").fillna(0.0)
    df["outdoor_temperature_c"] = pd.to_numeric(df.get("outdoor_temperature_c", 28), errors="coerce").fillna(28.0)

    for lag in [1, 2, 3, 6, 12, 24]:
        df[f"lag_{lag}"] = energy.shift(lag).fillna(energy.mean())
    for window in [6, 12, 24]:
        df[f"rolling_{window}"] = energy.rolling(window=window, min_periods=1).mean()
    return df
