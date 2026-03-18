"""
remove_nav_link.py
Removes the Deal Checker link from the navbar
Run from: C:\\Users\\WAFI\\irish-property-insights
"""

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# Try various forms it might appear as
removals = [
    '<a href="/deal-checker">Deal Checker</a>',
    '<a href=\'/deal-checker\'>Deal Checker</a>',
    '<a href="/deal-checker" >Deal Checker</a>',
]

removed = False
for r in removals:
    if r in content:
        content = content.replace(r, '')
        print(f"Removed: {r}")
        removed = True
        break

if not removed:
    # Search more broadly
    import re
    pattern = r'<a[^>]*href=["\']\/deal-checker["\'][^>]*>Deal Checker<\/a>'
    match = re.search(pattern, content)
    if match:
        print(f"Found: {match.group()}")
        content = re.sub(pattern, '', content)
        print("Removed Deal Checker nav link")
        removed = True

if removed:
    with open("app.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Done! Now run:")
    print("  git add app.py")
    print("  git commit -m \"Remove deal checker from navbar\"")
    print("  git push")
else:
    print("Link not found - may already be removed or in a different format")
