"""
Finds and replaces the hero section in your current app.py.
Works regardless of which patches have already been applied.
Run: python fix_hero2.py
"""

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# ── Detect current state ──
has_old = "Stop Guessing" in content
has_new = "Data-Driven Map" in content

print(f"Old hero present: {has_old}")
print(f"New hero present: {has_new}")

if has_new:
    print("✅ New hero is already live! Changes should be visible on Railway.")
    print("   Try a hard refresh: Ctrl+Shift+R in your browser.")
    exit()

if not has_old:
    print("⚠️  Could not find 'Stop Guessing' in app.py.")
    print("   Searching for the hero section another way...")

# ── Find the hero section by its class ──
HERO_START = '<section class="hero">'
HERO_END   = '</section>\n<div class="cb">'

start = content.find(HERO_START)
end   = content.find(HERO_END)

if start == -1 or end == -1:
    print(f"ERROR: Could not locate hero section (start={start}, end={end})")
    print("Please upload your current app.py to Claude and ask to fix the hero.")
    exit(1)

end_full = end + len(HERO_END)

print(f"Found hero section at characters {start}–{end_full}")

NEW_HERO = '''<section class="hero" style="padding:7rem 2rem 3rem;">
  <div class="hc">

    <div style="display:inline-flex;align-items:center;gap:0.5rem;padding:0.4rem 1rem;background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.2);border-radius:100px;font-size:0.78rem;font-weight:600;color:var(--green);margin-bottom:2rem;">
      <span style="width:6px;height:6px;border-radius:50%;background:var(--green);animation:pulse 2s infinite;flex-shrink:0;"></span>
      Built on official PPR &amp; RTB data — 727,000 transactions
    </div>

    <h1 style="font-family:var(--fd);font-size:clamp(2.6rem,5.5vw,4.4rem);font-weight:700;line-height:1.08;letter-spacing:-0.03em;margin-bottom:1.5rem;">
      The Data-Driven Map<br>for <em style="font-style:italic;color:var(--green);">Irish Property</em> Investors
    </h1>

    <p class="hs" style="font-size:1.15rem;max-width:580px;margin:0 auto 0.75rem;">
      We analyse RTB and Property Price Register data to surface high-yield micro-areas you won\'t find on Daft.
    </p>
    <p style="font-size:0.9rem;color:var(--t3);max-width:480px;margin:0 auto 2.5rem;line-height:1.6;">
      Every micro-area across all 26 counties ranked by rental yield, 5-year growth, and investment risk — free.
    </p>

    <div style="display:flex;gap:0.75rem;flex-wrap:wrap;justify-content:center;margin-bottom:2.5rem;">
      <div style="padding:0.4rem 0.9rem;background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.15);border-radius:6px;font-size:0.82rem;color:var(--green);font-weight:500;">✓ 500+ micro-areas ranked</div>
      <div style="padding:0.4rem 0.9rem;background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.15);border-radius:6px;font-size:0.82rem;color:var(--green);font-weight:500;">✓ All 26 counties</div>
      <div style="padding:0.4rem 0.9rem;background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.15);border-radius:6px;font-size:0.82rem;color:var(--green);font-weight:500;">✓ Official government data only</div>
      <div style="padding:0.4rem 0.9rem;background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.15);border-radius:6px;font-size:0.82rem;color:var(--green);font-weight:500;">✓ Updated Q2 2025</div>
    </div>

    <div class="hctas">
      <a href="#snap" class="bp" style="font-size:1.05rem;padding:1rem 2.2rem;">Find High-Yield Areas Free &#8594;</a>
      <a href="#reports" class="bs">Full County Report &mdash; &euro;29</a>
    </div>
    <p style="font-size:0.8rem;color:var(--t3);margin-top:1rem;">No credit card &middot; No signup &middot; Instant download</p>

    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;max-width:680px;margin:3.5rem auto 0;text-align:left;">
      <div style="background:var(--card);border:1px solid var(--border);border-radius:12px;padding:1.25rem;border-top:2px solid var(--green);">
        <div style="font-size:1.2rem;margin-bottom:0.5rem;">&#128205;</div>
        <div style="font-size:0.85rem;font-weight:600;margin-bottom:0.3rem;color:var(--t1);">Where to invest</div>
        <div style="font-size:0.8rem;color:var(--t3);line-height:1.5;">Every micro-area ranked &mdash; not vague county averages</div>
      </div>
      <div style="background:var(--card);border:1px solid var(--border);border-radius:12px;padding:1.25rem;border-top:2px solid var(--gold);">
        <div style="font-size:1.2rem;margin-bottom:0.5rem;">&#128176;</div>
        <div style="font-size:0.85rem;font-weight:600;margin-bottom:0.3rem;color:var(--t1);">What return to expect</div>
        <div style="font-size:0.8rem;color:var(--t3);line-height:1.5;">Gross yield from live RTB rent data</div>
      </div>
      <div style="background:var(--card);border:1px solid var(--border);border-radius:12px;padding:1.25rem;border-top:2px solid var(--blue);">
        <div style="font-size:1.2rem;margin-bottom:0.5rem;">&#128737;</div>
        <div style="font-size:0.85rem;font-weight:600;margin-bottom:0.3rem;color:var(--t1);">How risky it is</div>
        <div style="font-size:0.8rem;color:var(--t3);line-height:1.5;">Scored by price volatility &amp; transaction volume</div>
      </div>
    </div>

  </div>
</section>
<div class="cb"><div class="cbi"><div class="ci"><div class="cn">727k</div><div class="cl">PPR Transactions</div></div><div class="ci"><div class="cn">15yr</div><div class="cl">Price History</div></div><div class="ci"><div class="cn">500+</div><div class="cl">Micro-Areas Scored</div></div><div class="ci"><div class="cn">&euro;29</div><div class="cl">Full County Report</div></div></div><p style="text-align:center;font-size:.8rem;color:var(--t3);margin-top:1.5rem;font-weight:500">Data: <a href="https://www.propertypriceregister.ie" target="_blank" style="color:var(--t2);text-decoration:none;">Property Price Register</a> &amp; <a href="https://www.rtb.ie" target="_blank" style="color:var(--t2);text-decoration:none;">Residential Tenancies Board</a> &mdash; official Irish government records.</p></div>'''

new_content = content[:start] + NEW_HERO + content[end_full:]

with open("app.py", "w", encoding="utf-8") as f:
    f.write(new_content)

print("✅ Hero section replaced successfully!")
print("\nNow run:")
print("  git add app.py")
print('  git commit -m "New above-the-fold hero section"')
print("  git push")
