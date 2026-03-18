"""
Replaces the hero + stats bar with a sharper above-the-fold landing page.
Run from C:\\Users\\WAFI\\irish-property-insights:
    python fix_hero.py
"""

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# ── Target: nav + hero + stats bar ──
OLD_HERO = '''<nav><a href="#" class="nl">Irish<span>Property</span>Insights</a><ul class="nk"><li><a href="#how">How It Works</a></li><li><a href="#who">Who It\'s For</a></li><li><a href="#meth">Methodology</a></li><li><a href="#reports" class="nc">Get Report</a></li></ul></nav>
<section class="hero"><div class="hc"><div class="hb">Updated with RTB Q2 2025 data</div><h1>Stop Guessing. Start Investing With Data.</h1><p class="hs">We rank every micro-area across all 26 counties by rental yield, 5-year price growth, and investment risk — built on 727,000 real transactions from the Property Price Register and official RTB rental data.</p><div style="display:flex;gap:1rem;flex-wrap:wrap;justify-content:center;margin-bottom:1rem"><div style="background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.2);border-radius:8px;padding:.5rem 1rem;font-size:.85rem;color:var(--green)">✓ 500+ micro-areas ranked</div><div style="background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.2);border-radius:8px;padding:.5rem 1rem;font-size:.85rem;color:var(--green)">✓ All 26 counties covered</div><div style="background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.2);border-radius:8px;padding:.5rem 1rem;font-size:.85rem;color:var(--green)">✓ Official government data only</div></div><div class="hctas"><a href="#snap" class="bp">See Top Investment Areas Free →</a><a href="#reports" class="bs">Unlock Full County Report — €29</a></div><p style="font-size:.8rem;color:var(--t3);margin-top:.75rem">Free for every county — no credit card, no signup required</p></div></section>
<div class="cb"><div class="cbi"><div class="ci"><div class="cn">26</div><div class="cl">Counties Covered</div></div><div class="ci"><div class="cn">15yr</div><div class="cl">Transaction History</div></div><div class="ci"><div class="cn">500+</div><div class="cl">Micro-Areas Scored</div></div><div class="ci"><div class="cn">3</div><div class="cl">Risk-Adjusted Signals</div></div></div><p style="text-align:center;font-size:.8rem;color:var(--t3);margin-top:1.5rem;font-weight:500">Built exclusively on official Irish government data — Property Price Register &amp; Residential Tenancies Board.</p></div>'''

NEW_HERO = '''<nav><a href="#" class="nl">Irish<span>Property</span>Insights</a><ul class="nk"><li><a href="#how">How It Works</a></li><li><a href="#who">Who It\'s For</a></li><li><a href="#meth">Methodology</a></li><li><a href="#reports" class="nc">Get Report</a></li></ul></nav>

<!-- ── HERO ── -->
<section class="hero" style="padding:7rem 2rem 3rem;">
  <div class="hc">

    <!-- Data source badge -->
    <div style="display:inline-flex;align-items:center;gap:0.5rem;padding:0.4rem 1rem;background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.2);border-radius:100px;font-size:0.78rem;font-weight:600;color:var(--green);margin-bottom:2rem;">
      <span style="width:6px;height:6px;border-radius:50%;background:var(--green);animation:pulse 2s infinite;flex-shrink:0;"></span>
      Built on official PPR &amp; RTB data — 727,000 transactions
    </div>

    <!-- Headline -->
    <h1 style="font-family:var(--fd);font-size:clamp(2.6rem,5.5vw,4.4rem);font-weight:700;line-height:1.08;letter-spacing:-0.03em;margin-bottom:1.5rem;">
      The Data-Driven Map<br>for <em style="font-style:italic;color:var(--green);">Irish Property</em> Investors
    </h1>

    <!-- Sub-headline — answers "what is this?" in one sentence -->
    <p class="hs" style="font-size:1.15rem;max-width:580px;margin:0 auto 1rem;">
      We analyse RTB and Property Price Register data to surface high-yield micro-areas you won't find on Daft.
    </p>
    <p style="font-size:0.9rem;color:var(--t3);max-width:480px;margin:0 auto 2.5rem;line-height:1.6;">
      Every micro-area across all 26 counties ranked by rental yield, 5-year growth, and investment risk — for free.
    </p>

    <!-- Trust pills -->
    <div style="display:flex;gap:0.75rem;flex-wrap:wrap;justify-content:center;margin-bottom:2.5rem;">
      <div style="display:flex;align-items:center;gap:0.4rem;padding:0.4rem 0.9rem;background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.15);border-radius:6px;font-size:0.82rem;color:var(--green);font-weight:500;">
        ✓ 500+ micro-areas ranked
      </div>
      <div style="display:flex;align-items:center;gap:0.4rem;padding:0.4rem 0.9rem;background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.15);border-radius:6px;font-size:0.82rem;color:var(--green);font-weight:500;">
        ✓ All 26 counties
      </div>
      <div style="display:flex;align-items:center;gap:0.4rem;padding:0.4rem 0.9rem;background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.15);border-radius:6px;font-size:0.82rem;color:var(--green);font-weight:500;">
        ✓ Official government data only
      </div>
      <div style="display:flex;align-items:center;gap:0.4rem;padding:0.4rem 0.9rem;background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.15);border-radius:6px;font-size:0.82rem;color:var(--green);font-weight:500;">
        ✓ Updated Q2 2025
      </div>
    </div>

    <!-- CTAs -->
    <div class="hctas">
      <a href="#snap" class="bp" style="font-size:1.05rem;padding:1rem 2.2rem;">Find High-Yield Areas Free →</a>
      <a href="#reports" class="bs">Full County Report — €29</a>
    </div>
    <p style="font-size:0.8rem;color:var(--t3);margin-top:1rem;">No credit card · No signup · Instant download</p>

    <!-- "What you get" quick explainer — the 10-second pitch -->
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;max-width:680px;margin:3.5rem auto 0;text-align:left;">
      <div style="background:var(--card);border:1px solid var(--border);border-radius:12px;padding:1.25rem;border-top:2px solid var(--green);">
        <div style="font-size:1.2rem;margin-bottom:0.5rem;">📍</div>
        <div style="font-size:0.85rem;font-weight:600;margin-bottom:0.3rem;">Where to invest</div>
        <div style="font-size:0.8rem;color:var(--t3);line-height:1.5;">Every micro-area ranked — not vague county averages</div>
      </div>
      <div style="background:var(--card);border:1px solid var(--border);border-radius:12px;padding:1.25rem;border-top:2px solid var(--gold);">
        <div style="font-size:1.2rem;margin-bottom:0.5rem;">💰</div>
        <div style="font-size:0.85rem;font-weight:600;margin-bottom:0.3rem;">What return to expect</div>
        <div style="font-size:0.8rem;color:var(--t3);line-height:1.5;">Gross yield calculated from live RTB rent data</div>
      </div>
      <div style="background:var(--card);border:1px solid var(--border);border-radius:12px;padding:1.25rem;border-top:2px solid var(--blue);">
        <div style="font-size:1.2rem;margin-bottom:0.5rem;">🛡️</div>
        <div style="font-size:0.85rem;font-weight:600;margin-bottom:0.3rem;">How risky it is</div>
        <div style="font-size:0.8rem;color:var(--t3);line-height:1.5;">Risk-scored by price volatility &amp; transaction volume</div>
      </div>
    </div>

  </div>
</section>

<!-- ── STATS BAR ── -->
<div class="cb">
  <div class="cbi">
    <div class="ci"><div class="cn">727k</div><div class="cl">PPR Transactions</div></div>
    <div class="ci"><div class="cn">15yr</div><div class="cl">Price History</div></div>
    <div class="ci"><div class="cn">500+</div><div class="cl">Micro-Areas Scored</div></div>
    <div class="ci"><div class="cn">€29</div><div class="cl">Full County Report</div></div>
  </div>
  <p style="text-align:center;font-size:.8rem;color:var(--t3);margin-top:1.5rem;font-weight:500;">
    Data source: <a href="https://www.propertypriceregister.ie" target="_blank" style="color:var(--t2);text-decoration:none;">Property Price Register</a> &amp; <a href="https://www.rtb.ie" target="_blank" style="color:var(--t2);text-decoration:none;">Residential Tenancies Board</a> — official Irish government records.
  </p>
</div>

<!-- Add responsive style for the 3-card grid -->
<style>
@media(max-width:540px){
  div[style*="grid-template-columns:repeat(3,1fr)"].hc > div,
  .hc div[style*="grid-template-columns:repeat(3,1fr)"]{
    grid-template-columns:1fr !important;
  }
}
</style>'''

if OLD_HERO in content:
    content = content.replace(OLD_HERO, NEW_HERO)
    with open("app.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ Hero section updated successfully!")
    print("\nNow run:")
    print("  git add app.py")
    print('  git commit -m "Improve above-the-fold hero section"')
    print("  git push")
else:
    print("❌ Could not find the old hero block.")
    print("   Make sure app.py hasn't been modified since uploading.")
    print("   Try running fix_heatmap_final.py first, then this script.")
