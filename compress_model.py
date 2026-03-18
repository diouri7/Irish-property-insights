"""
compress_model.py
Compresses the model using joblib's built-in compression
to get it small enough to push to GitHub (under 100MB)
Run from: C:\\Users\\WAFI\\irish-property-insights
"""
import joblib
import os

print("Loading model...")
model = joblib.load("deal_scorer_model.pkl")

print("Original size:", os.path.getsize("deal_scorer_model.pkl") / 1024 / 1024, "MB")

# Try different compression levels
for level in [3, 6, 9]:
    fname = f"model_compressed_{level}.pkl"
    joblib.dump(model, fname, compress=level)
    size = os.path.getsize(fname) / 1024 / 1024
    print(f"Compression level {level}: {size:.1f} MB")

print("\nDone. Check which size is under 100MB.")
print("If any are under 100MB, we can push to GitHub directly.")
