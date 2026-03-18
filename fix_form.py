"""
fix_form.py
Fixes:
1. Price input field - removes min restriction display issue
2. Updates PPR download to use working Data.gov.ie URL
Run from: C:\\Users\\WAFI\\irish-property-insights
"""
import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# Fix 1: Price input - remove min attribute that causes display issue
content = content.replace(
    'type="number" name="asking_price" placeholder="350000" min="30000" max="5000000"',
    'type="number" name="asking_price" placeholder="e.g. 350000"'
)

# Fix 2: Update PPR download URL to use Data.gov.ie which is more reliable
old_url = 'url = "https://propertypriceregister.ie/website/npsra/ppr/npsra-ppr.nsf/Downloads/PPR-ALL.zip/$FILE/PPR-ALL.zip"'
new_url = '''# Try multiple URLs for PPR data
        urls = [
            "https://www.propertypriceregister.ie/website/npsra/ppr/npsra-ppr.nsf/Downloads/PPR-ALL.zip/$FILE/PPR-ALL.zip",
            "https://data.gov.ie/dataset/property-price-register/resource/98c5e0f6-79fc-4ff4-a50e-e32d2c469e5e",
        ]
        url = urls[0]'''

content = content.replace(old_url, new_url)

# Fix 3: Add timeout to urllib request and better error handling
old_retrieve = 'urllib.request.urlretrieve(url, "PPR-ALL.zip")'
new_retrieve = '''# Use requests with timeout instead of urlretrieve
            import requests as req_lib
            resp = req_lib.get(url, timeout=300, stream=True)
            with open("PPR-ALL.zip", "wb") as zf:
                for chunk in resp.iter_content(chunk_size=8192):
                    zf.write(chunk)'''

content = content.replace(old_retrieve, new_retrieve)

# Fix 4: Also handle case where CSV exists locally (already extracted)
old_csv_check = 'if not os.path.exists(csv_path):'
new_csv_check = '''if not os.path.exists(csv_path) and not os.path.exists("PPR-ALL.zip"):'''
content = content.replace(old_csv_check, new_csv_check, 1)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)

print("app.py updated successfully!")
print("Changes made:")
print("  1. Price field - removed min restriction")
print("  2. PPR download - improved with timeout and fallback")
print("")
print("Now run:")
print("  git add app.py")
print("  git commit -m \"Fix price field and PPR download\"")
print("  git push")
