import os
import sqlite3
import pandas as pd
import numpy as np
from ai.anomaly.detector import detect_anomalies_for_campus
from sklearn.metrics import precision_score, recall_score, f1_score

print("="*60)
print("TASK 4: ANOMALY DETECTION METRICS & SYNTHETIC INJECTION")
print("="*60)
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# Part A: Run on real seeded campus records
conn = sqlite3.connect("backend/app.db")
query = "SELECT * FROM energy_records"
df_records = pd.read_sql(query, conn)
conn.close()

campuses = df_records['campus_id'].unique()

print("\n--- PART A: PROJECT DETECTOR ON CURRENT CAMPUS DATA ---")
print("Detector parameters: IsolationForest(contamination=0.1, random_state=42, n_estimators=200)")
print("Decision rule: (|z_score| >= 1.9) | (iso_scores >= 0.7) | (|deviation| >= 12%)")

for cid in sorted(campuses):
    records = df_records[df_records['campus_id'] == cid].to_dict(orient="records")
    res = detect_anomalies_for_campus(cid, records)
    total = res['total_records']
    detected = res['anomalies_detected']
    pct = (detected / total) * 100 if total else 0
    print(f"\nCampus '{cid}':")
    print(f"  Total records: {total}")
    print(f"  Flagged anomalies: {detected} ({pct:.2f}%)")
    print(f"  Severity Distribution: CRITICAL={res['critical']}, HIGH={res['high']}, MEDIUM={res['medium']}, LOW={res['low']}")
    
    # Root cause samples
    if res['anomalies']:
        print(f"  Sample Root Cause: {res['anomalies'][0]['root_cause']}")

# Check real anomaly labels
print("\n--- REAL ANOMALY LABELS CHECK ---")
has_real_labels = "is_anomaly" in df_records.columns or "anomaly" in df_records.columns
print(f"Real anomaly label column present in dataset: {has_real_labels}")
if not has_real_labels:
    print("Real anomaly labels: NOT AVAILABLE (no ground-truth anomaly label column in datasets or DB).")

# Part B: Synthetic Validation
print("\n--- PART B: SYNTHETIC INJECTION TEST (CONTROLLED VALIDATION) ---")
print(f"Random seed: {RANDOM_SEED}")
# We inject N known anomalies into a COPY of each campus data.
# For each campus: inject N = 50 anomalies (25 spikes +40%, 25 drops -40%) at random timestamps.
for cid in sorted(campuses):
    campus_df = df_records[df_records['campus_id'] == cid].copy().sort_values("timestamp").reset_index(drop=True)
    N_spikes = 25
    N_drops = 25
    N_total_injected = N_spikes + N_drops
    
    # Ground truth array
    y_true = np.zeros(len(campus_df), dtype=int)
    
    # Randomly select indices (seeded)
    rng = np.random.default_rng(RANDOM_SEED)
    chosen_indices = rng.choice(len(campus_df), size=N_total_injected, replace=False)
    spike_indices = chosen_indices[:N_spikes]
    drop_indices = chosen_indices[N_spikes:]
    
    # Inject +40% spikes
    campus_df.loc[spike_indices, 'energy_consumption_kwh'] *= 1.40
    # Inject -40% drops
    campus_df.loc[drop_indices, 'energy_consumption_kwh'] *= 0.60
    
    y_true[chosen_indices] = 1
    
    # Run project's detector
    records_copy = campus_df.to_dict(orient="records")
    res_synthetic = detect_anomalies_for_campus(cid, records_copy)
    
    # Flagged indices
    flagged_timestamps = set(a['timestamp'] for a in res_synthetic['anomalies'])
    campus_df['iso_ts'] = pd.to_datetime(campus_df['timestamp']).dt.strftime('%Y-%m-%dT%H:%M:%S')
    y_pred = campus_df['iso_ts'].isin(flagged_timestamps).astype(int).to_numpy()
    
    # Compute precision, recall, F1 specifically on synthetic injection test
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    
    print(f"\n[synthetic injection test] Campus '{cid}':")
    print(f"  Injected anomalies N: {N_total_injected} (25 spikes +40%, 25 drops -40%)")
    print(f"  Total records: {len(campus_df)}")
    print(f"  Total flagged by detector: {res_synthetic['anomalies_detected']}")
    print(f"  Correctly detected injected (True Positives): {np.sum((y_true == 1) & (y_pred == 1))}/{N_total_injected}")
    print(f"  Precision: {prec:.4f}")
    print(f"  Recall:    {rec:.4f}")
    print(f"  F1 Score:  {f1:.4f}")

# Part C: Root-cause categories count
print("\n--- PART C: ROOT-CAUSE CATEGORIES ---")
# Count distinct branches in ai/anomaly/detector.py and app/ml/anomaly_detector.py
print("In ai/anomaly/detector.py (_root_cause_text): 4 distinct conditional categories:")
print("  1. Inefficient HVAC operation during low occupancy (HVAC dominant & occupancy < 70)")
print("  2. Equipment load dominant contributor")
print("  3. HVAC dominant contributor with elevated runtimes")
print("  4. Combination of load drivers exceeding baseline")
print("In app/ml/anomaly_detector.py (_root_causes): 6 distinct root-cause categories:")
print("  1. HVAC energy significantly above baseline (>1.2x)")
print("  2. Lighting load elevated vs baseline (>1.2x)")
print("  3. Equipment load above expected levels (>1.2x)")
print("  4. High energy during low occupancy (<0.7x baseline occupancy)")
print("  5. HVAC runtime exceeds baseline (>1.25x)")
print("  6. Elevated outdoor temperature increasing HVAC load (>3C)")
print("Total root-cause rules/categories defined: 10 across both detector modules (4 in active ai/ service).")

