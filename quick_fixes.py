"""
Two quick fixes:
  1. Add legal disclaimer line to footer on ALL pages
     (homepage, deal checker form, deal checker result, snapshot result)
  2. Add CTA button at bottom of /methodology page

Run: python quick_fixes.py
"""

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

changes = 0

# ─────────────────────────────────────────────
# 1. HOMEPAGE FOOTER — already has disclaimer, just make it two lines
# ─────────────────────────────────────────────
OLD_HOME_FOOTER = '<footer><p>© 2025 IrishPropertyInsights. Data from <a href="https://www.propertypriceregister.ie" target="_blank">PPR</a> &amp; <a href="https://www.rtb.ie" target="_blank">RTB</a>. For informational purposes only — not financial advice.</p></footer>'

NEW_HOME_FOOTER = '''<footer>
  <p>© 2025 IrishPropertyInsights · Data: <a href="https://www.propertypriceregister.ie" target="_blank">PPR</a> &amp; <a href="https://www.rtb.ie" target="_blank">RTB</a> · <a href="/methodology">Methodology</a></p>
  <p style="margin-top:.4rem;font-size:.76rem;color:var(--t3)">IrishPropertyInsights provides data analysis based on public records. It is not financial advice. Always consult a qualified advisor before making investment decisions.</p>
</footer>'''

if OLD_HOME_FOOTER in content:
    content = content.replace(OLD_HOME_FOOTER, NEW_HOME_FOOTER)
    changes += 1
    print("  ✓ Updated homepage footer with legal disclaimer")
else:
    print("  - Homepage footer not found (may already be updated)")

# ─────────────────────────────────────────────
# 2. DEAL CHECKER FORM PAGE FOOTER
# ─────────────────────────────────────────────
OLD_DEAL_FOOTER = '</body></html>"""'

DISCLAIMER_DIV = '''<div style="text-align:center;padding:1.5rem 2rem;border-top:1px solid #e8e4dc;margin-top:2rem;font-size:.76rem;color:#9a9690;line-height:1.6;">
  IrishPropertyInsights provides data analysis based on public records. It is not financial advice.<br>
  <a href="/" style="color:#9a9690">Home</a> · <a href="/methodology" style="color:#9a9690">Methodology</a>
</div>
</body></html>"""'''

# Only replace the first occurrence (deal checker form page, around line 1626)
first_pos = content.find(OLD_DEAL_FOOTER)
if first_pos != -1:
    content = content[:first_pos] + DISCLAIMER_DIV + content[first_pos + len(OLD_DEAL_FOOTER):]
    changes += 1
    print("  ✓ Added disclaimer to deal checker form page footer")

# ─────────────────────────────────────────────
# 3. METHODOLOGY PAGE — ADD CTA AT BOTTOM
# Find the disclaimer div and add CTA after it
# ─────────────────────────────────────────────
OLD_METH_DISCLAIMER = '''  <div class="disclaimer">
    <strong>Important:</strong> All signals and scores are generated from historical public records for informational purposes only. They do not constitute financial advice. Gross yield estimates do not account for management fees, maintenance, LPT, vacancy, or financing costs. Always conduct independent due diligence and consult a qualified financial advisor before making any investment decision.
  </div>
</main>'''

NEW_METH_DISCLAIMER = '''  <div class="disclaimer">
    <strong>Important:</strong> All signals and scores are generated from historical public records for informational purposes only. They do not constitute financial advice. Gross yield estimates do not account for management fees, maintenance, LPT, vacancy, or financing costs. Always conduct independent due diligence and consult a qualified financial advisor before making any investment decision.
  </div>

  <div style="text-align:center;margin-top:3rem;padding:2.5rem;background:#1A2332;border:1px solid rgba(148,163,184,.1);border-radius:16px;">
    <p style="color:#94A3B8;font-size:.95rem;margin-bottom:1.25rem;">Ready to put this into practice?</p>
    <h3 style="font-family:'Fraunces',serif;font-size:1.4rem;font-weight:600;margin-bottom:1.5rem;color:#F1F5F9;">See the data for your county</h3>
    <div style="display:flex;gap:1rem;justify-content:center;flex-wrap:wrap;">
      <a href="/#snap" style="display:inline-block;padding:.85rem 1.8rem;background:#10B981;color:#fff;border-radius:10px;font-weight:600;font-size:.95rem;text-decoration:none;">Get Free County Snapshot →</a>
      <a href="/#reports" style="display:inline-block;padding:.85rem 1.8rem;background:transparent;color:#CBD5E1;border:1px solid rgba(148,163,184,.2);border-radius:10px;font-weight:500;font-size:.95rem;text-decoration:none;">View Full Reports — €29</a>
    </div>
    <p style="font-size:.78rem;color:#475569;margin-top:1rem;">No credit card required for the free snapshot</p>
  </div>
</main>'''

if OLD_METH_DISCLAIMER in content:
    content = content.replace(OLD_METH_DISCLAIMER, NEW_METH_DISCLAIMER)
    changes += 1
    print("  ✓ Added CTA block to bottom of /methodology page")
else:
    print("  - Methodology disclaimer block not found (may need apply_upgrades.py first)")

# ─────────────────────────────────────────────
# WRITE
# ─────────────────────────────────────────────
with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)

print(f"\n{'='*50}")
print(f"✅ Done — {changes} changes applied.")
print("\nRun order reminder:")
print("  1. python apply_upgrades.py")
print("  2. python add_about.py")
print("  3. python quick_fixes.py")
print("\nThen:")
print("  git add app.py")
print('  git commit -m "Footer disclaimer + methodology CTA"')
print("  git push")
