"""
fix_gdrive.py
Updates PPR download to use Google Drive URL
Run from: C:\\Users\\WAFI\\irish-property-insights
"""

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# The file ID from the Google Drive link
FILE_ID = "1_swvDrOfx66RHsDWwaGpn6Cifx3NLktV"

old = '''# Try multiple URLs for PPR data
        urls = [
            "https://www.propertypriceregister.ie/website/npsra/ppr/npsra-ppr.nsf/Downloads/PPR-ALL.zip/$FILE/PPR-ALL.zip",
            "https://data.gov.ie/dataset/property-price-register/resource/98c5e0f6-79fc-4ff4-a50e-e32d2c469e5e",
        ]
        url = urls[0]'''

new = f'''# Download from Google Drive
        url = "https://drive.google.com/uc?export=download&id={FILE_ID}"'''

if old in content:
    content = content.replace(old, new)
    print("Updated download URL to Google Drive")
else:
    # Try finding any existing URL setting
    import re
    # Replace any url = "https://..." line in the download section
    content = re.sub(
        r'url = "https://[^"]*propertypriceregister[^"]*"',
        f'url = "https://drive.google.com/uc?export=download&id={FILE_ID}"',
        content
    )
    content = re.sub(
        r'urls = \[.*?\]\s*url = urls\[0\]',
        f'url = "https://drive.google.com/uc?export=download&id={FILE_ID}"',
        content, flags=re.DOTALL
    )
    print("Updated download URL to Google Drive (method 2)")

# Also make sure we handle Google Drive's virus scan warning for large files
old_req = '''resp = req_lib.get(url, timeout=300, stream=True, verify=False)
            with open("PPR-ALL.zip", "wb") as zf:
                for chunk in resp.iter_content(chunk_size=8192):
                    zf.write(chunk)'''

new_req = '''# Google Drive large file download (handles virus scan confirmation)
            session = req_lib.Session()
            resp = session.get(url, stream=True, verify=False, timeout=300)
            # Check for Google Drive confirmation page
            token = None
            for key, value in resp.cookies.items():
                if key.startswith("download_warning"):
                    token = value
                    break
            if token:
                params = {"confirm": token, "id": "''' + FILE_ID + '''"}
                resp = session.get("https://drive.google.com/uc?export=download", 
                                   params=params, stream=True, verify=False, timeout=300)
            with open("PPR-ALL.csv", "wb") as cf:
                for chunk in resp.iter_content(chunk_size=32768):
                    if chunk:
                        cf.write(chunk)
            csv_path = "PPR-ALL.csv"  # Already a CSV, no zip extraction needed'''

if old_req in content:
    content = content.replace(old_req, new_req)
    print("Updated download handler for Google Drive large files")

# Remove the zip extraction code since we're downloading CSV directly
old_zip = '''import zipfile
            with zipfile.ZipFile("PPR-ALL.zip", "r") as z:
                z.extractall(".")
            print("PPR CSV downloaded and extracted.")'''

new_zip = '''print("PPR CSV downloaded from Google Drive.")'''

content = content.replace(old_zip, new_zip)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)

print("\nDone! app.py updated to download from Google Drive.")
print("Now run:")
print("  git add app.py")
print("  git commit -m \"Use Google Drive for PPR download\"")
print("  git push")
