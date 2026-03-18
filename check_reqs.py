required = [
    "flask",
    "pandas",
    "numpy",
    "scikit-learn",
    "joblib",
    "gunicorn",
]

with open("requirements.txt", "r") as f:
    current = f.read()

print("Current requirements.txt:")
print(current)
print("---")

missing = []
for pkg in required:
    if pkg.lower() not in current.lower():
        missing.append(pkg)

if missing:
    print("MISSING packages:", missing)
    # Add them
    with open("requirements.txt", "a") as f:
        for pkg in missing:
            f.write(f"\n{pkg}")
    print("Added missing packages to requirements.txt")
else:
    print("All required packages present - requirements.txt is fine")
