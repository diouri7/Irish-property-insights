with open("app.py", "r") as f:
    text = f.read()

old = 'print("Loading property data from:", DATA_PATH)\ndf = pd.read_csv(DATA_PATH, encoding="latin-1", low_memory=False)'

new = '''import urllib.request

def load_data():
    if os.path.exists(DATA_PATH):
        print("Loading from local file:", DATA_PATH)
        return pd.read_csv(DATA_PATH, encoding="latin-1", low_memory=False)
    cached = os.path.join(TMP_DIR, "PPR-ALL.csv")
    if os.path.exists(cached):
        print("Loading from cache:", cached)
        return pd.read_csv(cached, encoding="latin-1", low_memory=False)
    print("Downloading PPR data...")
    try:
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve("https://www.propertypriceregister.ie/website/npsra/pprweb.nsf/PPR-ALL.csv", cached)
        print("Downloaded to:", cached)
        return pd.read_csv(cached, encoding="latin-1", low_memory=False)
    except Exception as e:
        print("Download failed:", e)
        raise

print("Loading property data...")
df = load_data()'''

if old in text:
    text = text.replace(old, new)
    with open("app.py", "w") as f:
        f.write(text)
    print("SUCCESS")
else:
    print("NOT FOUND")