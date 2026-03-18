import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# Common nav link patterns to find and insert after
# We'll look for existing nav links and add Deal Checker

replacements = [
    # Pattern: methodology link
    ('href="/methodology"', 'href="/methodology"'),
]

# Find a nav link to insert after - try several common ones
inserted = False

nav_candidates = [
    '/methodology',
    '/about', 
    '/reports',
    '/counties',
]

for candidate in nav_candidates:
    if candidate in content:
        # Find the closing </a> after this href
        idx = content.find(candidate)
        # Find the </a> after this position
        end_a = content.find('</a>', idx)
        if end_a != -1:
            # Check if deal-checker link already exists
            if '/deal-checker' in content[:content.find('</nav>', idx)] if '</nav>' in content[idx:] else '/deal-checker' in content:
                print("Deal Checker link already exists in nav")
                inserted = True
                break
            
            insert_pos = end_a + 4  # after </a>
            # Figure out what style the existing links use
            # Extract the existing link for reference
            start_a = content.rfind('<a ', 0, idx)
            existing_link = content[start_a:end_a+4]
            print(f"Found nav link: {existing_link[:80]}")
            
            # Build new link matching same style
            new_link = existing_link
            # Replace the href
            new_link = re.sub(r'href="[^"]*"', 'href="/deal-checker"', new_link)
            # Replace the text content
            new_link = re.sub(r'>([^<]+)</a>', '>Deal Checker</a>', new_link)
            
            content = content[:insert_pos] + new_link + content[insert_pos:]
            print(f"Inserted: {new_link[:80]}")
            inserted = True
            break

if not inserted:
    # Fallback: find </nav> and insert before it
    nav_end = content.find('</nav>')
    if nav_end != -1:
        new_link = '<a href="/deal-checker">Deal Checker</a>'
        content = content[:nav_end] + new_link + content[nav_end:]
        print(f"Inserted fallback link before </nav>")
        inserted = True

if inserted:
    with open("app.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("app.py updated successfully!")
    print("Now run:")
    print("  git add app.py")
    print("  git commit -m Add deal checker to nav")
    print("  git push")
else:
    print("Could not find nav - please share a snippet of your navbar HTML")
