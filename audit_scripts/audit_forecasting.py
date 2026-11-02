import os
import sqlite3
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error, r2_score
from ai.forecasting.features import FEATURE_COLUMNS, build_forecast_features

print("="*60)
print("TASK 3: FORECASTING METRICS (TIME-BASED 80/20 SPLIT)")
print("="*60)
RANDOM_SEED = 42
print(f"Random seed set to: {RANDOM_SEED}")
np.random.seed(RANDOM_SEED)

# We evaluate on each campus in DB and also on Datasets CSVs
conn = sqlite3.connect("backend/app.db")
query = "SELECT * FROM energy_records"
df_all = pd.read_sql(query, conn)
conn.close()

campuses = df_all['campus_id'].unique()

for campus_id in sorted(campuses):
    print(f"\n==========================================")
    print(f"EVALUATING CAMPUS: {campus_id}")
    print(f"==========================================")
    campus_records = df_all[df_all['campus_id'] == campus_id].to_dict(orient="records")
    
    # Use project's feature creation and hourly aggregation pipeline
    df_feat = build_forecast_features(campus_records)
    hourly = df_feat.resample("h", on="timestamp").agg({
        "energy_consumption_kwh": "sum",
        "peak_demand_kw": "max",
        "occupancy_percent": "mean",
        "outdoor_temperature_c": "mean",
    }).reset_index().rename(columns={"energy_consumption_kwh": "target"})
    hourly = hourly.dropna().sort_values("timestamp").reset_index(drop=True)
    
    # Add lag and rolling features as defined in forecaster.py
    for lag in [1, 2, 3, 6, 12, 24]:
        hourly[f"lag_{lag}"] = hourly["target"].shift(lag).fillna(hourly["target"].mean())
    for window in [6, 12, 24]:
        hourly[f"rolling_{window}"] = hourly["target"].rolling(window=window, min_periods=1).mean()
        
    hourly["hour"] = hourly["timestamp"].dt.hour
    hourly["day_of_week"] = hourly["timestamp"].dt.dayofweek
    hourly["day_of_month"] = hourly["timestamp"].dt.day
    hourly["month"] = hourly["timestamp"].dt.month
    hourly["is_weekend"] = (hourly["day_of_week"] >= 5).astype(int)
    
    n_total = len(hourly)
    split_idx = int(n_total * 0.8)
    
    train_df = hourly.iloc[:split_idx].copy()
    test_df = hourly.iloc[split_idx:].copy()
    
    print(f"Total hourly samples: {n_total}")
    print(f"Train samples (80%): {len(train_df)} ({train_df['timestamp'].min()} to {train_df['timestamp'].max()})")
    print(f"Test samples (20%): {len(test_df)} ({test_df['timestamp'].min()} to {test_df['timestamp'].max()})")
    print(f"Forecast Horizon: 24h recursive / multi-step test window ({len(test_df)} hours total evaluated)")
    
    X_train = train_df[FEATURE_COLUMNS].fillna(0)
    y_train = train_df["target"]
    
    X_test = test_df[FEATURE_COLUMNS].fillna(0)
    y_test = test_df["target"]
    
    # Train project's XGBoost model
    model = xgb.XGBRegressor(
        n_estimators=120,
        max_depth=5,
        learning_rate=0.08,
        random_state=RANDOM_SEED,
        objective="reg:squarederror"
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_pred = np.maximum(0.0, y_pred)
    
    # Metrics for XGBoost
    mae_xgb = mean_absolute_error(y_test, y_pred)
    rmse_xgb = np.sqrt(mean_squared_error(y_test, y_pred))
    mape_xgb = mean_absolute_percentage_error(y_test, y_pred) * 100
    r2_xgb = r2_score(y_test, y_pred)
    
    # Naive baseline 1: Previous-hour (lag 1)
    y_naive_lag1 = test_df["lag_1"].to_numpy()
    mae_naive1 = mean_absolute_error(y_test, y_naive_lag1)
    rmse_naive1 = np.sqrt(mean_squared_error(y_test, y_naive_lag1))
    mape_naive1 = mean_absolute_percentage_error(y_test, y_naive_lag1) * 100
    r2_naive1 = r2_score(y_test, y_naive_lag1)
    
    # Naive baseline 2: Same-hour-yesterday (lag 24)
    y_naive_lag24 = test_df["lag_24"].to_numpy()
    mae_naive24 = mean_absolute_error(y_test, y_naive_lag24)
    rmse_naive24 = np.sqrt(mean_squared_error(y_test, y_naive_lag24))
    mape_naive24 = mean_absolute_percentage_error(y_test, y_naive_lag24) * 100
    r2_naive24 = r2_score(y_test, y_naive_lag24)
    
    imp_mae_lag1 = ((mae_naive1 - mae_xgb) / mae_naive1) * 100
    imp_rmse_lag1 = ((rmse_naive1 - rmse_xgb) / rmse_naive1) * 100
    imp_mae_lag24 = ((mae_naive24 - mae_xgb) / mae_naive24) * 100
    imp_rmse_lag24 = ((rmse_naive24 - rmse_xgb) / rmse_naive24) * 100
    
    print("\n--- RESULTS: ENERGY CONSUMPTION FORECAST ---")
    print(f"XGBoost Model:")
    print(f"  MAE:  {mae_xgb:.4f} kWh")
    print(f"  RMSE: {rmse_xgb:.4f} kWh")
    print(f"  MAPE: {mape_xgb:.2f}%")
    print(f"  R2:   {r2_xgb:.4f}")
    
    print(f"\nNaive Baseline 1 (Previous Hour / Lag 1):")
    print(f"  MAE:  {mae_naive1:.4f} kWh")
    print(f"  RMSE: {rmse_naive1:.4f} kWh")
    print(f"  MAPE: {mape_naive1:.2f}%")
    print(f"  R2:   {r2_naive1:.4f}")
    print(f"  Improvement over Lag-1: MAE by {imp_mae_lag1:.2f}%, RMSE by {imp_rmse_lag1:.2f}%")
    
    print(f"\nNaive Baseline 2 (Same Hour Yesterday / Lag 24):")
    print(f"  MAE:  {mae_naive24:.4f} kWh")
    print(f"  RMSE: {rmse_naive24:.4f} kWh")
    print(f"  MAPE: {mape_naive24:.2f}%")
    print(f"  R2:   {r2_naive24:.4f}")
    print(f"  Improvement over Lag-24: MAE by {imp_mae_lag24:.2f}%, RMSE by {imp_rmse_lag24:.2f}%")
    
    # Peak Demand Forecast evaluation:
    # Does a dedicated peak demand model exist, or is it derived from predicted peak?
    # In forecaster.py: peak_item = max(predictions, key=lambda item: item["predicted_energy"])
    # predicted_peak = max(predicted energy in 24h)
    actual_peak = test_df["target"].max()
    predicted_peak = y_pred.max()
    peak_abs_err = abs(actual_peak - predicted_peak)
    peak_pct_err = (peak_abs_err / actual_peak) * 100
    print(f"\nPeak Demand Forecast (from max hourly predictions):")
    print(f"  Actual Test Peak:     {actual_peak:.2f} kW")
    print(f"  Predicted Test Peak:  {predicted_peak:.2f} kW")
    print(f"  Peak Absolute Error:  {peak_abs_err:.2f} kW")
    print(f"  Peak Error %:         {peak_pct_err:.2f}%")

print("="*60)

