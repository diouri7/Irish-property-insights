"""
add_homepage_checker.py
Adds an inline deal checker section to the homepage
Run from: C:\\Users\\WAFI\\irish-property-insights
"""
import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

COUNTIES_JS = '["Carlow","Cavan","Clare","Cork","Donegal","Dublin","Galway","Kerry","Kildare","Kilkenny","Laois","Leitrim","Limerick","Longford","Louth","Mayo","Meath","Monaghan","Offaly","Roscommon","Sligo","Tipperary","Waterford","Westmeath","Wexford","Wicklow"]'

DEAL_SECTION = '''
<!-- ── DEAL CHECKER SECTION ── -->
<section style="background:#0f1014;padding:5rem 2rem;">
  <div style="max-width:700px;margin:0 auto;text-align:center;">
    <div style="display:inline-block;font-size:0.72rem;font-weight:500;letter-spacing:0.15em;text-transform:uppercase;color:#c9a84c;border:1px solid #c9a84c;padding:0.3rem 0.8rem;border-radius:2px;margin-bottom:1.5rem;">Free Tool</div>
    <h2 style="font-family:'Playfair Display',serif;font-size:clamp(1.8rem,4vw,2.6rem);font-weight:900;color:white;line-height:1.15;margin-bottom:1rem;">Is That Property a Good Deal?</h2>
    <p style="color:#9a9690;font-size:1rem;font-weight:300;line-height:1.7;max-width:500px;margin:0 auto 2.5rem;">Enter any Irish property and we'll compare it against 700,000+ real PPR transactions instantly.</p>
    <div style="background:#1a1c20;border:1px solid #2a2c30;border-radius:4px;padding:2rem 2.5rem;text-align:left;">
      <form method="POST" action="/deal-checker" style="display:grid;grid-template-columns:1fr 1fr 1fr auto;gap:1rem;align-items:end;">
        <div>
          <label style="display:block;font-size:0.72rem;font-weight:500;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;margin-bottom:0.4rem;">County</label>
          <select name="county" required style="width:100%;font-family:inherit;font-size:0.95rem;padding:0.7rem 1rem;border:1px solid #2a2c30;border-radius:3px;background:#0f1014;color:white;">
            <option value="" disabled selected>Select</option>
            ''' + '\n            '.join(f'<option value="{c}">{c}</option>' for c in ["Carlow","Cavan","Clare","Cork","Donegal","Dublin","Galway","Kerry","Kildare","Kilkenny","Laois","Leitrim","Limerick","Longford","Louth","Mayo","Meath","Monaghan","Offaly","Roscommon","Sligo","Tipperary","Waterford","Westmeath","Wexford","Wicklow"]) + '''
          </select>
        </div>
        <div>
          <label style="display:block;font-size:0.72rem;font-weight:500;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;margin-bottom:0.4rem;">Area / Town</label>
          <input type="text" name="area" placeholder="e.g. Blackrock" required style="width:100%;font-family:inherit;font-size:0.95rem;padding:0.7rem 1rem;border:1px solid #2a2c30;border-radius:3px;background:#0f1014;color:white;">
        </div>
        <div>
          <label style="display:block;font-size:0.72rem;font-weight:500;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;margin-bottom:0.4rem;">Asking Price</label>
          <div style="position:relative;">
            <span style="position:absolute;left:1rem;top:50%;transform:translateY(-50%);color:#6b6860;">€</span>
            <input type="number" name="asking_price" placeholder="350000" required style="width:100%;font-family:inherit;font-size:0.95rem;padding:0.7rem 1rem 0.7rem 1.8rem;border:1px solid #2a2c30;border-radius:3px;background:#0f1014;color:white;">
          </div>
        </div>
        <div>
          <button type="submit" style="width:100%;padding:0.7rem 1.5rem;background:#c9a84c;color:#0f1014;border:none;border-radius:3px;font-family:inherit;font-size:0.85rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;cursor:pointer;white-space:nowrap;">Analyse →</button>
        </div>
      </form>
      <p style="margin-top:1rem;font-size:0.75rem;color:#4a4845;text-align:center;">Not financial advice. Based on PPR data 2010–2024.</p>
    </div>
  </div>
</section>
<!-- ── END DEAL CHECKER SECTION ── -->
'''

# Find the "Real Sample" / "See exactly what you get" section to insert before it
markers = [
    'Real Sample',
    'See exactly what you get',
    'see exactly what you get',
]

inserted = False
for marker in markers:
    idx = content.find(marker)
    if idx != -1:
        # Find the opening < of the section/div tag before this marker
        section_start = content.rfind('<section', 0, idx)
        div_start = content.rfind('<div', 0, idx)
        insert_at = max(section_start, div_start)
        
        if insert_at > 0:
            content = content[:insert_at] + DEAL_SECTION + content[insert_at:]
            print(f"Inserted deal checker section before '{marker}' marker")
            inserted = True
            break

if not inserted:
    print("Could not find insertion point. Looking for alternative...")
    # Try inserting after the stats section (26 Counties Covered etc)
    stats_markers = ['500+', 'Micro-Areas Scored', 'Transaction History']
    for marker in stats_markers:
        idx = content.find(marker)
        if idx != -1:
            # Find the closing </section> or </div> after this
            end = content.find('</section>', idx)
            if end != -1:
                content = content[:end+10] + DEAL_SECTION + content[end+10:]
                print(f"Inserted after stats section (found '{marker}')")
                inserted = True
                break

if inserted:
    with open("app.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("app.py updated!")
    print("\nNow run:")
    print("  git add app.py")
    print("  git commit -m \"Add deal checker to homepage\"")
    print("  git push")
else:
    print("ERROR: Could not find insertion point")
