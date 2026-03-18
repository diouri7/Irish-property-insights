"""
fix_heatmap_size.py
- Makes the map bigger
- Removes the black empty space
- Fixes mobile map visibility
Run from: C:\\Users\\WAFI\\irish-property-insights
"""

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

changes = 0

# Fix 1: Remove the black space - it's caused by the section padding being too much
# and the map container not filling the space properly
for old, new in [
    (
        'style="background:#0a0c0f;padding:5rem 2rem;border-top:1px solid #1a1c20;"',
        'style="background:#0a0c0f;padding:3rem 2rem 3rem;border-top:1px solid #1a1c20;"'
    ),
]:
    if old in content:
        content = content.replace(old, new)
        print("✓ Fixed section padding")
        changes += 1

# Fix 2: Make map fill more space - increase flex ratio
for old, new in [
    ('style="flex:1;min-width:0;"', 'style="flex:2;min-width:0;"'),
]:
    if old in content:
        content = content.replace(old, new, 1)  # only first occurrence
        print("✓ Fixed map flex ratio")
        changes += 1

# Fix 3: Make SVG viewBox scale up - bigger counties
for old, new in [
    (
        'viewBox="0 0 370 420" style="width:100%;height:auto;"',
        'viewBox="0 0 370 420" style="width:100%;height:auto;min-height:380px;"'
    ),
]:
    if old in content:
        content = content.replace(old, new)
        print("✓ Fixed SVG min-height")
        changes += 1

# Fix 4: Scale up all county path coordinates by 1.35x and move labels
# We do this by changing the viewBox to zoom in on Ireland
for old, new in [
    (
        'viewBox="0 0 370 420" style="width:100%;height:auto;min-height:380px;"',
        'viewBox="15 10 310 360" style="width:100%;height:auto;min-height:400px;"'
    ),
]:
    if old in content:
        content = content.replace(old, new)
        print("✓ Zoomed in viewBox for bigger counties")
        changes += 1

# Fix 5: Add mobile responsive - show map on mobile too
old_style = '''.hm-toggle { transition: background 0.2s, color 0.2s; }
@media (max-width: 640px) {
  #hm-map-flex { flex-direction: column !important; gap: 1rem !important; }
  #hm-map-flex > div:first-child { min-width: unset !important; }
  #hm-map-flex > div:last-child { width: 100% !important; min-width: unset !important; }
}'''

new_style = '''.hm-toggle { transition: background 0.2s, color 0.2s; }
@media (max-width: 700px) {
  #hm-map-flex { flex-direction: column !important; gap: 1.5rem !important; }
  #hm-map-flex > div:first-child { flex: unset !important; width: 100% !important; }
  #hm-map-flex > div:last-child { width: 100% !important; min-width: unset !important; }
  #ireland-map { min-height: 300px !important; }
}'''

# Try both possible style blocks
if old_style in content:
    content = content.replace(old_style, new_style)
    print("✓ Fixed mobile responsive styles")
    changes += 1
else:
    # Try adding after existing style tag
    old_style2 = '.hm-toggle { transition: background 0.2s, color 0.2s; }'
    new_style2 = '''.hm-toggle { transition: background 0.2s, color 0.2s; }
@media (max-width: 700px) {
  #hm-map-flex { flex-direction: column !important; gap: 1.5rem !important; }
  #hm-map-flex > div:first-child { flex: unset !important; width: 100% !important; }
  #hm-map-flex > div:last-child { width: 100% !important; }
}'''
    if old_style2 in content:
        content = content.replace(old_style2, new_style2)
        print("✓ Fixed mobile responsive styles (method 2)")
        changes += 1

print(f"\n{changes} changes applied")

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)

print("\nNow run:")
print("  git add app.py")
print("  git commit -m \"Fix heatmap size and mobile layout\"")
print("  git push")
