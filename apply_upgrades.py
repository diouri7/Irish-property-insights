"""
Three changes in one script:
  1. Rename signals: STRONG BUY -> HIGH POTENTIAL, BUY -> GOOD PROSPECT,
                     MODERATE -> MODERATE POTENTIAL, AVOID -> CAUTION
  2. Add confidence badge (Gold/Silver/Bronze) to PDF table + snapshot
  3. Add /methodology route

Run: python apply_upgrades.py
"""

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

changes = 0

# ─────────────────────────────────────────────
# 1. RENAME SIGNALS
# ─────────────────────────────────────────────

SIGNAL_RENAMES = [
    # Python logic
    ('return "STRONG BUY"',         'return "HIGH POTENTIAL"'),
    ('return "BUY"',                 'return "GOOD PROSPECT"'),
    ('return "MODERATE"',            'return "MODERATE POTENTIAL"'),
    ('return "AVOID"',               'return "CAUTION"'),
    # signal_order dict
    ('"STRONG BUY": 0, "BUY": 1, "MODERATE": 2, "HOLD": 3, "AVOID": 4',
     '"HIGH POTENTIAL": 0, "GOOD PROSPECT": 1, "MODERATE POTENTIAL": 2, "HOLD": 3, "CAUTION": 4'),
    # PDF chart colours
    ('if s == "STRONG BUY":', 'if s == "HIGH POTENTIAL":'),
    ('elif s == "BUY":', 'elif s == "GOOD PROSPECT":'),
    # PDF table colour-coding
    ('if signal == "STRONG BUY":', 'if signal == "HIGH POTENTIAL":'),
    ('elif signal == "BUY":', 'elif signal == "GOOD PROSPECT":'),
    ('elif signal == "MODERATE":', 'elif signal == "MODERATE POTENTIAL":'),
    ('elif signal == "AVOID":', 'elif signal == "CAUTION":'),
    # Methodology text in PDF
    ('"Each micro-area receives a composite investment signal (STRONG BUY / BUY / MODERATE / HOLD / AVOID) "',
     '"Each micro-area receives a data signal (HIGH POTENTIAL / GOOD PROSPECT / MODERATE POTENTIAL / HOLD / CAUTION) "'),
    ('"well across all three dimensions to receive a STRONG BUY rating."',
     '"well across all three dimensions to receive a HIGH POTENTIAL rating."'),
    # Deal checker verdicts
    ('verdict,color,bg = "STRONG BUY","#1a6b3c","#f0faf4"',
     'verdict,color,bg = "HIGH POTENTIAL","#1a6b3c","#f0faf4"'),
    # Heatmap JS signals
    ("signal:'STRONG BUY'", "signal:'HIGH POTENTIAL'"),
    ("d.signal==='STRONG BUY'", "d.signal==='HIGH POTENTIAL'"),
    # Sample table in landing HTML
    ('>STRONG BUY</span>', '>HIGH POTENTIAL</span>'),
    # Snapshot PDF teaser
    ('f"The snapshot shows {display_n} of {len(micro_df)} ranked micro-areas in {county}. "',
     'f"The snapshot shows {display_n} of {len(micro_df)} ranked micro-areas in {county}. "'),
]

for old, new in SIGNAL_RENAMES:
    if old in content:
        content = content.replace(old, new)
        changes += 1
        print(f"  ✓ Renamed: {old[:60]}")
    else:
        print(f"  - Not found (skip): {old[:60]}")

# ─────────────────────────────────────────────
# 2. ADD CONFIDENCE BADGE FUNCTION
# After compute_signal function, insert confidence helper
# ─────────────────────────────────────────────

CONF_FUNC = '''

def confidence_badge(transactions):
    """Return (label, emoji, tooltip) based on transaction count."""
    if transactions >= 15:
        return "High Confidence", "🟡", "Based on 15+ recent sales — statistically reliable."
    elif transactions >= 6:
        return "Medium Confidence", "⚪", "Based on 6-14 sales — good indicator, check for outliers."
    else:
        return "Low Confidence", "🟤", "Based on fewer than 6 sales — use as early indicator only."

'''

INSERT_AFTER = 'def compute_signal(growth, gross_yield, risk):'
# Find end of compute_signal function (next def or blank lines before next def)
cs_pos = content.find(INSERT_AFTER)
if cs_pos != -1:
    # Find the next 'def ' after compute_signal
    next_def = content.find('\ndef ', cs_pos + len(INSERT_AFTER))
    if next_def != -1 and CONF_FUNC.strip() not in content:
        content = content[:next_def] + CONF_FUNC + content[next_def:]
        changes += 1
        print("  ✓ Added confidence_badge() function")
    else:
        print("  - confidence_badge already present or insertion point not found")
else:
    print("  - compute_signal not found")

# ─────────────────────────────────────────────
# 3. ADD CONFIDENCE COLUMN TO PDF TABLE
# In the table header and rows
# ─────────────────────────────────────────────

OLD_HEADER = '    header = ["#", "Micro-Area", "Median Price", "5yr Growth", "Yield", "Risk", "Signal", "Txns"]'
NEW_HEADER = '    header = ["#", "Micro-Area", "Median Price", "5yr Growth", "Yield", "Risk", "Signal", "Txns", "Confidence"]'

if OLD_HEADER in content:
    content = content.replace(OLD_HEADER, NEW_HEADER)
    changes += 1
    print("  ✓ Added Confidence column to PDF table header")

OLD_ROW = '''        table_rows.append([
            str(rank),
            str(row["area"])[:25],
            f"€{row['median_price']:,.0f}",
            f"{row['growth_5yr']:+.1f}%",
            f"{row['gross_yield']:.1f}%",
            row["risk"],
            row["signal"],
            str(row["transactions"]),
        ])'''

NEW_ROW = '''        conf_label, conf_emoji, _ = confidence_badge(row["transactions"])
        table_rows.append([
            str(rank),
            str(row["area"])[:25],
            f"€{row['median_price']:,.0f}",
            f"{row['growth_5yr']:+.1f}%",
            f"{row['gross_yield']:.1f}%",
            row["risk"],
            row["signal"],
            str(row["transactions"]),
            f"{conf_emoji} {conf_label.split()[0]}",
        ])'''

if OLD_ROW in content:
    content = content.replace(OLD_ROW, NEW_ROW)
    changes += 1
    print("  ✓ Added confidence badge to PDF table rows")

# Update column widths to include confidence column
OLD_COLW = '    col_w = [0.6*cm, 4.2*cm, 2.4*cm, 2*cm, 1.6*cm, 1.6*cm, 2.4*cm, 1.4*cm]'
NEW_COLW = '    col_w = [0.5*cm, 3.8*cm, 2.2*cm, 1.8*cm, 1.4*cm, 1.4*cm, 2.2*cm, 1.1*cm, 2.0*cm]'

if OLD_COLW in content:
    content = content.replace(OLD_COLW, NEW_COLW)
    changes += 1
    print("  ✓ Updated PDF column widths")

# ─────────────────────────────────────────────
# 4. ADD /methodology ROUTE
# Insert before if __name__ == "__main__"
# ─────────────────────────────────────────────

METH_ROUTE = '''
@app.route("/methodology")
def methodology():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Methodology | IrishPropertyInsights</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=Fraunces:wght@300;500;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'DM Sans',sans-serif;background:#0B1120;color:#F1F5F9;line-height:1.7}
nav{padding:1.2rem 2rem;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid rgba(148,163,184,.1);background:rgba(11,17,32,.9)}
.nl{font-family:'Fraunces',serif;font-size:1.2rem;font-weight:700;color:#F1F5F9;text-decoration:none}
.nl span{color:#10B981}
.back{font-size:.85rem;color:#94A3B8;text-decoration:none}
.back:hover{color:#F1F5F9}
main{max-width:760px;margin:0 auto;padding:4rem 2rem}
h1{font-family:'Fraunces',serif;font-size:2.4rem;font-weight:700;margin-bottom:.75rem;line-height:1.15}
.sub{color:#94A3B8;font-size:1.05rem;margin-bottom:3rem;max-width:560px}
.section{margin-bottom:2.5rem;padding:2rem;background:#1A2332;border:1px solid rgba(148,163,184,.1);border-radius:12px;border-left:3px solid #10B981}
.section.gold{border-left-color:#F59E0B}
.section.blue{border-left-color:#3B82F6}
.section.red{border-left-color:#EF4444}
h2{font-family:'Fraunces',serif;font-size:1.25rem;font-weight:600;margin-bottom:.75rem;color:#F1F5F9}
p{color:#94A3B8;font-size:.95rem;margin-bottom:.75rem}
p:last-child{margin-bottom:0}
strong{color:#CBD5E1}
.conf-table{width:100%;border-collapse:collapse;margin-top:1rem;font-size:.88rem}
.conf-table th{text-align:left;padding:.6rem 1rem;background:rgba(148,163,184,.08);color:#64748B;font-weight:600;font-size:.78rem;text-transform:uppercase;letter-spacing:.06em}
.conf-table td{padding:.6rem 1rem;border-top:1px solid rgba(148,163,184,.08);color:#94A3B8}
.conf-table tr:hover td{background:rgba(255,255,255,.02)}
.badge{display:inline-block;padding:.2rem .6rem;border-radius:4px;font-size:.75rem;font-weight:700}
.badge.gold{background:rgba(245,158,11,.15);color:#F59E0B}
.badge.silver{background:rgba(148,163,184,.15);color:#CBD5E1}
.badge.bronze{background:rgba(180,120,60,.15);color:#C97A3A}
.disclaimer{margin-top:3rem;padding:1.5rem;background:rgba(239,68,68,.06);border:1px solid rgba(239,68,68,.15);border-radius:8px;font-size:.85rem;color:#94A3B8}
footer{text-align:center;padding:2rem;border-top:1px solid rgba(148,163,184,.1);font-size:.8rem;color:#475569}
footer a{color:#64748B;text-decoration:none}
</style>
</head>
<body>
<nav>
  <a href="/" class="nl">Irish<span>Property</span>Insights</a>
  <a href="/" class="back">← Back to site</a>
</nav>
<main>
  <h1>Data Transparency &amp; Methodology</h1>
  <p class="sub">How we turn 727,000 raw property transactions into actionable investment signals — and how to read our confidence scores.</p>

  <div class="section">
    <h2>📊 Data Source 1 — Property Price Register (PPR)</h2>
    <p>We ingest every residential property transaction registered in Ireland since 2010 from the <strong>Property Services Regulatory Authority's Property Price Register</strong> — the official government record of all settled sale prices.</p>
    <p>Unlike asking prices on listing sites like Daft or MyHome, PPR data reflects <strong>actual completed transactions</strong>. We clean, deduplicate, and normalise this data to extract micro-area signals.</p>
    <p><strong>Coverage:</strong> 727,000+ transactions across all 26 counties, 2010–2024.</p>
  </div>

  <div class="section gold">
    <h2>🏠 Data Source 2 — RTB Rental Index</h2>
    <p>Rental yield estimates are cross-referenced with <strong>Residential Tenancies Board (RTB) Q2 2025 quarterly rent data</strong> — the official Irish government rental index.</p>
    <p>We map county-level RTB rents to micro-areas using a <strong>0.4× dampening factor</strong> that adjusts for the price difference between a micro-area and its county average. This prevents overstating yields in lower-priced areas.</p>
    <p><strong>Formula:</strong> Gross Yield = (Adjusted Annual Rent ÷ Micro-Area Median Price) × 100</p>
  </div>

  <div class="section blue">
    <h2>📈 Growth Calculation</h2>
    <p>5-year <strong>Compound Annual Growth Rate (CAGR)</strong> is calculated for each micro-area using yearly median sale prices. Only micro-areas with <strong>10+ transactions in the 5-year window</strong> are included — thin markets are excluded entirely.</p>
    <p><strong>Formula:</strong> CAGR = ((Latest Median ÷ Earliest Median) ^ (1 ÷ Years)) − 1</p>
  </div>

  <div class="section">
    <h2>⚖️ Risk Model</h2>
    <p>Risk is assessed using the <strong>Coefficient of Variation (CV)</strong> — price standard deviation divided by mean — combined with average annual transaction volume.</p>
    <p><strong>Low Risk:</strong> CV &lt; 15% and 5+ annual transactions.<br>
       <strong>Medium Risk:</strong> CV &lt; 25% or 3+ annual transactions.<br>
       <strong>High Risk:</strong> All others. Thinly-traded markets are penalised.</p>
  </div>

  <div class="section gold">
    <h2>🎯 Investment Signals</h2>
    <p>Each micro-area receives a composite data signal based on weighted scoring of growth rate, gross yield, and risk classification. These are <strong>data indicators, not financial advice</strong>.</p>
    <table class="conf-table">
      <tr><th>Signal</th><th>What it means</th></tr>
      <tr><td><strong>HIGH POTENTIAL</strong></td><td>Strong yield, strong growth, low-medium risk. Score ≥ 6.</td></tr>
      <tr><td><strong>GOOD PROSPECT</strong></td><td>Above-average on multiple dimensions. Score 4–5.</td></tr>
      <tr><td><strong>MODERATE POTENTIAL</strong></td><td>Some positive indicators but not across the board. Score 2–3.</td></tr>
      <tr><td><strong>HOLD</strong></td><td>Neutral — no strong positive or negative signals. Score 0–1.</td></tr>
      <tr><td><strong>CAUTION</strong></td><td>Negative growth, high risk, or poor yield combination. Score &lt; 0.</td></tr>
    </table>
  </div>

  <div class="section blue">
    <h2>🏅 Data Confidence Score</h2>
    <p>Every micro-area is assigned a confidence level based on the number of recent transactions. Low sample sizes can be skewed by a single high-value sale — the confidence score tells you how much weight to give the signal.</p>
    <table class="conf-table">
      <tr><th>Badge</th><th>Transactions</th><th>Meaning</th></tr>
      <tr><td><span class="badge gold">🟡 High</span></td><td>15+ sales</td><td>Statistically significant. Trends are reliable.</td></tr>
      <tr><td><span class="badge silver">⚪ Medium</span></td><td>6–14 sales</td><td>Good indicator. Check for 1–2 outliers that may skew the average.</td></tr>
      <tr><td><span class="badge bronze">🟤 Low</span></td><td>1–5 sales</td><td>Small sample. Use as early-stage indicator only — not a final valuation.</td></tr>
    </table>
  </div>

  <div class="disclaimer">
    <strong>Important:</strong> All signals and scores are generated from historical public records for informational purposes only. They do not constitute financial advice. Gross yield estimates do not account for management fees, maintenance, LPT, vacancy, or financing costs. Always conduct independent due diligence and consult a qualified financial advisor before making any investment decision.
  </div>
</main>
<footer><p>© 2025 IrishPropertyInsights · Data: <a href="https://www.propertypriceregister.ie" target="_blank">PPR</a> &amp; <a href="https://www.rtb.ie" target="_blank">RTB</a> · <a href="/">Back to site</a></p></footer>
</body>
</html>"""


'''

MAIN_MARKER = '\nif __name__ == "__main__":'
if MAIN_MARKER in content and '/methodology' not in content:
    content = content.replace(MAIN_MARKER, METH_ROUTE + MAIN_MARKER)
    changes += 1
    print("  ✓ Added /methodology route")
elif '/methodology' in content:
    print("  - /methodology already exists")
else:
    print("  - Could not find insertion point for /methodology")

# ─────────────────────────────────────────────
# 5. ADD METHODOLOGY LINK TO NAVBAR
# ─────────────────────────────────────────────
OLD_NAV = '<li><a href="#meth">Methodology</a></li>'
NEW_NAV = '<li><a href="/methodology">Methodology</a></li>'

if OLD_NAV in content:
    content = content.replace(OLD_NAV, NEW_NAV)
    changes += 1
    print("  ✓ Updated navbar Methodology link to /methodology")

# ─────────────────────────────────────────────
# WRITE OUTPUT
# ─────────────────────────────────────────────
with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)

print(f"\n{'='*50}")
print(f"✅ Done — {changes} changes applied.")
print("\nNow run:")
print("  git add app.py")
print('  git commit -m "Rename signals, add confidence scores, add methodology page"')
print("  git push")
