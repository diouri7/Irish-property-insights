"""
Two additions:
  1. "Why I Built This" section on homepage (above footer)
  2. Hoverable tooltips on confidence badges in /methodology page

Run: python add_about.py
"""

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

changes = 0

# ─────────────────────────────────────────────
# 1. "WHY I BUILT THIS" SECTION
# Insert just before the footer tag in LANDING_HTML
# ─────────────────────────────────────────────

ABOUT_SECTION = '''<section style="padding:5rem 2rem;background:var(--bg2);border-top:1px solid var(--border)">
  <div style="max-width:680px;margin:0 auto">
    <div style="font-size:.75rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--green);margin-bottom:1rem">The Story</div>
    <h2 style="font-family:var(--fd);font-size:clamp(1.6rem,3vw,2.2rem);font-weight:700;line-height:1.2;margin-bottom:1.5rem">Why I built this</h2>
    <div style="display:grid;grid-template-columns:1fr;gap:1.5rem">
      <div style="padding:1.5rem;background:var(--card);border:1px solid var(--border);border-radius:12px;border-left:3px solid var(--green)">
        <div style="font-size:.82rem;font-weight:700;color:var(--green);margin-bottom:.6rem;text-transform:uppercase;letter-spacing:.08em">The Problem</div>
        <p style="color:var(--t2);font-size:.95rem;line-height:1.7">As anyone watching the Irish property market knows, county-level averages are misleading. A "6% yield in Dublin" tells you nothing about whether a specific street in Dublin 15 is a solid investment versus a cul-de-sac in Dublin 6 that hasn't moved in a decade.</p>
      </div>
      <div style="padding:1.5rem;background:var(--card);border:1px solid var(--border);border-radius:12px;border-left:3px solid var(--gold)">
        <div style="font-size:.82rem;font-weight:700;color:var(--gold);margin-bottom:.6rem;text-transform:uppercase;letter-spacing:.08em">The Goal</div>
        <p style="color:var(--t2);font-size:.95rem;line-height:1.7">I built this tool to surface the micro-data that mainstream listing sites hide. By connecting the Property Price Register with RTB rental data, the aim is to give individual buyers and local investors the same granular insight that institutional funds already use — without the €500/month price tag.</p>
      </div>
      <div style="padding:1.5rem;background:var(--card);border:1px solid var(--border);border-radius:12px;border-left:3px solid #3B82F6">
        <div style="font-size:.82rem;font-weight:700;color:#3B82F6;margin-bottom:.6rem;text-transform:uppercase;letter-spacing:.08em">The Philosophy</div>
        <p style="color:var(--t2);font-size:.95rem;line-height:1.7">Data should be transparent, not a black box. This is not a financial advice tool — it is a data analysis tool built on publicly available government records. Every signal, every yield estimate, and every confidence score is explained on the <a href="/methodology" style="color:var(--green);text-decoration:none">Methodology page</a>. No guesswork, no hidden model.</p>
      </div>
    </div>
    <p style="font-size:.82rem;color:var(--t3);margin-top:1.5rem;text-align:center">All data from <a href="https://www.propertypriceregister.ie" target="_blank" style="color:var(--t2);text-decoration:none">Property Price Register</a> &amp; <a href="https://www.rtb.ie" target="_blank" style="color:var(--t2);text-decoration:none">Residential Tenancies Board</a> — official Irish government sources.</p>
  </div>
</section>
'''

FOOTER_TAG = '<footer><p>© 2025 IrishPropertyInsights.'

if FOOTER_TAG in content and 'Why I built this' not in content:
    content = content.replace(FOOTER_TAG, ABOUT_SECTION + FOOTER_TAG)
    changes += 1
    print("  ✓ Added 'Why I Built This' section above footer")
elif 'Why I built this' in content:
    print("  - 'Why I Built This' already present")
else:
    print("  - Could not find footer insertion point")

# ─────────────────────────────────────────────
# 2. ADD TOOLTIP CSS + HOVER TO METHODOLOGY PAGE
# Find the confidence table rows and add tooltip markup
# ─────────────────────────────────────────────

OLD_CONF_CSS = '.badge.bronze{background:rgba(180,120,60,.15);color:#C97A3A}'

NEW_CONF_CSS = '''.badge.bronze{background:rgba(180,120,60,.15);color:#C97A3A}
.tip{position:relative;cursor:help;display:inline-block}
.tip .tiptext{visibility:hidden;opacity:0;width:260px;background:#1E293B;color:#CBD5E1;font-size:.78rem;line-height:1.6;padding:.7rem 1rem;border-radius:8px;border:1px solid rgba(148,163,184,.15);position:absolute;z-index:10;bottom:130%;left:50%;transform:translateX(-50%);transition:opacity .2s;pointer-events:none;text-align:left}
.tip .tiptext::after{content:"";position:absolute;top:100%;left:50%;transform:translateX(-50%);border:5px solid transparent;border-top-color:#1E293B}
.tip:hover .tiptext{visibility:visible;opacity:1}'''

if OLD_CONF_CSS in content and '.tip{position:relative' not in content:
    content = content.replace(OLD_CONF_CSS, NEW_CONF_CSS)
    changes += 1
    print("  ✓ Added tooltip CSS to methodology page")

# Replace plain badge spans with hoverable tooltip versions
OLD_GOLD_BADGE = '<td><span class="badge gold">🟡 High</span></td><td>15+ sales</td><td>Statistically significant. Trends are reliable.</td>'
NEW_GOLD_BADGE = '<td><span class="tip"><span class="badge gold">🟡 High</span><span class="tiptext">Calculated from 15+ recent transactions. This area shows high liquidity and consistent price trends, making the projected yield statistically reliable.</span></span></td><td>15+ sales</td><td>Statistically significant. Trends are reliable.</td>'

OLD_SILVER_BADGE = '<td><span class="badge silver">⚪ Medium</span></td><td>6–14 sales</td><td>Good indicator. Check for 1–2 outliers that may skew the average.</td>'
NEW_SILVER_BADGE = '<td><span class="tip"><span class="badge silver">⚪ Medium</span><span class="tiptext">Based on a moderate number of sales. While the trend is clear, we recommend checking for individual high-value outliers that may slightly skew the average.</span></span></td><td>6–14 sales</td><td>Good indicator. Check for 1–2 outliers that may skew the average.</td>'

OLD_BRONZE_BADGE = '<td><span class="badge bronze">🟤 Low</span></td><td>1–5 sales</td><td>Small sample. Use as early-stage indicator only — not a final valuation.</td>'
NEW_BRONZE_BADGE = '<td><span class="tip"><span class="badge bronze">🟤 Low</span><span class="tiptext">Data is based on a small sample size (fewer than 6 sales). This signal should be used as an early-stage indicator rather than a definitive valuation. A single high-value sale can skew the average significantly.</span></span></td><td>1–5 sales</td><td>Small sample. Use as early-stage indicator only — not a final valuation.</td>'

for old, new, label in [
    (OLD_GOLD_BADGE, NEW_GOLD_BADGE, "Gold badge tooltip"),
    (OLD_SILVER_BADGE, NEW_SILVER_BADGE, "Silver badge tooltip"),
    (OLD_BRONZE_BADGE, NEW_BRONZE_BADGE, "Bronze badge tooltip"),
]:
    if old in content:
        content = content.replace(old, new)
        changes += 1
        print(f"  ✓ Added hover tooltip: {label}")
    else:
        print(f"  - Not found: {label}")

# ─────────────────────────────────────────────
# WRITE
# ─────────────────────────────────────────────
with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)

print(f"\n{'='*50}")
print(f"✅ Done — {changes} changes applied.")
print("\nNow run:")
print("  git add app.py")
print('  git commit -m "Add About section and confidence tooltips"')
print("  git push")
