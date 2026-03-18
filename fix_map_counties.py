"""
fix_map_counties.py
Fixes:
1. Cavan and Monaghan floating away from rest of map
2. Map too small on desktop - not filling container
Run from: C:\\Users\\WAFI\\irish-property-insights
"""
import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

changes = 0

# Fix 1: Cavan - move it to connect properly with Monaghan, Meath, Longford, Leitrim
old_cavan = '''<path id="hm-Cavan"     onclick="hmSel('Cavan')"     class="hmc" d="M147,60 L173,57 L192,64 L196,79 L188,91 L166,84 L151,74 L143,66 Z"/>'''
new_cavan = '''<path id="hm-Cavan"     onclick="hmSel('Cavan')"     class="hmc" d="M151,74 L173,72 L192,79 L196,91 L188,91 L166,84 L155,94 L143,83 Z"/>'''
if old_cavan in content:
    content = content.replace(old_cavan, new_cavan)
    print("✓ Fixed Cavan position")
    changes += 1

# Fix 2: Monaghan - move to connect with Cavan and NI border
old_mono = '''<path id="hm-Monaghan"  onclick="hmSel('Monaghan')"  class="hmc" d="M173,49 L200,45 L215,57 L211,72 L192,75 L192,64 L181,55 Z"/>'''
new_mono = '''<path id="hm-Monaghan"  onclick="hmSel('Monaghan')"  class="hmc" d="M192,64 L211,60 L225,72 L218,84 L200,87 L192,79 L173,72 Z"/>'''
if old_mono in content:
    content = content.replace(old_mono, new_mono)
    print("✓ Fixed Monaghan position")
    changes += 1

# Fix 3: Update Cavan label position
old_cav_label = '''<text x="170" y="72"  font-size="6"   fill="rgba(255,255,255,0.55)" text-anchor="middle" pointer-events="none">Cavan</text>'''
new_cav_label = '''<text x="170" y="85"  font-size="6"   fill="rgba(255,255,255,0.55)" text-anchor="middle" pointer-events="none">Cavan</text>'''
if old_cav_label in content:
    content = content.replace(old_cav_label, new_cav_label)
    print("✓ Fixed Cavan label")
    changes += 1

# Fix 4: Update Monaghan label position
old_mono_label = '''<text x="194" y="61"  font-size="5.5" fill="rgba(255,255,255,0.55)" text-anchor="middle" pointer-events="none">Monaghan</text>'''
new_mono_label = '''<text x="207" y="76"  font-size="5.5" fill="rgba(255,255,255,0.55)" text-anchor="middle" pointer-events="none">Monaghan</text>'''
if old_mono_label in content:
    content = content.replace(old_mono_label, new_mono_label)
    print("✓ Fixed Monaghan label")
    changes += 1

# Fix 5: NI shape - update to match new Cavan/Monaghan positions
old_ni = '''<path style="fill:#1a1c20;stroke:#111316;stroke-width:1;pointer-events:none;" d="M165,30 L218,23 L232,45 L218,68 L188,76 L158,68 L178,52 Z"/>'''
new_ni = '''<path style="fill:#1a1c20;stroke:#111316;stroke-width:1;pointer-events:none;" d="M165,30 L218,23 L240,45 L230,70 L218,84 L192,64 L178,52 Z"/>'''
if old_ni in content:
    content = content.replace(old_ni, new_ni)
    print("✓ Fixed NI shape")
    changes += 1

# Fix 6: Make map bigger on desktop by changing the viewBox to show more
# Currently viewBox="20 12 265 310" - tighten it to zoom in more
old_vb = 'viewBox="20 12 265 310"'
new_vb = 'viewBox="18 12 255 270"'
if old_vb in content:
    content = content.replace(old_vb, new_vb)
    print("✓ Tightened viewBox to zoom in on map")
    changes += 1

# Fix 7: Make the map panel taller on desktop
old_map_wrap = 'style="background:#111316;border:1px solid #1a1c20;border-radius:4px;padding:1rem;display:flex;align-items:center;justify-content:center;"'
new_map_wrap = 'style="background:#111316;border:1px solid #1a1c20;border-radius:4px;padding:1.5rem;display:flex;align-items:center;justify-content:center;min-height:450px;"'
if old_map_wrap in content:
    content = content.replace(old_map_wrap, new_map_wrap)
    print("✓ Made map panel taller")
    changes += 1

print(f"\n{changes} changes applied")

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)

print("\nNow run:")
print("  git add app.py")
print("  git commit -m \"Fix map counties and size\"")
print("  git push")
