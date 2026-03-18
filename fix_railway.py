"""
fix_railway.py
Run from: C:\\Users\\WAFI\\irish-property-insights
What it does:
  1. Reads your existing app.py
  2. Replaces the deal-checker route with a version that
     retrains the model on Railway if .pkl files are missing
  3. Saves app.py ready to push
"""

import os, re

APP_PATH = "app.py"

NEW_ROUTE = '''
# ── DEAL CHECKER ──────────────────────────────────────────────
import threading
_model_cache = {}

def _load_or_train():
    import joblib, json, numpy as np
    import pandas as pd
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import LabelEncoder

    pkl = "deal_scorer_model.pkl"

    # Already trained?
    if os.path.exists(pkl):
        try:
            _model_cache["model"]    = joblib.load(pkl)
            _model_cache["le_county"] = joblib.load("le_county.pkl")
            _model_cache["le_desc"]   = joblib.load("le_desc.pkl")
            _model_cache["le_micro"]  = joblib.load("le_micro.pkl")
            with open("known_values.json") as f:
                _model_cache["known"] = json.load(f)
            _model_cache["ready"] = True
            print("Model loaded from disk.")
            return
        except Exception as e:
            print("Load failed, retraining:", e)

    # Download PPR CSV
    csv_path = "PPR-ALL.csv"
    if not os.path.exists(csv_path):
        print("Downloading PPR CSV…")
        import urllib.request
        url = "https://propertypriceregister.ie/website/npsra/ppr/npsra-ppr.nsf/Downloads/PPR-ALL.zip/$FILE/PPR-ALL.zip"
        try:
            urllib.request.urlretrieve(url, "PPR-ALL.zip")
            import zipfile
            with zipfile.ZipFile("PPR-ALL.zip", "r") as z:
                z.extractall(".")
            print("PPR CSV downloaded and extracted.")
        except Exception as e:
            print("Download failed:", e)
            _model_cache["ready"] = False
            _model_cache["error"] = str(e)
            return

    print("Training model…")
    try:
        df = pd.read_csv(csv_path, encoding="latin-1", low_memory=False)
        df.columns = ["date_of_sale","address","county","eircode","price",
                      "not_full_market_price","vat_exclusive","description",
                      "property_size_desc"]
        df["price"] = df["price"].astype(str).str.replace(r"[^\\d.]","",regex=True)
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        df = df[df["not_full_market_price"].astype(str).str.strip() == "No"].copy()
        df = df.dropna(subset=["price","county","description"])
        df = df[(df["price"] >= 30000) & (df["price"] <= 3_000_000)]
        df["year"] = pd.to_datetime(df["date_of_sale"], dayfirst=True, errors="coerce").dt.year
        df["micro"] = df["address"].astype(str).str.split(",").str[-2].str.strip().str.title()

        le_county = LabelEncoder(); df["county_enc"] = le_county.fit_transform(df["county"].astype(str))
        le_desc   = LabelEncoder(); df["desc_enc"]   = le_desc.fit_transform(df["description"].astype(str))
        le_micro  = LabelEncoder(); df["micro_enc"]  = le_micro.fit_transform(df["micro"].astype(str))

        import numpy as np
        X = df[["county_enc","micro_enc","desc_enc","year"]]
        y = np.log1p(df["price"])

        model = RandomForestRegressor(n_estimators=50, n_jobs=-1, random_state=42)
        model.fit(X, y)

        joblib.dump(model,    "deal_scorer_model.pkl")
        joblib.dump(le_county,"le_county.pkl")
        joblib.dump(le_desc,  "le_desc.pkl")
        joblib.dump(le_micro, "le_micro.pkl")
        known = {"counties": sorted(df["county"].dropna().unique().tolist()),
                 "descriptions": sorted(df["description"].dropna().unique().tolist())}
        with open("known_values.json","w") as f:
            json.dump(known, f)

        _model_cache["model"]     = model
        _model_cache["le_county"] = le_county
        _model_cache["le_desc"]   = le_desc
        _model_cache["le_micro"]  = le_micro
        _model_cache["known"]     = known
        _model_cache["ready"]     = True
        print("Model trained and saved.")
    except Exception as e:
        print("Training failed:", e)
        _model_cache["ready"] = False
        _model_cache["error"] = str(e)

# Start training in background when app boots
threading.Thread(target=_load_or_train, daemon=True).start()


COUNTIES_LIST = [
    "Carlow","Cavan","Clare","Cork","Donegal","Dublin","Galway","Kerry",
    "Kildare","Kilkenny","Laois","Leitrim","Limerick","Longford","Louth",
    "Mayo","Meath","Monaghan","Offaly","Roscommon","Sligo","Tipperary",
    "Waterford","Westmeath","Wexford","Wicklow"
]

@app.route("/deal-checker", methods=["GET", "POST"])
def deal_checker():
    import numpy as np

    county_opts = "\\n".join(
        f\'<option value="{c}">{c}</option>\' for c in COUNTIES_LIST
    )

    FORM_HTML = f"""<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Deal Checker | Irish Property Insights</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root{{--ink:#0f1014;--paper:#f5f2ec;--gold:#c9a84c;--muted:#6b6860;--border:#ddd8ce;}}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:var(--paper);color:var(--ink);font-family:\'DM Sans\',sans-serif;min-height:100vh;}}
nav{{border-bottom:1px solid var(--border);padding:1.2rem 2rem;display:flex;align-items:center;justify-content:space-between;background:var(--paper);}}
.nav-logo{{font-family:\'Playfair Display\',serif;font-size:1.2rem;font-weight:700;color:var(--ink);text-decoration:none;}}
.hero{{padding:4rem 2rem 2rem;max-width:700px;margin:0 auto;text-align:center;}}
.hero-tag{{display:inline-block;font-size:0.72rem;font-weight:500;letter-spacing:0.15em;text-transform:uppercase;color:var(--gold);border:1px solid var(--gold);padding:0.3rem 0.8rem;border-radius:2px;margin-bottom:1.5rem;}}
.hero h1{{font-family:\'Playfair Display\',serif;font-size:clamp(2rem,5vw,3rem);font-weight:900;line-height:1.1;margin-bottom:1rem;}}
.hero p{{color:var(--muted);font-size:1rem;font-weight:300;line-height:1.7;max-width:500px;margin:0 auto;}}
.form-wrapper{{max-width:620px;margin:2rem auto 4rem;padding:0 1.5rem;}}
.form-card{{background:white;border:1px solid var(--border);border-radius:4px;padding:2.5rem;box-shadow:0 4px 24px rgba(0,0,0,0.06);}}
.form-row{{display:grid;grid-template-columns:1fr 1fr;gap:1.2rem;margin-bottom:1.2rem;}}
.form-group{{display:flex;flex-direction:column;gap:0.4rem;}}
label{{font-size:0.78rem;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;color:var(--muted);}}
input,select{{font-family:\'DM Sans\',sans-serif;font-size:1rem;padding:0.75rem 1rem;border:1px solid var(--border);border-radius:3px;background:var(--paper);color:var(--ink);}}
.price-wrap{{position:relative;}}
.price-wrap span{{position:absolute;left:1rem;top:50%;transform:translateY(-50%);color:var(--muted);}}
.price-wrap input{{padding-left:1.8rem;}}
.submit-btn{{width:100%;padding:1rem;background:var(--ink);color:white;border:none;border-radius:3px;font-family:\'DM Sans\',sans-serif;font-size:0.9rem;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;cursor:pointer;margin-top:0.5rem;}}
.notice{{text-align:center;padding:2rem;color:var(--muted);font-size:0.9rem;}}
.disclaimer{{text-align:center;font-size:0.75rem;color:var(--muted);margin-top:1rem;}}
</style></head>
<body>
<nav><a href="/" class="nav-logo">IrishProperty<span style="color:#4ade80">Insights</span></a><a href="/" style="font-size:0.85rem;color:#6b6860;text-decoration:none;">← Back</a></nav>
<div class="hero">
  <div class="hero-tag">AI-Powered Analysis</div>
  <h1>Is This Property a Good Deal?</h1>
  <p>Trained on 700,000+ real Irish property transactions from the PPR.</p>
</div>
<div class="form-wrapper">
  <div class="form-card">
    <form method="POST" action="/deal-checker">
      <div class="form-row">
        <div class="form-group">
          <label>County</label>
          <select name="county" required>
            <option value="" disabled selected>Select county</option>
            {county_opts}
          </select>
        </div>
        <div class="form-group">
          <label>Area / Town</label>
          <input type="text" name="area" placeholder="e.g. Blackrock" required>
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Asking Price</label>
          <div class="price-wrap">
            <span>€</span>
            <input type="number" name="asking_price" placeholder="350000" min="30000" max="5000000" required>
          </div>
        </div>
      </div>
      <button type="submit" class="submit-btn">Analyse This Property</button>
    </form>
    <p class="disclaimer">Not financial advice. Based on PPR data 2010–2024.</p>
  </div>
</div>
</body></html>"""

    if request.method == "GET":
        return FORM_HTML

    # POST — score the property
    if not _model_cache.get("ready"):
        training = _model_cache.get("ready") is None or "model" not in _model_cache
        msg = "Model is still training, please try again in 60 seconds." if training else _model_cache.get("error","Unknown error")
        return f"""<!DOCTYPE html><html><body style="font-family:sans-serif;padding:2rem;">
        <h2>One moment...</h2><p>{msg}</p>
        <a href="/deal-checker">← Try again</a></body></html>"""

    county       = request.form.get("county","").strip().title()
    area         = request.form.get("area","").strip().title()
    asking_price = float(request.form.get("asking_price", 0))

    le_county = _model_cache["le_county"]
    le_desc   = _model_cache["le_desc"]
    le_micro  = _model_cache["le_micro"]
    model     = _model_cache["model"]

    try: county_enc = le_county.transform([county])[0]
    except: county_enc = 0
    try: micro_enc = le_micro.transform([area])[0]
    except: micro_enc = 0
    desc_enc = 0

    import pandas as pd
    X = pd.DataFrame([{{"county_enc":county_enc,"micro_enc":micro_enc,"desc_enc":desc_enc,"year":2024}}])
    predicted  = np.expm1(model.predict(X)[0])
    diff_pct   = ((asking_price - predicted) / predicted) * 100

    if diff_pct <= -15: verdict,color,bg = "STRONG BUY","#1a6b3c","#f0faf4"
    elif diff_pct <= -5: verdict,color,bg = "GOOD DEAL","#1a6b3c","#f0faf4"
    elif diff_pct <= 5:  verdict,color,bg = "FAIR","#a07c10","#fffbf0"
    elif diff_pct <= 15: verdict,color,bg = "OVERPRICED","#d4821a","#fff8f0"
    else:                verdict,color,bg = "AVOID","#c0392b","#fdf2f2"

    return f"""<!DOCTYPE html>
<html><head>
<meta charset="UTF-8"><title>Deal Checker | Irish Property Insights</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:#f5f2ec;font-family:\'DM Sans\',sans-serif;}}
nav{{border-bottom:1px solid #ddd8ce;padding:1.2rem 2rem;display:flex;align-items:center;justify-content:space-between;background:#f5f2ec;}}
.nav-logo{{font-family:\'Playfair Display\',serif;font-size:1.2rem;font-weight:700;color:#0f1014;text-decoration:none;}}
.result-card{{max-width:620px;margin:3rem auto;padding:0 1.5rem;}}
.result-inner{{background:white;border:1px solid #ddd8ce;border-radius:4px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.06);}}
.verdict-banner{{padding:2rem 2.5rem;border-bottom:1px solid #ddd8ce;background:{bg};border-left:5px solid {color};}}
.verdict-label{{font-size:0.72rem;letter-spacing:0.15em;text-transform:uppercase;color:#6b6860;margin-bottom:0.5rem;}}
.verdict-text{{font-family:\'Playfair Display\',serif;font-size:2rem;font-weight:900;color:{color};}}
.verdict-diff{{margin-top:0.4rem;font-size:0.95rem;color:#6b6860;}}
.metrics{{display:grid;grid-template-columns:1fr 1fr;border-bottom:1px solid #ddd8ce;}}
.metric{{padding:1.5rem 2.5rem;border-right:1px solid #ddd8ce;}}
.metric:last-child{{border-right:none;}}
.metric-label{{font-size:0.72rem;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;margin-bottom:0.4rem;}}
.metric-value{{font-family:\'Playfair Display\',serif;font-size:1.6rem;font-weight:700;}}
.footer{{padding:1.2rem 2.5rem;background:#f5f2ec;font-size:0.8rem;color:#6b6860;}}
.try-again{{display:block;text-align:center;margin-top:1.5rem;color:#6b6860;text-decoration:underline;cursor:pointer;}}
</style></head>
<body>
<nav><a href="/" class="nav-logo">IrishProperty<span style="color:#4ade80">Insights</span></a><a href="/" style="font-size:0.85rem;color:#6b6860;text-decoration:none;">← Back</a></nav>
<div class="result-card">
  <div class="result-inner">
    <div class="verdict-banner">
      <div class="verdict-label">Our verdict for {area}, {county}</div>
      <div class="verdict-text">{verdict}</div>
      <div class="verdict-diff">{diff_pct:+.1f}% vs estimated market value</div>
    </div>
    <div class="metrics">
      <div class="metric">
        <div class="metric-label">Asking Price</div>
        <div class="metric-value">€{asking_price:,.0f}</div>
      </div>
      <div class="metric">
        <div class="metric-label">Estimated Value</div>
        <div class="metric-value">€{predicted:,.0f}</div>
      </div>
    </div>
    <div class="footer">Based on PPR data 2010–2024. Not financial advice. <a href="/" style="color:#0f1014">View full reports →</a></div>
  </div>
  <a class="try-again" href="/deal-checker">Check another property</a>
</div>
</body></html>"""
# ── END DEAL CHECKER ───────────────────────────────────────────
'''

# ── Read app.py ──────────────────────────────────────────────
with open(APP_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# ── Remove any existing deal-checker block ──────────────────
patterns = [
    r"# ── DEAL CHECKER ─+.*?# ── END DEAL CHECKER ─+\n",
    r"@app\.route\(['\"]\/deal-checker['\"].*?(?=\n@app\.route|\nif __name__)",
]
for pat in patterns:
    content = re.sub(pat, "", content, flags=re.DOTALL)

# ── Find insertion point (just before if __name__) ───────────
marker = "\nif __name__ =="
idx = content.find(marker)
if idx == -1:
    marker = "\napp.run("
    idx = content.find(marker)

if idx == -1:
    print("ERROR: Could not find insertion point in app.py")
    exit(1)

# ── Insert new route ─────────────────────────────────────────
new_content = content[:idx] + "\n" + NEW_ROUTE + content[idx:]

with open(APP_PATH, "w", encoding="utf-8") as f:
    f.write(new_content)

print("✅ app.py patched successfully!")
print("Now run:")
print("  git add app.py")
print("  git commit -m 'Fix deal checker - auto train on Railway'")
print("  git push")
