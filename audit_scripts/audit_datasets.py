import os
import glob
import pandas as pd
import numpy as np

print("="*60)
print("AUDIT: DATASETS INSPECTION (HANDLING ENCODINGS)")
print("="*60)

datasets_folder = "Datasets"
files = glob.glob(os.path.join(datasets_folder, "*.csv"))
# Also check backend/datasets
b_files = glob.glob(os.path.join("backend", "datasets", "*.csv"))
all_found = [("Datasets", f) for f in files] + [("backend/datasets", f) for f in b_files]

print(f"Found {len(all_found)} CSV files across Datasets and backend/datasets:")

total_records = 0
all_dfs = []

for folder, f in sorted(all_found):
    size_bytes = os.path.getsize(f)
    df = None
    used_encoding = None
    for enc in ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']:
        try:
            df = pd.read_csv(f, encoding=enc)
            used_encoding = enc
            break
        except Exception:
            continue
            
    if df is None:
        print(f"Could not read {f}")
        continue
        
    total_records += len(df)
    print(f"\n--- File: {folder}/{os.path.basename(f)} ---")
    print(f"Size (bytes): {size_bytes} ({size_bytes/1024:.2f} KB)")
    print(f"Encoding used: {used_encoding}")
    print(f"Row count: {len(df)}")
    print(f"Columns ({len(df.columns)}): {list(df.columns)}")
    print(f"First 2 rows:")
    print(df.head(2))
    print("Null count per column:")
    print(df.isnull().sum().to_dict())
    
    # Try finding timestamp column
    ts_col = None
    for c in df.columns:
        if any(term in c.lower() for term in ['time', 'date', 'ts', 'hour']):
            ts_col = c
            break
            
    if ts_col:
        try:
            df['parsed_ts'] = pd.to_datetime(df[ts_col])
            min_ts = df['parsed_ts'].min()
            max_ts = df['parsed_ts'].max()
            sorted_ts = df['parsed_ts'].sort_values().drop_duplicates()
            diffs = sorted_ts.diff().dropna()
            median_interval = diffs.median() if len(diffs) > 0 else "N/A"
            print(f"Timestamp column: '{ts_col}'")
            print(f"Min timestamp: {min_ts}")
            print(f"Max timestamp: {max_ts}")
            print(f"Median time gap: {median_interval}")
        except Exception as e:
            print(f"Could not parse timestamp in '{ts_col}': {e}")
    else:
        print("No timestamp column found")
        
    all_dfs.append((os.path.basename(f), df))

print("\n" + "="*60)
print(f"TOTAL ROWS ACROSS ALL CSV FILES IN Datasets/: {sum(len(d) for name, d in all_dfs if 'sample' not in name)}")
print(f"TOTAL ROWS INCLUDING backend/datasets: {total_records}")
print("="*60)
