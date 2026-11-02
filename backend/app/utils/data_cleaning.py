"""Data validation and cleaning utilities."""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Optional

import numpy as np
import pandas as pd


def is_invalid_number(value: Any) -> bool:
    if value is None:
        return True
    try:
        f = float(value)
        return math.isnan(f) or math.isinf(f)
    except (TypeError, ValueError):
        return True


def safe_float(value: Any, default: float = 0.0) -> float:
    if is_invalid_number(value):
        return default
    return float(value)


def safe_int(value: Any, default: int = 0) -> int:
    if is_invalid_number(value):
        return default
    return int(float(value))


def parse_timestamp(value: Any) -> Optional[datetime]:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    try:
        parsed = pd.to_datetime(value, errors="coerce")
        if pd.isna(parsed):
            return None
        return parsed.to_pydatetime()
    except Exception:
        return None


def clean_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Clean raw dataframe; return cleaned df and warnings."""
    warnings: list[str] = []
    df = df.copy()
    df = df.dropna(how="all")
    df = df.replace([np.inf, -np.inf], np.nan)

    # Remove completely empty columns
    empty_cols = [c for c in df.columns if df[c].isna().all()]
    if empty_cols:
        df = df.drop(columns=empty_cols)
        warnings.append(f"Dropped empty columns: {empty_cols}")

    return df, warnings


def validate_record_row(row: dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate a normalized record dict. Returns (valid, rejection_reason)."""
    ts = row.get("timestamp")
    if ts is None:
        return False, "missing timestamp"

    building = row.get("building_name")
    if not building or str(building).strip() == "":
        return False, "missing building name"

    energy = safe_float(row.get("energy_consumption_kwh"), default=-1)
    if energy < 0:
        return False, "negative energy consumption"

    occupancy = safe_float(row.get("occupancy_percent", 0))
    if occupancy < 0 or occupancy > 100:
        return False, "invalid occupancy percent"

    occ_count = safe_int(row.get("occupancy_count", 0))
    if occ_count < 0:
        return False, "negative occupancy count"

    for field in ["hvac_energy_kwh", "lighting_energy_kwh", "equipment_energy_kwh", "peak_demand_kw"]:
        val = safe_float(row.get(field, 0))
        if val < 0:
            return False, f"negative {field}"

    return True, None


def json_safe(value: Any) -> Any:
    """Ensure value is JSON-serializable (no NaN/Inf)."""
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return 0.0
        return round(value, 4)
    if isinstance(value, dict):
        return {k: json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_safe(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return json_safe(float(value))
    return value
