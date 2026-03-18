"""
retrain_small.py
Retrains with a much smaller model (10 trees instead of 50)
Result will be ~15MB instead of 68MB
Run from: C:\\Users\\WAFI\\irish-property-insights
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import joblib
import json
import os

print("Loading PPR data...")
df = pd.read_csv("PPR-ALL.csv", encoding="latin-1", low_memory=False)
df.columns = ["date_of_sale","address","county","eircode","price",
              "not_full_market_price","vat_exclusive","description",
              "property_size_desc"]

df["price"] = df["price"].astype(str).str.replace(r"[^\d.]","",regex=True)
df["price"] = pd.to_numeric(df["price"], errors="coerce")
df = df[df["not_full_market_price"].astype(str).str.strip() == "No"].copy()
df = df.dropna(subset=["price","county","description"])
df = df[(df["price"] >= 30000) & (df["price"] <= 3_000_000)]
df["year"] = pd.to_datetime(df["date_of_sale"], dayfirst=True, errors="coerce").dt.year
df["micro"] = df["address"].astype(str).str.split(",").str[-2].str.strip().str.title()

print(f"Training on {len(df):,} rows...")

le_county = LabelEncoder(); df["county_enc"] = le_county.fit_transform(df["county"].astype(str))
le_desc   = LabelEncoder(); df["desc_enc"]   = le_desc.fit_transform(df["description"].astype(str))
le_micro  = LabelEncoder(); df["micro_enc"]  = le_micro.fit_transform(df["micro"].astype(str))

X = df[["county_enc","micro_enc","desc_enc","year"]]
y = np.log1p(df["price"])

# Use only 10 trees — still accurate enough, much smaller file
model = RandomForestRegressor(n_estimators=10, n_jobs=-1, random_state=42, max_depth=20)
model.fit(X, y)

joblib.dump(model, "deal_scorer_model.pkl", compress=9)
joblib.dump(le_county, "le_county.pkl", compress=9)
joblib.dump(le_desc,   "le_desc.pkl",   compress=9)
joblib.dump(le_micro,  "le_micro.pkl",  compress=9)

known = {
    "counties": sorted(df["county"].dropna().unique().tolist()),
    "descriptions": sorted(df["description"].dropna().unique().tolist())
}
with open("known_values.json","w") as f:
    json.dump(known, f)

size = os.path.getsize("deal_scorer_model.pkl") / 1024 / 1024
print(f"Model saved: {size:.1f} MB")
print("Done! Now run:")
print("  git add deal_scorer_model.pkl le_county.pkl le_desc.pkl le_micro.pkl known_values.json")
print("  git commit -m \"Smaller model for Railway\"")
print("  git push")
