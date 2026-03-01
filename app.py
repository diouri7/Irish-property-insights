
import os
import datetime
import tempfile
import requests

import matplotlib
matplotlib.use("Agg")

import pandas as pd
import numpy as np

from flask import Flask, render_template_string, request, jsonify, send_file
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

# ─── CONFIG ─────────────────────────────────────────────
app = Flask(__name__)
TMP_DIR = tempfile.gettempdir()
DATA_PATH = os.environ.get("PPR_DATA_PATH", "PPR-ALL.csv")
PORT = int(os.environ.get("PORT", 5000))

# ─── RTB RENT DATA ──────────────────────────────────────
RTB_RENT = {
    "Dublin": 2230, "Cork": 1543, "Galway": 1380,
    "Kildare": 1713, "Meath": 1713, "Limerick": 1449,
}

# ─── LOAD DATA ──────────────────────────────────────────
def load_data():
    if os.path.exists(DATA_PATH):
        return pd.read_csv(DATA_PATH, encoding="latin-1", low_memory=False)

    cached = os.path.join(TMP_DIR, "PPR-ALL.csv")

    if os.path.exists(cached):
        return pd.read_csv(cached, encoding="latin-1", low_memory=False)

    url = "https://github.com/diouri7/Irish-property-insights/releases/download/v1.0/PPR-ALL.csv"
    r = requests.get(url)
    r.raise_for_status()

    with open(cached, "wb") as f:
        f.write(r.content)

    return pd.read_csv(cached, encoding="latin-1", low_memory=False)


df = None

def get_data():
    global df
    if df is None:
        print("Loading property data...")
        df = load_data()
        print("Columns found:", df.columns.tolist())

        # Normalize column names to lowercase with underscores
        df.columns = (
            df.columns.str.strip()
                      .str.lower()
                      .str.replace(" ", "_")
                      .str.replace(r"[^\w]", "_", regex=True)
        )
        print("Normalized columns:", df.columns.tolist())

        # Find the date column
        date_col = next((c for c in df.columns if "date" in c), None)
        if date_col:
            df["date"] = pd.to_datetime(df[date_col], errors="coerce")
        df["year"] = df["date"].dt.year

        # Find the price column
        price_col = next((c for c in df.columns if "price" in c), None)
        if price_col:
            if price_col != "price":
                df["price"] = df[price_col]
            df["price"] = (
                df["price"].astype(str)
                .str.replace(r"[€\$£,\s]", "", regex=True)
                .str.replace(r"[^\d.]", "", regex=True)
            )
            df["price"] = pd.to_numeric(df["price"], errors="coerce")
            print("Price sample after cleaning:", df["price"].dropna().head(5).tolist())

        # Find the county column
        county_col = next((c for c in df.columns if "county" in c), None)
        if county_col and county_col != "county":
            df["county"] = df[county_col].str.strip()
        else:
            df["county"] = df["county"].str.strip()

        print("Loaded:", len(df), "records")
        print("Sample counties:", df["county"].dropna().unique()[:10].tolist())
    return df


# ─── PDF REPORT GENERATOR ───────────────────────────────
def generate_report(county_name):
    data = get_data()
    cdf = data[data["county"] == county_name].copy()

    if len(cdf) < 50:
        return None

    yearly = (
        cdf.groupby("year")
        .agg(
            median_price=("price", "median"),
            avg_price=("price", "mean"),
            total_sales=("price", "count"),
        )
        .reset_index()
    )

    if yearly.empty:
        return None

    latest_year = yearly["year"].max()
    latest = yearly[yearly["year"] == latest_year].iloc[0]

    pdf_path = os.path.join(TMP_DIR, county_name + "_Property_Report_2025.pdf")

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"{county_name} Property Market Report", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(
        Paragraph(
            f"Latest Median Price: €{latest['median_price']:,.0f}",
            styles["Normal"],
        )
    )

    doc.build(elements)

    return pdf_path


# ─── SIMPLE HTML PAGE ───────────────────────────────────
HTML = """
<!DOCTYPE html>
<html>
<head><title>IrishPropertyInsights</title></head>
<body>
<h1>Generate County Report</h1>
<form method="post" action="/generate">
County: <input name="county"><br><br>
<button type="submit">Generate</button>
</form>
</body>
</html>
"""


# ─── ROUTES ─────────────────────────────────────────────
@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/generate", methods=["POST"])
def generate():
    county = request.form.get("county")

    try:
        pdf_path = generate_report(county)

        if pdf_path is None:
            return "Not enough data"

        filename = os.path.basename(pdf_path)
        return f"<a href='/download/{filename}'>Download Report</a>"

    except Exception as e:
        return str(e)


@app.route("/download/<filename>")
def download(filename):
    path = os.path.join(TMP_DIR, filename)
    if not os.path.exists(path):
        return "File not found", 404
    return send_file(path, as_attachment=True)


# ─── RUN ────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
