"""Dataset upload, validation, normalization, and storage."""

from __future__ import annotations

import io
from typing import Any, Optional

import pandas as pd
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.energy_record import EnergyRecord
from app.utils.calculations import (
    derive_co2,
    derive_peak_demand_kwh,
    deterministic_seed,
    estimate_equipment_energy,
    estimate_hvac_energy,
    estimate_lighting_energy,
    estimate_occupancy_profile,
)
from app.utils.data_cleaning import (
    clean_dataframe,
    parse_timestamp,
    safe_float,
    safe_int,
    validate_record_row,
)
from app.utils.data_mapping import map_columns, validate_mapped_columns

settings = get_settings()


def _read_upload(content: bytes, filename: str) -> pd.DataFrame:
    lower = filename.lower()
    if lower.endswith(".csv"):
        return pd.read_csv(io.BytesIO(content))
    if lower.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(content))
    raise ValueError(f"Unsupported file format: {filename}")


def _row_from_mapped(
    row: pd.Series,
    mapped: dict[str, str],
    campus_id: str,
    campus_type: str,
) -> dict[str, Any]:
    """Convert a DataFrame row to normalized record dict with derivations."""
    record: dict[str, Any] = {}
    derived_fields: set[str] = set()

    for canonical, original in mapped.items():
        record[canonical] = row.get(original)

    record["timestamp"] = parse_timestamp(record.get("timestamp"))
    record["building_name"] = str(record.get("building_name", "")).strip()
    record["floor"] = str(record.get("floor", "")).strip() or None
    record["zone"] = str(record.get("zone", "")).strip() or None

    energy = safe_float(record.get("energy_consumption_kwh"))
    record["energy_consumption_kwh"] = energy

    ts = record["timestamp"]
    hour = ts.hour if ts else 12
    dow = ts.weekday() if ts else 0
    building = record["building_name"] or "Unknown"
    seed = deterministic_seed(campus_id, building)

    # Occupancy
    if record.get("occupancy_percent") is None or pd.isna(record.get("occupancy_percent")):
        if record.get("occupancy_count") is not None and not pd.isna(record.get("occupancy_count")):
            count = safe_int(record["occupancy_count"])
            record["occupancy_percent"] = min(100.0, count * 2.5)
            record["occupancy_count"] = count
        else:
            count, pct = estimate_occupancy_profile(building, campus_type, hour, dow, seed)
            record["occupancy_count"] = count
            record["occupancy_percent"] = pct
            derived_fields.add("occupancy")
    else:
        record["occupancy_percent"] = safe_float(record["occupancy_percent"])
        record["occupancy_count"] = safe_int(record.get("occupancy_count", int(record["occupancy_percent"])))

    outdoor = safe_float(record.get("outdoor_temperature_c"), 28.0)
    indoor = safe_float(record.get("indoor_temperature_c"), 24.0)
    record["outdoor_temperature_c"] = outdoor
    record["indoor_temperature_c"] = indoor
    record["humidity_percent"] = safe_float(record.get("humidity_percent"), 55.0)

    occ_pct = record["occupancy_percent"]

    # HVAC
    if record.get("hvac_energy_kwh") is None or pd.isna(record.get("hvac_energy_kwh")):
        record["hvac_energy_kwh"] = estimate_hvac_energy(energy, occ_pct, outdoor, indoor, hour, seed)
        derived_fields.add("hvac")
    else:
        record["hvac_energy_kwh"] = safe_float(record["hvac_energy_kwh"])

    # Lighting
    if record.get("lighting_energy_kwh") is None or pd.isna(record.get("lighting_energy_kwh")):
        record["lighting_energy_kwh"] = estimate_lighting_energy(energy, occ_pct, hour, seed)
        derived_fields.add("lighting")
    else:
        record["lighting_energy_kwh"] = safe_float(record["lighting_energy_kwh"])

    # Equipment
    if record.get("equipment_energy_kwh") is None or pd.isna(record.get("equipment_energy_kwh")):
        record["equipment_energy_kwh"] = estimate_equipment_energy(energy, building, occ_pct, hour, seed)
        derived_fields.add("equipment")
    else:
        record["equipment_energy_kwh"] = safe_float(record["equipment_energy_kwh"])

    # Normalize component splits to not exceed total
    components = record["hvac_energy_kwh"] + record["lighting_energy_kwh"] + record["equipment_energy_kwh"]
    if components > energy * 1.05 and energy > 0:
        scale = energy / components
        record["hvac_energy_kwh"] = round(record["hvac_energy_kwh"] * scale, 4)
        record["lighting_energy_kwh"] = round(record["lighting_energy_kwh"] * scale, 4)
        record["equipment_energy_kwh"] = round(record["equipment_energy_kwh"] * scale, 4)

    # Peak demand
    if record.get("peak_demand_kw") is None or pd.isna(record.get("peak_demand_kw")):
        record["peak_demand_kw"] = derive_peak_demand_kwh(energy)
        derived_fields.add("peak_demand")
    else:
        record["peak_demand_kw"] = safe_float(record["peak_demand_kw"])

    record["hvac_runtime_hours"] = safe_float(record.get("hvac_runtime_hours"), max(0, hour % 12))
    record["hvac_setpoint_c"] = safe_float(record.get("hvac_setpoint_c"), 24.0)
    record["equipment_runtime_hours"] = safe_float(record.get("equipment_runtime_hours"), max(0, hour % 10))
    record["electricity_tariff"] = safe_float(record.get("electricity_tariff"), settings.default_electricity_tariff)

    if record.get("co2_emission_kg") is None or pd.isna(record.get("co2_emission_kg")):
        record["co2_emission_kg"] = derive_co2(energy)
        derived_fields.add("co2")
    else:
        record["co2_emission_kg"] = safe_float(record["co2_emission_kg"])

    record["data_source"] = "derived" if derived_fields else "dataset"
    record["_derived_fields"] = derived_fields
    return record


def process_dataset_upload(
    db: Session,
    campus_id: str,
    campus_type: str,
    content: bytes,
    filename: str,
) -> dict[str, Any]:
    """Full upload pipeline: read → validate → map → derive → store."""
    raw_df = _read_upload(content, filename)
    df, warnings = clean_dataframe(raw_df)

    if df.empty:
        raise ValueError("Uploaded file contains no valid data rows")

    mapped = map_columns(list(df.columns))
    missing = validate_mapped_columns(mapped)
    if missing:
        raise ValueError(f"Missing required columns (after mapping): {', '.join(missing)}")

    processed = 0
    rejected = 0
    seen_keys: set[tuple] = set()
    derived_count = 0

    for _, row in df.iterrows():
        record = _row_from_mapped(row, mapped, campus_id, campus_type)
        valid, reason = validate_record_row(record)
        if not valid:
            rejected += 1
            warnings.append(f"Rejected row: {reason}")
            continue

        dedup_key = (record["timestamp"], record["building_name"], record.get("floor"), record.get("zone"))
        if dedup_key in seen_keys:
            rejected += 1
            continue
        seen_keys.add(dedup_key)

        if record.get("_derived_fields"):
            derived_count += 1

        db_record = EnergyRecord(
            campus_id=campus_id,
            timestamp=record["timestamp"],
            building_name=record["building_name"],
            floor=record.get("floor"),
            zone=record.get("zone"),
            energy_consumption_kwh=record["energy_consumption_kwh"],
            hvac_energy_kwh=record["hvac_energy_kwh"],
            lighting_energy_kwh=record["lighting_energy_kwh"],
            equipment_energy_kwh=record["equipment_energy_kwh"],
            peak_demand_kw=record["peak_demand_kw"],
            occupancy_count=record["occupancy_count"],
            occupancy_percent=record["occupancy_percent"],
            indoor_temperature_c=record["indoor_temperature_c"],
            outdoor_temperature_c=record["outdoor_temperature_c"],
            humidity_percent=record["humidity_percent"],
            hvac_runtime_hours=record["hvac_runtime_hours"],
            hvac_setpoint_c=record["hvac_setpoint_c"],
            equipment_runtime_hours=record["equipment_runtime_hours"],
            electricity_tariff=record["electricity_tariff"],
            co2_emission_kg=record["co2_emission_kg"],
            data_source=record["data_source"],
        )
        db.add(db_record)
        processed += 1

    db.commit()

    return {
        "success": True,
        "campus_id": campus_id,
        "filename": filename,
        "records_processed": processed,
        "records_rejected": rejected,
        "warnings": warnings[:20],
        "mapped_columns": mapped,
        "derived_records": derived_count,
    }


def get_campus_records(db: Session, campus_id: str) -> list[EnergyRecord]:
    """Query energy records for a single campus only."""
    return (
        db.query(EnergyRecord)
        .filter(EnergyRecord.campus_id == campus_id)
        .order_by(EnergyRecord.timestamp.asc())
        .all()
    )
