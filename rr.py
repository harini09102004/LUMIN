import pandas as pd
import os
from glob import glob
from functools import reduce
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
import joblib

# -----------------------
# 1. Paths
# -----------------------
meteo_folder = r'D:\Solar\Meteorological_dataset'
pv_folder = r'D:\Solar\PV_dataset'

# -----------------------
# 2. Load meteorological data
# -----------------------
meteo_files = glob(os.path.join(meteo_folder, '*.csv'))
meteo_dfs = []

for f in meteo_files:
    df = pd.read_csv(f)
    df['Timestamp'] = pd.to_datetime(df['Time'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['Timestamp']).drop(columns=['Time'])

    prefix = os.path.splitext(os.path.basename(f))[0]
    df = df.rename(columns={c: f"{prefix}_{c}" for c in df.columns if c != 'Timestamp'})
    df = df.sort_values('Timestamp')

    meteo_dfs.append(df)

if not meteo_dfs:
    raise ValueError("No meteorological files found")

meteo_data = reduce(
    lambda l, r: pd.merge_asof(l, r, on='Timestamp', direction='nearest'),
    meteo_dfs
)

# -----------------------
# 3. Load PV data
# -----------------------
zone_a1 = pd.read_csv(os.path.join(pv_folder, 'Zone A1.csv'))
zone_a1['Timestamp'] = pd.to_datetime(zone_a1['Time'], dayfirst=True, errors='coerce')
zone_a1 = zone_a1.dropna(subset=['Timestamp']).drop(columns=['Time']).sort_values('Timestamp')

zone_inv = pd.read_csv(os.path.join(pv_folder, 'Zone A1_Inverter.csv'), low_memory=False)
zone_inv['Timestamp'] = pd.to_datetime(zone_inv['Time'], dayfirst=True, errors='coerce')
zone_inv = zone_inv.dropna(subset=['Timestamp']).drop(columns=['Time']).sort_values('Timestamp')

pv_data = pd.merge_asof(zone_a1, zone_inv, on='Timestamp', direction='nearest')

# -----------------------
# 4. Merge all data
# -----------------------
data = pd.merge_asof(pv_data, meteo_data, on='Timestamp', direction='nearest')

# -----------------------
# 5. Time features
# -----------------------
data['Hour'] = data['Timestamp'].dt.hour
data['Weekday'] = data['Timestamp'].dt.weekday

# -----------------------
# 6. Features & target
# -----------------------
pv_cols = [
    'dcVoltage(V)',
    'L1_acCurrent(A)',
    'L2_acCurrent(A)',
    'L3_acCurrent(A)'
]

meteo_cols = [c for c in meteo_data.columns if c != 'Timestamp']
context_cols = ['Hour', 'Weekday']

features = [c for c in pv_cols + meteo_cols + context_cols if c in data.columns]
target = 'totalActivePower(W)'

data = data.dropna(subset=features + [target])

X = data[features]
y = data[target]

# -----------------------
# 7. Time-based split
# -----------------------
split_idx = int(len(data) * 0.8)

X_train = X.iloc[:split_idx]
y_train = y.iloc[:split_idx]
X_test = X.iloc[split_idx:]
y_test = y.iloc[split_idx:]

# -----------------------
# 8. Train Ridge Regression
# -----------------------
ridge_model = Ridge(
    alpha=10.0,      # higher alpha = more conservative
    random_state=42
)

ridge_model.fit(X_train, y_train)

# -----------------------
# 9. Evaluate
# -----------------------
y_pred = ridge_model.predict(X_test)
accuracy_percent = r2_score(y_test, y_pred) * 100

print(f"Ridge model accuracy on future data: {accuracy_percent:.2f}%")

# -----------------------
# 10. Save model
# -----------------------
joblib.dump(ridge_model, 'pv_ridge_model.pkl')
joblib.dump(features, 'pv_ridge_features.pkl')

print("Model saved as 'pv_ridge_model.pkl'")
print("Features saved as 'pv_ridge_features.pkl'")
