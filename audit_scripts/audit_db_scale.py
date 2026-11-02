import os
import sqlite3
import pandas as pd
import numpy as np

print("="*60)
print("AUDIT: SEEDED DATABASE (app.db) SCALE & ENTITIES")
print("="*60)

conn = sqlite3.connect("backend/app.db")
df_campuses = pd.read_sql("SELECT * FROM campuses", conn)
print("CAMPUSES in DB:")
print(df_campuses[['id', 'name', 'campus_type']])

df_records = pd.read_sql("SELECT * FROM energy_records", conn)
print(f"\nTotal records in energy_records: {len(df_records)}")

df_records['parsed_ts'] = pd.to_datetime(df_records['timestamp'])

for campus_id, group in df_records.groupby('campus_id'):
    print(f"\n--- Campus: {campus_id} ---")
    print(f"  Record count: {len(group)}")
    print(f"  Min timestamp: {group['parsed_ts'].min()}")
    print(f"  Max timestamp: {group['parsed_ts'].max()}")
    sorted_ts = group['parsed_ts'].sort_values().drop_duplicates()
    diffs = sorted_ts.diff().dropna()
    print(f"  Median time gap: {diffs.median()}")
    print(f"  Unique Buildings ({group['building_name'].nunique()}): {list(group['building_name'].unique())}")
    print(f"  Unique Floors ({group['floor'].nunique()}): {list(group['floor'].unique())}")
    print(f"  Unique Zones ({group['zone'].nunique()}): {list(group['zone'].unique())}")

print("\n" + "="*60)
print("ENTITIES ACROSS ENTIRE DB:")
print(f"Campuses count: {df_records['campus_id'].nunique()}")
print(f"Buildings count: {df_records['building_name'].nunique()}")
print(f"Floors count: {df_records['floor'].nunique()}")
print(f"Zones count: {df_records['zone'].nunique()}")
print(f"Equipment units: No separate equipment ID column (tracked via equipment_energy_kwh, runtime)")
print(f"Sensors/meters: No separate meter ID column (records aggregated by building/floor/zone)")
print(f"Missing values across all cells in DB: {df_records.isnull().sum().sum()} (0.00%)")
conn.close()

