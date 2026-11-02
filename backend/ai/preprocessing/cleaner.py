"""Campus-scoped data preprocessing utilities."""

from __future__ import annotations

from typing import Any

import pandas as pd


def prepare_campus_dataset(campus_id: str, records: list[Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Clean and normalize a campus dataset before ML analysis."""
    if not records:
        return [], {"campus_id": campus_id, "rows_before": 0, "rows_after": 0, "removed_duplicates": 0, "missing_values_filled": 0, "invalid_rows_removed": 0}

    rows = []
    for record in records:
        if hasattr(record, "__dict__"):
            row = {k: getattr(record, k) for k in [
                "timestamp", "building_name", "floor", "zone", "energy_consumption_kwh",
                "peak_demand_kw", "occupancy_percent", "outdoor_temperature_c", "humidity_percent",
                "hvac_energy_kwh", "lighting_energy_kwh", "equipment_energy_kwh", "co2_emission_kg",
            ] if hasattr(record, k)}
        else:
            row = dict(record)
        if row.get("timestamp") is not None:
            rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty:
        return [], {"campus_id": campus_id, "rows_before": len(rows), "rows_after": 0, "removed_duplicates": 0, "missing_values_filled": 0, "invalid_rows_removed": 0}

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    before = len(df)
    df = df.drop_duplicates(subset=["timestamp", "building_name", "floor", "zone"], keep="last")
    duplicates = before - len(df)

    numeric_cols = [
        "energy_consumption_kwh", "peak_demand_kw", "occupancy_percent", "outdoor_temperature_c",
        "humidity_percent", "hvac_energy_kwh", "lighting_energy_kwh", "equipment_energy_kwh", "co2_emission_kg"
    ]
    for col in numeric_cols:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in numeric_cols:
        median_val = df[col].median()
        if pd.isna(median_val):
            median_val = 0.0
        df[col] = df[col].fillna(median_val)

    invalid_mask = (
        (df["energy_consumption_kwh"] < 0) |
        (df["occupancy_percent"].fillna(0) < 0) |
        (df["occupancy_percent"].fillna(0) > 100) |
        (df["humidity_percent"].fillna(0) < 0) |
        (df["humidity_percent"].fillna(0) > 100)
    )
    invalid_count = int(invalid_mask.sum())
    df = df.loc[~invalid_mask].copy()

    for col in numeric_cols:
        global_min = df[col].min()
        global_max = df[col].max()
        if pd.notna(global_min) and pd.notna(global_max) and global_max > global_min:
            df[col] = (df[col] - global_min) / (global_max - global_min)

    df["hour"] = df["timestamp"].dt.hour
    df["day"] = df["timestamp"].dt.day
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["day_of_month"] = df["timestamp"].dt.day
    df["month"] = df["timestamp"].dt.month
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["is_working_hour"] = ((df["hour"] >= 8) & (df["hour"] <= 18)).astype(int)

    if "energy_consumption_kwh" in df.columns:
        df["rolling_mean"] = df["energy_consumption_kwh"].rolling(window=3, min_periods=1).mean()
        df["rolling_std"] = df["energy_consumption_kwh"].rolling(window=3, min_periods=1).std().fillna(0)
        df["energy_change"] = df["energy_consumption_kwh"].diff().fillna(0)
        df["energy_change_percentage"] = ((df["energy_change"] / df["rolling_mean"].replace(0, 1)).fillna(0)) * 100

    if "occupancy_percent" in df.columns and "hvac_energy_kwh" in df.columns:
        df["occupancy_ratio"] = df["occupancy_percent"] / 100.0
        df["hvac_ratio"] = df["hvac_energy_kwh"] / (df["energy_consumption_kwh"].replace(0, 1))
        df["lighting_ratio"] = df["lighting_energy_kwh"] / (df["energy_consumption_kwh"].replace(0, 1))
        df["equipment_ratio"] = df["equipment_energy_kwh"] / (df["energy_consumption_kwh"].replace(0, 1))

    prepared = df.where(pd.notna(df), 0).to_dict("records")
    summary = {
        "campus_id": campus_id,
        "rows_before": int(before),
        "rows_after": len(prepared),
        "removed_duplicates": int(duplicates),
        "missing_values_filled": int(df.isna().sum().sum()),
        "invalid_rows_removed": int(invalid_count),
    }
    return prepared, summary
