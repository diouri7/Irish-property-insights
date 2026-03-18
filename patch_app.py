"""
Run this script from your irish-property-insights folder:
    python patch_app.py

It will add the /deal-checker route to your app.py automatically.
"""

DEAL_CHECKER_CODE = '''

@app.route("/deal-checker", methods=["GET", "POST"])
def deal_checker():
    import joblib
    county_opts = "\\n".join(f\'<option value="{c}">{c}</option>\' for c in COUNTIES)

    if request.method == "GET":
        return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Deal Checker | Irish Property Insights</title><link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet"><style>:root{{--ink:#0f1014;--paper:#f5f2ec;--gold:#c9a84c;--green:#1a6b3c;--red:#c0392b;--amber:#d4821a;--muted:#6b6860;--border:#ddd8ce;}}*{{margin:0;padding:0;box-sizing:border-box;}}body{{background:var(--paper);color:var(--ink);font-family:\'DM Sans\',sans-serif;min-height:100vh;}}nav{{border-bottom:1px solid var(--border);padding:1.2rem 2rem;display:flex;align-items:center;justify-content:space-between;background:var(--paper);}}.nav-logo{{font-family:\'Playfair Display\',serif;font-size:1.2rem;font-weight:700;color:var(--ink);text-decoration:none;}}.nav-back{{font-size:0.85rem;color:var(--muted);text-decoration:none;}}.hero{{padding:4rem 2rem 2rem;max-width:700px;margin:0 auto;text-align:center;}}.hero-tag{{display:inline-block;font-size:0.72rem;font-weight:500;letter-spacing:0.15em;text-transform:uppercase;color:var(--gold);border:1px solid var(--gold);padding:0.3rem 0.8rem;border-radius:2px;margin-bottom:1.5rem;}}.hero h1{{font-family:\'Playfair Display\',serif;font-size:clamp(2rem,5vw,3rem);font-weight:900;line-height:1.1;margin-bottom:1rem;}}.hero p{{color:var(--muted);font-size:1rem;font-weight:300;line-height:1.7;max-width:500px;margin:0 auto;}}.stats{{max-width:620px;margin:2rem auto;padding:0 1.5rem;display:grid;grid-template-columns:1fr 1fr 1fr;gap:1rem;}}.stat{{text-align:center;padding:1.2rem;border:1px solid var(--border);border-radius:3px;background:white;}}.stat-num{{font-family:\'Playfair Display\',serif;font-size:1.4rem;font-weight:700;}}.stat-label{{font-size:0.72rem;color:var(--muted);margin-top:0.2rem;}}.form-wrapper{{max-width:620px;margin:1rem auto 4rem;padding:0 1.5rem;}}.form-card{{background:white;border:1px solid var(--border);border-radius:4px;padding:2.5rem;box-shadow:0 4px 24px rgba(0,0,0,0.06);}}.form-row{{display:grid;grid-template-columns:1fr 1fr;gap:1.2rem;margin-bottom:1.2rem;}}.form-group{{display:flex;flex-direction:column;gap:0.4rem;}}label{{font-size:0.78rem;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;color:var(--muted);}}input,select{{font-family:\'DM Sans\',sans-serif;font-size:1rem;padding:0.75rem 1rem;border:1px solid var(--border);border-radius:3px;background:var(--paper);color:var(--ink);}}.price-wrap{{position:relative;}}.price-wrap span{{position:absolute;left:1rem;top:50%;transform:translateY(-50%);color:var(--muted);}}.price-wrap input{{padding-left:1.8rem;}}.submit-btn{{width:100%;padding:1rem;background:var(--ink);color:white;border:none;border-radius:3px;font-family:\'DM Sans\',sans-serif;font-size:0.9rem;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;cursor:pointer;margin-top:0.5rem;}}.disclaimer{{text-align:center;font-size:0.75rem;color:var(--muted);margin-top:1rem;}}</style></head><body><nav><a href="/" class="nav-logo">IrishProperty<span style="color:#4ade80">Insights</span></a><a href="/" class="nav-back">← Back</a></nav><div class="hero"><div class="hero-tag">AI-Powered Analysis</div><h1>Is This Property a Good Deal?</h1><p>Trained on 727,000 real Irish property transactions.</p></div><div class="stats"><div class="stat"><div class="stat-num">727K</div><div class="stat-label">Transactions</div></div><div class="stat"><div class="stat-num">26</div><div class="stat-label">Counties</div></div><div class="stat"><div class="stat-num">2010-2024</div><div class="stat-label">Data range</div></div></div><div class="form-wrapper"><div class="form-card"><form method="POST" action="/deal-checker"><div class="form-row"><div class="form-group"><label>County</label><select name="county" required><option value="" disabled selected>Select county</option>{county_opts}</select></div><div class="form-group"><label>Area</label><input type="text" name="area" placeholder="e.g. Blackrock" required></div></div><div class="form-row"><div class="form-group"><label>Asking Price</label><div class="price-wrap"><span>&#8364;</span><input type="number" name="asking_price" placeholder="350000" min="30000" max="5000000" required></div></div></div><button type="submit" class="submit-btn">Analyse This Property</button></form><p class="disclaimer">Not financial advice</p></div></div></body></html>"""

    try:
        deal_model = joblib.load("deal_scorer_model.pkl")
        le_county  = joblib.load("le_county.pkl")
        le_desc    = joblib.load("le_desc.pkl")
        le_micro   = joblib.load("le_micro.pkl")
    except Exception as e:
        return f"Model not available: {e}", 503

    county       = request.form.get("county", "").strip().title()
    area         = request.form.get("area", "").strip().title()
    asking_price = float(request.form.get("asking_price", 0))

    try: county_enc = le_county.transform([county])[0]
    except: county_enc = 0
    try: micro_enc = le_micro.transform([area])[0]
    except: micro_enc = 0
    try: desc_enc = le_desc.transform([le_desc.classes_[0]])[0]
    except: desc_enc = 0

    X         = pd.DataFrame([{"county_enc": county_enc, "micro_enc": micro_enc, "desc_enc": desc_enc, "year": 2024}])
    predicted = np.expm1(deal_model.predict(X)[0])
    diff_pct  = ((asking_price - predicted) / predicted) * 100

    if diff_pct <= -15:  verdict = "STRONG BUY"; color = "#1a6b3c"; bg = "#f0faf4"
    elif diff_pct <= -5: verdict = "GOOD DEAL";  color = "#1a6b3c"; bg = "#f0faf4"
    elif diff_pct <= 5:  verdict = "FAIR";        color = "#a07c10"; bg = "#fffbf0"
    elif diff_pct <= 15: verdict = "OVERPRICED";  color = "#d4821a"; bg = "#fff8f0"
    else:                verdict = "AVOID";        color = "#c0392b"; bg = "#fdf2f2"

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Deal Checker | Irish Property Insights</title><link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet"><style>*{{margin:0;padding:0;box-sizing:border-box;}}body{{background:#f5f2ec;font-family:\'DM Sans\',sans-serif;}}nav{{border-bottom:1px solid #ddd8ce;padding:1.2rem 2rem;display:flex;align-items:center;justify-content:space-between;background:#f5f2ec;}}.nav-logo{{font-family:\'Playfair Display\',serif;font-size:1.2rem;font-weight:700;color:#0f1014;text-decoration:none;}}.result-card{{max-width:620px;margin:3rem auto;padding:0 1.5rem;}}.result-inner{{background:white;border:1px solid #ddd8ce;border-radius:4px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.06);}}.verdict-banner{{padding:2rem 2.5rem;border-bottom:1px solid #ddd8ce;background:{bg};border-left:5px solid {color};}}.verdict-label{{font-size:0.72rem;letter-spacing:0.15em;text-transform:uppercase;color:#6b6860;margin-bottom:0.5rem;}}.verdict-text{{font-family:\'Playfair Display\',serif;font-size:2rem;font-weight:900;color:{color};}}.verdict-diff{{margin-top:0.4rem;font-size:0.95rem;color:#6b6860;}}.metrics{{display:grid;grid-template-columns:1fr 1fr;border-bottom:1px solid #ddd8ce;}}.metric{{padding:1.5rem 2.5rem;border-right:1px solid #ddd8ce;}}.metric:last-child{{border-right:none;}}.metric-label{{font-size:0.72rem;text-transform:uppercase;color:#6b6860;margin-bottom:0.4rem;}}.metric-value{{font-family:\'Playfair Display\',serif;font-size:1.6rem;font-weight:700;}}.footer{{padding:1.2rem 2.5rem;background:#f5f2ec;font-size:0.8rem;color:#6b6860;}}.try-again{{display:block;text-align:center;margin-top:1.5rem;color:#6b6860;text-decoration:underline;}}</style></head><body><nav><a href="/" class="nav-logo">IrishProperty<span style="color:#4ade80">Insights</span></a><a href="/" style="font-size:0.85rem;color:#6b6860;text-decoration:none;">← Back</a></nav><div class="result-card"><div class="result-inner"><div class="verdict-banner"><div class="verdict-label">Our verdict</div><div class="verdict-text">{verdict}</div><div class="verdict-diff">{diff_pct:+.1f}% vs estimated market value</div></div><div class="metrics"><div class="metric"><div class="metric-label">Asking Price</div><div class="metric-value">&#8364;{asking_price:,.0f}</div></div><div class="metric"><div class="metric-label">Estimated Value</div><div class="metric-value">&#8364;{predicted:,.0f}</div></div></div><div class="footer">Based on PPR data 2010-2024. Not financial advice. <a href="/" style="color:#0f1014">View full reports &#8594;</a></div></div><a class="try-again" href="/deal-checker">Check another property</a></div></body></html>"""

'''

# Read current app.py
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if already patched
if '/deal-checker' in content:
    print('✅ Deal checker route already exists in app.py — no changes made.')
else:
    # Insert before the if __name__ == "__main__": block
    insert_before = 'if __name__ == "__main__":'
    if insert_before in content:
        content = content.replace(insert_before, DEAL_CHECKER_CODE + '\n' + insert_before)
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print('✅ Deal checker route added to app.py successfully!')
    else:
        # Just append at end
        with open('app.py', 'a', encoding='utf-8') as f:
            f.write(DEAL_CHECKER_CODE)
        print('✅ Deal checker route appended to app.py successfully!')

print('Next step: git add app.py && git commit -m "Add deal checker" && git push')
