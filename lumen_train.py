import pandas as pd
import os
from glob import glob
from functools import reduce
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
import joblib

# -----------------------
# 1. Paths to folders
# -----------------------
meteo_folder = r'D:\Solar\Meteorological_dataset'
pv_folder = r'D:\Solar\PV_dataset'

# -----------------------
# 2. Load all meteorological CSV files dynamically
# -----------------------
meteo_files = glob(os.path.join(meteo_folder, '*.csv'))
meteo_dfs = []

for f in meteo_files:
    df = pd.read_csv(f)
    df['Timestamp'] = pd.to_datetime(df['Time'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['Timestamp'])
    df = df.drop(columns=['Time'])

    # Prefix all columns with CSV name for uniqueness
    csv_prefix = os.path.splitext(os.path.basename(f))[0]
    df = df.rename(columns={c: f"{csv_prefix}_{c}" for c in df.columns if c != 'Timestamp'})
    
    df = df.sort_values('Timestamp')
    meteo_dfs.append(df)

if len(meteo_dfs) == 0:
    raise ValueError("No meteorological CSV files found!")

# Merge all meteorological variables by nearest timestamp
meteo_data = reduce(lambda left, right: pd.merge_asof(
    left, right,
    on='Timestamp',
    direction='nearest'
), meteo_dfs)

print("Meteorological columns detected:", list(meteo_data.columns))

# -----------------------
# 3. Load PV CSV files
# -----------------------
zone_a1_file = os.path.join(pv_folder, 'Zone A1.csv')
zone_inv_file = os.path.join(pv_folder, 'Zone A1_Inverter.csv')

zone_a1 = pd.read_csv(zone_a1_file)
zone_a1['Timestamp'] = pd.to_datetime(zone_a1['Time'], dayfirst=True, errors='coerce')
zone_a1 = zone_a1.dropna(subset=['Timestamp']).drop(columns=['Time']).sort_values('Timestamp')

zone_inv = pd.read_csv(zone_inv_file, low_memory=False)
zone_inv['Timestamp'] = pd.to_datetime(zone_inv['Time'], dayfirst=True, errors='coerce')
zone_inv = zone_inv.dropna(subset=['Timestamp']).drop(columns=['Time']).sort_values('Timestamp')

# Merge Zone A1 and Inverter data
pv_data = pd.merge_asof(zone_a1, zone_inv, on='Timestamp', direction='nearest')

# -----------------------
# 4. Merge PV and meteorological data
# -----------------------
data = pd.merge_asof(pv_data, meteo_data, on='Timestamp', direction='nearest')
print("Final merged columns:", list(data.columns))

# -----------------------
# 5. Add usage context features
# -----------------------
data['Hour'] = data['Timestamp'].dt.hour
data['Weekday'] = data['Timestamp'].dt.weekday

# -----------------------
# 6. Define features and target dynamically
# -----------------------
pv_cols = ['dcVoltage(V)','L1_acCurrent(A)','L2_acCurrent(A)','L3_acCurrent(A)']
meteo_cols = [c for c in meteo_data.columns if c != 'Timestamp']
context_cols = ['Hour','Weekday']

features = [c for c in pv_cols + meteo_cols + context_cols if c in data.columns]
target = 'totalActivePower(W)'

data = data.dropna(subset=features + [target])
X = data[features]
y = data[target]

# -----------------------
# 7. Time-based train-test split (first 80% train, last 20% test)
# -----------------------
split_idx = int(len(data) * 0.8)
X_train = X.iloc[:split_idx]
y_train = y.iloc[:split_idx]
X_test = X.iloc[split_idx:]
y_test = y.iloc[split_idx:]

# Train Random Forest
baseline_model = RandomForestRegressor(n_estimators=200, random_state=42)
baseline_model.fit(X_train, y_train)

# Predict on test set
y_pred_test = baseline_model.predict(X_test)

# -----------------------
# 8. Accuracy as percentage on future (test) data
# -----------------------
accuracy_percent = r2_score(y_test, y_pred_test) * 100
print(f"Model accuracy on future (test) data: {accuracy_percent:.2f}%")

# -----------------------
# 9. Save trained model and features for future testing
# -----------------------
joblib.dump(baseline_model, 'pv_baseline_model.pkl')
joblib.dump(features, 'pv_model_features.pkl')
print("Trained model saved as 'pv_baseline_model.pkl'")
print("Feature list saved as 'pv_model_features.pkl'")
