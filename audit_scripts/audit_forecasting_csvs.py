import os
import glob
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error, r2_score
from app.utils.data_mapping import map_columns

print("="*60)
print("TASK 3 EVALUATION ON RAW CSV DATASETS (Datasets/*.csv)")
print("="*60)
RANDOM_SEED = 42

FEATURE_COLS = [
    "hour", "day_of_week", "day_of_month", "is_weekend",
    "occupancy_percent", "outdoor_temperature_c",
    "lag_1", "lag_2", "lag_3", "lag_6", "lag_12", "lag_24",
    "rolling_6", "rolling_12", "rolling_24"
]

for f in sorted(glob.glob("Datasets/*.csv")):
    fname = os.path.basename(f)
    enc = 'latin1' if '1' in f else 'utf-8'
    df = pd.read_csv(f, encoding=enc)
    mapping = map_columns(list(df.columns))
    df = df.rename(columns={orig: canon for canon, orig in mapping.items()})
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Resample hourly
    hourly = df.groupby('timestamp').agg({
        'energy_consumption_kwh': 'sum',
        'peak_demand_kw': 'max',
        'occupancy_percent': 'mean',
        'outdoor_temperature_c': 'mean'
    }).reset_index().rename(columns={'energy_consumption_kwh': 'target'}).sort_values('timestamp').reset_index(drop=True)
    
    if len(hourly) < 20:
        # If timestamps are not across many hours, evaluate row-level time series
        hourly = df.sort_values('timestamp').reset_index(drop=True).rename(columns={'energy_consumption_kwh': 'target'})
    
    for lag in [1, 2, 3, 6, 12, 24]:
        hourly[f"lag_{lag}"] = hourly["target"].shift(lag).fillna(hourly["target"].mean())
    for window in [6, 12, 24]:
        hourly[f"rolling_{window}"] = hourly["target"].rolling(window=window, min_periods=1).mean()
        
    hourly["hour"] = hourly["timestamp"].dt.hour
    hourly["day_of_week"] = hourly["timestamp"].dt.dayofweek
    hourly["day_of_month"] = hourly["timestamp"].dt.day
    hourly["is_weekend"] = (hourly["day_of_week"] >= 5).astype(int)
    
    n_total = len(hourly)
    split_idx = int(n_total * 0.8)
    
    train_df = hourly.iloc[:split_idx]
    test_df = hourly.iloc[split_idx:]
    
    X_train = train_df[FEATURE_COLS].fillna(0)
    y_train = train_df["target"]
    X_test = test_df[FEATURE_COLS].fillna(0)
    y_test = test_df["target"]
    
    model = xgb.XGBRegressor(
        n_estimators=100, max_depth=5, learning_rate=0.08, random_state=RANDOM_SEED
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    mae_xgb = mean_absolute_error(y_test, y_pred)
    rmse_xgb = np.sqrt(mean_squared_error(y_test, y_pred))
    mape_xgb = mean_absolute_percentage_error(y_test, y_pred) * 100
    r2_xgb = r2_score(y_test, y_pred)
    
    y_naive_lag1 = test_df["lag_1"].to_numpy()
    mae_naive1 = mean_absolute_error(y_test, y_naive_lag1)
    rmse_naive1 = np.sqrt(mean_squared_error(y_test, y_naive_lag1))
    mape_naive1 = mean_absolute_percentage_error(y_test, y_naive_lag1) * 100
    r2_naive1 = r2_score(y_test, y_naive_lag1)
    
    y_naive_lag24 = test_df["lag_24"].to_numpy()
    mae_naive24 = mean_absolute_error(y_test, y_naive_lag24)
    rmse_naive24 = np.sqrt(mean_squared_error(y_test, y_naive_lag24))
    mape_naive24 = mean_absolute_percentage_error(y_test, y_naive_lag24) * 100
    r2_naive24 = r2_score(y_test, y_naive_lag24)
    
    imp_mae_lag1 = ((mae_naive1 - mae_xgb) / mae_naive1) * 100
    imp_rmse_lag1 = ((rmse_naive1 - rmse_xgb) / rmse_naive1) * 100
    
    imp_mae_lag24 = ((mae_naive24 - mae_xgb) / mae_naive24) * 100
    imp_rmse_lag24 = ((rmse_naive24 - rmse_xgb) / rmse_naive24) * 100
    
    actual_peak = test_df["target"].max()
    pred_peak = y_pred.max()
    
    print(f"\n--- File: {fname} ---")
    print(f"Total samples: {n_total}, Train (80%): {len(train_df)}, Test (20%): {len(test_df)}")
    print(f"XGBoost  -> MAE: {mae_xgb:.4f}, RMSE: {rmse_xgb:.4f}, MAPE: {mape_xgb:.2f}%, R2: {r2_xgb:.4f}")
    print(f"Naive-1h -> MAE: {mae_naive1:.4f}, RMSE: {rmse_naive1:.4f}, MAPE: {mape_naive1:.2f}%, R2: {r2_naive1:.4f}")
    print(f"  Improvement over Naive-1h: MAE {imp_mae_lag1:+.2f}%, RMSE {imp_rmse_lag1:+.2f}%")
    print(f"Naive-24h-> MAE: {mae_naive24:.4f}, RMSE: {rmse_naive24:.4f}, MAPE: {mape_naive24:.2f}%, R2: {r2_naive24:.4f}")
    print(f"  Improvement over Naive-24h: MAE {imp_mae_lag24:+.2f}%, RMSE {imp_rmse_lag24:+.2f}%")
    print(f"Peak Demand: Actual={actual_peak:.2f}, Predicted={pred_peak:.2f}, Err={abs(actual_peak-pred_peak):.2f} ({abs(actual_peak-pred_peak)/actual_peak*100:.2f}%)")

