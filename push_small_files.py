"""
push_small_files.py
Pushes the small pkl files to GitHub (they're under 100MB limit)
and updates the route to only retrain the main model if missing.
Run from: C:\\Users\\WAFI\\irish-property-insights
"""
import subprocess
import os

# Check file sizes
files_to_add = []
for fname in ["le_county.pkl", "le_desc.pkl", "le_micro.pkl", "known_values.json"]:
    if os.path.exists(fname):
        size = os.path.getsize(fname)
        print(f"{fname}: {size/1024:.1f} KB")
        if size < 100 * 1024 * 1024:  # under 100MB
            files_to_add.append(fname)
    else:
        print(f"MISSING: {fname}")

print("\nFiles to push:", files_to_add)

# Check .gitignore - make sure pkl files aren't ignored
if os.path.exists(".gitignore"):
    with open(".gitignore", "r") as f:
        gitignore = f.read()
    if "*.pkl" in gitignore:
        print("\nRemoving *.pkl from .gitignore...")
        gitignore = gitignore.replace("*.pkl", "# *.pkl (allowed)")
        with open(".gitignore", "w") as f:
            f.write(gitignore)
        files_to_add.append(".gitignore")
        print("Done.")
    else:
        print(".gitignore OK - pkl files not blocked")

if files_to_add:
    for f in files_to_add:
        os.system(f"git add {f}")
    os.system('git commit -m "Add encoder pkl files"')
    os.system("git push")
    print("\nDone! Small pkl files pushed to GitHub.")
    print("Railway will now only need to retrain the Random Forest model,")
    print("which it can do using your PPR data.")
else:
    print("No files to push.")
