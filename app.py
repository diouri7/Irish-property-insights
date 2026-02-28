import os
import sys
import re
import datetime
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import numpy as np

from flask import Flask, render_template_string, request, jsonify, send_file
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.lib.enums import TA_CENTER

# ─── CONFIG ───────────────────────────────────────────────────
app = Flask(__name__)
TMP_DIR = tempfile.gettempdir()
DATA_PATH = os.environ.get("PPR_DATA_PATH", "PPR-ALL.csv")
PORT = int(os.environ.get("PORT", 5000))

# ─── RTB RENT DATA (Q2 2025 — official RTB/ESRI Rent Index) ──
RTB_RENT = {
    "Dublin": 2230, "Cork": 1543, "Galway": 1380, "Kildare": 1713,
    "Meath": 1713, "Limerick": 1449, "Wexford": 1253, "Wicklow": 1713,
    "Waterford": 1174, "Kerry": 1289, "Louth": 1557, "Tipperary": 1183,
    "Clare": 1277, "Kilkenny": 1302, "Laois": 1351, "Offaly": 1159,
    "Roscommon": 1095, "Sligo": 1159, "Carlow": 1274, "Mayo": 1159,
    "Donegal": 1021, "Cavan": 1134, "Monaghan": 1166, "Longford": 1073,
    "Leitrim": 1112, "Westmeath": 1258,
}

# ─── LOAD & CLEAN PPR DATA ────────────────────────────────────
import urllib.request

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
df = load_data()
df.columns = df.columns.str.strip()
df.columns = [
    "date", "address", "county", "eircode", "price",
    "not_full_market", "vat_exclusive", "description", "size"
]
df["price"] = df["price"].str.replace("\x80", "").str.replace(",", "").astype(float)
df["date"] = pd.to_datetime(df["date"], dayfirst=True)
df["year"] = df["date"].dt.year
df = df[df["not_full_market"] == "No"]
df = df[df["price"].between(20000, 3000000)]
df = df.dropna(subset=["price"])


def extract_area(row):
    if pd.notna(row["eircode"]) and str(row["eircode"]).strip() != "":
        return str(row["eircode"]).strip()[:3].upper()
    address = str(row["address"]).upper()
    m = re.search(r"DUBLIN\s*(\d+)", address)
    if m:
        return "D" + m.group(1)
    return str(row["county"]).strip()


df["area_code"] = df.apply(extract_area, axis=1)
print("Loaded:", len(df), "records |", df["area_code"].nunique(), "areas")

# ─── NATIONAL METRICS ─────────────────────────────────────────
latest_date = df["date"].max()
twelve_months_ago = latest_date - pd.DateOffset(months=12)
recent = df[df["date"] >= twelve_months_ago]
county_prices = recent.groupby("county")["price"].median().reset_index()
county_prices.columns = ["county", "median_sale_price"]
rent_df = pd.DataFrame([{"county": k, "annual_rent": v * 12} for k, v in RTB_RENT.items()])
cy = county_prices.merge(rent_df, on="county", how="inner")
cy["gross_yield"] = (cy["annual_rent"] / cy["median_sale_price"]) * 100
NATIONAL_MEDIAN_YIELD = round(cy["gross_yield"].median(), 2)

all_vols = []
for c in df["county"].unique():
    c_yearly = df[df["county"] == c].groupby("year")["price"].median().pct_change().dropna() * 100
    if len(c_yearly) >= 3:
        all_vols.append(c_yearly.std())
VOL_THRESHOLD = round(pd.Series(all_vols).median(), 1)
print("National median yield:", NATIONAL_MEDIAN_YIELD, "% | Vol threshold:", VOL_THRESHOLD, "%")


# ─── AREA METRICS WITH YIELD ──────────────────────────────────
def build_county_metrics(county_name):
    cdf = df[df["county"] == county_name].copy()
    if len(cdf) < 50:
        return None

    ld = cdf["date"].max()
    t12 = ld - pd.DateOffset(months=12)
    t5y = ld - pd.DateOffset(years=5)
    t3y = ld - pd.DateOffset(years=3)

    c12 = cdf[cdf["date"] >= t12]
    c_med = c12["price"].median()
    c_prev = cdf[(cdf["date"] >= t12 - pd.DateOffset(months=12)) & (cdf["date"] < t12)]["price"].median()
    c_yoy = ((c_med - c_prev) / c_prev) * 100 if c_prev else 0

    c_yearly = cdf[cdf["date"] >= t5y].groupby("year")["price"].median().reset_index().sort_values("year")
    if len(c_yearly) >= 2:
        s, e = c_yearly.iloc[0]["price"], c_yearly.iloc[-1]["price"]
        yrs = c_yearly.iloc[-1]["year"] - c_yearly.iloc[0]["year"]
        c_cagr = ((e / s) ** (1 / yrs) - 1) * 100 if yrs > 0 else 0
    else:
        c_cagr = 0

    c_rent = RTB_RENT.get(county_name, 1362)
    c_yield = (c_rent * 12 / c_med) * 100 if c_med > 0 else 0

    results = []
    for area in cdf["area_code"].unique():
        adf = cdf[cdf["area_code"] == area]
        a12 = adf[adf["date"] >= t12]
        a5y = adf[adf["date"] >= t5y]
        a3y = adf[adf["date"] >= t3y]
        if len(a12) < 10:
            continue

        med = a12["price"].median()
        sales = len(a12)
        s3 = len(a3y) / 3

        prev = adf[(adf["date"] >= t12 - pd.DateOffset(months=12)) & (adf["date"] < t12)]
        yoy = ((med - prev["price"].median()) / prev["price"].median()) * 100 if len(prev) >= 5 else None

        ay = a5y.groupby("year")["price"].median().reset_index().sort_values("year")
        if len(ay) >= 2:
            s0, e0 = ay.iloc[0]["price"], ay.iloc[-1]["price"]
            yr = ay.iloc[-1]["year"] - ay.iloc[0]["year"]
            cagr = ((e0 / s0) ** (1 / yr) - 1) * 100 if yr > 0 and s0 > 0 else None
        else:
            cagr = None

        a3yy = a3y.groupby("year")["price"].median().reset_index().sort_values("year")
        vol = round(a3yy["price"].pct_change().dropna().std() * 100, 1) if len(a3yy) >= 3 else None

        rel = ((med - c_med) / c_med) * 100
        damp = 0.4
        pr = med / c_med if c_med > 0 else 1
        est_rent = round(c_rent * (1 + (pr - 1) * damp))
        g_yield = round((est_rent * 12 / med) * 100, 2) if med > 0 else None

        # Signal logic
        sig = "INSUFFICIENT DATA"
        if yoy is not None and cagr is not None:
            hv = vol is not None and vol > VOL_THRESHOLD
            sa = sales > s3
            ya = g_yield is not None and g_yield > c_yield
            if yoy > c_yoy and cagr > c_cagr and sa and not hv and ya:
                sig = "STRONG BUY"
            elif yoy < -5 and sales < s3 * 0.8:
                sig = "HIGH CAUTION"
            elif yoy < 0 or (hv and yoy < c_yoy * 0.5):
                sig = "CAUTION"
            elif (yoy >= c_yoy and not hv) or (yoy > 0 and ya and cagr > c_cagr * 0.8):
                sig = "BUY"
            else:
                sig = "HOLD"

        results.append({
            "area_code": area, "median_12m": round(med), "sales_12m": sales,
            "yoy_growth": round(yoy, 2) if yoy is not None else None,
            "cagr_5y": round(cagr, 2) if cagr is not None else None,
            "volatility_3y": vol, "sales_3y_avg": round(s3, 1),
            "relative_to_county": round(rel, 1),
            "est_monthly_rent": est_rent, "gross_yield": g_yield,
            "signal": sig,
            "county_yoy": round(c_yoy, 2), "county_cagr": round(c_cagr, 2),
            "county_median": round(c_med), "county_monthly_rent": c_rent,
            "county_gross_yield": round(c_yield, 2),
        })

    rdf = pd.DataFrame(results)
    so = {"STRONG BUY": 0, "BUY": 1, "HOLD": 2, "CAUTION": 3, "HIGH CAUTION": 4, "INSUFFICIENT DATA": 5}
    rdf["sr"] = rdf["signal"].map(so)
    rdf = rdf.sort_values(["sr", "sales_12m"], ascending=[True, False]).drop("sr", axis=1)
    return rdf


def get_area_table(county_name):
    m = build_county_metrics(county_name)
    if m is None or len(m) == 0:
        return pd.DataFrame()
    return m[m["sales_12m"] >= 20].head(10)


# ─── PDF REPORT GENERATOR ─────────────────────────────────────
def generate_report(county_name):
    cdf = df[df["county"] == county_name].copy()
    if len(cdf) < 50:
        return None

    yearly = cdf.groupby("year").agg(
        median_price=("price", "median"),
        avg_price=("price", "mean"),
        total_sales=("price", "count"),
    ).reset_index()
    yearly = yearly[yearly["year"] < 2026]

    latest = yearly[yearly["year"] == yearly["year"].max()].iloc[0]
    oldest = yearly[yearly["year"] == yearly["year"].min()].iloc[0]
    prev = yearly[yearly["year"] == (yearly["year"].max() - 1)]
    yoy = 0
    if len(prev) > 0:
        yoy = ((latest["median_price"] - prev.iloc[0]["median_price"]) / prev.iloc[0]["median_price"]) * 100
    yc = latest["year"] - oldest["year"]
    tg = ((latest["median_price"] - oldest["median_price"]) / oldest["median_price"]) * 100
    cagr10 = ((latest["median_price"] / oldest["median_price"]) ** (1 / yc) - 1) * 100 if yc > 0 else 0

    f5 = yearly[yearly["year"] >= (latest["year"] - 5)]
    cagr5 = ((f5.iloc[-1]["median_price"] / f5.iloc[0]["median_price"]) ** (1 / 5) - 1) * 100 if len(f5) >= 2 else cagr10

    if yoy > 7:
        sig = "STRONG GROWTH"
    elif yoy > 3:
        sig = "STABLE GROWTH"
    elif yoy > 0:
        sig = "SLOW GROWTH"
    else:
        sig = "DECLINING"

    c_rent = RTB_RENT.get(county_name, 1362)
    c_yld = (c_rent * 12 / latest["median_price"]) * 100 if latest["median_price"] > 0 else 0

    # Charts
    pd2 = yearly.copy()
    pd2["growth"] = pd2["median_price"].pct_change() * 100
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(county_name + " Property Market Report", fontsize=16, fontweight="bold")

    ax1 = axes[0, 0]
    ax1.plot(pd2["year"], pd2["median_price"], color="#2E86AB", linewidth=2.5, marker="o", markersize=5)
    ax1.fill_between(pd2["year"], pd2["median_price"], alpha=0.1, color="#2E86AB")
    ax1.set_title("Median Sale Price", fontweight="bold")
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: "EUR {:,.0f}".format(x)))
    ax1.grid(True, alpha=0.3)

    ax2 = axes[0, 1]
    ax2.bar(pd2["year"], pd2["total_sales"], color="#A23B72", alpha=0.8)
    ax2.set_title("Annual Sales Volume", fontweight="bold")
    ax2.grid(True, alpha=0.3, axis="y")

    ax3 = axes[1, 0]
    cc = ["#2ECC71" if x >= 0 else "#E74C3C" for x in pd2["growth"].fillna(0)]
    ax3.bar(pd2["year"], pd2["growth"].fillna(0), color=cc, alpha=0.8)
    ax3.set_title("Year-on-Year Price Growth (%)", fontweight="bold")
    ax3.axhline(y=0, color="black", linewidth=0.8)
    ax3.grid(True, alpha=0.3, axis="y")

    ax4 = axes[1, 1]
    ax4.plot(pd2["year"], pd2["median_price"], color="#2E86AB", linewidth=2.5, label="Median", marker="o", markersize=4)
    ax4.plot(pd2["year"], pd2["avg_price"], color="#E74C3C", linewidth=2.5, label="Average", marker="s", markersize=4)
    ax4.set_title("Average vs Median Price", fontweight="bold")
    ax4.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: "EUR {:,.0f}".format(x)))
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    chart_path = os.path.join(TMP_DIR, county_name + "_chart.png")
    plt.savefig(chart_path, bbox_inches="tight", dpi=150)
    plt.close()

    # PDF
    pdf_path = os.path.join(TMP_DIR, county_name + "_Property_Report_2025.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    els = []

    t1 = ParagraphStyle("T1", parent=styles["Title"], fontSize=24, textColor=colors.HexColor("#2E86AB"), spaceAfter=6, alignment=TA_CENTER)
    t2 = ParagraphStyle("T2", parent=styles["Normal"], fontSize=12, textColor=colors.grey, spaceAfter=20, alignment=TA_CENTER)
    t3 = ParagraphStyle("T3", parent=styles["Heading2"], fontSize=14, textColor=colors.HexColor("#2E86AB"), spaceBefore=16, spaceAfter=8)
    t4 = ParagraphStyle("T4", parent=styles["Normal"], fontSize=10, spaceAfter=8, leading=16)
    t5 = ParagraphStyle("T5", parent=styles["Normal"], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    t6 = ParagraphStyle("T6", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#555555"), spaceAfter=4, leading=12)

    els.append(Paragraph(county_name + " Property Market Report", t1))
    els.append(Paragraph("Comprehensive Analysis 2010-2025 | Generated " + datetime.date.today().strftime("%B %d, %Y"), t2))
    els.append(Table([[""]], colWidths=[17*cm], style=TableStyle([("LINEABOVE", (0,0), (-1,0), 2, colors.HexColor("#2E86AB"))])))
    els.append(Spacer(1, 12))

    els.append(Paragraph("Key Market Metrics", t3))
    md = [
        ["Metric", "Value", "Notes"],
        ["Current Median Price", "EUR {:,.0f}".format(latest["median_price"]), "Last 12 months"],
        ["Average Price", "EUR {:,.0f}".format(latest["avg_price"]), "Last 12 months"],
        ["Year-on-Year Growth", "{:.1f}%".format(yoy), "vs previous 12 months"],
        ["5-Year CAGR", "{:.1f}%".format(cagr5), "Compound annual 2020-2025"],
        ["Since-2010 CAGR", "{:.1f}%".format(cagr10), "Compound annual 2010-2025"],
        ["Avg Monthly Rent", "EUR {:,.0f}".format(c_rent), "RTB Q2 2025 (new tenancies)"],
        ["Gross Rental Yield", "{:.2f}%".format(c_yld), "(Annual Rent / Median Price)"],
        ["Total Sales", "{:,.0f}".format(latest["total_sales"]), str(int(latest["year"]))],
        ["Market Signal", sig, "Based on YoY growth"],
    ]
    mt = Table(md, colWidths=[5.5*cm, 5*cm, 6.5*cm])
    mt.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#2E86AB")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#F5F5F5"), colors.white]),
        ("GRID", (0,0), (-1,-1), 0.5, colors.lightgrey),
        ("PADDING", (0,0), (-1,-1), 7),
        ("TEXTCOLOR", (2,1), (-1,-1), colors.HexColor("#888888")),
        ("FONTNAME", (2,1), (-1,-1), "Helvetica-Oblique"),
    ]))
    els.append(mt)
    els.append(Spacer(1, 16))

    els.append(Paragraph("Market Trends", t3))
    els.append(Image(chart_path, width=17*cm, height=11*cm))
    els.append(Spacer(1, 16))

    # Micro-area table
    areas = get_area_table(county_name)
    if len(areas) > 0:
        ca_yoy = areas.iloc[0]["county_yoy"]
        ca_cagr = areas.iloc[0]["county_cagr"]
        ca_med = areas.iloc[0]["county_median"]
        ca_rent = areas.iloc[0]["county_monthly_rent"]
        ca_yld = areas.iloc[0]["county_gross_yield"]

        els.append(Paragraph("Micro-Area Intelligence", t3))
        els.append(Paragraph(
            "County baseline — Median: EUR {:,.0f} | YoY: {:.1f}% | 5Y CAGR: {:.1f}% | "
            "Rent: EUR {:,.0f}/mo | Yield: {:.2f}%. "
            "Sorted by investment opportunity. Signals incorporate growth, risk, and return.".format(
                ca_med, ca_yoy, ca_cagr, ca_rent, ca_yld), t4))

        scm = {"STRONG BUY": "#27AE60", "BUY": "#2ECC71", "HOLD": "#F39C12",
               "CAUTION": "#E74C3C", "HIGH CAUTION": "#C0392B", "INSUFFICIENT DATA": "#BDC3C7"}

        atd = [["Area", "Median", "YoY%", "Rent/mo", "Yield%", "Vol(3Y)", "Signal"]]
        for _, row in areas.iterrows():
            vs = "{:.1f}".format(row["volatility_3y"]) if pd.notna(row["volatility_3y"]) else "N/A"
            ys = "{:.2f}%".format(row["gross_yield"]) if pd.notna(row["gross_yield"]) else "N/A"
            s = row["signal"]
            if row["sales_12m"] < 100 and s in ["STRONG BUY", "BUY"]:
                s = s + "*"
            atd.append([
                str(row["area_code"]),
                "EUR {:,.0f}".format(row["median_12m"]),
                "{:.1f}%".format(row["yoy_growth"]) if pd.notna(row["yoy_growth"]) else "N/A",
                "EUR {:,.0f}".format(row["est_monthly_rent"]),
                ys, vs, s
            ])

        at = Table(atd, colWidths=[2.2*cm, 3*cm, 1.6*cm, 2.5*cm, 1.8*cm, 1.6*cm, 4.3*cm])
        ts = [
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#2E86AB")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 8),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#F5F5F5"), colors.white]),
            ("GRID", (0,0), (-1,-1), 0.5, colors.lightgrey),
            ("PADDING", (0,0), (-1,-1), 5),
        ]
        for i, row in enumerate(areas.itertuples(), start=1):
            sc = colors.HexColor(scm.get(row.signal, "#95A5A6"))
            ts.append(("TEXTCOLOR", (6, i), (6, i), sc))
            ts.append(("FONTNAME", (6, i), (6, i), "Helvetica-Bold"))
            if pd.notna(row.gross_yield):
                yc = "#27AE60" if row.gross_yield > row.county_gross_yield else "#E74C3C"
                ts.append(("TEXTCOLOR", (4, i), (4, i), colors.HexColor(yc)))
        at.setStyle(TableStyle(ts))
        els.append(at)
        els.append(Spacer(1, 10))

        els.append(Paragraph("Signal Methodology (Growth + Risk + Return):", t6))
        els.append(Paragraph("STRONG BUY: YoY > County YoY AND CAGR > County CAGR AND Sales rising AND Vol(3Y) below threshold AND Yield above county yield", t6))
        els.append(Paragraph("BUY: YoY >= County YoY with low volatility, OR positive growth with above-county yield and strong CAGR", t6))
        els.append(Paragraph("HOLD: Mixed signals — positive growth but below county benchmarks on multiple dimensions", t6))
        els.append(Paragraph("CAUTION: Negative YoY OR high volatility with weak growth", t6))
        els.append(Paragraph("HIGH CAUTION: YoY < -5% AND declining sales volume", t6))
        els.append(Paragraph("Vol(3Y) threshold: {:.1f}%. Yield%: Est. gross rental yield. Rent from RTB Q2 2025, adjusted by area price differential (dampening: 0.4). * = fewer than 100 transactions.".format(VOL_THRESHOLD), t6))
        els.append(Spacer(1, 10))

    els.append(Paragraph("Market Analysis", t3))
    els.append(Paragraph(
        county_name + " property prices have grown {:.1f}%".format(tg) +
        " since 2010 (CAGR: {:.1f}%).".format(cagr10) +
        " Over the past 5 years, the compound annual growth rate was {:.1f}%.".format(cagr5) +
        " The current median price stands at EUR {:,.0f}".format(latest["median_price"]) +
        " with {:,.0f} transactions recorded.".format(latest["total_sales"]), t4))
    els.append(Paragraph(
        "Based on RTB Q2 2025 data, the average monthly rent for new tenancies in " +
        county_name + " is EUR {:,.0f}".format(c_rent) +
        ", giving a county-level gross rental yield of {:.2f}%.".format(c_yld) +
        " The national median gross yield across all counties is {:.2f}%.".format(NATIONAL_MEDIAN_YIELD), t4))

    els.append(Spacer(1, 20))
    els.append(Paragraph(
        "Disclaimer: Based on Irish Property Price Register (sale prices) and RTB/ESRI Rent Index Q2 2025 (rental data). "
        "Yield estimates are gross and do not account for management costs, void periods, taxes, or maintenance. "
        "For informational purposes only. Not financial advice.", t5))

    doc.build(els)
    return pdf_path


# ─── LANDING PAGE HTML ─────────────────────────────────────────
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IrishPropertyInsights — Investment Intelligence Reports</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'DM Sans',sans-serif;background:#FAFAF8;color:#1a1a2e;-webkit-font-smoothing:antialiased;}
nav{background:#0B1D26;padding:18px 40px;display:flex;justify-content:space-between;align-items:center;}
nav .logo{font-family:'Playfair Display',serif;color:#fff;font-size:22px;letter-spacing:-0.5px;}
nav .logo span{color:#C9A84C;}
nav .tag{color:rgba(255,255,255,0.5);font-size:13px;letter-spacing:0.5px;text-transform:uppercase;}
.hero{background:linear-gradient(160deg,#0B1D26 0%,#142E3C 50%,#1A3A4A 100%);color:#fff;padding:100px 40px 80px;text-align:center;position:relative;overflow:hidden;}
.hero::before{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:radial-gradient(circle at 30% 40%,rgba(201,168,76,0.06) 0%,transparent 50%);pointer-events:none;}
.hero h1{font-family:'Playfair Display',serif;font-size:48px;line-height:1.15;margin-bottom:20px;letter-spacing:-1px;max-width:700px;margin-left:auto;margin-right:auto;}
.hero h1 em{font-style:normal;color:#C9A84C;}
.hero p{font-size:17px;opacity:0.7;max-width:560px;margin:0 auto 48px;line-height:1.7;}
.order-box{background:#fff;border-radius:16px;padding:44px 40px;max-width:440px;margin:0 auto;box-shadow:0 30px 80px rgba(0,0,0,0.35);border:1px solid rgba(255,255,255,0.08);position:relative;z-index:2;}
.order-box h2{font-family:'Playfair Display',serif;font-size:21px;margin-bottom:6px;color:#0B1D26;text-align:center;}
.order-box .sub{font-size:13px;color:#888;text-align:center;margin-bottom:28px;}
.order-box select,.order-box input{width:100%;padding:14px 16px;border:1.5px solid #e0e0e0;border-radius:10px;font-size:15px;font-family:'DM Sans',sans-serif;margin-bottom:14px;outline:none;transition:border 0.2s;background:#FAFAF8;color:#1a1a2e;}
.order-box select:focus,.order-box input:focus{border-color:#C9A84C;}
.btn{width:100%;padding:17px;background:#C9A84C;color:#0B1D26;border:none;border-radius:10px;font-size:16px;font-weight:700;cursor:pointer;transition:all 0.2s;font-family:'DM Sans',sans-serif;letter-spacing:0.3px;}
.btn:hover{background:#B8963F;transform:translateY(-1px);box-shadow:0 4px 20px rgba(201,168,76,0.3);}
.btn:disabled{background:#ccc;cursor:not-allowed;transform:none;box-shadow:none;}
.trust{display:flex;justify-content:center;gap:20px;margin-top:16px;font-size:12px;color:#999;}
.trust span::before{content:'\\2713';margin-right:4px;color:#C9A84C;}
.status{padding:16px;border-radius:10px;margin-top:16px;text-align:center;display:none;font-size:14px;}
.status.loading{background:#FFF8E1;color:#8D6E00;display:block;}
.status.success{background:#E8F5E9;color:#2E7D32;display:block;}
.status.success a{color:#1B5E20;font-weight:700;}
.status.error{background:#FFEBEE;color:#C62828;display:block;}
.features{padding:90px 40px;background:#fff;}
.features h2{font-family:'Playfair Display',serif;font-size:32px;text-align:center;margin-bottom:12px;color:#0B1D26;}
.features .intro{text-align:center;color:#777;margin-bottom:56px;font-size:15px;}
.features-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:28px;max-width:920px;margin:0 auto;}
.fc{padding:32px 28px;border-radius:14px;background:#FAFAF8;border:1px solid #EDEDEB;transition:all 0.25s;}
.fc:hover{border-color:#C9A84C;transform:translateY(-3px);box-shadow:0 12px 36px rgba(0,0,0,0.06);}
.fc .icon{font-size:28px;margin-bottom:14px;width:52px;height:52px;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#0B1D26,#1A3A4A);border-radius:12px;color:#C9A84C;}
.fc h3{font-size:15px;margin-bottom:8px;font-weight:700;color:#0B1D26;}
.fc p{font-size:13px;color:#777;line-height:1.65;}
.metrics{padding:80px 40px;background:#0B1D26;color:#fff;text-align:center;}
.metrics h2{font-family:'Playfair Display',serif;font-size:32px;margin-bottom:8px;}
.metrics .intro{color:rgba(255,255,255,0.5);margin-bottom:48px;font-size:14px;}
.metrics-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;max-width:900px;margin:0 auto;}
.mc{background:rgba(255,255,255,0.04);padding:28px 20px;border-radius:14px;border:1px solid rgba(255,255,255,0.08);text-align:left;}
.mc .label{font-size:11px;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;}
.mc .value{font-family:'Playfair Display',serif;font-size:26px;color:#C9A84C;}
.mc .sub{font-size:12px;color:rgba(255,255,255,0.35);margin-top:6px;}
.yield-section{padding:80px 40px;background:#FAFAF8;text-align:center;}
.yield-section h2{font-family:'Playfair Display',serif;font-size:30px;margin-bottom:12px;color:#0B1D26;}
.yield-section .intro{color:#777;margin-bottom:40px;font-size:14px;}
.yield-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;max-width:700px;margin:0 auto;}
.yc{background:#fff;padding:28px 24px;border-radius:14px;border-left:4px solid #C9A84C;text-align:left;}
.yc .county{font-size:13px;color:#888;margin-bottom:4px;}
.yc .yield-val{font-family:'Playfair Display',serif;font-size:24px;color:#0B1D26;}
.yc .detail{font-size:11px;color:#aaa;margin-top:4px;}
footer{background:#0B1D26;color:rgba(255,255,255,0.3);text-align:center;padding:36px;font-size:12px;border-top:1px solid rgba(255,255,255,0.06);}
@media(max-width:768px){
.hero h1{font-size:32px;}
.features-grid,.metrics-grid{grid-template-columns:1fr;}
.yield-grid{grid-template-columns:1fr;}
nav{padding:14px 20px;}
.hero{padding:60px 20px 50px;}
.order-box{padding:32px 24px;margin:0 16px;}
.features,.metrics,.yield-section{padding:60px 20px;}
}
</style>
</head>
<body>
<nav>
<div class="logo">Irish<span>Property</span>Insights</div>
<div class="tag">Investment Intelligence</div>
</nav>
<div class="hero">
<h1>Identify <em>High-Yield, Low-Risk</em> Areas Before You Invest</h1>
<p>Data-driven property investment reports for every Irish county. Powered by 15 years of real sales data and official RTB rental figures.</p>
<div class="order-box">
<h2>Get Your Investment Report</h2>
<div class="sub">Instant PDF delivery &mdash; professional intelligence for &euro;19.99</div>
<select id="county">
<option value="">Select a County...</option>
<option>Dublin</option><option>Cork</option><option>Galway</option><option>Kildare</option>
<option>Meath</option><option>Limerick</option><option>Wexford</option><option>Wicklow</option>
<option>Waterford</option><option>Kerry</option><option>Louth</option><option>Tipperary</option>
<option>Clare</option><option>Kilkenny</option><option>Laois</option><option>Offaly</option>
<option>Roscommon</option><option>Sligo</option><option>Carlow</option><option>Mayo</option>
<option>Donegal</option><option>Cavan</option><option>Monaghan</option><option>Longford</option>
<option>Leitrim</option><option>Westmeath</option>
</select>
<input type="email" id="email" placeholder="Your email address">
<button class="btn" id="orderBtn" onclick="orderReport()">Get Report &mdash; &euro;19.99</button>
<div class="trust">
<span>Real PPR data</span>
<span>RTB rental yields</span>
<span>Instant PDF</span>
</div>
<div class="status" id="status"></div>
</div>
</div>
<div class="features">
<h2>What You Get</h2>
<div class="intro">Every report includes institutional-grade analysis you won't find on free property portals.</div>
<div class="features-grid">
<div class="fc"><div class="icon">&#x1F4C8;</div><h3>15-Year Price Trends</h3><p>Median and average prices from 2010 to 2025 with year-on-year growth charts.</p></div>
<div class="fc"><div class="icon">&#x1F3AF;</div><h3>Micro-Area Scoring</h3><p>Top 10 sub-markets ranked by investment opportunity using county-relative signals.</p></div>
<div class="fc"><div class="icon">&#x1F4B0;</div><h3>Rental Yield Estimates</h3><p>Gross yield per area using official RTB rent data — see where cash flow is strongest.</p></div>
<div class="fc"><div class="icon">&#x26A0;</div><h3>Volatility Risk</h3><p>3-year price volatility for every area — know your downside before you commit.</p></div>
<div class="fc"><div class="icon">&#x1F4CA;</div><h3>Growth vs Return</h3><p>5-year CAGR alongside yield — balance capital growth and rental income.</p></div>
<div class="fc"><div class="icon">&#x2705;</div><h3>Transparent Logic</h3><p>Full methodology disclosed. Signal definitions, data sources, confidence flags — no black boxes.</p></div>
</div>
</div>
<div class="metrics">
<h2>Sample Dublin Intelligence</h2>
<div class="intro">Preview of the data depth inside every report</div>
<div class="metrics-grid">
<div class="mc"><div class="label">Median Price</div><div class="value">&euro;475,000</div><div class="sub">Dublin county, last 12 months</div></div>
<div class="mc"><div class="label">Gross Yield</div><div class="value">5.63%</div><div class="sub">Based on RTB Q2 2025 rent</div></div>
<div class="mc"><div class="label">5-Year CAGR</div><div class="value">5.7%</div><div class="sub">Compound annual growth</div></div>
<div class="mc"><div class="label">Market Signal</div><div class="value" style="color:#2ECC71;">STABLE</div><div class="sub">YoY: +5.6%</div></div>
</div>
</div>
<div class="yield-section">
<h2>Highest Yield Counties</h2>
<div class="intro">National median yield: 5.41% &mdash; these counties offer the strongest gross returns</div>
<div class="yield-grid">
<div class="yc"><div class="county">Longford</div><div class="yield-val">6.92%</div><div class="detail">Median: &euro;186k | Rent: &euro;1,073/mo</div></div>
<div class="yc"><div class="county">Donegal</div><div class="yield-val">6.45%</div><div class="detail">Median: &euro;190k | Rent: &euro;1,021/mo</div></div>
<div class="yc"><div class="county">Leitrim</div><div class="yield-val">6.43%</div><div class="detail">Median: &euro;208k | Rent: &euro;1,112/mo</div></div>
</div>
</div>
<footer>
<p>&copy; 2025 IrishPropertyInsights | Sale data: Property Price Register | Rental data: RTB/ESRI Rent Index Q2 2025 | For informational purposes only</p>
</footer>
<script>
function orderReport(){
var county=document.getElementById("county").value;
var email=document.getElementById("email").value;
if(!county){alert("Please select a county");return;}
if(!email||!email.includes("@")){alert("Please enter a valid email");return;}
var btn=document.getElementById("orderBtn");
var status=document.getElementById("status");
btn.disabled=true;btn.textContent="Generating...";
status.className="status loading";
status.textContent="Generating your "+county+" investment report...";
fetch("/generate",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({county:county,email:email})
})
.then(function(r){return r.json();})
.then(function(data){
if(data.status==="success"){
status.className="status success";
status.innerHTML="Report ready! <a href='"+data.download_url+"' download>Download your "+county+" report</a>";
btn.textContent="Get Another Report";btn.disabled=false;
}else{
status.className="status error";
status.textContent="Error: "+data.message;
btn.disabled=false;btn.textContent="Get Report \\u2014 \\u20ac19.99";}
});
}
</script>
</body>
</html>"""


# ─── ROUTES ────────────────────────────────────────────────────
@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    county = data.get("county")
    email = data.get("email")
    print("Order:", county, "for", email)
    try:
        pdf_path = generate_report(county)
        if pdf_path is None:
            return jsonify({"status": "error", "message": "Not enough data for " + county})
        fname = os.path.basename(pdf_path)
        return jsonify({"status": "success", "download_url": "/download/" + fname})
    except Exception as e:
        print("Error generating report:", str(e))
        return jsonify({"status": "error", "message": "Report generation failed"})


@app.route("/download/<filename>")
def download(filename):
    path = os.path.join(TMP_DIR, filename)
    if not os.path.exists(path):
        return "File not found", 404
    return send_file(path, as_attachment=True)


# ─── RUN ───────────────────────────────────────────────────────
if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=PORT, debug=debug_mode)