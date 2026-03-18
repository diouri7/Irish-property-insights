"""
Fixes the deal checker homepage form so it works on mobile.
Run from C:\\Users\\WAFI\\irish-property-insights:
    python fix_deal_checker_mobile.py
"""

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

OLD = '''    <div style="background:#1a1c20;border:1px solid #2a2c30;border-radius:4px;padding:2rem 2.5rem;text-align:left;">
      <form method="POST" action="/deal-checker" style="display:grid;grid-template-columns:1fr 1fr 1fr auto;gap:1rem;align-items:end;">
        <div>
          <label style="display:block;font-size:0.72rem;font-weight:500;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;margin-bottom:0.4rem;">County</label>
          <select name="county" required style="width:100%;font-family:inherit;font-size:0.95rem;padding:0.7rem 1rem;border:1px solid #2a2c30;border-radius:3px;background:#0f1014;color:white;">
            <option value="" disabled selected>Select</option>
            <option value="Carlow">Carlow</option>
            <option value="Cavan">Cavan</option>
            <option value="Clare">Clare</option>
            <option value="Cork">Cork</option>
            <option value="Donegal">Donegal</option>
            <option value="Dublin">Dublin</option>
            <option value="Galway">Galway</option>
            <option value="Kerry">Kerry</option>
            <option value="Kildare">Kildare</option>
            <option value="Kilkenny">Kilkenny</option>
            <option value="Laois">Laois</option>
            <option value="Leitrim">Leitrim</option>
            <option value="Limerick">Limerick</option>
            <option value="Longford">Longford</option>
            <option value="Louth">Louth</option>
            <option value="Mayo">Mayo</option>
            <option value="Meath">Meath</option>
            <option value="Monaghan">Monaghan</option>
            <option value="Offaly">Offaly</option>
            <option value="Roscommon">Roscommon</option>
            <option value="Sligo">Sligo</option>
            <option value="Tipperary">Tipperary</option>
            <option value="Waterford">Waterford</option>
            <option value="Westmeath">Westmeath</option>
            <option value="Wexford">Wexford</option>
            <option value="Wicklow">Wicklow</option>
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
    </div>'''

NEW = '''    <div style="background:#1a1c20;border:1px solid #2a2c30;border-radius:4px;padding:2rem 2rem;text-align:left;">
      <style>
        .dc-form{display:grid;grid-template-columns:1fr 1fr 1fr;gap:1rem;}
        .dc-inp{width:100%;font-family:inherit;font-size:0.95rem;padding:0.75rem 1rem;border:1px solid #2a2c30;border-radius:3px;background:#0f1014;color:white;outline:none;}
        .dc-inp:focus{border-color:#c9a84c;}
        .dc-label{display:block;font-size:0.7rem;font-weight:500;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;margin-bottom:0.4rem;}
        .dc-btn{width:100%;margin-top:1rem;padding:0.85rem 1rem;background:#c9a84c;color:#0f1014;border:none;border-radius:3px;font-family:inherit;font-size:0.85rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;cursor:pointer;}
        .dc-btn:hover{background:#d4b86a;}
        @media(max-width:600px){.dc-form{grid-template-columns:1fr 1fr;}}
        @media(max-width:400px){.dc-form{grid-template-columns:1fr;}}
      </style>
      <form method="POST" action="/deal-checker">
        <div class="dc-form">
          <div>
            <label class="dc-label">County</label>
            <select name="county" required class="dc-inp">
              <option value="" disabled selected>Select county</option>
              <option value="Carlow">Carlow</option>
              <option value="Cavan">Cavan</option>
              <option value="Clare">Clare</option>
              <option value="Cork">Cork</option>
              <option value="Donegal">Donegal</option>
              <option value="Dublin">Dublin</option>
              <option value="Galway">Galway</option>
              <option value="Kerry">Kerry</option>
              <option value="Kildare">Kildare</option>
              <option value="Kilkenny">Kilkenny</option>
              <option value="Laois">Laois</option>
              <option value="Leitrim">Leitrim</option>
              <option value="Limerick">Limerick</option>
              <option value="Longford">Longford</option>
              <option value="Louth">Louth</option>
              <option value="Mayo">Mayo</option>
              <option value="Meath">Meath</option>
              <option value="Monaghan">Monaghan</option>
              <option value="Offaly">Offaly</option>
              <option value="Roscommon">Roscommon</option>
              <option value="Sligo">Sligo</option>
              <option value="Tipperary">Tipperary</option>
              <option value="Waterford">Waterford</option>
              <option value="Westmeath">Westmeath</option>
              <option value="Wexford">Wexford</option>
              <option value="Wicklow">Wicklow</option>
            </select>
          </div>
          <div>
            <label class="dc-label">Area / Town</label>
            <input type="text" name="area" placeholder="e.g. Blackrock" required class="dc-inp">
          </div>
          <div>
            <label class="dc-label">Asking Price</label>
            <div style="position:relative;">
              <span style="position:absolute;left:1rem;top:50%;transform:translateY(-50%);color:#6b6860;pointer-events:none;">€</span>
              <input type="number" name="asking_price" placeholder="350000" required class="dc-inp" style="padding-left:1.8rem;">
            </div>
          </div>
        </div>
        <button type="submit" class="dc-btn">Analyse This Property →</button>
      </form>
      <p style="margin-top:0.75rem;font-size:0.75rem;color:#4a4845;text-align:center;">Not financial advice. Based on PPR data 2010–2024.</p>
    </div>'''

if OLD in content:
    content = content.replace(OLD, NEW)
    with open("app.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ Deal checker form fixed for mobile!")
    print("\nNow run:")
    print("  git add app.py")
    print('  git commit -m "Fix deal checker form mobile layout"')
    print("  git push")
else:
    print("❌ Could not find the form block to replace.")
    print("   Make sure app.py is in the same folder as this script.")
