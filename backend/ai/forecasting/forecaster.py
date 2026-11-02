"""Campus-scale forecasting with XGBoost or statistical fallback."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from ai.forecasting.features import FEATURE_COLUMNS, build_forecast_features

try:
    import xgboost as xgb
except Exception:  # pragma: no cover
    xgb = None


def forecast_campus(campus_id: str, records: list[dict[str, Any]], horizon_hours: int = 24) -> dict[str, Any]:
    """Generate forecasted energy and peak demand for the selected campus."""
    if not records:
        return {"campus_id": campus_id, "forecast_horizon": "24h", "predictions": [], "predicted_peak": 0, "peak_time": None, "expected_energy": 0, "confidence_lower": 0, "confidence_upper": 0, "model": "none"}

    df = build_forecast_features(records)
    if df.empty:
        return {"campus_id": campus_id, "forecast_horizon": "24h", "predictions": [], "predicted_peak": 0, "peak_time": None, "expected_energy": 0, "confidence_lower": 0, "confidence_upper": 0, "model": "none"}

    hourly = df.resample("h", on="timestamp").agg({
        "energy_consumption_kwh": "sum",
        "occupancy_percent": "mean",
        "outdoor_temperature_c": "mean",
    }).reset_index().rename(columns={"energy_consumption_kwh": "target"})
    hourly = hourly.dropna().sort_values("timestamp").reset_index(drop=True)
    if hourly.empty:
        return {"campus_id": campus_id, "forecast_horizon": "24h", "predictions": [], "predicted_peak": 0, "peak_time": None, "expected_energy": 0, "confidence_lower": 0, "confidence_upper": 0, "model": "none"}

    hourly["timestamp"] = pd.to_datetime(hourly["timestamp"])
    for lag in [1, 2, 3, 6, 12, 24]:
        hourly[f"lag_{lag}"] = hourly["target"].shift(lag).fillna(hourly["target"].mean())
    for window in [6, 12, 24]:
        hourly[f"rolling_{window}"] = hourly["target"].rolling(window=window, min_periods=1).mean()
    hourly["hour"] = hourly["timestamp"].dt.hour
    hourly["day_of_week"] = hourly["timestamp"].dt.dayofweek
    hourly["day_of_month"] = hourly["timestamp"].dt.day
    hourly["month"] = hourly["timestamp"].dt.month
    hourly["is_weekend"] = (hourly["day_of_week"] >= 5).astype(int)

    predictions = []
    model_used = "statistical_baseline"
    if xgb is not None and len(hourly) >= 24:
        features = hourly[FEATURE_COLUMNS].copy().fillna(0)
        target = hourly["target"].copy()
        model = xgb.XGBRegressor(n_estimators=120, max_depth=5, learning_rate=0.08, random_state=42, objective="reg:squarederror")
        model.fit(features, target)
        model_used = "xgboost"
        last_ts = hourly["timestamp"].iloc[-1]
        for i in range(1, horizon_hours + 1):
            ts = last_ts + pd.Timedelta(hours=i)
            row = {
                "hour": ts.hour,
                "day_of_week": ts.dayofweek,
                "day_of_month": ts.day,
                "month": ts.month,
                "is_weekend": int(ts.dayofweek >= 5),
                "occupancy_percent": float(hourly["occupancy_percent"].iloc[-1]),
                "outdoor_temperature_c": float(hourly["outdoor_temperature_c"].iloc[-1]),
                "lag_1": float(hourly["target"].iloc[-1]),
                "lag_2": float(hourly["target"].iloc[-2]) if len(hourly) > 1 else float(hourly["target"].iloc[-1]),
                "lag_3": float(hourly["target"].iloc[-3]) if len(hourly) > 2 else float(hourly["target"].iloc[-1]),
                "lag_6": float(hourly["target"].iloc[-6]) if len(hourly) > 5 else float(hourly["target"].iloc[-1]),
                "lag_12": float(hourly["target"].iloc[-12]) if len(hourly) > 11 else float(hourly["target"].iloc[-1]),
                "lag_24": float(hourly["target"].iloc[-24]) if len(hourly) > 23 else float(hourly["target"].iloc[-1]),
                "rolling_6": float(hourly["target"].tail(6).mean()),
                "rolling_12": float(hourly["target"].tail(12).mean()),
                "rolling_24": float(hourly["target"].tail(24).mean()),
            }
            value = max(0.0, float(model.predict(pd.DataFrame([row])[FEATURE_COLUMNS])[0]))
            predictions.append({
                "timestamp": ts.isoformat(),
                "predicted_energy": round(float(value), 2),
                "confidence_lower": round(float(max(0.0, value * 0.92)), 2),
                "confidence_upper": round(float(value * 1.08), 2),
            })
            hourly = pd.concat([hourly, pd.DataFrame([{"timestamp": ts, "target": value, "occupancy_percent": row["occupancy_percent"], "outdoor_temperature_c": row["outdoor_temperature_c"]}])], ignore_index=True)
    else:
        last_ts = hourly["timestamp"].iloc[-1]
        mean = float(hourly["target"].mean())
        for i in range(1, horizon_hours + 1):
            ts = last_ts + pd.Timedelta(hours=i)
            value = max(0.0, mean * (1 + 0.05 * np.sin((ts.hour / 24.0) * np.pi * 2)))
            predictions.append({
                "timestamp": ts.isoformat(),
                "predicted_energy": round(float(value), 2),
                "confidence_lower": round(float(max(0.0, value * 0.90)), 2),
                "confidence_upper": round(float(value * 1.10), 2),
            })

    if not predictions:
        return {"campus_id": campus_id, "forecast_horizon": "24h", "predictions": [], "predicted_peak": 0, "peak_time": None, "expected_energy": 0, "confidence_lower": 0, "confidence_upper": 0, "model": "none"}

    peak_item = max(predictions, key=lambda item: item["predicted_energy"])
    expected_energy = sum(item["predicted_energy"] for item in predictions)
    return {
        "campus_id": campus_id,
        "forecast_horizon": "24h",
        "predictions": predictions,
        "predicted_peak": round(float(peak_item["predicted_energy"]), 2),
        "peak_time": peak_item["timestamp"],
        "expected_energy": round(float(expected_energy), 2),
        "confidence_lower": round(float(min(item["confidence_lower"] for item in predictions)), 2),
        "confidence_upper": round(float(max(item["confidence_upper"] for item in predictions)), 2),
        "model": model_used,
    }
