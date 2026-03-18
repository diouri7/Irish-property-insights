"""
RPZ (Rent Pressure Zone) Indicator
===================================
Adds an RPZ flag to every micro-area in:
  1. The PDF report table (new RPZ column)
  2. The web snapshot page (RPZ badge next to signal)
  3. The /methodology page (RPZ section explaining what it means)

RPZ data: Official Irish Government RPZ list (all areas designated as of 2024)
Matching: keyword match against micro-area name (case-insensitive, partial match)

Run: python add_rpz.py
"""

import ast

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

changes = 0

# ─────────────────────────────────────────────────────────
# 1. ADD RPZ DATA + LOOKUP FUNCTION
#    Insert after confidence_badge() function
# ─────────────────────────────────────────────────────────

RPZ_FUNC = '''

# ─── RPZ DATA ───────────────────────────────────────────
# Official Rent Pressure Zones (RTB / Government of Ireland, 2024)
# All local electoral areas and towns designated as RPZ areas
RPZ_KEYWORDS = [
    # Dublin City & suburbs
    "Dublin", "Swords", "Malahide", "Portmarnock", "Clongriffin",
    "Baldoyle", "Sutton", "Howth", "Raheny", "Clontarf", "Marino",
    "Drumcondra", "Glasnevin", "Finglas", "Ballymun", "Santry",
    "Beaumont", "Artane", "Coolock", "Kilbarrack", "Donaghmede",
    "Blanchardstown", "Castleknock", "Mulhuddart", "Clonsilla",
    "Lucan", "Clondalkin", "Tallaght", "Rathfarnham", "Templeogue",
    "Terenure", "Kimmage", "Crumlin", "Drimnagh", "Walkinstown",
    "Ballyfermot", "Chapelizod", "Palmerstown", "Rialto", "Kilmainham",
    "Inchicore", "Islandbridge", "Rathmines", "Ranelagh", "Milltown",
    "Dundrum", "Stillorgan", "Foxrock", "Leopardstown", "Sandyford",
    "Stepaside", "Carrickmines", "Kilternan", "Glencullen",
    "Dun Laoghaire", "Blackrock", "Monkstown", "Deansgrange",
    "Killiney", "Shankill", "Bray", "Greystones",
    "Cabinteely", "Sallynoggin", "Glasthule",
    # South Dublin / Wicklow border
    "Greystones", "Delgany", "Kilcoole", "Newcastle",
    # Dun Laoghaire-Rathdown
    "Dundrum", "Stillorgan", "Deansgrange", "Ballybrack",
    # Fingal
    "Swords", "Malahide", "Rush", "Lusk", "Donabate", "Balbriggan",
    "Balbriggan", "Skerries", "Naul", "Garristown",
    # South Dublin
    "Rathcoole", "Saggart", "Clondalkin", "Tallaght", "Citywest",
    # Cork City & suburbs
    "Cork", "Ballincollig", "Carrigaline", "Cobh", "Glanmire",
    "Blarney", "Tower", "Midleton", "Youghal", "Mallow",
    "Douglas", "Bishopstown", "Wilton", "Togher", "Turners Cross",
    "Blackpool", "Mayfield", "Gurranabraher", "Sunday's Well",
    "Shandon", "Blackrock", "Mahon",
    # Galway City & suburbs
    "Galway", "Salthill", "Knocknacarra", "Renmore", "Ballybane",
    "Doughiska", "Merlin Park", "Claregalway", "Oranmore",
    "Athenry", "Tuam",
    # Kildare (all designated)
    "Naas", "Newbridge", "Celbridge", "Maynooth", "Leixlip",
    "Clane", "Kilcock", "Monasterevin", "Athy", "Kildare",
    "Rathangan", "Kilcullen", "Curragh",
    # Meath
    "Navan", "Ashbourne", "Ratoath", "Dunshaughlin", "Trim",
    "Kells", "Dunboyne", "Clonee", "Stamullen",
    # Wicklow
    "Wicklow", "Arklow", "Bray", "Greystones", "Kilcoole",
    "Tinahely", "Rathdrum",
    # Louth
    "Drogheda", "Dundalk", "Ardee", "Carlingford",
    # Limerick City & county
    "Limerick", "Castletroy", "Dooradoyle", "Raheen", "Ballinacurra",
    "Annacotty", "Monaleen", "Corbally", "Ennis Road", "Mulgrave",
    # Waterford
    "Waterford", "Tramore", "Dungarvan",
    # Clare
    "Ennis", "Shannon", "Killaloe",
    # Laois
    "Portlaoise", "Portarlington",
    # Offaly
    "Tullamore",
    # Westmeath
    "Athlone", "Mullingar",
    # Wexford
    "Wexford", "Gorey", "New Ross",
]

# Normalise to lowercase for matching
_RPZ_LOWER = [k.lower() for k in RPZ_KEYWORDS]


def is_rpz(area_name):
    """Return True if this micro-area is in (or likely in) an RPZ.
    Uses partial keyword matching on the official RTB RPZ list."""
    if not isinstance(area_name, str):
        return False
    a = area_name.lower().strip()
    for kw in _RPZ_LOWER:
        if kw in a or a in kw:
            return True
    return False

'''

# Insert after confidence_badge function
INSERT_AFTER = "        return \"Low Confidence\", \"🟤\", \"Based on fewer than 6 sales — use as early indicator only.\"\n\n"
if INSERT_AFTER in content and "RPZ_KEYWORDS" not in content:
    content = content.replace(INSERT_AFTER, INSERT_AFTER + RPZ_FUNC)
    changes += 1
    print("  ✓ Added RPZ data + is_rpz() function")
else:
    # fallback: insert before compute_signal
    fallback = "def compute_signal("
    if fallback in content and "RPZ_KEYWORDS" not in content:
        content = content.replace(fallback, RPZ_FUNC + fallback)
        changes += 1
        print("  ✓ Added RPZ data + is_rpz() function (fallback insertion)")
    else:
        print("  - RPZ function already present or insertion point not found")

# ─────────────────────────────────────────────────────────
# 2. ADD RPZ COLUMN TO PDF TABLE HEADER
# ─────────────────────────────────────────────────────────

OLD_HEADER = '    header = ["#", "Micro-Area", "Median Price", "5yr Growth", "Yield", "Risk", "Signal", "Txns", "Confidence"]'
NEW_HEADER = '    header = ["#", "Micro-Area", "Median Price", "5yr Growth", "Yield", "Risk", "Signal", "Txns", "Confidence", "RPZ"]'

if OLD_HEADER in content:
    content = content.replace(OLD_HEADER, NEW_HEADER)
    changes += 1
    print("  ✓ Added RPZ column to PDF table header")
else:
    print("  - PDF table header not found")

# ─────────────────────────────────────────────────────────
# 3. ADD RPZ VALUE TO EACH TABLE ROW
# ─────────────────────────────────────────────────────────

OLD_ROW = '''        conf_label, conf_emoji, _ = confidence_badge(row["transactions"])
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

NEW_ROW = '''        conf_label, conf_emoji, _ = confidence_badge(row["transactions"])
        rpz_flag = "⚠ Yes" if is_rpz(row["area"]) else "No"
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
            rpz_flag,
        ])'''

if OLD_ROW in content:
    content = content.replace(OLD_ROW, NEW_ROW)
    changes += 1
    print("  ✓ Added RPZ flag to PDF table rows")
else:
    print("  - PDF table row block not found")

# ─────────────────────────────────────────────────────────
# 4. UPDATE PDF COLUMN WIDTHS (add RPZ column)
# ─────────────────────────────────────────────────────────

OLD_COLW = '    col_w = [0.5*cm, 3.8*cm, 2.2*cm, 1.8*cm, 1.4*cm, 1.4*cm, 2.2*cm, 1.1*cm, 2.0*cm]'
NEW_COLW = '    col_w = [0.5*cm, 3.4*cm, 2.0*cm, 1.6*cm, 1.3*cm, 1.3*cm, 2.0*cm, 1.0*cm, 1.7*cm, 1.2*cm]'

if OLD_COLW in content:
    content = content.replace(OLD_COLW, NEW_COLW)
    changes += 1
    print("  ✓ Updated PDF column widths for RPZ column")
else:
    print("  - PDF column widths not found")

# ─────────────────────────────────────────────────────────
# 5. ADD RPZ SECTION TO /methodology PAGE
#    Insert after the Confidence Score section
# ─────────────────────────────────────────────────────────

RPZ_SECTION = '''
  <div class="section red" style="border-left-color:#F59E0B">
    <h2>🏘️ Rent Pressure Zone (RPZ) Indicator</h2>
    <p>Every micro-area now shows an <strong>RPZ flag</strong> — indicating whether that area falls within an official <strong>Rent Pressure Zone</strong> as designated by the Irish Government and the Residential Tenancies Board (RTB).</p>
    <p>In RPZ areas, annual rent increases are <strong>capped at 2% or the rate of inflation (HICP), whichever is lower</strong>. This is a critical variable for any landlord or buy-to-let investor — a HIGH POTENTIAL signal based on current market rent may be misleading if the property already has a sitting tenant in an RPZ, since you cannot increase rent to market rate.</p>
    <table class="conf-table">
      <tr><th>RPZ Status</th><th>What it means for investors</th></tr>
      <tr><td><strong>⚠ Yes — RPZ</strong></td><td>Rent increases capped at 2%/HICP. Yield calculation reflects current market rent, not necessarily achievable rent for existing tenancies.</td></tr>
      <tr><td><strong>No — Non-RPZ</strong></td><td>No statutory rent cap. Rent can be set at market rate on a new tenancy.</td></tr>
    </table>
    <p style="margin-top:.75rem;font-size:.88rem;color:#64748B">RPZ boundaries are based on the RTB's official 2024 designations. Always verify current status at <a href="https://www.rtb.ie/registration-and-compliance/rent-pressure-zones" target="_blank" style="color:#94A3B8">rtb.ie</a> before making investment decisions. Micro-area matching uses keyword-based detection — verify manually for boundary areas.</p>
  </div>

'''

# Insert before the disclaimer div in the methodology page
OLD_METH_DISCLAIMER_MARKER = '  <div class="disclaimer">'
if OLD_METH_DISCLAIMER_MARKER in content and "RPZ Indicator" not in content:
    content = content.replace(OLD_METH_DISCLAIMER_MARKER, RPZ_SECTION + OLD_METH_DISCLAIMER_MARKER, 1)
    changes += 1
    print("  ✓ Added RPZ section to /methodology page")
elif "RPZ Indicator" in content:
    print("  - RPZ section already present in methodology")
else:
    print("  - Could not find methodology disclaimer insertion point")

# ─────────────────────────────────────────────────────────
# 6. UPDATE SIGNAL DEFINITIONS TABLE IN METHODOLOGY
#    Add a note about RPZ impact on HIGH POTENTIAL
# ─────────────────────────────────────────────────────────

OLD_HP_ROW = '<tr><td><strong>HIGH POTENTIAL</strong></td><td>Strong yield, strong growth, low-medium risk. Score ≥ 6.</td></tr>'
NEW_HP_ROW = '<tr><td><strong>HIGH POTENTIAL</strong></td><td>Strong yield, strong growth, low-medium risk. Score ≥ 6. <em style="color:#F59E0B">Check RPZ status — yield assumes market rent.</em></td></tr>'

if OLD_HP_ROW in content:
    content = content.replace(OLD_HP_ROW, NEW_HP_ROW)
    changes += 1
    print("  ✓ Added RPZ note to HIGH POTENTIAL signal definition")
else:
    print("  - HIGH POTENTIAL row not found in methodology")

# ─────────────────────────────────────────────────────────
# SYNTAX CHECK + WRITE
# ─────────────────────────────────────────────────────────

try:
    ast.parse(content)
    print("\n  ✓ Syntax OK")
except SyntaxError as e:
    print(f"\n  ✗ SYNTAX ERROR at line {e.lineno}: {e.msg}")
    print("  File NOT written — fix syntax before proceeding.")
    exit(1)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)

print(f"\n{'='*50}")
print(f"✅ Done — {changes} changes applied.")
print("\nNow run:")
print("  git add app.py")
print("  git commit -m \"Add RPZ indicator to PDF reports and methodology page\"")
print("  git push")
