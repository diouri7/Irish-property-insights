"""
fix_heatmap_desktop.py
Fixes the large gap between map and sidebar on desktop
The flex container is wrapping when it shouldn't be
Run from: C:\\Users\\WAFI\\irish-property-insights
"""

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

changes = 0

# Fix 1: Remove flex-wrap so sidebar stays beside map on desktop
for old, new in [
    (
        'id="hm-map-flex" style="display:flex;gap:1.5rem;align-items:flex-start;flex-wrap:wrap;"',
        'id="hm-map-flex" style="display:flex;gap:2rem;align-items:flex-start;"'
    ),
    (
        'style="display:flex;gap:1.5rem;align-items:flex-start;flex-wrap:wrap;"',
        'id="hm-map-flex" style="display:flex;gap:2rem;align-items:flex-start;"'
    ),
    (
        'style="display:flex;gap:2.5rem;align-items:flex-start;flex-wrap:wrap;"',
        'id="hm-map-flex" style="display:flex;gap:2rem;align-items:flex-start;"'
    ),
]:
    if old in content:
        content = content.replace(old, new)
        print(f"✓ Fixed flex container")
        changes += 1
        break

# Fix 2: Make map take remaining space, sidebar fixed width
for old, new in [
    (
        'style="flex:1;min-width:260px;max-width:100%;"',
        'style="flex:1;min-width:0;"'
    ),
    (
        'style="flex:1;min-width:280px;"',
        'style="flex:1;min-width:0;"'
    ),
]:
    if old in content:
        content = content.replace(old, new)
        print(f"✓ Fixed map div")
        changes += 1
        break

# Fix 3: Sidebar - fixed width, no flex-grow
for old, new in [
    (
        'style="width:280px;flex-shrink:0;min-width:260px;flex:1;"',
        'style="width:260px;flex-shrink:0;"'
    ),
    (
        'style="width:280px;flex-shrink:0;"',
        'style="width:260px;flex-shrink:0;"'
    ),
]:
    if old in content:
        content = content.replace(old, new)
        print(f"✓ Fixed sidebar div")
        changes += 1
        break

# Fix 4: Make the outer section max-width wider
for old, new in [
    (
        'style="max-width:960px;margin:0 auto;"',
        'style="max-width:1000px;margin:0 auto;"'
    ),
]:
    if old in content:
        content = content.replace(old, new)
        print(f"✓ Fixed outer container width")
        changes += 1

print(f"\n{changes} changes applied")

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)

print("\nNow run:")
print("  git add app.py")
print("  git commit -m \"Fix heatmap desktop layout\"")
print("  git push")
