import pandas as pd
import numpy as np
import joblib
import time
import glob
from functools import reduce
from datetime import datetime, timedelta

# ----------------------------
# CONFIG
# ----------------------------
METEO_DIR = "Meteorological_dataset"
PV_DIR = "PV_dataset"

ZONE_FILE = f"{PV_DIR}/Zone A4.csv"
INVERTER_FILE = f"{PV_DIR}/Zone A4_Inverter.csv"

MODEL_FILE = "pv_baseline_model.pkl"
FEATURE_FILE = "pv_model_features.pkl"

SLEEP_SECONDS = 5  # simulate live feed

# ----------------------------
# LOAD MODEL
# ----------------------------
model = joblib.load(MODEL_FILE)
features = joblib.load(FEATURE_FILE)
print("Model loaded")

# ----------------------------
# LOAD METEOROLOGICAL DATA
# ----------------------------
def load_meteorological_data():
    dfs = []

    for file in glob.glob(f"{METEO_DIR}/*.csv"):
        name = file.split("\\")[-1].replace(".csv", "")
        df = pd.read_csv(file, low_memory=False)

        df["Timestamp"] = pd.to_datetime(
            df["Time"], format="mixed", dayfirst=True, errors="coerce"
        )
        df = df.dropna(subset=["Timestamp"])

        value_cols = [c for c in df.columns if c not in ["Time", "Timestamp"]]
        for col in value_cols:
            df.rename(columns={col: f"{name}_{col}"}, inplace=True)

        dfs.append(df[["Timestamp"] + [c for c in df.columns if c.startswith(name)]])

    if not dfs:
        raise RuntimeError("No meteorological CSV files found")

    meteo = reduce(
        lambda l, r: pd.merge_asof(
            l.sort_values("Timestamp"),
            r.sort_values("Timestamp"),
            on="Timestamp",
            tolerance=pd.Timedelta("5min"),
            direction="nearest",
        ),
        dfs,
    )
    return meteo

# ----------------------------
# LOAD PV DATA
# ----------------------------
zone = pd.read_csv(ZONE_FILE, low_memory=False)
zone["Timestamp"] = pd.to_datetime(zone["Time"], format="mixed", dayfirst=True, errors="coerce")
zone = zone.dropna(subset=["Timestamp"])

inverter = pd.read_csv(INVERTER_FILE, low_memory=False)
inverter["Timestamp"] = pd.to_datetime(inverter["Time"], format="mixed", dayfirst=True, errors="coerce")
inverter = inverter.dropna(subset=["Timestamp"])

# ----------------------------
# MERGE DATA
# ----------------------------
meteo = load_meteorological_data()

pv = pd.merge_asof(
    zone.sort_values("Timestamp"),
    inverter.sort_values("Timestamp"),
    on="Timestamp",
    tolerance=pd.Timedelta("5min"),
    direction="nearest",
)

data = pd.merge_asof(
    pv.sort_values("Timestamp"),
    meteo.sort_values("Timestamp"),
    on="Timestamp",
    tolerance=pd.Timedelta("5min"),
    direction="nearest",
)

# ----------------------------
# TIME FEATURES (REAL CALENDAR)
# ----------------------------
data["Hour"] = data["Timestamp"].dt.hour
data["Minute"] = data["Timestamp"].dt.minute
data["Weekday"] = data["Timestamp"].dt.weekday

# ----------------------------
# SAFE FEATURE HANDLING (CRITICAL FIX)
# ----------------------------
missing = [f for f in features if f not in data.columns]
if missing:
    raise RuntimeError(f"Model features missing in dataset: {missing}")

# Fill instead of dropping everything
data[features] = data[features].ffill().bfill()

print(f"Live dataset ready: {len(data)} rows")
print("\nSimulated live prediction started...\n")

# ----------------------------
# LIVE SIMULATION LOOP
# ----------------------------
try:
    while True:
        now = datetime.now()

        # match full calendar date + time
        candidates = data[
            (data["Timestamp"].dt.date == now.date())
            & (
                (data["Hour"] < now.hour)
                | ((data["Hour"] == now.hour) & (data["Minute"] <= now.minute))
            )
        ]

        # fallback: latest available data
        if candidates.empty:
            row = data.iloc[-1]
        else:
            row = candidates.iloc[-1]

        X = pd.DataFrame([row[features]], columns=features)
        predicted = model.predict(X)[0]

        actual = row.get("totalActivePower(W)", 0.0)
        irradiance = float(row.filter(like="Irradiance").iloc[0])

        ts = now.strftime("%d-%m %H:%M")

        # ----------------------------
        # INTERPRETATION LAYER
        # ----------------------------
        if irradiance < 200:
            status = "Normal (low sun angle)"
        elif actual >= 0.9 * predicted:
            status = "Healthy"
        elif actual < 0.85 * predicted:
            status = "Underperformance → Possible soiling / shading / fault"
        else:
            status = "Performance drift suspected"

        print(
            f"[{ts}] "
            f"Irr={irradiance:.0f} W/m² | "
            f"Expected={predicted:.1f} W | "
            f"Actual={actual:.1f} W | "
            f"{status}"
        )

        time.sleep(SLEEP_SECONDS)

except KeyboardInterrupt:
    print("\nPrediction stopped by user.")
