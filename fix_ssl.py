"""
fix_ssl.py
Fixes the SSL certificate error when downloading PPR CSV on Railway
Run from: C:\\Users\\WAFI\\irish-property-insights
"""

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

old = '''import requests as req_lib
            resp = req_lib.get(url, timeout=300, stream=True)
            with open("PPR-ALL.zip", "wb") as zf:
                for chunk in resp.iter_content(chunk_size=8192):
                    zf.write(chunk)'''

new = '''import requests as req_lib
            import ssl
            resp = req_lib.get(url, timeout=300, stream=True, verify=False)
            with open("PPR-ALL.zip", "wb") as zf:
                for chunk in resp.iter_content(chunk_size=8192):
                    zf.write(chunk)'''

if old in content:
    content = content.replace(old, new)
    print("Fixed SSL verification issue")
else:
    # Try simpler approach - find any requests.get in the download section
    old2 = 'resp = req_lib.get(url, timeout=300, stream=True)'
    new2 = 'resp = req_lib.get(url, timeout=300, stream=True, verify=False)'
    if old2 in content:
        content = content.replace(old2, new2)
        print("Fixed SSL verification issue (method 2)")
    else:
        print("Pattern not found - checking what's in app.py...")
        idx = content.find('req_lib')
        if idx > -1:
            print("Found req_lib at:", content[idx-50:idx+100])
        else:
            print("req_lib not found - the download code may look different")

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)

print("\nNow run:")
print("  git add app.py")
print("  git commit -m \"Fix SSL for PPR download\"")
print("  git push")
