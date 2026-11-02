"""Energy consumption forecasting with XGBoost and statistical fallback."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.ml.feature_engineering import aggregate_hourly, build_forecast_features, records_to_dataframe

FORECAST_FEATURES = [
    "hour", "day_of_week", "day_of_month", "month",
    "occupancy_percent", "outdoor_temperature_c",
    "lag_1", "lag_2", "rolling_mean", "rolling_std",
]

MIN_RECORDS_XGB = 48
FORECAST_HORIZON = 24


def _statistical_forecast(hourly: pd.DataFrame, horizon: int) -> list[dict]:
    """Simple mean + weekly pattern fallback."""
    if hourly.empty:
        return []

    mean_energy = hourly["energy_consumption_kwh"].mean()
    hourly["hour"] = hourly["timestamp"].dt.hour
    hourly["dow"] = hourly["timestamp"].dt.dayofweek
    pattern = hourly.groupby(["dow", "hour"])["energy_consumption_kwh"].mean().to_dict()

    last_ts = hourly["timestamp"].max()
    forecasts = []
    for i in range(1, horizon + 1):
        ts = last_ts + pd.Timedelta(hours=i)
        key = (ts.dayofweek, ts.hour)
        predicted = pattern.get(key, mean_energy)
        forecasts.append({"timestamp": ts.isoformat(), "energy_kwh": round(float(predicted), 2)})
    return forecasts


def forecast_energy(records: list, horizon: int = FORECAST_HORIZON) -> dict[str, Any]:
    """Generate energy forecast for campus records."""
    df = records_to_dataframe(records)
    if df.empty:
        return {
            "success": False,
            "message": "No historical data available for forecasting",
            "historical": [],
            "forecast": [],
            "predicted_peak": 0,
            "predicted_peak_time": None,
            "model": "none",
        }

    hourly = aggregate_hourly(df)
    if len(hourly) < 5:
        return {
            "success": False,
            "message": "Insufficient historical data for forecasting (minimum 5 hourly points)",
            "historical": [
                {"timestamp": r.timestamp.isoformat(), "energy_kwh": r.energy_consumption_kwh}
                for r in records[-100:]
            ],
            "forecast": [],
            "predicted_peak": 0,
            "predicted_peak_time": None,
            "model": "none",
        }

    historical = [
        {"timestamp": row["timestamp"].isoformat(), "energy_kwh": round(float(row["energy_consumption_kwh"]), 2)}
        for _, row in hourly.tail(168).iterrows()
    ]

    if len(hourly) < MIN_RECORDS_XGB:
        forecast_points = _statistical_forecast(hourly, horizon)
        peak = max(forecast_points, key=lambda x: x["energy_kwh"]) if forecast_points else None
        return {
            "success": True,
            "message": "Using statistical baseline due to limited historical data",
            "historical": historical,
            "forecast": forecast_points,
            "predicted_peak": peak["energy_kwh"] if peak else 0,
            "predicted_peak_time": peak["timestamp"] if peak else None,
            "model": "statistical_baseline",
        }

    try:
        import xgboost as xgb

        featured = build_forecast_features(hourly.rename(columns={"timestamp": "timestamp"}))
        featured = featured.rename(columns={"energy_consumption_kwh": "target"})
        # Re-align after feature build
        featured["timestamp"] = hourly["timestamp"].values
        featured["target"] = hourly["energy_consumption_kwh"].values

        X = featured[FORECAST_FEATURES].fillna(0)
        y = featured["target"]

        model = xgb.XGBRegressor(
            n_estimators=80,
            max_depth=4,
            learning_rate=0.1,
            random_state=42,
            objective="reg:squarederror",
        )
        model.fit(X, y)

        # Recursive multi-step forecast
        working = featured.copy()
        forecast_points = []
        last_ts = working["timestamp"].max()

        for step in range(1, horizon + 1):
            ts = last_ts + pd.Timedelta(hours=step)
            row = {
                "timestamp": ts,
                "hour": ts.hour,
                "day_of_week": ts.dayofweek,
                "day_of_month": ts.day,
                "month": ts.month,
                "occupancy_percent": working["occupancy_percent"].iloc[-1] if "occupancy_percent" in working else 50,
                "outdoor_temperature_c": working["outdoor_temperature_c"].iloc[-1] if "outdoor_temperature_c" in working else 28,
            }
            recent = working["target"].tail(3)
            row["lag_1"] = recent.iloc[-1]
            row["lag_2"] = recent.iloc[-2] if len(recent) >= 2 else recent.iloc[-1]
            row["rolling_mean"] = recent.mean()
            row["rolling_std"] = recent.std() if len(recent) > 1 else 0

            X_pred = pd.DataFrame([row])[FORECAST_FEATURES].fillna(0)
            pred = float(model.predict(X_pred)[0])
            pred = max(0, pred)
            forecast_points.append({"timestamp": ts.isoformat(), "energy_kwh": round(pred, 2)})

            new_row = pd.DataFrame([{**row, "target": pred}])
            working = pd.concat([working, new_row], ignore_index=True)

        peak = max(forecast_points, key=lambda x: x["energy_kwh"])
        return {
            "success": True,
            "message": "Forecast generated using XGBoost regression",
            "historical": historical,
            "forecast": forecast_points,
            "predicted_peak": peak["energy_kwh"],
            "predicted_peak_time": peak["timestamp"],
            "model": "xgboost",
        }
    except Exception as exc:
        forecast_points = _statistical_forecast(hourly, horizon)
        peak = max(forecast_points, key=lambda x: x["energy_kwh"]) if forecast_points else None
        return {
            "success": True,
            "message": f"XGBoost unavailable ({exc}); using statistical baseline",
            "historical": historical,
            "forecast": forecast_points,
            "predicted_peak": peak["energy_kwh"] if peak else 0,
            "predicted_peak_time": peak["timestamp"] if peak else None,
            "model": "statistical_baseline",
        }
