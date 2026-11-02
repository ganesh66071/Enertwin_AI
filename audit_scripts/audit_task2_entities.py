import os
import glob
import pandas as pd
import numpy as np
from app.utils.data_cleaning import clean_dataframe
from app.utils.data_mapping import map_columns

print("="*60)
print("TASK 2 DEEP DIVE: ENTITIES & CLEANING")
print("="*60)

files = sorted(glob.glob("Datasets/*.csv"))

campuses_set = set()
buildings_set = set()
floors_set = set()
zones_rooms_set = set()
building_ids_set = set()

total_raw_rows = 0
total_cells = 0
total_null_cells = 0
total_exact_duplicates = 0
total_cleaned_rows = 0
all_warnings = []

for f in files:
    enc = 'latin1' if '1' in f else 'utf-8'
    df = pd.read_csv(f, encoding=enc)
    n_raw = len(df)
    total_raw_rows += n_raw
    total_cells += df.size
    null_in_file = df.isnull().sum().sum()
    total_null_cells += null_in_file
    
    dups_in_file = df.duplicated().sum()
    total_exact_duplicates += dups_in_file
    
    cleaned_df, warnings = clean_dataframe(df)
    total_cleaned_rows += len(cleaned_df)
    all_warnings.extend(warnings)
    
    print(f"\nFile: {os.path.basename(f)}")
    print(f"  Raw rows: {n_raw}, Duplicates: {dups_in_file}, Null cells: {null_in_file} ({null_in_file/df.size*100:.2f}%)")
    
    for col in df.columns:
        cl = col.lower()
        if 'building name' in cl or cl == 'building_name':
            buildings_set.update(df[col].dropna().unique())
        if 'building id' in cl or cl == 'building_id':
            building_ids_set.update(df[col].dropna().unique())
        if 'floor' in cl:
            floors_set.update(df[col].dropna().unique())
        if 'zone' in cl or 'room' in cl:
            zones_rooms_set.update(df[col].dropna().unique())

print("\n" + "="*60)
print("AGGREGATE SUMMARY ACROSS Datasets/*.csv:")
print(f"Total raw records: {total_raw_rows}")
print(f"Total cells: {total_cells}")
print(f"Total null cells: {total_null_cells}")
print(f"Overall missing-value %: {(total_null_cells / total_cells) * 100:.4f}%")
print(f"Exact duplicates across rows: {total_exact_duplicates}")
print(f"Cleaning warnings: {all_warnings}")
print(f"Rows after clean_dataframe: {total_cleaned_rows}")

print(f"\nUnique Building IDs ({len(building_ids_set)}): {sorted(list(building_ids_set))}")
print(f"Unique Building Names ({len(buildings_set)}): {sorted(list(buildings_set))}")
print(f"Unique Floors ({len(floors_set)}): {sorted(list(floors_set))}")
print(f"Unique Zones/Rooms ({len(zones_rooms_set)}): {sorted(list(zones_rooms_set))}")

# Check if there are columns for equipment or sensors/meters in dataset
for f in files:
    enc = 'latin1' if '1' in f else 'utf-8'
    df = pd.read_csv(f, encoding=enc)
    eq_cols = [c for c in df.columns if any(k in c.lower() for k in ['equip', 'meter', 'sensor', 'unit'])]
    print(f"Columns related to equipment/sensors in {os.path.basename(f)}: {eq_cols}")

print("="*60)
