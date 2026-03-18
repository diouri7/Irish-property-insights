"""
fix_dataframe.py
Fixes: TypeError: unhashable type: 'dict' in deal checker route
Run from: C:\\Users\\WAFI\\irish-property-insights
"""

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# The broken line uses double braces which got mangled
old = 'X = pd.DataFrame([{{"county_enc":county_enc,"micro_enc":micro_enc,"desc_enc":desc_enc,"year":2024}}])'
new = 'X = pd.DataFrame({"county_enc":[county_enc],"micro_enc":[micro_enc],"desc_enc":[desc_enc],"year":[2024]})'

if old in content:
    content = content.replace(old, new)
    print("Fixed DataFrame construction")
else:
    # Try other variants
    variants = [
        ('X = pd.DataFrame([{"county_enc":county_enc,"micro_enc":micro_enc,"desc_enc":desc_enc,"year":2024}])',
         'X = pd.DataFrame({"county_enc":[county_enc],"micro_enc":[micro_enc],"desc_enc":[desc_enc],"year":[2024]})'),
    ]
    fixed = False
    for o, n in variants:
        if o in content:
            content = content.replace(o, n)
            print("Fixed DataFrame construction (variant)")
            fixed = True
            break
    
    if not fixed:
        # Find the line manually
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'pd.DataFrame' in line and 'county_enc' in line:
                print(f"Found at line {i+1}: {line.strip()}")
                lines[i] = '    X = pd.DataFrame({"county_enc":[county_enc],"micro_enc":[micro_enc],"desc_enc":[desc_enc],"year":[2024]})'
                content = '\n'.join(lines)
                print("Fixed!")
                fixed = True
                break
        
        if not fixed:
            print("Could not find the line - searching for context...")
            idx = content.find('county_enc":county_enc')
            if idx > -1:
                print("Found at:", content[idx-20:idx+100])

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)

print("\nNow run:")
print("  git add app.py")
print("  git commit -m \"Fix DataFrame error\"")
print("  git push")
