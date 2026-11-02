import os
import sqlite3
import pandas as pd
from app.core.database import SessionLocal
from app.services.dataset_service import get_campus_records
from ai.anomaly.detector import detect_anomalies_for_campus

db = SessionLocal()
records = get_campus_records(db, "viit")
print(f"Total records fetched for 'viit' by get_campus_records: {len(records)}")
res = detect_anomalies_for_campus("viit", records)
print(f"Anomalies detected: {res['anomalies_detected']}")
print(f"Length of anomalies list: {len(res['anomalies'])}")
if records:
    r0 = records[0]
    print("Record 0 attributes:", dir(r0))
    print("Record 0 dict:", {c: getattr(r0, c) for c in ['timestamp', 'building_name', 'energy_consumption_kwh']})
db.close()

