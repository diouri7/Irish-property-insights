"""
push_model.py
Renames compressed model and updates app.py to load it
Run from: C:\\Users\\WAFI\\irish-property-insights
"""
import os
import shutil

# Use the level 9 compressed version (68.7MB)
src = "model_compressed_9.pkl"
dst = "deal_scorer_model.pkl"

print(f"Replacing {dst} with compressed version ({os.path.getsize(src)/1024/1024:.1f} MB)...")
shutil.copy2(src, dst)
print(f"New size: {os.path.getsize(dst)/1024/1024:.1f} MB")

# Remove the other compressed files
for f in ["model_compressed_3.pkl", "model_compressed_6.pkl", "model_compressed_9.pkl"]:
    if os.path.exists(f):
        os.remove(f)
        print(f"Removed {f}")

# Check .gitignore - remove *.pkl if it's there
if os.path.exists(".gitignore"):
    with open(".gitignore", "r") as f:
        gitignore = f.read()
    if "*.pkl" in gitignore and "# *.pkl" not in gitignore:
        gitignore = gitignore.replace("*.pkl", "# *.pkl")
        with open(".gitignore", "w") as f:
            f.write(gitignore)
        print("Removed *.pkl from .gitignore")

# Git add and push
print("\nAdding files to git...")
os.system("git add deal_scorer_model.pkl le_county.pkl le_desc.pkl le_micro.pkl known_values.json")
os.system('git commit -m "Add compressed model and encoder files"')
os.system("git push")

print("\nDone! Model pushed to GitHub.")
print("Railway will now load it directly - no download needed!")
