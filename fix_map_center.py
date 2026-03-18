"""
fix_map_center.py
- Centers the map in its black box
- Makes counties bigger by tightening the viewBox
- Ensures map fills the container properly
Run from: C:\\Users\\WAFI\\irish-property-insights
"""
import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

changes = 0

# Fix 1: Make the map container take more space in the grid
# Change grid to give map more room
old_grid = 'style="display:grid;grid-template-columns:1fr 260px;gap:2rem;align-items:start;"'
new_grid = 'style="display:grid;grid-template-columns:1.8fr 260px;gap:2rem;align-items:start;"'
if old_grid in content:
    content = content.replace(old_grid, new_grid)
    print("✓ Widened map column in grid")
    changes += 1

# Fix 2: Make the black map box taller and center content
old_box = 'style="background:#111316;border:1px solid #1a1c20;border-radius:4px;padding:1.5rem;display:flex;align-items:center;justify-content:center;min-height:450px;"'
new_box = 'style="background:#111316;border:1px solid #1a1c20;border-radius:4px;padding:2rem;display:flex;align-items:center;justify-content:center;min-height:500px;"'
if old_box in content:
    content = content.replace(old_box, new_box)
    print("✓ Made map box taller and padded")
    changes += 1

# Fix 3: Tighten the SVG viewBox to zoom in on the counties
# Current viewBox="0 0 400 440" - counties only occupy roughly 20-320 x 10-320
old_vb = 'viewBox="0 0 400 440"'
new_vb = 'viewBox="10 10 300 320"'
if old_vb in content:
    content = content.replace(old_vb, new_vb)
    print("✓ Tightened viewBox to zoom in on counties")
    changes += 1

# Fix 4: Make SVG itself bigger in its container
old_svg_style = 'style="width:100%;display:block;"'
new_svg_style = 'style="width:100%;max-width:520px;display:block;margin:0 auto;"'
if old_svg_style in content:
    content = content.replace(old_svg_style, new_svg_style)
    print("✓ Made SVG fill container with max-width")
    changes += 1

print(f"\n{changes} changes applied")

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)

print("\nNow run:")
print("  git add app.py")
print("  git commit -m \"Fix map centering and size\"")
print("  git push")
