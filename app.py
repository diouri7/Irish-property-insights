import os
import datetime
import tempfile
import io
import requests
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

import pandas as pd
import numpy as np

from flask import Flask, render_template_string, request, send_file

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable
)

warnings.filterwarnings("ignore")

# ─── CONFIG ─────────────────────────────────────────────
app = Flask(__name__)
TMP_DIR = tempfile.gettempdir()
DATA_PATH = os.environ.get("PPR_DATA_PATH", "PPR-ALL.csv")
PORT = int(os.environ.get("PORT", 5000))

# ─── COLORS ─────────────────────────────────────────────
C_DARK = HexColor("#0B1120")
C_GREEN = HexColor("#10B981")
C_GREEN_BG = HexColor("#ECFDF5")
C_GOLD = HexColor("#F59E0B")
C_GOLD_BG = HexColor("#FFFBEB")
C_RED = HexColor("#EF4444")
C_RED_BG = HexColor("#FEF2F2")
C_BLUE = HexColor("#3B82F6")
C_GRAY = HexColor("#64748B")
C_LIGHT = HexColor("#F8FAFC")
C_BORDER = HexColor("#E2E8F0")
C_WHITE = white

# ─── RTB RENT DATA (Monthly, Q2 2025) ──────────────────
RTB_RENT = {
    "Carlow": 1200, "Cavan": 1050, "Clare": 1180, "Cork": 1543,
    "Donegal": 950, "Dublin": 2230, "Galway": 1380, "Kerry": 1150,
    "Kildare": 1713, "Kilkenny": 1200, "Laois": 1150, "Leitrim": 900,
    "Limerick": 1449, "Longford": 950, "Louth": 1450, "Mayo": 1050,
    "Meath": 1713, "Monaghan": 1000, "Offaly": 1100, "Roscommon": 950,
    "Sligo": 1100, "Tipperary": 1050, "Waterford": 1250, "Westmeath": 1200,
    "Wexford": 1200, "Wicklow": 1650,
}

YIELD_DAMPEN = 0.4  # Dampen county rent to micro-area level

# ─── LOAD DATA ──────────────────────────────────────────
df_global = None

def load_data():
    if os.path.exists(DATA_PATH):
        return pd.read_csv(DATA_PATH, encoding="latin-1", low_memory=False)
    cached = os.path.join(TMP_DIR, "PPR-ALL.csv")
    if os.path.exists(cached):
        return pd.read_csv(cached, encoding="latin-1", low_memory=False)
    url = "https://github.com/diouri7/Irish-property-insights/releases/download/v1.0/PPR-ALL.csv"
    r = requests.get(url, timeout=180, verify=False)
    r.raise_for_status()
    with open(cached, "wb") as f:
        f.write(r.content)
    return pd.read_csv(cached, encoding="latin-1", low_memory=False)


def get_data():
    global df_global
    if df_global is None:
        print("Loading property data...")
        raw = load_data()
        print("Columns found:", raw.columns.tolist())

        raw.columns = (
            raw.columns.str.strip()
            .str.lower()
            .str.replace(" ", "_")
            .str.replace(r"[^\w]", "_", regex=True)
        )
        print("Normalized columns:", raw.columns.tolist())

        # Date
        date_col = next((c for c in raw.columns if "date" in c), None)
        if date_col:
            raw["date"] = pd.to_datetime(raw[date_col], dayfirst=True, errors="coerce")
        raw["year"] = raw["date"].dt.year

        # Price
        price_col = next((c for c in raw.columns if "price" in c), None)
        if price_col:
            raw["price"] = (
                raw[price_col].astype(str)
                .str.replace(r"[€\$£,\s]", "", regex=True)
                .str.replace(r"[^\d.]", "", regex=True)
            )
            raw["price"] = pd.to_numeric(raw["price"], errors="coerce")

        # County
        county_col = next((c for c in raw.columns if "county" in c), None)
        if county_col:
            raw["county"] = raw[county_col].astype(str).str.strip()
            # Normalize county names
            raw["county"] = raw["county"].str.replace("^Dublin.*", "Dublin", regex=True)

        # Address → micro-area extraction
        addr_col = next((c for c in raw.columns if "address" in c), None)
        if addr_col:
            raw["address_raw"] = raw[addr_col].astype(str)
        else:
            raw["address_raw"] = ""

        raw["micro_area"] = raw["address_raw"].apply(extract_micro_area)

        # Filter valid
        raw = raw.dropna(subset=["price", "year", "county"])
        raw = raw[raw["price"] > 10000]
        raw = raw[raw["year"] >= 2010]

        df_global = raw
        print(f"Loaded {len(df_global)} valid records")
    return df_global


def extract_micro_area(address):
    """Extract town/area name from Irish property address."""
    if not isinstance(address, str) or address.strip() == "":
        return "Unknown"

    addr = address.strip()

    # Split by comma and work backwards to find the area
    parts = [p.strip() for p in addr.split(",")]

    # Remove county references and very short parts
    cleaned = []
    for p in parts:
        p_lower = p.lower().strip()
        if any(x in p_lower for x in ["county", "co.", "co "]):
            continue
        if len(p) < 3:
            continue
        # Skip numeric-heavy parts (house numbers, eircode)
        alpha_ratio = sum(c.isalpha() for c in p) / max(len(p), 1)
        if alpha_ratio < 0.5:
            continue
        cleaned.append(p)

    if not cleaned:
        return "Unknown"

    # Take the last meaningful part (usually the town/area)
    # But if it's a well-known Dublin area, prefer that
    area = cleaned[-1] if len(cleaned) > 0 else "Unknown"

    # If there are multiple parts, the second-to-last is often the town
    if len(cleaned) >= 2:
        area = cleaned[-1]

    # Clean up
    area = area.strip().title()

    # Remove common prefixes
    for prefix in ["The ", "An ", "Na "]:
        if area.startswith(prefix) and len(area) > len(prefix) + 2:
            pass  # Keep these, they're valid Irish place names

    if len(area) < 3 or area == "Unknown" or area == "Ireland":
        return "Unknown"

    return area


# ─── ANALYSIS ENGINE ────────────────────────────────────
def analyse_county(county_name):
    """Full micro-area analysis for a county."""
    data = get_data()
    cdf = data[data["county"] == county_name].copy()

    if len(cdf) < 50:
        return None

    # ── County-level stats ──
    yearly = (
        cdf.groupby("year")
        .agg(median_price=("price", "median"), total_sales=("price", "count"))
        .reset_index()
        .sort_values("year")
    )

    latest_year = int(yearly["year"].max())
    earliest_year = int(yearly["year"].min())
    latest_median = yearly[yearly["year"] == latest_year]["median_price"].iloc[0]
    total_transactions = int(cdf["price"].count())

    # County 5-year growth
    y5_ago = latest_year - 5
    if y5_ago in yearly["year"].values:
        p_old = yearly[yearly["year"] == y5_ago]["median_price"].iloc[0]
        county_growth_5yr = ((latest_median / p_old) ** (1 / 5) - 1) * 100
    else:
        county_growth_5yr = None

    county_rent = RTB_RENT.get(county_name, None)
    if county_rent and latest_median > 0:
        county_yield = (county_rent * 12 / latest_median) * 100
    else:
        county_yield = None

    # ── Micro-area analysis ──
    # Filter to recent 5 years for growth, all time for volume
    recent = cdf[cdf["year"] >= y5_ago].copy()
    micro_areas = recent[recent["micro_area"] != "Unknown"].copy()

    # Only areas with enough transactions
    area_counts = micro_areas.groupby("micro_area").size()
    valid_areas = area_counts[area_counts >= 10].index
    micro_areas = micro_areas[micro_areas["micro_area"].isin(valid_areas)]

    if len(valid_areas) == 0:
        return None

    results = []
    for area in valid_areas:
        adf = micro_areas[micro_areas["micro_area"] == area]

        area_yearly = (
            adf.groupby("year")
            .agg(median_price=("price", "median"), count=("price", "count"))
            .reset_index()
            .sort_values("year")
        )

        if len(area_yearly) < 2:
            continue

        latest_area_year = area_yearly["year"].max()
        earliest_area_year = area_yearly["year"].min()
        latest_price = area_yearly[area_yearly["year"] == latest_area_year]["median_price"].iloc[0]
        earliest_price = area_yearly[area_yearly["year"] == earliest_area_year]["median_price"].iloc[0]

        # Growth (CAGR)
        years_span = latest_area_year - earliest_area_year
        if years_span > 0 and earliest_price > 0:
            cagr = ((latest_price / earliest_price) ** (1 / years_span) - 1) * 100
        else:
            cagr = 0.0

        # Risk: Coefficient of variation of yearly median prices
        if len(area_yearly) >= 3:
            cv = area_yearly["median_price"].std() / area_yearly["median_price"].mean() * 100
        else:
            cv = 50.0  # Penalise thin data

        # Transaction volume
        total_vol = int(adf["price"].count())
        avg_annual_vol = total_vol / max(years_span, 1)

        # Yield
        if county_rent and latest_price > 0:
            dampened_rent = county_rent * YIELD_DAMPEN + county_rent * (1 - YIELD_DAMPEN) * (latest_median / latest_price) ** 0.5
            gross_yield = (dampened_rent * 12 / latest_price) * 100
        else:
            gross_yield = 0.0

        # Risk score classification
        if cv < 15 and avg_annual_vol >= 5:
            risk_label = "Low"
        elif cv < 25 or avg_annual_vol >= 3:
            risk_label = "Medium"
        else:
            risk_label = "High"

        # Investment signal
        signal = compute_signal(cagr, gross_yield, risk_label)

        results.append({
            "area": area,
            "median_price": latest_price,
            "growth_5yr": round(cagr, 1),
            "gross_yield": round(gross_yield, 1),
            "cv": round(cv, 1),
            "risk": risk_label,
            "signal": signal,
            "transactions": total_vol,
            "avg_annual_vol": round(avg_annual_vol, 1),
        })

    if not results:
        return None

    results_df = pd.DataFrame(results)

    # Sort by signal strength, then yield, then growth
    signal_order = {"HIGH POTENTIAL": 0, "GOOD PROSPECT": 1, "MODERATE POTENTIAL": 2, "HOLD": 3, "CAUTION": 4}
    results_df["signal_rank"] = results_df["signal"].map(signal_order)
    results_df = results_df.sort_values(
        ["signal_rank", "gross_yield", "growth_5yr"],
        ascending=[True, False, False]
    ).reset_index(drop=True)

    return {
        "county": county_name,
        "latest_median": latest_median,
        "total_transactions": total_transactions,
        "latest_year": latest_year,
        "earliest_year": earliest_year,
        "county_growth_5yr": round(county_growth_5yr, 1) if county_growth_5yr else None,
        "county_yield": round(county_yield, 1) if county_yield else None,
        "county_rent": county_rent,
        "yearly": yearly,
        "micro_areas": results_df,
        "num_areas": len(results_df),
    }


def compute_signal(growth, gross_yield, risk):
    """Compute investment signal based on growth, yield, and risk."""
    score = 0

    # Growth scoring
    if growth >= 7:
        score += 3
    elif growth >= 5:
        score += 2
    elif growth >= 3:
        score += 1
    elif growth < 0:
        score -= 1

    # Yield scoring
    if gross_yield >= 6:
        score += 3
    elif gross_yield >= 5:
        score += 2
    elif gross_yield >= 4:
        score += 1

    # Risk scoring
    if risk == "Low":
        score += 2
    elif risk == "Medium":
        score += 1
    elif risk == "High":
        score -= 1

    if score >= 6:
        return "HIGH POTENTIAL"
    elif score >= 4:
        return "GOOD PROSPECT"
    elif score >= 2:
        return "MODERATE POTENTIAL"
    elif score >= 0:
        return "HOLD"
    else:
        return "CAUTION"


# ─── CHART GENERATION ───────────────────────────────────

def confidence_badge(transactions):
    """Return (label, emoji, tooltip) based on transaction count."""
    if transactions >= 15:
        return "High Confidence", "🟡", "Based on 15+ recent sales — statistically reliable."
    elif transactions >= 6:
        return "Medium Confidence", "⚪", "Based on 6-14 sales — good indicator, check for outliers."
    else:
        return "Low Confidence", "🟤", "Based on fewer than 6 sales — use as early indicator only."



# ─── RPZ DATA ───────────────────────────────────────────
# Official Rent Pressure Zones (RTB / Government of Ireland, 2024)
# All local electoral areas and towns designated as RPZ areas
RPZ_KEYWORDS = [
    # Dublin City & suburbs
    "Dublin", "Swords", "Malahide", "Portmarnock", "Clongriffin",
    "Baldoyle", "Sutton", "Howth", "Raheny", "Clontarf", "Marino",
    "Drumcondra", "Glasnevin", "Finglas", "Ballymun", "Santry",
    "Beaumont", "Artane", "Coolock", "Kilbarrack", "Donaghmede",
    "Blanchardstown", "Castleknock", "Mulhuddart", "Clonsilla",
    "Lucan", "Clondalkin", "Tallaght", "Rathfarnham", "Templeogue",
    "Terenure", "Kimmage", "Crumlin", "Drimnagh", "Walkinstown",
    "Ballyfermot", "Chapelizod", "Palmerstown", "Rialto", "Kilmainham",
    "Inchicore", "Islandbridge", "Rathmines", "Ranelagh", "Milltown",
    "Dundrum", "Stillorgan", "Foxrock", "Leopardstown", "Sandyford",
    "Stepaside", "Carrickmines", "Kilternan", "Glencullen",
    "Dun Laoghaire", "Blackrock", "Monkstown", "Deansgrange",
    "Killiney", "Shankill", "Bray", "Greystones",
    "Cabinteely", "Sallynoggin", "Glasthule",
    # South Dublin / Wicklow border
    "Greystones", "Delgany", "Kilcoole", "Newcastle",
    # Dun Laoghaire-Rathdown
    "Dundrum", "Stillorgan", "Deansgrange", "Ballybrack",
    # Fingal
    "Swords", "Malahide", "Rush", "Lusk", "Donabate", "Balbriggan",
    "Balbriggan", "Skerries", "Naul", "Garristown",
    # South Dublin
    "Rathcoole", "Saggart", "Clondalkin", "Tallaght", "Citywest",
    # Cork City & suburbs
    "Cork", "Ballincollig", "Carrigaline", "Cobh", "Glanmire",
    "Blarney", "Tower", "Midleton", "Youghal", "Mallow",
    "Douglas", "Bishopstown", "Wilton", "Togher", "Turners Cross",
    "Blackpool", "Mayfield", "Gurranabraher", "Sunday's Well",
    "Shandon", "Blackrock", "Mahon",
    # Galway City & suburbs
    "Galway", "Salthill", "Knocknacarra", "Renmore", "Ballybane",
    "Doughiska", "Merlin Park", "Claregalway", "Oranmore",
    "Athenry", "Tuam",
    # Kildare (all designated)
    "Naas", "Newbridge", "Celbridge", "Maynooth", "Leixlip",
    "Clane", "Kilcock", "Monasterevin", "Athy", "Kildare",
    "Rathangan", "Kilcullen", "Curragh",
    # Meath
    "Navan", "Ashbourne", "Ratoath", "Dunshaughlin", "Trim",
    "Kells", "Dunboyne", "Clonee", "Stamullen",
    # Wicklow
    "Wicklow", "Arklow", "Bray", "Greystones", "Kilcoole",
    "Tinahely", "Rathdrum",
    # Louth
    "Drogheda", "Dundalk", "Ardee", "Carlingford",
    # Limerick City & county
    "Limerick", "Castletroy", "Dooradoyle", "Raheen", "Ballinacurra",
    "Annacotty", "Monaleen", "Corbally", "Ennis Road", "Mulgrave",
    # Waterford
    "Waterford", "Tramore", "Dungarvan",
    # Clare
    "Ennis", "Shannon", "Killaloe",
    # Laois
    "Portlaoise", "Portarlington",
    # Offaly
    "Tullamore",
    # Westmeath
    "Athlone", "Mullingar",
    # Wexford
    "Wexford", "Gorey", "New Ross",
]

# Normalise to lowercase for matching
_RPZ_LOWER = [k.lower() for k in RPZ_KEYWORDS]


def is_rpz(area_name):
    """Return True if this micro-area is in (or likely in) an RPZ.
    Uses partial keyword matching on the official RTB RPZ list."""
    if not isinstance(area_name, str):
        return False
    a = area_name.lower().strip()
    for kw in _RPZ_LOWER:
        if kw in a or a in kw:
            return True
    return False


def make_price_chart(yearly_df, county_name):
    """Generate a price trend chart and return as bytes."""
    fig, ax = plt.subplots(figsize=(7, 3.2))

    years = yearly_df["year"].values
    prices = yearly_df["median_price"].values

    ax.plot(years, prices, color="#10B981", linewidth=2.5, marker="o", markersize=4, zorder=3)
    ax.fill_between(years, prices, alpha=0.08, color="#10B981")

    ax.set_title(f"{county_name} — Median Sale Price by Year", fontsize=11, fontweight="bold", color="#1E293B", pad=12)
    ax.set_xlabel("")
    ax.set_ylabel("Median Price (€)", fontsize=9, color="#64748B")

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"€{x/1000:.0f}k"))
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.tick_params(colors="#94A3B8", labelsize=8)

    ax.grid(True, alpha=0.15, color="#94A3B8")
    ax.set_facecolor("#FAFBFC")
    fig.patch.set_facecolor("white")

    for spine in ax.spines.values():
        spine.set_visible(False)

    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def make_top_areas_chart(micro_df, county_name, top_n=10):
    """Horizontal bar chart of top areas by yield."""
    top = micro_df.head(top_n).copy()
    top = top.sort_values("gross_yield", ascending=True)

    fig, ax = plt.subplots(figsize=(7, max(3, top_n * 0.38)))

    colors = []
    for s in top["signal"]:
        if s == "HIGH POTENTIAL":
            colors.append("#10B981")
        elif s == "GOOD PROSPECT":
            colors.append("#3B82F6")
        elif s == "MODERATE":
            colors.append("#F59E0B")
        else:
            colors.append("#94A3B8")

    bars = ax.barh(top["area"], top["gross_yield"], color=colors, height=0.65, edgecolor="white", linewidth=0.5)

    for bar, val in zip(bars, top["gross_yield"]):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}%", va="center", fontsize=8, color="#475569", fontweight="bold")

    ax.set_title(f"Top {len(top)} Micro-Areas by Gross Yield — {county_name}", fontsize=11, fontweight="bold", color="#1E293B", pad=12)
    ax.set_xlabel("Estimated Gross Yield (%)", fontsize=9, color="#64748B")
    ax.tick_params(colors="#94A3B8", labelsize=8)
    ax.grid(True, axis="x", alpha=0.15, color="#94A3B8")
    ax.set_facecolor("#FAFBFC")
    fig.patch.set_facecolor("white")

    for spine in ax.spines.values():
        spine.set_visible(False)

    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


# ─── PDF REPORT BUILDER ────────────────────────────────
def build_pdf_report(analysis, is_snapshot=False):
    """Build a professional PDF report from analysis data."""
    county = analysis["county"]
    suffix = "_Snapshot" if is_snapshot else "_Full_Report"
    pdf_path = os.path.join(TMP_DIR, f"{county}_Property{suffix}_2025.pdf")

    doc = SimpleDocTemplate(
        pdf_path, pagesize=A4,
        rightMargin=1.8 * cm, leftMargin=1.8 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    s_title = ParagraphStyle("RTitle", parent=styles["Title"], fontSize=22, textColor=C_DARK,
                             spaceAfter=6, fontName="Helvetica-Bold")
    s_subtitle = ParagraphStyle("RSub", parent=styles["Normal"], fontSize=11, textColor=C_GRAY,
                                spaceAfter=20)
    s_h2 = ParagraphStyle("RH2", parent=styles["Heading2"], fontSize=14, textColor=C_DARK,
                           spaceBefore=24, spaceAfter=10, fontName="Helvetica-Bold")
    s_h3 = ParagraphStyle("RH3", parent=styles["Heading3"], fontSize=11, textColor=HexColor("#334155"),
                           spaceBefore=16, spaceAfter=6, fontName="Helvetica-Bold")
    s_body = ParagraphStyle("RBody", parent=styles["Normal"], fontSize=9.5, textColor=HexColor("#475569"),
                            leading=14, spaceAfter=8)
    s_small = ParagraphStyle("RSmall", parent=styles["Normal"], fontSize=8, textColor=C_GRAY,
                             leading=11)
    s_metric_val = ParagraphStyle("MetricVal", parent=styles["Normal"], fontSize=18,
                                   fontName="Helvetica-Bold", textColor=C_DARK, alignment=TA_CENTER)
    s_metric_label = ParagraphStyle("MetricLabel", parent=styles["Normal"], fontSize=8,
                                     textColor=C_GRAY, alignment=TA_CENTER, spaceAfter=4)

    elements = []

    # ── PAGE 1: Header ──
    elements.append(Paragraph(f"{county} Property Investment Report", s_title))
    elements.append(Paragraph(
        f"Micro-area intelligence  •  Updated with RTB Q2 2025 data  •  Generated {datetime.date.today().strftime('%B %Y')}",
        s_subtitle
    ))
    elements.append(HRFlowable(width="100%", thickness=2, color=C_GREEN, spaceAfter=16))

    # ── Key metrics row ──
    metrics_data = [
        [f"€{analysis['latest_median']:,.0f}", f"{analysis['county_growth_5yr']}%" if analysis['county_growth_5yr'] else "N/A",
         f"{analysis['county_yield']:.1f}%" if analysis['county_yield'] else "N/A", str(analysis['num_areas'])],
        ["Median Price", "5yr County Growth", "County Gross Yield", "Micro-Areas Analysed"],
    ]

    # Build metric cards as table
    metric_cells_top = []
    metric_cells_bot = []
    for i in range(4):
        metric_cells_top.append(Paragraph(metrics_data[0][i], s_metric_val))
        metric_cells_bot.append(Paragraph(metrics_data[1][i], s_metric_label))

    metrics_table = Table(
        [metric_cells_top, metric_cells_bot],
        colWidths=[doc.width / 4] * 4,
    )
    metrics_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, C_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, C_BORDER),
        ("TOPPADDING", (0, 0), (-1, 0), 12),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 10),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(metrics_table)
    elements.append(Spacer(1, 16))

    # ── Price trend chart ──
    elements.append(Paragraph("Price Trend", s_h2))
    chart_buf = make_price_chart(analysis["yearly"], county)
    elements.append(Image(chart_buf, width=16 * cm, height=7.2 * cm))
    elements.append(Spacer(1, 8))

    # ── Top areas chart ──
    micro_df = analysis["micro_areas"]
    display_n = min(10, len(micro_df)) if not is_snapshot else min(3, len(micro_df))

    elements.append(Paragraph("Top Micro-Areas by Estimated Yield", s_h2))
    areas_chart_buf = make_top_areas_chart(micro_df, county, top_n=display_n)
    chart_h = max(7, display_n * 0.85) * cm
    elements.append(Image(areas_chart_buf, width=16 * cm, height=chart_h))

    # ── PAGE 2: Ranking Table ──
    elements.append(PageBreak())
    elements.append(Paragraph("Micro-Area Ranking Table", s_h2))

    if is_snapshot:
        elements.append(Paragraph(
            f"Showing top {display_n} of {len(micro_df)} ranked micro-areas. "
            f"Full report includes all {len(micro_df)} areas with detailed risk breakdown.",
            s_body
        ))
        table_data_df = micro_df.head(display_n)
    else:
        elements.append(Paragraph(
            f"All {len(micro_df)} micro-areas ranked by investment signal, yield, and growth.",
            s_body
        ))
        table_data_df = micro_df

    # Table header
    header = ["#", "Micro-Area", "Median Price", "5yr Growth", "Yield", "Risk", "Signal", "Txns", "Confidence", "RPZ"]

    table_rows = [header]
    for idx, row in table_data_df.iterrows():
        rank = len(table_rows)
        conf_label, conf_emoji, _ = confidence_badge(row["transactions"])
        rpz_flag = "⚠ Yes" if is_rpz(row["area"]) else "No"
        table_rows.append([
            str(rank),
            str(row["area"])[:25],
            f"€{row['median_price']:,.0f}",
            f"{row['growth_5yr']:+.1f}%",
            f"{row['gross_yield']:.1f}%",
            row["risk"],
            row["signal"],
            str(row["transactions"]),
            f"{conf_emoji} {conf_label.split()[0]}",
            rpz_flag,
        ])

    # Column widths
    col_w = [0.5*cm, 3.4*cm, 2.0*cm, 1.6*cm, 1.3*cm, 1.3*cm, 2.0*cm, 1.0*cm, 1.7*cm, 1.2*cm]

    tbl = Table(table_rows, colWidths=col_w, repeatRows=1)

    # Table styling
    tbl_style = [
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), C_DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, C_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),  # Rank
        ("ALIGN", (2, 0), (-1, -1), "CENTER"),  # Numbers
        ("ALIGN", (1, 0), (1, -1), "LEFT"),  # Area name
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_WHITE, C_LIGHT]),
    ]

    # Color-code signals
    for i, row in enumerate(table_rows[1:], start=1):
        signal = row[6]
        if signal == "HIGH POTENTIAL":
            tbl_style.append(("TEXTCOLOR", (6, i), (6, i), C_GREEN))
            tbl_style.append(("FONTNAME", (6, i), (6, i), "Helvetica-Bold"))
        elif signal == "GOOD PROSPECT":
            tbl_style.append(("TEXTCOLOR", (6, i), (6, i), C_BLUE))
            tbl_style.append(("FONTNAME", (6, i), (6, i), "Helvetica-Bold"))
        elif signal == "MODERATE POTENTIAL":
            tbl_style.append(("TEXTCOLOR", (6, i), (6, i), C_GOLD))
        elif signal == "CAUTION":
            tbl_style.append(("TEXTCOLOR", (6, i), (6, i), C_RED))

        # Color-code risk
        risk = row[5]
        if risk == "Low":
            tbl_style.append(("TEXTCOLOR", (5, i), (5, i), C_GREEN))
        elif risk == "High":
            tbl_style.append(("TEXTCOLOR", (5, i), (5, i), C_RED))

    tbl.setStyle(TableStyle(tbl_style))
    elements.append(tbl)

    # ── Snapshot: teaser for full report ──
    if is_snapshot:
        elements.append(Spacer(1, 20))
        elements.append(HRFlowable(width="100%", thickness=1, color=C_BORDER, spaceAfter=12))
        elements.append(Paragraph("Want the full picture?", s_h2))
        elements.append(Paragraph(
            f"This snapshot shows {display_n} of {len(micro_df)} ranked micro-areas in {county}. "
            f"The full report includes:",
            s_body
        ))
        for item in [
            f"All {len(micro_df)} micro-areas ranked with growth, yield, risk, and signal",
            "Complete risk model breakdown (volatility, transaction frequency, price consistency)",
            "Area-by-area commentary and watchlist zones",
            "Full methodology appendix",
        ]:
            elements.append(Paragraph(f"•  {item}", s_body))

        elements.append(Spacer(1, 12))
        elements.append(Paragraph(
            '<b>Get the full report →</b> <font color="#3B82F6">web-production-d1e11.up.railway.app</font>',
            ParagraphStyle("CTA", parent=s_body, fontSize=11, textColor=C_GREEN)
        ))

    # ── Full report: methodology page ──
    if not is_snapshot:
        elements.append(PageBreak())
        elements.append(Paragraph("Methodology", s_h2))
        elements.append(HRFlowable(width="100%", thickness=1, color=C_BORDER, spaceAfter=12))

        elements.append(Paragraph("Data Sources", s_h3))
        elements.append(Paragraph(
            "This report analyses residential property transactions from the Property Price Register (PPR), "
            "maintained by the Property Services Regulatory Authority. Transaction data spans 2010 to present. "
            "Rental data is sourced from the Residential Tenancies Board (RTB) Q2 2025 quarterly report.",
            s_body
        ))

        elements.append(Paragraph("Growth Calculation", s_h3))
        elements.append(Paragraph(
            "5-year compound annual growth rate (CAGR) is calculated for each micro-area using yearly median "
            "sale prices. Areas with fewer than 10 transactions in the 5-year window are excluded to ensure "
            "statistical reliability.",
            s_body
        ))

        elements.append(Paragraph("Risk Scoring", s_h3))
        elements.append(Paragraph(
            "Risk is assessed using the coefficient of variation (CV) of yearly median prices, combined with "
            "average annual transaction volume. Low risk: CV < 15% and 5+ annual transactions. Medium risk: "
            "CV < 25% or 3+ annual transactions. High risk: all others. Thinly-traded markets are penalised.",
            s_body
        ))

        elements.append(Paragraph("Yield Estimation", s_h3))
        elements.append(Paragraph(
            f"Gross rental yield is calculated as (Annual Rent / Median Sale Price) × 100. County-level RTB "
            f"rents are adjusted to micro-area level using a {YIELD_DAMPEN} dampening factor to avoid overstating "
            f"yields in lower-priced areas. These are gross estimates — actual net yields will depend on vacancy, "
            f"management costs, and individual purchase price.",
            s_body
        ))

        elements.append(Paragraph("Investment Signal", s_h3))
        elements.append(Paragraph(
            "Each micro-area receives a data signal (HIGH POTENTIAL / GOOD PROSPECT / MODERATE POTENTIAL / HOLD / CAUTION) "
            "based on a weighted scoring of growth rate, gross yield, and risk classification. Areas must perform "
            "well across all three dimensions to receive a HIGH POTENTIAL rating.",
            s_body
        ))

        elements.append(Spacer(1, 20))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceAfter=8))
        elements.append(Paragraph(
            "This report is for informational purposes only and does not constitute financial advice. "
            "Past performance does not guarantee future results. Always conduct independent due diligence "
            "before making investment decisions.",
            s_small
        ))
        elements.append(Paragraph(
            f"© {datetime.date.today().year} IrishPropertyInsights  •  Data: PPR & RTB  •  "
            f"web-production-d1e11.up.railway.app",
            s_small
        ))

    doc.build(elements)
    return pdf_path


# ─── LANDING PAGE HTML ──────────────────────────────────
# (Embedded for single-file deployment)
LANDING_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-24NY207Q8J"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-24NY207Q8J');
</script>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IrishPropertyInsights — Best Rental Yield Areas Ireland 2025 | Property Investment Intelligence</title>
<meta name="description" content="Find the highest rental yield micro-areas across all 26 Irish counties. Ranked by yield, 5-year growth & investment risk using 727,000+ PPR transactions and RTB Q2 2025 data. Free county snapshot — no credit card.">
<meta name="keywords" content="best rental yield ireland 2025, irish property investment, buy to let ireland, property price register analysis, high yield areas ireland, RTB rental data, irish property micro-areas, dublin property investment, cork property yield">
<meta property="og:title" content="IrishPropertyInsights — Find High-Yield Irish Property Areas">
<meta property="og:description" content="727,000+ PPR transactions analysed. Every micro-area in all 26 counties ranked by yield, growth & risk. Free snapshot, no credit card.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://irishpropertyinsights.ie">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="IrishPropertyInsights — Irish Property Investment Data">
<meta name="twitter:description" content="Micro-area rankings across all 26 Irish counties. Yield, growth & risk scored from official PPR & RTB data.">
<link rel="canonical" href="https://irishpropertyinsights.ie">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Fraunces:ital,wght@0,300;0,500;0,700;1,400&display=swap" rel="stylesheet">
<style>
:root{--bg:#0B1120;--bg2:#111827;--card:#1A2332;--green:#10B981;--green-dim:rgba(16,185,129,.15);--gold:#F59E0B;--gold-dim:rgba(245,158,11,.12);--blue:#3B82F6;--blue-dim:rgba(59,130,246,.12);--t1:#F1F5F9;--t2:#94A3B8;--t3:#64748B;--border:rgba(148,163,184,.1);--fd:'Fraunces',Georgia,serif;--fb:'DM Sans',system-ui,sans-serif}
*{margin:0;padding:0;box-sizing:border-box}html{scroll-behavior:smooth}
body{font-family:var(--fb);background:var(--bg);color:var(--t1);line-height:1.6;overflow-x:hidden}
nav{position:fixed;top:0;left:0;right:0;z-index:100;padding:1rem 2rem;display:flex;align-items:center;justify-content:space-between;background:rgba(11,17,32,.85);backdrop-filter:blur(20px);border-bottom:1px solid var(--border)}
.nl{font-family:var(--fd);font-size:1.25rem;font-weight:700;color:var(--t1);text-decoration:none}.nl span{color:var(--green)}
.nk{display:flex;gap:2rem;align-items:center;list-style:none}.nk a{color:var(--t2);text-decoration:none;font-size:.9rem;font-weight:500;transition:color .2s}.nk a:hover{color:var(--t1)}
.nc{background:var(--green)!important;color:var(--bg)!important;padding:.5rem 1.25rem;border-radius:8px;font-weight:600!important}
.hero{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:8rem 2rem 4rem;position:relative}
.hero::before{content:'';position:absolute;top:-200px;right:-200px;width:600px;height:600px;background:radial-gradient(circle,rgba(16,185,129,.08) 0%,transparent 70%)}
.hc{max-width:820px;text-align:center;position:relative;z-index:1}
.hb{display:inline-flex;align-items:center;gap:.5rem;padding:.4rem 1rem;background:var(--green-dim);border:1px solid rgba(16,185,129,.25);border-radius:100px;font-size:.8rem;font-weight:600;color:var(--green);margin-bottom:2rem}
.hb::before{content:'';width:6px;height:6px;border-radius:50%;background:var(--green);animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.hc h1{font-family:var(--fd);font-size:clamp(2.5rem,5.5vw,4.2rem);font-weight:700;line-height:1.12;letter-spacing:-.03em;margin-bottom:1.5rem}
.hc h1 em{font-style:italic;color:var(--green)}
.hs{font-size:1.15rem;color:var(--t2);max-width:600px;margin:0 auto 2.5rem;line-height:1.7}
.hctas{display:flex;gap:1rem;justify-content:center;flex-wrap:wrap}
.bp{display:inline-flex;align-items:center;gap:.5rem;padding:.9rem 2rem;background:var(--green);color:var(--bg);border:none;border-radius:10px;font-family:var(--fb);font-size:1rem;font-weight:600;cursor:pointer;transition:all .25s;text-decoration:none}
.bp:hover{transform:translateY(-2px);box-shadow:0 8px 30px rgba(16,185,129,.35)}
.bs{display:inline-flex;align-items:center;gap:.5rem;padding:.9rem 2rem;background:0;color:var(--t2);border:1px solid var(--border);border-radius:10px;font-family:var(--fb);font-size:1rem;font-weight:500;cursor:pointer;transition:all .25s;text-decoration:none}
.bs:hover{border-color:var(--t3);color:var(--t1)}
.cb{padding:3rem 2rem;border-top:1px solid var(--border);border-bottom:1px solid var(--border)}
.cbi{max-width:900px;margin:0 auto;display:grid;grid-template-columns:repeat(4,1fr);gap:2rem;text-align:center}
.ci .cn{font-family:var(--fd);font-size:2rem;font-weight:700}.ci .cl{font-size:.82rem;color:var(--t3);margin-top:.25rem;font-weight:500}
section{padding:6rem 2rem}
.sh{text-align:center;max-width:640px;margin:0 auto 4rem}
.sh .ol{font-size:.75rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--green);margin-bottom:.75rem}
.sh h2{font-family:var(--fd);font-size:clamp(1.8rem,3.5vw,2.5rem);font-weight:700;letter-spacing:-.02em;line-height:1.2;margin-bottom:1rem}
.sh p{color:var(--t2);font-size:1.05rem}
.pg{max-width:1100px;margin:0 auto;display:grid;grid-template-columns:repeat(3,1fr);gap:1.5rem}
.pc{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:2.5rem 2rem;transition:all .3s;position:relative;overflow:hidden}
.pc::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;border-radius:16px 16px 0 0}
.pc:nth-child(1)::before{background:var(--green)}.pc:nth-child(2)::before{background:var(--gold)}.pc:nth-child(3)::before{background:var(--blue)}
.pc:hover{transform:translateY(-4px);border-color:rgba(148,163,184,.2)}
.pi{width:48px;height:48px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:1.4rem;margin-bottom:1.5rem}
.pc:nth-child(1) .pi{background:var(--green-dim)}.pc:nth-child(2) .pi{background:var(--gold-dim)}.pc:nth-child(3) .pi{background:var(--blue-dim)}
.pc h3{font-family:var(--fd);font-size:1.3rem;font-weight:600;margin-bottom:.75rem}.pc p{color:var(--t2);font-size:.95rem;line-height:1.65}
.sg{max-width:800px;margin:0 auto;display:flex;flex-direction:column}.sr{display:flex;align-items:flex-start;gap:2rem;padding:2rem 0;border-bottom:1px solid var(--border)}.sr:last-child{border-bottom:none}
.sn{font-family:var(--fd);font-size:3rem;font-weight:300;color:var(--green);opacity:.5;line-height:1;min-width:60px}
.st h3{font-size:1.1rem;font-weight:600;margin-bottom:.4rem}.st p{color:var(--t2);font-size:.95rem}
.is{background:var(--bg2)}
.ig{max-width:1000px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center}
.it h3{font-family:var(--fd);font-size:1.6rem;font-weight:600;margin-bottom:1rem}.it p{color:var(--t2);margin-bottom:1.5rem;line-height:1.7}
.itable{width:100%;border-collapse:separate;border-spacing:0;background:var(--card);border:1px solid var(--border);border-radius:12px;overflow:hidden;font-size:.88rem}
.itable thead{background:rgba(16,185,129,.08)}.itable th{padding:.9rem 1rem;text-align:left;font-weight:600;font-size:.78rem;text-transform:uppercase;letter-spacing:.06em;color:var(--t3)}
.itable td{padding:.8rem 1rem;border-top:1px solid var(--border);color:var(--t2)}.itable tbody tr:hover{background:rgba(255,255,255,.02)}
.ss{display:inline-block;padding:.15rem .6rem;border-radius:6px;font-size:.75rem;font-weight:700;background:var(--green-dim);color:var(--green)}
.sm{display:inline-block;padding:.15rem .6rem;border-radius:6px;font-size:.75rem;font-weight:700;background:var(--gold-dim);color:var(--gold)}
.blur td{filter:blur(5px);user-select:none}
.es{text-align:center}.eb{max-width:580px;margin:0 auto;background:var(--card);border:1px solid var(--border);border-radius:20px;padding:3.5rem 3rem;position:relative;overflow:hidden}
.eb::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,var(--green),var(--blue))}
.eb h2{font-family:var(--fd);font-size:1.8rem;font-weight:700;margin-bottom:.75rem}.eb>p{color:var(--t2);margin-bottom:1.25rem;font-size:.95rem}
.ef{display:flex;gap:.75rem}.ef input[type=email]{flex:1;padding:.85rem 1.2rem;background:var(--bg);border:1px solid var(--border);border-radius:10px;color:var(--t1);font-family:var(--fb);font-size:.95rem;outline:none}
.ef input[type=email]:focus{border-color:var(--green)}.ef button{padding:.85rem 1.5rem;white-space:nowrap}
.en{font-size:.78rem;color:var(--t3);margin-top:1rem}
.rs{background:var(--bg2);text-align:center}.csw{max-width:500px;margin:0 auto;display:flex;gap:.75rem}
.csw select{flex:1;padding:.85rem 1.2rem;background:var(--card);border:1px solid var(--border);border-radius:10px;color:var(--t1);font-family:var(--fb);font-size:.95rem;cursor:pointer;outline:none;appearance:none;
background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='%2394A3B8' viewBox='0 0 16 16'%3E%3Cpath d='M8 11L3 6h10l-5 5z'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 1rem center}
.csw select:focus{border-color:var(--green)}
.mc{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:1.75rem}.mc h4{font-size:.95rem;font-weight:600;margin-bottom:.5rem}.mc p{font-size:.88rem;color:var(--t2);line-height:1.6}
.mg{max-width:800px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:1.5rem}
/* Audience */
.ag{max-width:1000px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:2.5rem}
.ac h3{font-family:var(--fd);font-size:1.3rem;font-weight:600;margin-bottom:1.5rem;display:flex;align-items:center;gap:.6rem}
.al{list-style:none;display:flex;flex-direction:column;gap:1rem}.al li{display:flex;align-items:flex-start;gap:.75rem;font-size:.93rem;color:var(--t2);line-height:1.6}
.al .ic{flex-shrink:0;width:24px;height:24px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:.8rem;margin-top:2px}
.fl .ic{background:var(--green-dim);color:var(--green)}.nl2 .ic{background:rgba(239,68,68,.12);color:#EF4444}
.fq{max-width:800px;margin:3.5rem auto 0;display:flex;flex-direction:column}.fi{padding:1.5rem 0;border-bottom:1px solid var(--border)}.fi:first-child{border-top:1px solid var(--border)}
.fqq{font-weight:600;font-size:.95rem;cursor:pointer;display:flex;align-items:center;justify-content:space-between;gap:1rem;user-select:none;}
.fqq::after{content:"+";font-size:1.2rem;font-weight:300;color:var(--t3);flex-shrink:0;transition:transform .25s;}
.fi.open .fqq::after{transform:rotate(45deg);}
.fqa{font-size:.9rem;color:var(--t2);line-height:1.65;max-height:0;overflow:hidden;transition:max-height .3s ease;margin-bottom:0;}
.fi.open .fqa{max-height:300px;margin-bottom:.5rem;}
footer{padding:3rem 2rem;border-top:1px solid var(--border);text-align:center}footer p{font-size:.82rem;color:var(--t3)}footer a{color:var(--t2);text-decoration:none}
.toast{position:fixed;bottom:2rem;left:50%;transform:translateX(-50%) translateY(100px);background:var(--card);border:1px solid var(--green);color:var(--t1);padding:1rem 2rem;border-radius:12px;font-size:.9rem;font-weight:500;z-index:200;opacity:0;transition:all .4s;pointer-events:none}
.toast.show{transform:translateX(-50%) translateY(0);opacity:1}
.fade-in{opacity:0;transform:translateY(24px);transition:opacity .6s ease-out,transform .6s ease-out}.fade-in.visible{opacity:1;transform:translateY(0)}
@media(max-width:768px){.nk{display:none}.cbi{grid-template-columns:repeat(2,1fr)}.pg,.ig,.mg,.ag{grid-template-columns:1fr}.ef,.csw{flex-direction:column}.eb{padding:2.5rem 1.5rem}.sr{gap:1.25rem}.sn{font-size:2.2rem;min-width:40px}}

/* Sample Report Preview */
.rp-wrap{display:flex;justify-content:center;padding:0 1rem}
.rp-browser{width:100%;max-width:750px;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 25px 80px rgba(0,0,0,.5);border:1px solid rgba(255,255,255,.08)}
.rp-bar{background:#f1f3f5;padding:.6rem 1rem;display:flex;gap:.5rem;align-items:center}
.rp-bar span{width:12px;height:12px;border-radius:50%;background:#e5e7eb}
.rp-bar span:nth-child(1){background:#ef4444}.rp-bar span:nth-child(2){background:#f59e0b}.rp-bar span:nth-child(3){background:#10b981}
.rp-doc{background:#fff;padding:2rem 2.5rem;color:#1e293b;font-family:'DM Sans',sans-serif;position:relative}
.rp-header h2{font-size:1.4rem;font-weight:700;color:#0b1120;margin-bottom:.3rem}
.rp-header p{font-size:.78rem;color:#64748b;margin-bottom:1rem}
.rp-rule{height:2px;background:linear-gradient(90deg,#10b981,#3b82f6);border-radius:2px;margin-bottom:1.25rem}
.rp-metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:.75rem;margin-bottom:1.5rem}
.rp-m{background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:.75rem;text-align:center}
.rp-mv{font-size:1.1rem;font-weight:700;color:#0b1120}.rp-ml{font-size:.68rem;color:#94a3b8;margin-top:.2rem}
.rp-section-title{font-size:.82rem;font-weight:700;color:#0b1120;margin-bottom:.75rem;text-transform:uppercase;letter-spacing:.05em}
.rp-chart{display:flex;flex-direction:column;gap:.45rem}
.rp-bar-row{display:flex;align-items:center;gap:.75rem}
.rp-area{font-size:.72rem;color:#475569;width:170px;flex-shrink:0;text-align:right}
.rp-bar-wrap{flex:1;background:#f1f5f9;border-radius:4px;height:18px;overflow:hidden}
.rp-bar-fill{height:100%;border-radius:4px;background:#10b981}
.rp-pct{font-size:.72rem;font-weight:700;color:#10b981;width:38px;flex-shrink:0}
.rp-table{width:100%;border-collapse:collapse;font-size:.72rem;margin-top:.5rem}
.rp-table th{background:#0b1120;color:#fff;padding:.4rem .5rem;text-align:left;font-weight:600}
.rp-table td{padding:.35rem .5rem;border-bottom:1px solid #f1f5f9;color:#475569}
.rp-table tr:nth-child(even) td{background:#f8fafc}
.rp-table .g{color:#10b981;font-weight:600}
.sig{display:inline-block;padding:.1rem .4rem;border-radius:4px;font-weight:700;font-size:.68rem}
.sig.sb{background:rgba(16,185,129,.1);color:#10b981}
.blur-row td{filter:blur(4px);user-select:none;opacity:.6}
.rp-fade{position:absolute;bottom:0;left:0;right:0;height:80px;background:linear-gradient(to bottom,transparent,#fff)}

#stickyCTA{position:fixed;bottom:0;left:0;right:0;z-index:200;background:rgba(11,17,32,.95);backdrop-filter:blur(12px);border-top:1px solid rgba(16,185,129,.25);padding:.75rem 2rem;display:flex;align-items:center;justify-content:space-between;gap:1rem;transform:translateY(100%);transition:transform .35s ease;flex-wrap:wrap;}
#stickyCTA.visible{transform:translateY(0);}
#stickyCTA .sc-msg{font-size:.88rem;color:var(--t2);flex:1;min-width:180px;}
#stickyCTA .sc-msg strong{color:var(--t1);}
#stickyCTA .sc-actions{display:flex;gap:.6rem;align-items:center;flex-shrink:0;}
#stickyCTA .sc-dismiss{background:none;border:none;color:var(--t3);cursor:pointer;font-size:1.2rem;padding:.2rem .5rem;line-height:1;}
@media(max-width:480px){#stickyCTA{padding:.6rem 1rem;}#stickyCTA .sc-msg{font-size:.8rem;}}

/* ── EXIT INTENT POPUP ── */
#exitPopup{position:fixed;inset:0;background:rgba(11,17,32,.88);backdrop-filter:blur(10px);z-index:600;display:none;align-items:center;justify-content:center;padding:1rem;}
#exitPopup.show{display:flex;}
#exitPopupBox{background:var(--bg2);border:1px solid rgba(16,185,129,.3);border-radius:18px;max-width:480px;width:100%;padding:2.5rem 2rem;position:relative;box-shadow:0 30px 80px rgba(0,0,0,.6);text-align:center;}
#exitPopupBox .ep-badge{display:inline-block;background:rgba(16,185,129,.12);color:var(--green);font-size:.7rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;padding:.35rem .9rem;border-radius:20px;border:1px solid rgba(16,185,129,.25);margin-bottom:1.25rem;}
#exitPopupBox h3{font-family:var(--fd);font-size:clamp(1.4rem,3vw,1.8rem);font-weight:700;line-height:1.2;margin-bottom:.75rem;color:var(--t1);}
#exitPopupBox p{font-size:.9rem;color:var(--t2);margin-bottom:1.5rem;line-height:1.6;}
#exitPopupBox .ep-preview{display:grid;grid-template-columns:1fr 1fr 1fr;gap:.6rem;margin-bottom:1.5rem;}
#exitPopupBox .ep-card{background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:.65rem .5rem;font-size:.72rem;color:var(--t2);text-align:center;}
#exitPopupBox .ep-card strong{display:block;color:var(--green);font-size:1rem;font-weight:700;margin-bottom:.2rem;}
#exitPopupBox .ep-form{display:flex;flex-direction:column;gap:.75rem;}
#exitPopupBox .ep-input{padding:.9rem 1.1rem;background:var(--bg);border:1px solid var(--border);border-radius:10px;color:var(--t1);font-family:var(--fb);font-size:.95rem;outline:none;transition:border-color .2s;}
#exitPopupBox .ep-input:focus{border-color:var(--green);}
#exitPopupBox .ep-close{position:absolute;top:1rem;right:1.25rem;background:none;border:none;color:var(--t3);font-size:1.4rem;cursor:pointer;line-height:1;padding:.2rem;}
#exitPopupBox .ep-skip{font-size:.78rem;color:var(--t3);margin-top:.75rem;cursor:pointer;text-decoration:underline;background:none;border:none;}
/* ── TRUST LOGOS SECTION ── */
.trust-bar{padding:2.5rem 2rem;border-top:1px solid var(--border);border-bottom:1px solid var(--border);background:var(--bg2);}
.trust-bar-inner{max-width:900px;margin:0 auto;display:flex;align-items:center;justify-content:center;gap:2.5rem;flex-wrap:wrap;}
.trust-logo{display:flex;align-items:center;gap:.6rem;opacity:.7;transition:opacity .2s;}
.trust-logo:hover{opacity:1;}
.trust-logo span{font-size:.75rem;font-weight:600;color:var(--t2);letter-spacing:.04em;text-transform:uppercase;}
.trust-divider{width:1px;height:28px;background:var(--border);flex-shrink:0;}
.trust-used-by{font-size:.78rem;color:var(--t3);text-align:center;margin-top:1rem;width:100%;}
/* ── MICRO-AREA SEARCH ── */
#maSearch{background:var(--bg2);border-top:1px solid var(--border);padding:3rem 2rem;}
#maSearch .mas-inner{max-width:680px;margin:0 auto;}
#maSearch .mas-label{font-size:.75rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--green);margin-bottom:.6rem;}
#maSearch h3{font-family:var(--fd);font-size:1.4rem;font-weight:700;margin-bottom:1.25rem;color:var(--t1);}
#masInput{width:100%;padding:1rem 1.25rem 1rem 3rem;background:var(--bg);border:1px solid var(--border);border-radius:12px;color:var(--t1);font-family:var(--fb);font-size:1rem;outline:none;transition:border-color .2s;box-sizing:border-box;}
#masInput:focus{border-color:var(--green);}
#masWrap{position:relative;}
#masWrap svg{position:absolute;left:.9rem;top:50%;transform:translateY(-50%);pointer-events:none;}
#masResults{margin-top:.75rem;display:none;flex-direction:column;gap:.4rem;max-height:320px;overflow-y:auto;}
#masResults.show{display:flex;}
.mas-row{display:grid;grid-template-columns:1fr auto auto auto auto;align-items:center;gap:.75rem;padding:.75rem 1rem;background:var(--bg);border:1px solid var(--border);border-radius:10px;cursor:pointer;transition:border-color .15s;}
.mas-row:hover{border-color:var(--green);}
.mas-row .mr-name{font-size:.9rem;font-weight:600;color:var(--t1);}
.mas-row .mr-county{font-size:.72rem;color:var(--t3);}
.mas-row .mr-yield{font-size:.82rem;font-weight:700;color:var(--green);}
.mas-row .mr-growth{font-size:.82rem;color:var(--t2);}
.mas-row .mr-sig{font-size:.65rem;font-weight:700;padding:.2rem .55rem;border-radius:4px;}
.mas-row .mr-sig.sb{background:rgba(26,107,60,.3);color:#4ade80;}
.mas-row .mr-sig.mo{background:rgba(245,158,11,.15);color:#f59e0b;}
#masNoResult{display:none;padding:1rem;text-align:center;color:var(--t3);font-size:.88rem;}
/* ── MOBILE TABLE SCROLL ── */
/* ═══════════════════════════════════════
   MOBILE — comprehensive responsive fixes
   ═══════════════════════════════════════ */

/* ── Tablet: 768px ── */
@media(max-width:768px){
  .nk{display:none}
  /* Stats grid: 2 cols on tablet */
  .cbi{grid-template-columns:repeat(2,1fr);gap:1.25rem}
  /* All main 2/3-col grids collapse to 1 col */
  .pg,.ig,.mg,.ag{grid-template-columns:1fr}
  /* Forms stack vertically */
  .ef,.csw{flex-direction:column}
  /* Snapshot card padding */
  .eb{padding:2.5rem 1.5rem}
  /* How It Works steps */
  .sr{gap:1.25rem}
  .sn{font-size:2.2rem;min-width:40px}
  /* Heatmap: stack map + card */
  #hm-layout{grid-template-columns:1fr!important;}
  /* Compare counties selectors stack */
  #ccSelectors{flex-direction:column;align-items:stretch}
  #ccSelectors .cc-sel,#ccSelectors .cc-add{max-width:100%}
  /* Trust bar: smaller gaps */
  .trust-bar-inner{gap:1.25rem}
  .trust-divider{display:none}
  /* Blurred report preview: 1 col */
  div[style*="grid-template-columns:repeat(3,1fr)"][class*="fade-in"]{grid-template-columns:1fr!important}
  /* What's included checklist: 1 col */
  div[style*="grid-template-columns:1fr 1fr"][style*="gap:.75rem 2rem"]{grid-template-columns:1fr!important}
}

/* ── Mobile: 600px ── */
@media(max-width:600px){
  /* Section padding */
  section{padding:2.5rem 1.1rem!important}
  /* Hero */
  .hero{padding:5rem 1.25rem 2.5rem!important}
  .ht{font-size:clamp(2rem,8vw,2.8rem)!important}
  .hs{font-size:1rem!important}
  /* Headings */
  .sh h2{font-size:clamp(1.4rem,5.5vw,2rem)!important}
  h2{font-size:clamp(1.4rem,5.5vw,2.2rem)!important}
  /* All tables: horizontally scrollable */
  .rp-doc table,.itable,.cc-table,.rp-table{
    display:block;overflow-x:auto;
    -webkit-overflow-scrolling:touch;
    white-space:nowrap;
  }
  .rp-doc table thead,.itable thead,.cc-table thead{white-space:nowrap}
  /* Scroll hint label on tables */
  .rp-table-wrap,.cc-table-wrap,.rp-wrap{position:relative}
  /* Sample report browser: full width */
  .rp-browser{border-radius:10px}
  .rp-doc{padding:1.25rem 1rem}
  /* Report preview metrics: 2 cols */
  .rp-metrics{grid-template-columns:1fr 1fr!important}
  /* Micro-area search result rows: simpler layout */
  .mas-row{grid-template-columns:1fr auto auto!important;gap:.4rem}
  .mas-row .mr-growth,.mas-row>div:last-child{display:none}
  /* Snapshot comparison grid: stack */
  .eb>div[style*="grid-template-columns:1fr 1fr"]{grid-template-columns:1fr!important}
  /* Hero CTA buttons: stack */
  .hctas{flex-direction:column;align-items:center}
  .hctas a,.hctas button{width:100%;max-width:320px;justify-content:center;text-align:center}
  /* Stats: 2 per row */
  .cbi{grid-template-columns:1fr 1fr;gap:1rem}
  .cn{font-size:2rem}
  /* Value cards */
  .pg{gap:1rem}
  .pc{padding:1.5rem 1.25rem}
  /* How It Works */
  .sr{flex-direction:column;gap:.75rem;padding:1.5rem 0}
  .sn{font-size:1.8rem}
  /* Snap modal */
  #snapModal>div{padding:1.5rem 1.25rem!important;margin:.75rem}
  /* Exit popup */
  #exitPopupBox{padding:1.75rem 1.25rem}
  #exitPopupBox .ep-preview{grid-template-columns:1fr 1fr 1fr;gap:.4rem}
  #exitPopupBox .ep-card{padding:.5rem .35rem;font-size:.66rem}
  /* Compare counties table: allow scroll */
  #compare .cc-table-wrap{margin:0 -1.1rem;padding:0 1.1rem}
  /* Micro-area search */
  #masInput{font-size:.9rem;padding:.85rem 1rem .85rem 2.6rem}
  /* Trust bar */
  .trust-bar{padding:1.5rem 1rem}
  .trust-logo span{font-size:.68rem}
  /* Report preview page thumbnails: stack */
  div[style*="grid-template-columns:repeat(3,1fr)"][style*="gap:1.5rem"]{
    grid-template-columns:1fr!important
  }
  /* What's included checklist */
  div[style*="gap:.75rem 2rem"]{grid-template-columns:1fr!important}
  /* Sticky bar */
  #stickyCTA{padding:.5rem .9rem;gap:.5rem}
  #stickyCTA .sc-msg{font-size:.75rem}
  /* FAQ */
  .fqq{font-size:.95rem;cursor:pointer;}
  .fqa{font-size:.85rem}
  /* Methodology cards */
  .mg{gap:1rem}
  .mc{padding:1.25rem}
}

/* ── Small phones: 400px ── */
@media(max-width:400px){
  section{padding:2rem .9rem!important}
  .hero{padding:4.5rem .9rem 2rem!important}
  .ht{font-size:clamp(1.75rem,7vw,2.2rem)!important}
  .cn{font-size:1.75rem}
  .cbi{grid-template-columns:1fr 1fr;gap:.75rem}
  .rp-metrics{grid-template-columns:1fr 1fr!important;gap:.4rem!important}
  #exitPopupBox .ep-preview{grid-template-columns:1fr}
  .bp,.bs{font-size:.88rem;padding:.75rem 1.25rem}
  .sh{margin-bottom:2rem}
  .sh p{font-size:.88rem}
}
</style>
</head>
<body>
<!-- STICKY BAR -->
<div id="stickyCTA">
  <p class="sc-msg"><strong>IrishPropertyInsights</strong> &mdash; free micro-area data for every Irish county</p>
  <div class="sc-actions">
    <a href="#compare" class="bs" style="padding:.6rem 1.2rem;font-size:.85rem;">⚖ Compare</a>
    <a href="#snap" class="bp" style="padding:.6rem 1.2rem;font-size:.85rem;">Free Snapshot &rarr;</a>
    <a href="#reports" class="bs" style="padding:.6rem 1.2rem;font-size:.85rem;">Full Report &euro;29</a>
    <button class="sc-dismiss" onclick="var e=document.getElementById(&quot;stickyCTA&quot;);e.style.display=&quot;none&quot;;" title="Dismiss">&times;</button>
  </div>
</div>
<script>(function(){var b=document.getElementById("stickyCTA");window.addEventListener("scroll",function(){b.style.display!=="none"&&(window.scrollY>500?b.classList.add("visible"):b.classList.remove("visible"));},{passive:true});})();</script>

<!-- ── EXIT INTENT POPUP ── -->
<div id="exitPopup">
  <div id="exitPopupBox">
    <button class="ep-close" onclick="closeExitPopup()" title="Close">&times;</button>
    <div class="ep-badge">Wait — Free Offer</div>
    <h3>Before you go — get your free county snapshot</h3>
    <p>See the top 3 investment areas in any Irish county. No credit card, no commitment.</p>
    <div class="ep-preview">
      <div class="ep-card"><strong>Top 3</strong>Micro-areas ranked</div>
      <div class="ep-card"><strong>Yield</strong>Per area estimate</div>
      <div class="ep-card"><strong>Risk</strong>Low / Med / High</div>
    </div>
    <div class="ep-form">
      <select id="epCounty" class="ep-input" style="cursor:pointer;">
        <option value="" disabled selected>Select your county...</option>
        <option>Carlow</option><option>Cavan</option><option>Clare</option>
        <option>Cork</option><option>Donegal</option><option>Dublin</option>
        <option>Galway</option><option>Kerry</option><option>Kildare</option>
        <option>Kilkenny</option><option>Laois</option><option>Leitrim</option>
        <option>Limerick</option><option>Longford</option><option>Louth</option>
        <option>Mayo</option><option>Meath</option><option>Monaghan</option>
        <option>Offaly</option><option>Roscommon</option><option>Sligo</option>
        <option>Tipperary</option><option>Waterford</option><option>Westmeath</option>
        <option>Wexford</option><option>Wicklow</option>
      </select>
      <input type="email" id="epEmail" class="ep-input" placeholder="your@email.com" />
      <button class="bp" onclick="submitExitPopup()" style="justify-content:center;padding:1rem;font-size:1rem;">Get My Free Snapshot →</button>
    </div>
    <p style="font-size:.72rem;color:var(--t3);margin-top:.75rem;">🔒 No spam. Unsubscribe anytime. Your data is never sold.</p>
    <button class="ep-skip" onclick="closeExitPopup()">No thanks, I'll skip the free snapshot</button>
  </div>
</div>
<script>
(function(){
  var shown=false;
  // Only show once per session AND only if user has scrolled (engaged)
  var readyToShow=false;
  setTimeout(function(){readyToShow=true;},8000); // min 8s on page before eligible
  function show(){
    if(shown||!readyToShow)return;
    var dismissed=sessionStorage.getItem('exitDismissed');
    if(dismissed)return;
    shown=true;
    document.getElementById('exitPopup').classList.add('show');
  }
  // Desktop: mouse leaves viewport top
  document.addEventListener('mouseleave',function(e){
    if(e.clientY<=0) show();
  });
  // Mobile: after 60s if scrolled past hero
  var t=setTimeout(function(){
    if(window.scrollY>600) show();
  },60000);
  document.addEventListener('keydown',function(e){if(e.key==='Escape')closeExitPopup();});
})();
function closeExitPopup(){
  document.getElementById('exitPopup').classList.remove('show');
  sessionStorage.setItem('exitDismissed','1');
}
async function submitExitPopup(){
  var em=document.getElementById('epEmail').value;
  var co=document.getElementById('epCounty').value;
  if(!em||!em.includes('@')){showToast('Please enter a valid email.');return;}
  if(!co){showToast('Please select a county.');return;}
  try{
    await fetch('https://formspree.io/f/xdalrzrn',{method:'POST',
      headers:{'Content-Type':'application/json','Accept':'application/json'},
      body:JSON.stringify({email:em,county:co,type:'exit_intent_snapshot',message:'Exit intent snapshot: '+co+' by '+em})});
  }catch(e){}
  closeExitPopup();
  showToast('✓ Downloading your '+co+' snapshot...');
  setTimeout(function(){window.location.href='/snapshot?county='+encodeURIComponent(co);},600);
}
</script>

<nav><a href="#" class="nl">Irish<span>Property</span>Insights</a><span style="font-size:.68rem;color:var(--green);background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.2);padding:.25rem .75rem;border-radius:20px;font-weight:600;margin-left:.5rem;">🗓 RTB: Q2 2025 · PPR: Dec 2025 · Reports: Mar 2026</span><ul class="nk"><li><a href="#how">How It Works</a></li><li><a href="#who">Who It's For</a></li><li><a href="#compare">Compare Counties</a></li><li><a href="/methodology">Methodology</a></li><li><a href="#reports" class="nc">Get Report</a></li></ul></nav>

<!-- ── HERO ── -->
<section class="hero" style="padding:6rem 2rem 3rem;">
  <div style="max-width:1100px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;">

    <!-- LEFT: Text content -->
    <div>
      <!-- Badge -->
      <div style="display:inline-flex;align-items:center;gap:0.5rem;padding:0.4rem 1rem;background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.2);border-radius:100px;font-size:0.78rem;font-weight:600;color:var(--green);margin-bottom:1.75rem;">
        <span style="width:6px;height:6px;border-radius:50%;background:var(--green);animation:pulse 2s infinite;flex-shrink:0;"></span>
        Official PPR &amp; RTB data — 727,000 transactions
      </div>

      <!-- Headline -->
      <h1 style="font-family:var(--fd);font-size:clamp(2.2rem,4.5vw,3.8rem);font-weight:700;line-height:1.08;letter-spacing:-0.03em;margin-bottom:1.25rem;text-align:left;">
        Find the Most Profitable<br>Rental Areas in <em style="font-style:italic;color:var(--green);">Ireland</em>
      </h1>

      <!-- Sub-headline -->
      <p style="font-size:1.05rem;color:var(--t2);max-width:460px;margin:0 0 2rem;line-height:1.65;text-align:left;">
        Every micro-area across all 26 counties ranked by yield, growth &amp; risk — from official government data.
      </p>

      <!-- CTAs -->
      <div style="display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:1rem;">
        <a href="#snap" class="bp" style="font-size:1rem;padding:.9rem 2rem;">Get Free Snapshot →</a>
        <a href="#reports" class="bs" style="padding:.9rem 1.6rem;">Full Report — €29</a>
      </div>
      <p style="font-size:0.78rem;color:var(--t3);">No credit card · Based on 727,000+ verified transactions</p>

      <!-- Trust pills -->
      <div style="display:flex;gap:0.6rem;flex-wrap:wrap;margin-top:1.75rem;">
        <span style="padding:.35rem .8rem;background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.15);border-radius:6px;font-size:0.78rem;color:var(--green);font-weight:500;">✓ 500+ micro-areas</span>
        <span style="padding:.35rem .8rem;background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.15);border-radius:6px;font-size:0.78rem;color:var(--green);font-weight:500;">✓ All 26 counties</span>
        <span style="padding:.35rem .8rem;background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.15);border-radius:6px;font-size:0.78rem;color:var(--green);font-weight:500;">✓ Official data only</span>
        <span style="padding:.35rem .8rem;background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.15);border-radius:6px;font-size:0.78rem;color:var(--green);font-weight:500;">🗓 Updated Q2 2025</span>
      </div>
    </div>

    <!-- RIGHT: Blurred report preview -->
    <div style="position:relative;">
      <div style="background:var(--card);border:1px solid var(--border);border-radius:16px;overflow:hidden;box-shadow:0 25px 60px rgba(0,0,0,.5);">
        <!-- Report header -->
        <div style="background:var(--bg2);padding:1.25rem 1.5rem;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;">
          <div>
            <div style="font-size:.7rem;color:var(--green);font-weight:700;text-transform:uppercase;letter-spacing:.08em;margin-bottom:.2rem;">Dublin County Report</div>
            <div style="font-size:.75rem;color:var(--t3);">Updated with RTB Q2 2025 data</div>
          </div>
          <div style="background:var(--green);color:#0b1120;font-size:.65rem;font-weight:800;padding:.25rem .6rem;border-radius:20px;">PDF</div>
        </div>
        <!-- Metrics row -->
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0;border-bottom:1px solid var(--border);">
          <div style="padding:.9rem .75rem;text-align:center;border-right:1px solid var(--border);">
            <div style="font-size:1rem;font-weight:700;color:var(--t1);">€484k</div>
            <div style="font-size:.62rem;color:var(--t3);">Median Price</div>
          </div>
          <div style="padding:.9rem .75rem;text-align:center;border-right:1px solid var(--border);">
            <div style="font-size:1rem;font-weight:700;color:var(--green);">5.5%</div>
            <div style="font-size:.62rem;color:var(--t3);">County Yield</div>
          </div>
          <div style="padding:.9rem .75rem;text-align:center;border-right:1px solid var(--border);">
            <div style="font-size:1rem;font-weight:700;color:var(--green);">+5.3%</div>
            <div style="font-size:.62rem;color:var(--t3);">5yr Growth</div>
          </div>
          <div style="padding:.9rem .75rem;text-align:center;">
            <div style="font-size:1rem;font-weight:700;color:var(--t1);">415</div>
            <div style="font-size:.62rem;color:var(--t3);">Areas Scored</div>
          </div>
        </div>
        <!-- Top areas preview -->
        <div style="padding:1rem 1.5rem;">
          <div style="font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--t3);margin-bottom:.75rem;">Top Micro-Areas by Yield</div>
          <div style="display:flex;flex-direction:column;gap:.5rem;">
            <div style="display:flex;align-items:center;justify-content:space-between;font-size:.8rem;">
              <span style="color:var(--t2);">Snugborough Rd D15</span>
              <span style="color:var(--green);font-weight:700;">13.6%</span>
            </div>
            <div style="display:flex;align-items:center;justify-content:space-between;font-size:.8rem;">
              <span style="color:var(--t2);">Ballymun Dublin 11</span>
              <span style="color:var(--green);font-weight:700;">13.2%</span>
            </div>
            <div style="display:flex;align-items:center;justify-content:space-between;font-size:.8rem;">
              <span style="color:var(--t2);">Clondalkin Dublin 22</span>
              <span style="color:var(--green);font-weight:700;">11.9%</span>
            </div>
            <!-- Blurred rows -->
            <div style="filter:blur(5px);pointer-events:none;display:flex;flex-direction:column;gap:.5rem;">
              <div style="display:flex;align-items:center;justify-content:space-between;font-size:.8rem;">
                <span style="color:var(--t2);">████████████ D9</span>
                <span style="color:var(--green);font-weight:700;">11.1%</span>
              </div>
              <div style="display:flex;align-items:center;justify-content:space-between;font-size:.8rem;">
                <span style="color:var(--t2);">████████████ D22</span>
                <span style="color:var(--green);font-weight:700;">10.8%</span>
              </div>
              <div style="display:flex;align-items:center;justify-content:space-between;font-size:.8rem;">
                <span style="color:var(--t2);">████████████ D11</span>
                <span style="color:var(--green);font-weight:700;">10.4%</span>
              </div>
            </div>
          </div>
          <div style="margin-top:.75rem;padding:.6rem;background:rgba(16,185,129,.06);border:1px solid rgba(16,185,129,.15);border-radius:8px;text-align:center;font-size:.72rem;color:var(--green);font-weight:600;">+ 409 more areas in full report</div>
        </div>
      </div>
      <!-- Floating badge -->
      <div style="position:absolute;top:-12px;right:-12px;background:var(--green);color:#0b1120;font-size:.7rem;font-weight:800;padding:.4rem .9rem;border-radius:20px;box-shadow:0 4px 12px rgba(16,185,129,.4);">€29 Full Report</div>
    </div>

  </div>
</section>
<style>
@media(max-width:768px){
  section.hero > div[style*="grid-template-columns:1fr 1fr"]{
    grid-template-columns:1fr !important;
  }
  section.hero > div > div:last-child{display:none;}
}
</style>

<!-- ── STATS BAR ── -->
<div class="cb">
  <div class="cbi">
    <div class="ci"><div class="cn">727k</div><div class="cl">PPR Transactions</div></div>
    <div class="ci"><div class="cn">15yr</div><div class="cl">Price History</div></div>
    <div class="ci"><div class="cn">500+</div><div class="cl">Micro-Areas Scored</div></div>
    <div class="ci"><div class="cn">€29</div><div class="cl">Full County Report</div></div>
  </div>
  <p style="text-align:center;font-size:.8rem;color:var(--t3);margin-top:1.5rem;font-weight:500;">
    Data source: <a href="https://www.propertypriceregister.ie" target="_blank" style="color:var(--t2);text-decoration:none;">Property Price Register</a> &amp; <a href="https://www.rtb.ie" target="_blank" style="color:var(--t2);text-decoration:none;">Residential Tenancies Board</a> — official Irish government records.
  </p>
</div>

<!-- ── TRUST BAR ── -->
<div class="trust-bar">
  <div class="trust-bar-inner">
    <span style="font-size:.72rem;font-weight:600;color:var(--t3);letter-spacing:.08em;text-transform:uppercase;white-space:nowrap;">Data sourced from</span>
    <div class="trust-divider"></div>
    <!-- PPR logo -->
    <a href="https://www.propertypriceregister.ie" target="_blank" class="trust-logo" style="text-decoration:none;">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="24" height="24" rx="4" fill="#1A4D8F"/><path d="M4 20V10l8-6 8 6v10H15v-6h-6v6H4z" fill="white"/></svg>
      <span>Property Price Register</span>
    </a>
    <div class="trust-divider"></div>
    <!-- RTB logo -->
    <a href="https://www.rtb.ie" target="_blank" class="trust-logo" style="text-decoration:none;">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="24" height="24" rx="4" fill="#006747"/><text x="3" y="16" font-size="9" fill="white" font-weight="bold" font-family="sans-serif">RTB</text></svg>
      <span>Residential Tenancies Board</span>
    </a>
    <div class="trust-divider"></div>
    <!-- Gov.ie -->
    <a href="https://www.gov.ie" target="_blank" class="trust-logo" style="text-decoration:none;">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="24" height="24" rx="4" fill="#169B62"/><text x="3" y="16" font-size="7.5" fill="white" font-weight="bold" font-family="sans-serif">GOV</text></svg>
      <span>Irish Government Data</span>
    </a>
    <div class="trust-used-by">Trusted by landlords, mortgage advisors &amp; buy-to-let investors across Ireland</div>
  </div>
</div>

<!-- ── COMMUNITY PROOF ── -->
<section style="padding:3.5rem 2rem;background:var(--bg2);border-top:1px solid var(--border);border-bottom:1px solid var(--border);">
  <div style="max-width:1000px;margin:0 auto;">

    <!-- Reach stats bar -->
    <div style="text-align:center;margin-bottom:2.5rem;">
      <div style="font-size:.75rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--green);margin-bottom:.75rem;">Discussed Across the Irish Property Community</div>
      <div style="display:flex;justify-content:center;gap:2.5rem;flex-wrap:wrap;margin-bottom:1rem;">
        <div style="text-align:center;">
          <div style="font-family:var(--fd);font-size:2rem;font-weight:700;color:var(--t1);">37K+</div>
          <div style="font-size:.78rem;color:var(--t3);">Reddit views</div>
        </div>
        <div style="text-align:center;">
          <div style="font-family:var(--fd);font-size:2rem;font-weight:700;color:var(--t1);">2</div>
          <div style="font-size:.78rem;color:var(--t3);">Active threads</div>
        </div>
        <div style="text-align:center;">
          <div style="font-family:var(--fd);font-size:2rem;font-weight:700;color:var(--t1);">55+</div>
          <div style="font-size:.78rem;color:var(--t3);">Comments & questions</div>
        </div>
      </div>
      <div style="display:flex;justify-content:center;gap:.75rem;flex-wrap:wrap;">
        <span style="font-size:.75rem;color:var(--t3);background:var(--card);border:1px solid var(--border);padding:.3rem .8rem;border-radius:20px;">r/irishpersonalfinance · 31K views</span>
        <span style="font-size:.75rem;color:var(--t3);background:var(--card);border:1px solid var(--border);padding:.3rem .8rem;border-radius:20px;">r/HousingIreland · 6.8K views</span>
      </div>
    </div>

    <!-- Community quotes — third party only -->
    <div style="margin-bottom:1rem;font-size:.78rem;font-weight:600;color:var(--t3);text-transform:uppercase;letter-spacing:.08em;text-align:center;">What the community said about micro-area data analysis</div>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1.25rem;">

      <div style="background:var(--card);border:1px solid var(--border);border-radius:14px;padding:1.4rem;border-left:3px solid var(--green);">
        <p style="font-size:.88rem;color:var(--t2);line-height:1.65;margin-bottom:1rem;">"Interesting find! It's wild how some overlooked areas can really yield better returns than the fancy D4."</p>
        <div style="font-size:.75rem;color:var(--t3);">krystvey · r/irishpersonalfinance</div>
      </div>

      <div style="background:var(--card);border:1px solid var(--border);border-radius:14px;padding:1.4rem;border-left:3px solid var(--green);">
        <p style="font-size:.88rem;color:var(--t2);line-height:1.65;margin-bottom:1rem;">"I got a 9.8% yield buying in D2 and then a +50% capital gain increase on sale in less than 4.5 years. The management fees was lower than LPT."</p>
        <div style="font-size:.75rem;color:var(--t3);">Professional_Elk_483 · r/irishpersonalfinance</div>
      </div>

      <div style="background:var(--card);border:1px solid var(--border);border-radius:14px;padding:1.4rem;border-left:3px solid var(--green);">
        <p style="font-size:.88rem;color:var(--t2);line-height:1.65;margin-bottom:1rem;">"100%, yield reflects risk so makes perfect sense."</p>
        <div style="font-size:.75rem;color:var(--t3);">ZealousidealFloor2 · r/irishpersonalfinance</div>
      </div>

      <div style="background:var(--card);border:1px solid var(--border);border-radius:14px;padding:1.4rem;border-left:3px solid var(--green);">
        <p style="font-size:.88rem;color:var(--t2);line-height:1.65;margin-bottom:1rem;">"I'm not surprised by that at all. It's a risk reward point. In a recession the outer areas will swing down more as well. It's the classic example that you pay more for less risk."</p>
        <div style="font-size:.75rem;color:var(--t3);">commodoredundrum · r/irishpersonalfinance · 38 upvotes</div>
      </div>

      <div style="background:var(--card);border:1px solid var(--border);border-radius:14px;padding:1.4rem;border-left:3px solid var(--green);">
        <p style="font-size:.88rem;color:var(--t2);line-height:1.65;margin-bottom:1rem;">"You buy in D4 for the opportunities not the rental yield. Instead of one 1 million euro house you just buy 9 apartments in Finglas and lease them out."</p>
        <div style="font-size:.75rem;color:var(--t3);">Bog_warrior · r/irishpersonalfinance · 5 upvotes</div>
      </div>

      <div style="background:var(--card);border:1px solid var(--border);border-radius:14px;padding:1.4rem;border-left:3px solid var(--green);">
        <p style="font-size:.88rem;color:var(--t2);line-height:1.65;margin-bottom:1rem;">"I think there's something to this. My wife and I have bought and sold twice in D4 — a big part of our choice was avoiding price depreciation as opposed to maximising growth."</p>
        <div style="font-size:.75rem;color:var(--t3);">fencing123 · r/irishpersonalfinance · 8 upvotes</div>
      </div>

    </div>
    <p style="text-align:center;margin-top:1.5rem;font-size:.78rem;color:var(--t3);">Comments are from public Reddit threads discussing Irish property micro-area data analysis.</p>
  </div>
</section>



<!-- Add responsive style for the 3-card grid -->
<style>
@media(max-width:540px){
  div[style*="grid-template-columns:repeat(3,1fr)"].hc > div,
  .hc div[style*="grid-template-columns:repeat(3,1fr)"]{
    grid-template-columns:1fr !important;
  }
}
</style>

<section id="how"><div class="sh fade-in"><div class="ol">How It Works</div><h2>How we turn 15 years of raw data into clear investment signals</h2></div><div class="sg fade-in"><div class="sr"><div class="sn">01</div><div class="st"><h3>We ingest 15 years of PPR transactions</h3><p>Every residential property sale registered in Ireland since 2010, cleaned and normalised.</p></div></div><div class="sr"><div class="sn">02</div><div class="st"><h3>Cross-reference with RTB rental data</h3><p>Official Q2 2025 rent figures mapped to micro-areas for yield calculation.</p></div></div><div class="sr"><div class="sn">03</div><div class="st"><h3>Score every micro-area on 3 dimensions</h3><p>Growth trajectory, risk profile, and rental yield — combined into a clear investment signal.</p></div></div><div class="sr"><div class="sn">04</div><div class="st"><h3>Delivered instantly as a detailed PDF report</h3><p>County-by-county intelligence you can read, share, or use to brief your mortgage advisor.</p></div></div></div></section>
<section style="padding:5rem 2rem;background:var(--bg2)" id="sample">
<div class="sh fade-in" style="margin-bottom:3rem">
  

<!-- ── HEATMAP SECTION ── -->
<section style="background:#0a0c0f;padding:4rem 2rem;border-top:1px solid #1a1c20;">
  <div style="max-width:1100px;margin:0 auto;">

    <!-- Header -->
    <div style="text-align:center;margin-bottom:2rem;">
      <div style="display:inline-block;font-size:0.7rem;font-weight:500;letter-spacing:0.18em;text-transform:uppercase;color:#c9a84c;border:1px solid #c9a84c;padding:0.3rem 0.8rem;border-radius:2px;margin-bottom:1rem;">Interactive Map</div>
      <div style="display:flex;gap:.6rem;flex-wrap:wrap;justify-content:center;margin-bottom:1.25rem;">
        <span style="display:flex;align-items:center;gap:.35rem;font-size:.72rem;color:var(--t2);"><span style="width:12px;height:12px;border-radius:2px;background:#10b981;flex-shrink:0;"></span>Strong Buy</span>
        <span style="display:flex;align-items:center;gap:.35rem;font-size:.72rem;color:var(--t2);"><span style="width:12px;height:12px;border-radius:2px;background:#3b82f6;flex-shrink:0;"></span>High Potential</span>
        <span style="display:flex;align-items:center;gap:.35rem;font-size:.72rem;color:var(--t2);"><span style="width:12px;height:12px;border-radius:2px;background:#f59e0b;flex-shrink:0;"></span>Moderate</span>
        <span style="display:flex;align-items:center;gap:.35rem;font-size:.72rem;color:var(--t2);"><span style="width:12px;height:12px;border-radius:2px;background:#6b7280;flex-shrink:0;"></span>Data Loading</span>
      </div>
      <h2 style="font-family:'Playfair Display',serif;font-size:clamp(1.5rem,3vw,2.2rem);font-weight:900;color:white;line-height:1.1;margin-bottom:0.6rem;">Irish Property Investment Heatmap</h2>
      <p style="color:#9a9690;font-size:0.9rem;font-weight:300;max-width:480px;margin:0 auto;">Click any county to see yield, growth and risk. Full micro-area rankings in the report.</p>
    </div>

    <!-- Metric toggle -->
    <div style="display:flex;justify-content:center;margin-bottom:2rem;">
      <div style="display:flex;background:#1a1c20;border:1px solid #2a2c30;border-radius:3px;padding:0.25rem;">
        <button onclick="setMetric('yield',this)" class="hm-btn active-btn" style="padding:0.45rem 1.2rem;border:none;border-radius:2px;font-family:inherit;font-size:0.75rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;cursor:pointer;background:#c9a84c;color:#0f1014;transition:all 0.2s;">Rental Yield</button>
        <button onclick="setMetric('growth',this)" class="hm-btn" style="padding:0.45rem 1.2rem;border:none;border-radius:2px;font-family:inherit;font-size:0.75rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;cursor:pointer;background:transparent;color:#6b6860;transition:all 0.2s;">5yr Growth</button>
        <button onclick="setMetric('risk',this)" class="hm-btn" style="padding:0.45rem 1.2rem;border:none;border-radius:2px;font-family:inherit;font-size:0.75rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;cursor:pointer;background:transparent;color:#6b6860;transition:all 0.2s;">Risk Score</button>
      </div>
    </div>

    <!-- Map + Sidebar grid -->
    <div id="hm-layout" style="display:grid;grid-template-columns:1fr 280px;gap:2rem;align-items:start;">

      <!-- MAP PANEL -->
      <div style="background:#111316;border:1px solid #1a1c20;border-radius:4px;padding:1.5rem;display:flex;align-items:center;justify-content:center;">
        <svg id="hm-svg" viewBox="0 0 320 340" xmlns="http://www.w3.org/2000/svg"
             style="width:100%;height:auto;display:block;max-height:600px;">

          <!-- DONEGAL -->
          <path id="hm-Donegal"   onclick="hmSel('Donegal')"   class="hmc" d="M55,15 L130,8 L165,22 L172,48 L152,68 L128,82 L98,74 L68,54 L50,36 Z"/>
          <!-- MAYO -->
          <path id="hm-Mayo"      onclick="hmSel('Mayo')"      class="hmc" d="M15,88 L60,75 L88,70 L98,93 L82,113 L65,108 L50,128 L24,136 L10,118 Z"/>
          <!-- SLIGO -->
          <path id="hm-Sligo"     onclick="hmSel('Sligo')"     class="hmc" d="M78,75 L108,68 L122,80 L124,96 L106,106 L84,104 L70,92 Z"/>
          <!-- LEITRIM -->
          <path id="hm-Leitrim"   onclick="hmSel('Leitrim')"   class="hmc" d="M122,68 L148,62 L162,76 L158,98 L140,108 L124,106 L122,92 Z"/>
          <!-- CAVAN -->
          <path id="hm-Cavan"     onclick="hmSel('Cavan')"     class="hmc" d="M158,65 L192,58 L208,72 L206,94 L186,102 L164,98 L158,82 Z"/>
          <!-- MONAGHAN -->
          <path id="hm-Monaghan"  onclick="hmSel('Monaghan')"  class="hmc" d="M208,62 L238,56 L252,72 L246,90 L222,94 L206,86 Z"/>
          <!-- LOUTH -->
          <path id="hm-Louth"     onclick="hmSel('Louth')"     class="hmc" d="M246,66 L272,62 L284,82 L272,102 L248,102 L236,88 Z"/>
          <!-- ROSCOMMON -->
          <path id="hm-Roscommon" onclick="hmSel('Roscommon')" class="hmc" d="M96,113 L126,106 L144,116 L140,140 L122,150 L100,148 L88,134 Z"/>
          <!-- LONGFORD -->
          <path id="hm-Longford"  onclick="hmSel('Longford')"  class="hmc" d="M148,98 L174,94 L184,108 L180,126 L160,132 L144,122 Z"/>
          <!-- WESTMEATH -->
          <path id="hm-Westmeath" onclick="hmSel('Westmeath')" class="hmc" d="M174,94 L204,90 L218,104 L214,122 L194,130 L176,124 L180,108 Z"/>
          <!-- MEATH -->
          <path id="hm-Meath"     onclick="hmSel('Meath')"     class="hmc" d="M206,92 L238,88 L256,104 L250,130 L226,136 L206,128 L206,108 Z"/>
          <!-- DUBLIN -->
          <path id="hm-Dublin"    onclick="hmSel('Dublin')"    class="hmc" d="M256,100 L286,94 L300,116 L292,142 L266,148 L250,134 Z"/>
          <!-- GALWAY -->
          <path id="hm-Galway"    onclick="hmSel('Galway')"    class="hmc" d="M14,146 L52,136 L80,126 L94,138 L90,162 L72,178 L46,180 L18,166 Z"/>
          <!-- OFFALY -->
          <path id="hm-Offaly"    onclick="hmSel('Offaly')"    class="hmc" d="M148,132 L180,126 L194,140 L190,156 L166,162 L148,154 Z"/>
          <!-- KILDARE -->
          <path id="hm-Kildare"   onclick="hmSel('Kildare')"   class="hmc" d="M214,128 L246,124 L260,142 L252,164 L228,168 L212,154 Z"/>
          <!-- WICKLOW -->
          <path id="hm-Wicklow"   onclick="hmSel('Wicklow')"   class="hmc" d="M266,144 L296,138 L308,158 L300,182 L276,190 L258,176 Z"/>
          <!-- LAOIS -->
          <path id="hm-Laois"     onclick="hmSel('Laois')"     class="hmc" d="M176,158 L208,152 L220,166 L214,184 L192,190 L174,182 Z"/>
          <!-- CLARE -->
          <path id="hm-Clare"     onclick="hmSel('Clare')"     class="hmc" d="M46,184 L76,176 L94,164 L108,174 L112,192 L100,210 L76,216 L50,206 Z"/>
          <!-- TIPPERARY -->
          <path id="hm-Tipperary" onclick="hmSel('Tipperary')" class="hmc" d="M108,174 L140,168 L164,172 L178,190 L170,212 L150,220 L124,216 L108,202 Z"/>
          <!-- CARLOW -->
          <path id="hm-Carlow"    onclick="hmSel('Carlow')"    class="hmc" d="M214,182 L238,178 L248,194 L240,210 L220,212 L210,198 Z"/>
          <!-- KILKENNY -->
          <path id="hm-Kilkenny"  onclick="hmSel('Kilkenny')"  class="hmc" d="M176,206 L208,200 L224,212 L220,232 L200,240 L176,232 Z"/>
          <!-- LIMERICK -->
          <path id="hm-Limerick"  onclick="hmSel('Limerick')"  class="hmc" d="M74,224 L108,216 L130,220 L140,238 L128,254 L104,260 L78,250 L68,238 Z"/>
          <!-- WATERFORD -->
          <path id="hm-Waterford" onclick="hmSel('Waterford')" class="hmc" d="M150,224 L180,216 L202,222 L206,240 L188,254 L162,258 L146,244 Z"/>
          <!-- WEXFORD -->
          <path id="hm-Wexford"   onclick="hmSel('Wexford')"   class="hmc" d="M206,236 L234,228 L250,244 L246,268 L222,274 L200,262 L200,244 Z"/>
          <!-- KERRY -->
          <path id="hm-Kerry"     onclick="hmSel('Kerry')"     class="hmc" d="M34,258 L68,250 L80,268 L74,294 L52,308 L28,304 L16,282 L22,264 Z"/>
          <!-- CORK -->
          <path id="hm-Cork"      onclick="hmSel('Cork')"      class="hmc" d="M80,264 L118,256 L150,260 L168,270 L170,292 L156,308 L124,318 L92,314 L68,300 L66,278 Z"/>

          <!-- LABELS -->
          <text x="108" y="46"  font-size="9"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none" font-weight="600">Donegal</text>
          <text x="50"  y="108" font-size="8"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none" font-weight="600">Mayo</text>
          <text x="98"  y="90"  font-size="7"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Sligo</text>
          <text x="140" y="88"  font-size="6.5" fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Leitrim</text>
          <text x="182" y="84"  font-size="7"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Cavan</text>
          <text x="226" y="78"  font-size="7"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Monaghan</text>
          <text x="260" y="86"  font-size="7"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Louth</text>
          <text x="116" y="132" font-size="7"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Roscommon</text>
          <text x="162" y="116" font-size="6.5" fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Longford</text>
          <text x="196" y="112" font-size="7"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Westmeath</text>
          <text x="230" y="114" font-size="7.5" fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Meath</text>
          <text x="274" y="122" font-size="8"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Dublin</text>
          <text x="52"  y="156" font-size="8"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Galway</text>
          <text x="168" y="146" font-size="7"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Offaly</text>
          <text x="234" y="148" font-size="7"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Kildare</text>
          <text x="282" y="164" font-size="7"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Wicklow</text>
          <text x="196" y="172" font-size="7"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Laois</text>
          <text x="80"  y="196" font-size="7.5" fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Clare</text>
          <text x="140" y="196" font-size="8"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Tipperary</text>
          <text x="228" y="198" font-size="6.5" fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Carlow</text>
          <text x="198" y="220" font-size="7"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Kilkenny</text>
          <text x="104" y="238" font-size="7.5" fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Limerick</text>
          <text x="176" y="238" font-size="7"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Waterford</text>
          <text x="222" y="252" font-size="7"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Wexford</text>
          <text x="46"  y="280" font-size="8"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Kerry</text>
          <text x="118" y="286" font-size="9"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Cork</text>
        </svg>
      </div>

      <!-- SIDEBAR -->
      <div style="display:flex;flex-direction:column;gap:1rem;">
        <!-- Info card -->
        <div id="hm-info" style="background:#1a1c20;border:1px solid #2a2c30;border-radius:4px;padding:2rem;text-align:center;color:#4a4845;font-size:0.85rem;line-height:1.7;">
          <div style="font-size:2rem;margin-bottom:0.5rem;">🗺️</div>
          Click any county on the map to see its investment data
        </div>
        <!-- Legend -->
        <div style="background:#1a1c20;border:1px solid #2a2c30;border-radius:4px;padding:1rem;">
          <div style="font-size:0.65rem;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;margin-bottom:0.5rem;" id="hm-leg-title">Rental Yield</div>
          <div style="height:6px;border-radius:2px;background:linear-gradient(to right,#0d3d22,#1a6b3c,#c9a84c,#d4821a,#c0392b);margin-bottom:0.4rem;"></div>
          <div style="display:flex;justify-content:space-between;font-size:0.65rem;color:#4a4845;">
            <span id="hm-leg-lo">Low (3%)</span><span id="hm-leg-hi">High (8%+)</span>
          </div>
        </div>
        <!-- Rankings -->
        <div style="background:#1a1c20;border:1px solid #2a2c30;border-radius:4px;overflow:hidden;">
          <div style="padding:0.6rem 1rem;font-size:0.65rem;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;border-bottom:1px solid #2a2c30;" id="hm-rank-title">Top Counties by Yield</div>
          <div id="hm-rank-list"></div>
        </div>
      </div>
    </div><!-- end grid -->
  </div>
</section>

<style>
.hmc{stroke:#111316;stroke-width:1;cursor:pointer;transition:filter 0.12s,stroke 0.12s,stroke-width 0.12s;}
.hmc:hover{filter:brightness(1.35);stroke:white;stroke-width:2;}
.hmc.hm-sel{stroke:white;stroke-width:2.5;filter:brightness(1.4);}
.hm-btn{transition:background 0.2s,color 0.2s;}
@media(max-width:720px){
  #hm-layout{grid-template-columns:1fr !important;}
}
</style>

<script>
const hmD={
  Dublin:{yield:5.5,growth:5.3,risk:'Medium',signal:'HIGH POTENTIAL',price:484581,rpz:true},
  Cork:{yield:5.1,growth:6.2,risk:'Low',signal:'HIGH POTENTIAL',price:320000,rpz:true},
  Galway:{yield:4.8,growth:5.8,risk:'Low',signal:'HIGH POTENTIAL',price:285000,rpz:true},
  Kildare:{yield:4.2,growth:6.8,risk:'Low',signal:'HIGH POTENTIAL',price:355000,rpz:true},
  Meath:{yield:4.5,growth:7.1,risk:'Low',signal:'HIGH POTENTIAL',price:320000,rpz:true},
  Wicklow:{yield:3.9,growth:5.5,risk:'Low',signal:'MODERATE',price:380000,rpz:true},
  Limerick:{yield:5.4,growth:6.9,risk:'Low',signal:'HIGH POTENTIAL',price:245000,rpz:true},
  Waterford:{yield:5.2,growth:5.1,risk:'Medium',signal:'HIGH POTENTIAL',price:220000,rpz:true},
  Louth:{yield:5.0,growth:7.1,risk:'Low',signal:'HIGH POTENTIAL',price:235000,rpz:true},
  Wexford:{yield:4.6,growth:6.3,risk:'Low',signal:'HIGH POTENTIAL',price:210000,rpz:false},
  Kilkenny:{yield:4.4,growth:5.8,risk:'Low',signal:'MODERATE',price:230000,rpz:false},
  Tipperary:{yield:5.8,growth:4.2,risk:'Medium',signal:'MODERATE',price:175000,rpz:false},
  Clare:{yield:5.3,growth:5.6,risk:'Low',signal:'HIGH POTENTIAL',price:195000,rpz:true},
  Kerry:{yield:4.9,growth:6.1,risk:'Medium',signal:'HIGH POTENTIAL',price:215000,rpz:false},
  Mayo:{yield:6.2,growth:3.8,risk:'Medium',signal:'MODERATE',price:145000,rpz:false},
  Sligo:{yield:5.9,growth:4.1,risk:'Medium',signal:'MODERATE',price:155000,rpz:false},
  Donegal:{yield:6.5,growth:3.5,risk:'High',signal:'MODERATE',price:125000,rpz:false},
  Roscommon:{yield:6.8,growth:3.2,risk:'High',signal:'AVOID',price:115000,rpz:false},
  Laois:{yield:5.1,growth:5.9,risk:'Low',signal:'HIGH POTENTIAL',price:185000,rpz:true},
  Offaly:{yield:5.3,growth:5.2,risk:'Medium',signal:'MODERATE',price:165000,rpz:true},
  Westmeath:{yield:5.0,growth:5.4,risk:'Low',signal:'HIGH POTENTIAL',price:175000,rpz:true},
  Longford:{yield:7.1,growth:2.8,risk:'High',signal:'AVOID',price:95000,rpz:false},
  Cavan:{yield:6.1,growth:3.6,risk:'High',signal:'AVOID',price:130000,rpz:false},
  Monaghan:{yield:5.7,growth:4.0,risk:'Medium',signal:'MODERATE',price:140000,rpz:false},
  Carlow:{yield:5.2,growth:6.1,risk:'Low',signal:'HIGH POTENTIAL',price:190000,rpz:true},
  Leitrim:{yield:7.8,growth:2.5,risk:'High',signal:'AVOID',price:85000,rpz:false}
};

let hmM='yield', hmS=null;

function hmClr(n,m){
  const d=hmD[n]; if(!d) return'#1a1c20';
  if(m==='yield'){const v=d.yield;if(v>=7)return'#c0392b';if(v>=6)return'#d4821a';if(v>=5.5)return'#b8962e';if(v>=5)return'#2d8a5e';if(v>=4)return'#1a6b3c';return'#0d3d22';}
  if(m==='growth'){const v=d.growth;if(v>=7)return'#1a6b3c';if(v>=6)return'#2d8a5e';if(v>=5)return'#b8962e';if(v>=4)return'#d4821a';return'#c0392b';}
  if(d.risk==='Low')return'#1a6b3c';if(d.risk==='Medium')return'#b8962e';return'#c0392b';
}

function hmPaint(){
  Object.keys(hmD).forEach(n=>{const e=document.getElementById('hm-'+n);if(e)e.style.fill=hmClr(n,hmM);});
}

function setMetric(m,btn){
  hmM=m;
  document.querySelectorAll('.hm-btn').forEach(b=>{b.style.background='transparent';b.style.color='#6b6860';});
  btn.style.background='#c9a84c'; btn.style.color='#0f1014';
  const lt={yield:'Rental Yield',growth:'5yr Growth',risk:'Risk Score'};
  const lo={yield:'Low (3%)',growth:'Low (2%)',risk:'Low Risk'};
  const hi={yield:'High (8%+)',growth:'High (7%+)',risk:'High Risk'};
  document.getElementById('hm-leg-title').textContent=lt[m];
  document.getElementById('hm-leg-lo').textContent=lo[m];
  document.getElementById('hm-leg-hi').textContent=hi[m];
  document.getElementById('hm-rank-title').textContent=m==='yield'?'Top Counties by Yield':m==='growth'?'Top Counties by Growth':'Lowest Risk Counties';
  hmPaint(); hmRank(); if(hmS) hmCard(hmS);
}

function hmSel(n){
  document.querySelectorAll('.hmc').forEach(e=>e.classList.remove('hm-sel'));
  const el=document.getElementById('hm-'+n); if(el) el.classList.add('hm-sel');
  hmS=n; hmCard(n);
  document.querySelectorAll('.hm-ri').forEach(i=>i.style.background=i.dataset.c===n?'#22252a':'transparent');
}

function hmCard(n){
  const d=hmD[n]; if(!d) return;
  const sc=d.signal==='HIGH POTENTIAL'?'background:rgba(26,107,60,0.3);color:#4ade80':
           d.signal==='MODERATE'?'background:rgba(201,168,76,0.2);color:#c9a84c':
           'background:rgba(192,57,43,0.2);color:#ef4444';
  const gc=d.growth>=6?'#4ade80':d.growth>=4?'#c9a84c':'#ef4444';
  const yc=d.yield>=5?'#4ade80':d.yield>=4?'#c9a84c':'#ef4444';
  const rc=d.risk==='Low'?'#4ade80':d.risk==='Medium'?'#c9a84c':'#ef4444';
  const has=['Dublin','Cork','Galway','Kildare','Kerry','Meath','Wicklow'].includes(n);
  const cta=has
    ?`<a href="/#reports" style="display:block;text-align:center;padding:0.65rem;background:#c9a84c;color:#0f1014;border-radius:3px;font-size:0.72rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;text-decoration:none;margin-top:0.8rem;">Unlock All Micro-Areas in ${n} — €29 →</a>`
    :`<a href="/#snap" style="display:block;text-align:center;padding:0.65rem;background:#1a1c20;color:#9a9690;border:1px solid #2a2c30;border-radius:3px;font-size:0.72rem;font-weight:500;text-decoration:none;margin-top:0.8rem;">Get Free ${n} Snapshot →</a>`;
  document.getElementById('hm-info').innerHTML=`
    <div style="padding:0.9rem 1rem 0.7rem;border-bottom:1px solid #2a2c30;text-align:left;">
      <div style="font-family:'Playfair Display',serif;font-size:1.2rem;font-weight:700;color:white;">${n}</div>
      <div style="display:inline-block;font-size:0.6rem;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;padding:0.2rem 0.5rem;border-radius:2px;margin-top:0.3rem;${sc};">${d.signal}</div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;">
      <div style="padding:0.7rem 1rem;border-right:1px solid #2a2c30;border-bottom:1px solid #2a2c30;text-align:left;">
        <div style="font-size:0.6rem;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;margin-bottom:0.2rem;">Gross Yield</div>
        <div style="font-family:'Playfair Display',serif;font-size:1.1rem;font-weight:700;color:${yc};">${d.yield}%</div>
      </div>
      <div style="padding:0.7rem 1rem;border-bottom:1px solid #2a2c30;text-align:left;">
        <div style="font-size:0.6rem;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;margin-bottom:0.2rem;">5yr Growth</div>
        <div style="font-family:'Playfair Display',serif;font-size:1.1rem;font-weight:700;color:${gc};">+${d.growth}%</div>
      </div>
      <div style="padding:0.7rem 1rem;border-right:1px solid #2a2c30;text-align:left;">
        <div style="font-size:0.6rem;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;margin-bottom:0.2rem;">Risk</div>
        <div style="font-family:'Playfair Display',serif;font-size:1.1rem;font-weight:700;color:${rc};">${d.risk}</div>
      </div>
      <div style="padding:0.7rem 1rem;text-align:left;">
        <div style="font-size:0.6rem;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;margin-bottom:0.2rem;">Median Price</div>
        <div style="font-family:'Playfair Display',serif;font-size:1.1rem;font-weight:700;color:white;">€${d.price.toLocaleString()}</div>
      </div>
    </div>
    <div style="padding:0.6rem 1rem;border-top:1px solid #2a2c30;display:flex;align-items:center;justify-content:space-between;">
      <span style="font-size:0.6rem;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;">RPZ Status</span>
      <span style="font-size:0.75rem;font-weight:700;${d.rpz?'color:#f97316;':'color:#4ade80;'}">${d.rpz?'⚠ Yes — Rent Capped 2%':'✓ No — Market Rent OK'}</span>
    </div>
    ${cta}`;
}

function hmRank(){
  const sorted=Object.entries(hmD).sort((a,b)=>{
    if(hmM==='yield') return b[1].yield-a[1].yield;
    if(hmM==='growth') return b[1].growth-a[1].growth;
    const r={Low:0,Medium:1,High:2}; return r[a[1].risk]-r[b[1].risk];
  }).slice(0,8);
  document.getElementById('hm-rank-list').innerHTML=sorted.map(([n,d],i)=>{
    const val=hmM==='yield'?d.yield+'%':hmM==='growth'?'+'+d.growth+'%':d.risk;
    const bw=hmM==='risk'?(d.risk==='Low'?90:d.risk==='Medium'?55:20):(parseFloat(hmM==='yield'?d.yield:d.growth)/9*100);
    const bc=hmClr(n,hmM);
    return`<div class="hm-ri" data-c="${n}" onclick="hmSel('${n}')" style="display:flex;align-items:center;gap:0.6rem;padding:0.5rem 1rem;border-bottom:1px solid #2a2c30;cursor:pointer;transition:background 0.12s;">
      <span style="font-size:0.65rem;color:#4a4845;width:14px;">${i+1}</span>
      <span style="font-size:0.8rem;font-weight:500;flex:1;color:white;">${n}</span>
      <div style="width:40px;height:3px;background:#2a2c30;border-radius:2px;overflow:hidden;"><div style="width:${bw}%;height:100%;background:${bc};border-radius:2px;"></div></div>
      <span style="font-size:0.78rem;font-weight:600;color:${bc};min-width:36px;text-align:right;">${val}</span>
    </div>`;
  }).join('');
}

hmPaint(); hmRank();
</script>
<!-- ── END HEATMAP SECTION ── -->
<div style="text-align:center;padding:1.5rem 2rem 2rem;background:#0a0c0f;">
  <a href="#snap" style="display:inline-flex;align-items:center;gap:.5rem;padding:.85rem 2rem;background:var(--green);color:#0b1120;border-radius:10px;font-weight:700;font-size:.95rem;text-decoration:none;">Explore full county insights →</a>
</div>
<!-- ── DEAL CHECKER SECTION ── -->
<section style="background:#0f1014;padding:5rem 2rem;">
  <div style="max-width:700px;margin:0 auto;text-align:center;">
    <div style="display:inline-block;font-size:0.72rem;font-weight:500;letter-spacing:0.15em;text-transform:uppercase;color:#c9a84c;border:1px solid #c9a84c;padding:0.3rem 0.8rem;border-radius:2px;margin-bottom:1.5rem;">Free Tool</div>
    <h2 style="font-family:'Playfair Display',serif;font-size:clamp(1.8rem,4vw,2.6rem);font-weight:900;color:white;line-height:1.15;margin-bottom:1rem;">Is That Property a Good Deal?</h2>
    <p style="color:#9a9690;font-size:1rem;font-weight:300;line-height:1.7;max-width:500px;margin:0 auto 2.5rem;">Enter any Irish property and we'll compare it against 700,000+ real PPR transactions instantly.</p>
    <div style="background:#1a1c20;border:1px solid #2a2c30;border-radius:4px;padding:2rem 2rem;text-align:left;">
      <style>
        .dc-form{display:grid;grid-template-columns:1fr 1fr 1fr;gap:1rem;}
        .dc-inp{width:100%;font-family:inherit;font-size:0.95rem;padding:0.75rem 1rem;border:1px solid #2a2c30;border-radius:3px;background:#0f1014;color:white;outline:none;}
        .dc-inp:focus{border-color:#c9a84c;}
        .dc-label{display:block;font-size:0.7rem;font-weight:500;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;margin-bottom:0.4rem;}
        .dc-btn{width:100%;margin-top:1rem;padding:0.85rem 1rem;background:#c9a84c;color:#0f1014;border:none;border-radius:3px;font-family:inherit;font-size:0.85rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;cursor:pointer;}
        .dc-btn:hover{background:#d4b86a;}
        @media(max-width:600px){.dc-form{grid-template-columns:1fr 1fr;}}
        @media(max-width:400px){.dc-form{grid-template-columns:1fr;}}
      </style>
      <form method="POST" action="/deal-checker">
        <div class="dc-form">
          <div>
            <label class="dc-label">County</label>
            <select name="county" required class="dc-inp">
              <option value="" disabled selected>Select county</option>
              <option value="Carlow">Carlow</option>
              <option value="Cavan">Cavan</option>
              <option value="Clare">Clare</option>
              <option value="Cork">Cork</option>
              <option value="Donegal">Donegal</option>
              <option value="Dublin">Dublin</option>
              <option value="Galway">Galway</option>
              <option value="Kerry">Kerry</option>
              <option value="Kildare">Kildare</option>
              <option value="Kilkenny">Kilkenny</option>
              <option value="Laois">Laois</option>
              <option value="Leitrim">Leitrim</option>
              <option value="Limerick">Limerick</option>
              <option value="Longford">Longford</option>
              <option value="Louth">Louth</option>
              <option value="Mayo">Mayo</option>
              <option value="Meath">Meath</option>
              <option value="Monaghan">Monaghan</option>
              <option value="Offaly">Offaly</option>
              <option value="Roscommon">Roscommon</option>
              <option value="Sligo">Sligo</option>
              <option value="Tipperary">Tipperary</option>
              <option value="Waterford">Waterford</option>
              <option value="Westmeath">Westmeath</option>
              <option value="Wexford">Wexford</option>
              <option value="Wicklow">Wicklow</option>
            </select>
          </div>
          <div>
            <label class="dc-label">Area / Town</label>
            <input type="text" name="area" placeholder="e.g. Blackrock" required class="dc-inp">
          </div>
          <div>
            <label class="dc-label">Asking Price</label>
            <div style="position:relative;">
              <span style="position:absolute;left:1rem;top:50%;transform:translateY(-50%);color:#6b6860;pointer-events:none;">€</span>
              <input type="number" name="asking_price" placeholder="350000" required class="dc-inp" style="padding-left:1.8rem;">
            </div>
          </div>
        </div>
        <button type="submit" class="dc-btn">Analyse This Property →</button>
      </form>
      <p style="margin-top:0.75rem;font-size:0.75rem;color:#4a4845;text-align:center;">Not financial advice. Based on PPR data 2010–2024.</p>
    </div>
  </div>
</section>
<!-- ── END DEAL CHECKER SECTION ── -->

<!-- ── MICRO-AREA SEARCH ── -->
<div id="maSearch">
  <div class="mas-inner">
    <div class="mas-label">Quick Search</div>
    <h3>Find any micro-area instantly</h3>
    <div id="masWrap">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
      <input type="text" id="masInput" placeholder="Type a town or area — e.g. Ballymun, Salthill, Clondalkin..." oninput="masSearch(this.value)" autocomplete="off" />
    </div>
    <div id="masResults"></div>
    <div id="masNoResult">No areas found. Try: <span style="color:var(--green);cursor:pointer;" onclick="document.getElementById('masInput').value='Swords';masSearch('Swords')">Swords</span>, <span style="color:var(--green);cursor:pointer;" onclick="document.getElementById('masInput').value='Rathmines';masSearch('Rathmines')">Rathmines</span>, <span style="color:var(--green);cursor:pointer;" onclick="document.getElementById('masInput').value='Salthill';masSearch('Salthill')">Salthill</span>, or <span style="color:var(--green);cursor:pointer;" onclick="document.getElementById('masInput').value='Clondalkin';masSearch('Clondalkin')">Clondalkin</span></div>
  </div>
</div>
<script>
var MAS_DATA=[
  {name:"Snugborough Rd",county:"Dublin 15",yield:13.6,growth:6.4,sig:"HIGH POTENTIAL"},
  {name:"Ballymun",county:"Dublin 11",yield:13.2,growth:16.0,sig:"HIGH POTENTIAL"},
  {name:"Clondalkin",county:"Dublin 22",yield:11.9,growth:3.9,sig:"HIGH POTENTIAL"},
  {name:"Main St",county:"Blanchardstown",yield:11.7,growth:6.2,sig:"HIGH POTENTIAL"},
  {name:"Northwood",county:"Santry D9",yield:11.5,growth:16.2,sig:"HIGH POTENTIAL"},
  {name:"Monastery Rd",county:"Dublin 22",yield:10.8,growth:10.3,sig:"HIGH POTENTIAL"},
  {name:"Coolock",county:"Dublin 17",yield:10.7,growth:8.1,sig:"HIGH POTENTIAL"},
  {name:"Finglas Rd",county:"Dublin 11",yield:10.7,growth:7.3,sig:"HIGH POTENTIAL"},
  {name:"Swords",county:"Dublin 17",yield:8.2,growth:8.2,sig:"HIGH POTENTIAL"},
  {name:"Ballincollig",county:"Cork",yield:7.5,growth:7.5,sig:"HIGH POTENTIAL"},
  {name:"Salthill",county:"Co. Galway",yield:4.2,growth:5.1,sig:"MODERATE POTENTIAL"},
  {name:"Castletroy",county:"Co. Limerick",yield:5.4,growth:6.9,sig:"HIGH POTENTIAL"},
  {name:"Drogheda",county:"Co. Louth",yield:5.0,growth:7.1,sig:"HIGH POTENTIAL"},
  {name:"Naas",county:"Co. Kildare",yield:4.8,growth:7.4,sig:"HIGH POTENTIAL"},
  {name:"Newbridge",county:"Co. Kildare",yield:4.6,growth:6.8,sig:"HIGH POTENTIAL"},
  {name:"Maynooth",county:"Co. Kildare",yield:4.5,growth:7.1,sig:"HIGH POTENTIAL"},
  {name:"Bray",county:"Co. Wicklow",yield:3.9,growth:5.2,sig:"MODERATE POTENTIAL"},
  {name:"Greystones",county:"Co. Wicklow",yield:3.7,growth:5.8,sig:"MODERATE POTENTIAL"},
  {name:"Navan",county:"Co. Meath",yield:4.6,growth:7.5,sig:"HIGH POTENTIAL"},
  {name:"Trim",county:"Co. Meath",yield:4.8,growth:6.9,sig:"HIGH POTENTIAL"},
  {name:"Blackrock",county:"Dublin South",yield:3.2,growth:4.1,sig:"MODERATE POTENTIAL"},
  {name:"Rathmines",county:"Dublin 6",yield:4.1,growth:3.8,sig:"MODERATE POTENTIAL"},
  {name:"Tallaght",county:"Dublin 24",yield:9.8,growth:5.6,sig:"HIGH POTENTIAL"},
  {name:"Lucan",county:"Co. Dublin",yield:7.2,growth:6.1,sig:"HIGH POTENTIAL"},
  {name:"Portlaoise",county:"Co. Laois",yield:6.4,growth:5.2,sig:"HIGH POTENTIAL"},
  {name:"Mullingar",county:"Co. Westmeath",yield:6.1,growth:4.8,sig:"HIGH POTENTIAL"},
  {name:"Athlone",county:"Co. Westmeath",yield:5.8,growth:5.1,sig:"HIGH POTENTIAL"},
  {name:"Carlow Town",county:"Co. Carlow",yield:6.2,growth:5.4,sig:"HIGH POTENTIAL"},
  {name:"Wexford Town",county:"Co. Wexford",yield:5.5,growth:6.0,sig:"HIGH POTENTIAL"},
  {name:"Waterford City",county:"Co. Waterford",yield:5.8,growth:5.3,sig:"HIGH POTENTIAL"},
  {name:"Tralee",county:"Co. Kerry",yield:5.6,growth:5.8,sig:"HIGH POTENTIAL"},
  {name:"Killarney",county:"Co. Kerry",yield:4.9,growth:6.5,sig:"HIGH POTENTIAL"},
  {name:"Ennis",county:"Co. Clare",yield:5.4,growth:5.9,sig:"HIGH POTENTIAL"},
  {name:"Sligo Town",county:"Co. Sligo",yield:5.9,growth:4.1,sig:"MODERATE POTENTIAL"},
  {name:"Letterkenny",county:"Co. Donegal",yield:6.5,growth:3.5,sig:"MODERATE POTENTIAL"},
];
function masSearch(q){
  var res=document.getElementById('masResults');
  var none=document.getElementById('masNoResult');
  q=q.trim().toLowerCase();
  if(q.length<2){res.classList.remove('show');res.innerHTML='';none.style.display='none';return;}
  var matches=MAS_DATA.filter(function(d){
    return d.name.toLowerCase().includes(q)||d.county.toLowerCase().includes(q);
  });
  none.style.display='none';
  if(matches.length===0){res.classList.remove('show');res.innerHTML='';none.style.display='block';return;}
  // Build rows using data-county attribute — no inline JS escaping needed
  res.innerHTML=matches.slice(0,8).map(function(d){
    var sc=d.sig==='HIGH POTENTIAL'?'sb':'mo';
    var sigShort=d.sig==='HIGH POTENTIAL'?'HIGH POTENTIAL':'MODERATE';
    return '<div class="mas-row" data-county="'+d.county+'" data-name="'+d.name+'">'
      +'<div><div class="mr-name">'+d.name+'</div><div class="mr-county">'+d.county+'</div></div>'
      +'<div class="mr-yield">'+d.yield+'%</div>'
      +'<div class="mr-growth">+'+d.growth+'%</div>'
      +'<div class="mr-sig '+sc+'">'+sigShort+'</div>'
      +'<div style="font-size:.7rem;color:var(--green);white-space:nowrap;">Get Report →</div>'
      +'</div>';
  }).join('');
  res.classList.add('show');
}
// Wire up clicks via event delegation on the results container
// Using mousedown so it fires before the input blur hides the list
document.addEventListener('DOMContentLoaded',function(){
  var res=document.getElementById('masResults');
  var inp=document.getElementById('masInput');
  if(res){
    res.addEventListener('mousedown',function(e){
      // Prevent input from losing focus before we process the click
      e.preventDefault();
      var row=e.target.closest('.mas-row');
      if(row){
        masClick(row.getAttribute('data-county'), row.getAttribute('data-name'));
      }
    });
  }
  if(inp){
    inp.addEventListener('blur',function(){
      setTimeout(function(){
        if(res) res.classList.remove('show');
      },150);
    });
    // Also hide on Escape
    inp.addEventListener('keydown',function(e){
      if(e.key==='Escape'){res.classList.remove('show');inp.blur();}
    });
  }
});
function masClick(county, areaName){
  var res=document.getElementById('masResults');
  var inp=document.getElementById('masInput');
  if(res) res.classList.remove('show');
  if(inp){inp.value='';inp.blur();}
  // Extract base county name: "Dublin 15" → "Dublin", "Co. Kildare" → "Kildare"
  var countyBase=county.replace(/\s*(dublin)\s*\d*/i,'Dublin')
                       .replace(/^co[.]\s*/i,'')
                       .replace(/\s+\d+$/,'')
                       .trim();
  var sel=document.getElementById('countyBuySelect');
  var matched=false;
  if(sel){
    for(var i=0;i<sel.options.length;i++){
      var opt=sel.options[i].text.toLowerCase();
      var cb=countyBase.toLowerCase();
      if(opt===cb||opt===cb.toLowerCase()||opt.includes(cb)||cb.includes(opt)){
        if(sel.options[i].value&&sel.options[i].value!=='coming'){
          sel.value=sel.options[i].value;
          matched=true;
          break;
        }
      }
    }
  }
  document.getElementById('reports').scrollIntoView({behavior:'smooth'});
  if(matched){
    showToast('✓ '+countyBase+' selected — get the full report below');
  } else {
    showToast(countyBase+' report coming soon — request it below!');
  }
}
</script>

<div class="ol">Real Sample</div>
  <h2>Real data. Real areas. Real signals.</h2>
  <p>This is a real page from the Dublin report — generated live from 15 years of PPR data.</p>
</div>
<div class="rp-wrap fade-in">
  <div class="rp-browser">
    <div class="rp-bar"><span></span><span></span><span></span></div>
    <div class="rp-doc">
      <div class="rp-header">
        <h2>Dublin Property Investment Report</h2>
        <p>Micro-area intelligence &bull; Updated with RTB Q2 2025 data &bull; Generated March 2026</p>
        <div class="rp-rule"></div>
      </div>
      <div class="rp-metrics">
        <div class="rp-m"><div class="rp-mv">€484,581</div><div class="rp-ml">Median Price</div></div>
        <div class="rp-m"><div class="rp-mv">5.3%</div><div class="rp-ml">5yr County Growth</div></div>
        <div class="rp-m"><div class="rp-mv">5.5%</div><div class="rp-ml">County Gross Yield</div></div>
        <div class="rp-m"><div class="rp-mv">415</div><div class="rp-ml">Micro-Areas Analysed</div></div>
      </div>
      <div class="rp-section-title">Top Micro-Areas by Estimated Yield</div>
      <div class="rp-chart">
        <div class="rp-bar-row"><span class="rp-area">Snugborough Rd Dublin 15</span><div class="rp-bar-wrap"><div class="rp-bar-fill" style="width:100%"></div></div><span class="rp-pct">13.6%</span></div>
        <div class="rp-bar-row"><span class="rp-area">Ballymun Dublin 11</span><div class="rp-bar-wrap"><div class="rp-bar-fill" style="width:97%"></div></div><span class="rp-pct">13.2%</span></div>
        <div class="rp-bar-row"><span class="rp-area">Clondalkin, Dublin 22</span><div class="rp-bar-wrap"><div class="rp-bar-fill" style="width:87%"></div></div><span class="rp-pct">11.9%</span></div>
        <div class="rp-bar-row"><span class="rp-area">Main St, Blanchardstown</span><div class="rp-bar-wrap"><div class="rp-bar-fill" style="width:86%"></div></div><span class="rp-pct">11.7%</span></div>
        <div class="rp-bar-row"><span class="rp-area">Northwood, Santry D9</span><div class="rp-bar-wrap"><div class="rp-bar-fill" style="width:84%"></div></div><span class="rp-pct">11.5%</span></div>
        <div class="rp-bar-row"><span class="rp-area">Monastery Rd Dublin 22</span><div class="rp-bar-wrap"><div class="rp-bar-fill" style="width:79%"></div></div><span class="rp-pct">10.8%</span></div>
        <div class="rp-bar-row"><span class="rp-area">Coolock Dublin 17</span><div class="rp-bar-wrap"><div class="rp-bar-fill" style="width:79%"></div></div><span class="rp-pct">10.7%</span></div>
        <div class="rp-bar-row"><span class="rp-area">Finglas Rd Dublin 11</span><div class="rp-bar-wrap"><div class="rp-bar-fill" style="width:78%"></div></div><span class="rp-pct">10.7%</span></div>
      </div>
      <div class="rp-section-title" style="margin-top:14px;display:flex;align-items:center;justify-content:space-between;">
        Micro-Area Ranking Table
        <button onclick="(function(b,t){var h=document.getElementById('sampleTableWrap');var open=h.style.display!=='none';h.style.display=open?'none':'block';b.textContent=open?'▼ Show sample table':'▲ Hide table';})(this)" style="background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.25);color:var(--green);font-size:.72rem;font-weight:600;padding:.3rem .8rem;border-radius:20px;cursor:pointer;font-family:var(--fb);">▼ Show sample table</button>
      </div>
      <div id="sampleTableWrap" style="display:none;">
      <table class="rp-table">
        <thead><tr><th>#</th><th>Micro-Area</th><th>Median Price</th><th>5yr Growth</th><th>Yield</th><th>Risk</th><th>RPZ</th><th>Signal</th><th>Confidence</th></tr></thead>
        <tbody>
          <tr><td>1</td><td>Snugborough Rd Dublin 15</td><td>€245,000</td><td class="g">+6.4%</td><td>13.6%</td><td>Medium</td><td><span style="color:#f97316;font-size:.68rem;font-weight:700;">⚠ RPZ</span></td><td><span class="sig sb">HIGH POTENTIAL</span></td><td style="color:#f59e0b;">★★★</td></tr>
          <tr><td>2</td><td>Ballymun Dublin 11</td><td>€250,000</td><td class="g">+16.0%</td><td>13.2%</td><td>Medium</td><td><span style="color:#f97316;font-size:.68rem;font-weight:700;">⚠ RPZ</span></td><td><span class="sig sb">HIGH POTENTIAL</span></td><td style="color:#f59e0b;">★★★</td></tr>
          <tr><td>3</td><td>Clondalkin, Dublin 22</td><td>€270,000</td><td class="g">+3.9%</td><td>11.9%</td><td>Low</td><td><span style="color:#f97316;font-size:.68rem;font-weight:700;">⚠ RPZ</span></td><td><span class="sig sb">HIGH POTENTIAL</span></td><td style="color:#f59e0b;">★★★</td></tr>
          <tr><td>4</td><td>Main St, Blanchardstown</td><td>€274,000</td><td class="g">+6.2%</td><td>11.7%</td><td>Low</td><td><span style="color:#f97316;font-size:.68rem;font-weight:700;">⚠ RPZ</span></td><td><span class="sig sb">HIGH POTENTIAL</span></td><td style="color:#f59e0b;">★★☆</td></tr>
          <tr class="blur-row"><td>5</td><td>Northwood, Santry D9</td><td>€278,000</td><td>+16.2%</td><td>11.5%</td><td>Medium</td><td>⚠ RPZ</td><td><span class="sig sb">HIGH POTENTIAL</span></td><td>★★★</td></tr>
          <tr class="blur-row"><td>6</td><td>Monastery Rd Dublin 22</td><td>€290,000</td><td>+10.3%</td><td>10.8%</td><td>Low</td><td>⚠ RPZ</td><td><span class="sig sb">HIGH POTENTIAL</span></td><td>★★☆</td></tr>
        </tbody>
      </table>
      </div>
      <div class="rp-fade"></div>
    </div>
  </div>
</div>
<p style="text-align:center;font-size:.8rem;color:var(--t3);margin-top:1.5rem">Real data from the Dublin report &bull; Last rows blurred to show report depth</p>
<p style="text-align:center;font-size:.75rem;color:var(--t3);margin-top:.4rem;display:none;" class="mobile-swipe-hint">← Swipe table to see all columns →</p>
<style>@media(max-width:600px){.mobile-swipe-hint{display:block!important}}</style>
<p style="text-align:center;font-size:.78rem;color:#f97316;margin-top:.5rem;max-width:600px;margin-left:auto;margin-right:auto;">⚠ <strong>RPZ Note:</strong> All 4 areas above are in Rent Pressure Zones — annual rent increases are legally capped at 2%. Factor this into yield projections for existing tenancies.</p>
</section>
<section><div class="sh fade-in"><div class="ol">What You Get</div><h2>Three signals. Every micro-area.</h2></div><div class="pg"><div class="pc fade-in"><div class="pi">📈</div><h3>Growth</h3><p>5-year CAGR per micro-area vs county average.</p></div><div class="pc fade-in"><div class="pi">🛡️</div><h3>Risk</h3><p>Volatility + transaction volume, scored Low / Medium / High.</p></div><div class="pc fade-in"><div class="pi">💰</div><h3>Yield</h3><p>Gross rental yield from live RTB rent data.</p></div></div></section>
<section class="is"><div class="ig fade-in"><div class="it"><div class="ol" style="font-size:.75rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--green);margin-bottom:.75rem">Sample Data</div><h3>Micro-area precision — not vague county averages</h3><p>County-level data hides the real story. Our reports drill into individual areas — ranking them by growth, risk, and yield.</p><a href="#snap" class="bp" style="margin-top:.5rem">See Top Areas For Free →</a></div><div><table class="itable"><thead><tr><th>Micro-Area</th><th>Growth</th><th>Yield</th><th>RPZ</th><th>Signal</th></tr></thead><tbody><tr><td>Swords, Dublin 17</td><td style="color:var(--green)">+8.2%</td><td>5.1%</td><td><span style="color:#f97316;font-weight:700;font-size:.75rem;">⚠ Yes</span></td><td><span class="ss">HIGH POTENTIAL</span></td></tr><tr><td>Ballincollig, Cork</td><td style="color:var(--green)">+7.5%</td><td>4.8%</td><td><span style="color:#f97316;font-weight:700;font-size:.75rem;">⚠ Yes</span></td><td><span class="ss">HIGH POTENTIAL</span></td></tr><tr><td>Salthill, Co. Galway</td><td style="color:var(--gold)">+5.1%</td><td>4.2%</td><td><span style="color:#f97316;font-weight:700;font-size:.75rem;">⚠ Yes</span></td><td><span class="sm">MODERATE</span></td></tr><tr class="blur"><td>Castletroy, Co. Limerick</td><td>+6.9%</td><td>5.4%</td><td>No</td><td><span class="ss">HIGH POTENTIAL</span></td></tr><tr class="blur"><td>Drogheda, Louth</td><td>+7.1%</td><td>5.0%</td><td>⚠ Yes</td><td><span class="ss">HIGH POTENTIAL</span></td></tr></tbody></table><p style="font-size:.78rem;color:var(--t3);margin-top:.75rem;text-align:center">* Sample data — full reports contain all micro-areas per county</p></div></div></section>
<section class="es" id="snap"><div class="eb fade-in"><div class="ol" style="font-size:.75rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--green);margin-bottom:.75rem">Free — No Credit Card</div><h2>Get your free investor snapshot</h2><p style="margin-bottom:1.75rem">A 2-page investment briefing for any Irish county — free, instant, no credit card.</p>

<!-- ── PRICING COMPARISON TABLE ── -->
<style>
.pct{width:100%;border-collapse:collapse;margin:0 auto 1.75rem;max-width:560px;font-size:.85rem;}
.pct thead tr th{padding:.75rem 1rem;font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;border-bottom:2px solid var(--border);}
.pct thead .pct-free{color:var(--green);background:rgba(16,185,129,.06);border-radius:8px 0 0 0;}
.pct thead .pct-paid{color:var(--gold);background:rgba(201,168,76,.08);border-radius:0 8px 0 0;position:relative;}
.pct thead .pct-badge{display:inline-block;background:var(--gold);color:#0b1120;font-size:.6rem;font-weight:800;padding:.15rem .45rem;border-radius:20px;margin-left:.4rem;vertical-align:middle;letter-spacing:.05em;}
.pct tbody tr td{padding:.7rem 1rem;border-bottom:1px solid rgba(255,255,255,.04);vertical-align:middle;}
.pct tbody tr:last-child td{border-bottom:none;}
.pct tbody tr:hover td{background:rgba(255,255,255,.02);}
.pct .pct-feature{text-align:left;color:var(--t2);font-size:.83rem;}
.pct .pct-free,.pct .pct-paid{text-align:center;}
.pct .pct-yes{color:var(--green);font-size:1.1rem;font-weight:700;}
.pct .pct-no{color:var(--t3);font-size:1rem;}
.pct .pct-part{font-size:.72rem;font-weight:600;color:#f59e0b;background:rgba(245,158,11,.12);padding:.15rem .5rem;border-radius:10px;}
.pct .pct-full{font-size:.72rem;font-weight:600;color:var(--green);background:rgba(16,185,129,.12);padding:.15rem .5rem;border-radius:10px;}
.pct tfoot td{padding:.9rem 1rem;border-top:2px solid var(--border);}
.pct tfoot .pct-free{text-align:center;}
.pct tfoot .pct-paid{text-align:center;}
@media(max-width:480px){.pct{font-size:.78rem;}.pct thead tr th,.pct tbody tr td,.pct tfoot td{padding:.55rem .6rem;}}
</style>

<div style="overflow-x:auto;-webkit-overflow-scrolling:touch;">
<table class="pct">
  <thead>
    <tr>
      <th class="pct-feature" style="text-align:left;color:var(--t3);">Feature</th>
      <th class="pct-free">Free Snapshot</th>
      <th class="pct-paid">Full Report <span class="pct-badge">€29</span> <span style="display:inline-block;background:var(--green);color:#0b1120;font-size:.58rem;font-weight:800;padding:.15rem .5rem;border-radius:20px;margin-left:.3rem;vertical-align:middle;letter-spacing:.05em;">★ MOST POPULAR</span></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td class="pct-feature">Top 3 micro-areas</td>
      <td class="pct-free"><span class="pct-yes">✓</span></td>
      <td class="pct-paid"><span class="pct-yes">✓</span></td>
    </tr>
    <tr>
      <td class="pct-feature">Full micro-area rankings</td>
      <td class="pct-free"><span class="pct-no">✗</span></td>
      <td class="pct-paid"><span class="pct-yes">✓</span></td>
    </tr>
    <tr>
      <td class="pct-feature">Yield, growth &amp; risk scores</td>
      <td class="pct-free"><span class="pct-part">Partial</span></td>
      <td class="pct-paid"><span class="pct-full">Full</span></td>
    </tr>
    <tr>
      <td class="pct-feature">RPZ flags</td>
      <td class="pct-free"><span class="pct-part">Partial</span></td>
      <td class="pct-paid"><span class="pct-full">Full</span></td>
    </tr>
    <tr>
      <td class="pct-feature">Data confidence score (★★★)</td>
      <td class="pct-free"><span class="pct-no">✗</span></td>
      <td class="pct-paid"><span class="pct-yes">✓</span></td>
    </tr>
    <tr>
      <td class="pct-feature">Price trend 2010–2025</td>
      <td class="pct-free"><span class="pct-no">✗</span></td>
      <td class="pct-paid"><span class="pct-yes">✓</span></td>
    </tr>
    <tr>
      <td class="pct-feature">Methodology appendix</td>
      <td class="pct-free"><span class="pct-no">✗</span></td>
      <td class="pct-paid"><span class="pct-yes">✓</span></td>
    </tr>
    <tr>
      <td class="pct-feature">Instant PDF download</td>
      <td class="pct-free"><span class="pct-yes">✓</span></td>
      <td class="pct-paid"><span class="pct-yes">✓</span></td>
    </tr>
    <tr>
      <td class="pct-feature">No credit card needed</td>
      <td class="pct-free"><span class="pct-yes">✓</span></td>
      <td class="pct-paid"><span class="pct-no">—</span></td>
    </tr>
  </tbody>
  <tfoot>
    <tr>
      <td></td>
      <td class="pct-free">
        <div id="snapStep1" style="display:flex;flex-direction:column;gap:.5rem;align-items:center;">
          <select id="snapCounty" required style="width:100%;padding:.7rem .9rem;background:var(--bg);border:1px solid var(--border);border-radius:8px;color:var(--t1);font-family:var(--fb);font-size:.82rem;"><option value="" disabled selected>Select county...</option>%COUNTY_OPTIONS%</select>
          <button type="button" class="bp" onclick="openSnapModal()" style="width:100%;justify-content:center;padding:.7rem 1rem;font-size:.82rem;">Get Free →</button>
        </div>
      </td>
      <td class="pct-paid">
        <a href="#reports" class="bp" style="display:block;text-align:center;padding:.7rem 1rem;font-size:.82rem;text-decoration:none;">Get Full Report →</a>
      </td>
    </tr>
  </tfoot>
</table>
</div>
<p class="en">Free snapshot — enter your email to receive it. Upgrade to full report anytime for €29.</p></div></section>
<!-- Email Gate Modal -->
<div id="snapModal" style="display:none;position:fixed;inset:0;background:rgba(11,17,32,.85);backdrop-filter:blur(8px);z-index:500;align-items:center;justify-content:center">
<div style="background:var(--card);border:1px solid var(--border);border-radius:20px;padding:3rem 2.5rem;max-width:460px;width:90%;position:relative;border-top:3px solid var(--green)">
<button onclick="closeSnapModal()" style="position:absolute;top:1rem;right:1.25rem;background:none;border:none;color:var(--t3);font-size:1.4rem;cursor:pointer;line-height:1">×</button>
<h3 style="font-family:var(--fd);font-size:1.5rem;font-weight:700;margin-bottom:.5rem">One last step</h3>
<p style="font-size:.75rem;color:var(--green);font-weight:600;margin-bottom:.5rem;letter-spacing:.04em;">📥 Downloaded by 800+ investors across Ireland</p>
<p style="color:var(--t2);font-size:.93rem;margin-bottom:.75rem">Enter your email to download the free <strong id="modalCountyName"></strong> snapshot.</p>
<div style="background:rgba(16,185,129,.07);border:1px solid rgba(16,185,129,.2);border-radius:8px;padding:.7rem 1rem;margin-bottom:1rem;font-size:.82rem;color:var(--t2);text-align:left">💡 <strong>The snapshot shows the top 3 micro-areas.</strong> The <strong style="color:var(--green)">full report (€29)</strong> covers every micro-area with complete yield, growth &amp; risk scores.</div>
<div style="display:flex;flex-direction:column;gap:.75rem">
<input type="email" id="snapEmail" placeholder="your@email.com" style="padding:.9rem 1.2rem;background:var(--bg);border:1px solid var(--border);border-radius:10px;color:var(--t1);font-family:var(--fb);font-size:.95rem;outline:none" onfocus="this.style.borderColor='var(--green)'" onblur="this.style.borderColor='var(--border)'" />
<button class="bp" onclick="submitSnapModal()" style="justify-content:center;width:100%;padding:1rem">Download My Free Snapshot →</button>
</div>
<p style="font-size:.76rem;color:var(--t3);margin-top:1rem;text-align:center">No spam. Unsubscribe anytime.</p>
</div>
</div>

<section id="who"><div class="sh fade-in"><div class="ol">Straight Talk</div><h2>This report is built for serious investors</h2><p>We built this for people who make decisions based on data, not headlines.</p></div><div class="ag fade-in"><div class="ac"><h3><span style="font-size:1.1rem">✅</span> Built for you if…</h3><ul class="al fl"><li><span class="ic">✓</span><span>You're evaluating <strong>buy-to-let opportunities</strong> across Irish counties.</span></li><li><span class="ic">✓</span><span>You're an <strong>existing landlord</strong> exploring where to expand next.</span></li><li><span class="ic">✓</span><span>You're a <strong>mortgage broker or advisor</strong> wanting data-backed talking points.</span></li><li><span class="ic">✓</span><span>You want a <strong>quick shortlist</strong> worth investigating further.</span></li></ul></div><div class="ac"><h3><span style="font-size:1.1rem">✗</span> Probably not for you if…</h3><ul class="al nl2"><li><span class="ic">✗</span><span>You're looking for a <strong>crystal ball</strong>. We analyse trends — we don't predict.</span></li><li><span class="ic">✗</span><span>You expect <strong>individual property valuations</strong>. We score areas, not addresses.</span></li><li><span class="ic">✗</span><span>You need <strong>legal, tax, or planning</strong> advice. This is market data only.</span></li><li><span class="ic">✗</span><span>You're buying a <strong>home to live in</strong>. Signals are optimised for investment returns.</span></li></ul></div></div><div class="fq fade-in"><div class="fi"><div class="fqq">How accurate is the yield estimate?</div><div class="fqa">We use official RTB Q2 2025 rent data cross-referenced with PPR median sale prices, dampened by 0.4× at micro-area level. These are gross estimates — your actual yield depends on vacancy and costs. A reliable first filter, not a final calculation.</div></div><div class="fi"><div class="fqq">Isn't this just historical data?</div><div class="fqa">Yes — and that's the point. Investment patterns are visible in historical data before headlines. We track 5-year compound growth, transaction volumes, and volatility. Combined with current RTB rents, this gives a grounded view of where momentum exists.</div></div><div class="fi"><div class="fqq">Why trust micro-area scoring over my own research?</div><div class="fqa">You shouldn't rely on it alone. The report narrows 500+ areas to a shortlist worth deeper research. It replaces hours of manual PPR browsing, not your judgment.</div></div><div class="fi"><div class="fqq">What about new developments, zoning, local demand?</div><div class="fqa">We analyse transactions and rents — not planning applications or infrastructure. This is the quantitative layer. You bring the local knowledge.</div></div></div></section>
<!-- ── FULL REPORT PREVIEW (BLURRED) ── -->
<section style="padding:5rem 2rem;background:var(--bg);">
  <div style="max-width:1000px;margin:0 auto;">

    <!-- Header -->
    <div class="sh fade-in" style="margin-bottom:3rem;">
      <div class="ol">What You Get</div>
      <h2>Inside the full €29 report</h2>
      <p>A complete micro-area intelligence report for your county — every area ranked, scored, and explained. Here's exactly what it looks like.</p>
    </div>

    <!-- Page thumbnails row -->
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1.5rem;margin-bottom:3rem;" class="fade-in">

      <!-- Page 1 thumbnail: Cover + metrics -->
      <div style="background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 12px 40px rgba(0,0,0,.4);border:1px solid rgba(255,255,255,.06);">
        <div style="background:#f1f3f5;padding:.4rem .7rem;display:flex;gap:.35rem;align-items:center;">
          <span style="width:8px;height:8px;border-radius:50%;background:#ef4444;display:inline-block;"></span>
          <span style="width:8px;height:8px;border-radius:50%;background:#f59e0b;display:inline-block;"></span>
          <span style="width:8px;height:8px;border-radius:50%;background:#10b981;display:inline-block;"></span>
          <span style="font-size:.6rem;color:#94a3b8;margin-left:.5rem;">Page 1 — Overview</span>
        </div>
        <div style="padding:1rem;color:#0b1120;font-family:'DM Sans',sans-serif;">
          <div style="font-size:.7rem;font-weight:700;color:#10b981;margin-bottom:.3rem;text-transform:uppercase;letter-spacing:.06em;">Dublin County Report</div>
          <div style="height:2px;background:linear-gradient(90deg,#10b981,#3b82f6);border-radius:2px;margin-bottom:.75rem;"></div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:.4rem;margin-bottom:.75rem;">
            <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:4px;padding:.4rem;text-align:center;">
              <div style="font-size:.85rem;font-weight:700;color:#0b1120;">€484k</div>
              <div style="font-size:.5rem;color:#94a3b8;">Median Price</div>
            </div>
            <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:4px;padding:.4rem;text-align:center;">
              <div style="font-size:.85rem;font-weight:700;color:#10b981;">5.5%</div>
              <div style="font-size:.5rem;color:#94a3b8;">County Yield</div>
            </div>
            <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:4px;padding:.4rem;text-align:center;">
              <div style="font-size:.85rem;font-weight:700;color:#0b1120;">+5.3%</div>
              <div style="font-size:.5rem;color:#94a3b8;">5yr Growth</div>
            </div>
            <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:4px;padding:.4rem;text-align:center;">
              <div style="font-size:.85rem;font-weight:700;color:#0b1120;">415</div>
              <div style="font-size:.5rem;color:#94a3b8;">Areas Scored</div>
            </div>
          </div>
          <!-- Mini bar chart -->
          <div style="font-size:.55rem;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.4rem;">Top Areas by Yield</div>
          <div style="display:flex;flex-direction:column;gap:.25rem;">
            <div style="display:flex;align-items:center;gap:.4rem;"><span style="font-size:.52rem;color:#475569;width:80px;text-align:right;flex-shrink:0;">Snugborough Rd</span><div style="flex:1;background:#f1f5f9;border-radius:2px;height:8px;"><div style="width:100%;height:100%;background:#10b981;border-radius:2px;"></div></div><span style="font-size:.55rem;font-weight:700;color:#10b981;width:26px;">13.6%</span></div>
            <div style="display:flex;align-items:center;gap:.4rem;"><span style="font-size:.52rem;color:#475569;width:80px;text-align:right;flex-shrink:0;">Ballymun D11</span><div style="flex:1;background:#f1f5f9;border-radius:2px;height:8px;"><div style="width:97%;height:100%;background:#10b981;border-radius:2px;"></div></div><span style="font-size:.55rem;font-weight:700;color:#10b981;width:26px;">13.2%</span></div>
            <div style="display:flex;align-items:center;gap:.4rem;"><span style="font-size:.52rem;color:#475569;width:80px;text-align:right;flex-shrink:0;">Clondalkin D22</span><div style="flex:1;background:#f1f5f9;border-radius:2px;height:8px;"><div style="width:87%;height:100%;background:#10b981;border-radius:2px;"></div></div><span style="font-size:.55rem;font-weight:700;color:#10b981;width:26px;">11.9%</span></div>
            <div style="display:flex;align-items:center;gap:.4rem;filter:blur(3px);user-select:none;"><span style="font-size:.52rem;color:#475569;width:80px;text-align:right;flex-shrink:0;">████████</span><div style="flex:1;background:#f1f5f9;border-radius:2px;height:8px;"><div style="width:82%;height:100%;background:#10b981;border-radius:2px;"></div></div><span style="font-size:.55rem;font-weight:700;color:#10b981;width:26px;">11.1%</span></div>
            <div style="display:flex;align-items:center;gap:.4rem;filter:blur(3px);user-select:none;"><span style="font-size:.52rem;color:#475569;width:80px;text-align:right;flex-shrink:0;">████████</span><div style="flex:1;background:#f1f5f9;border-radius:2px;height:8px;"><div style="width:78%;height:100%;background:#10b981;border-radius:2px;"></div></div><span style="font-size:.55rem;font-weight:700;color:#10b981;width:26px;">10.6%</span></div>
          </div>
        </div>
      </div>

      <!-- Page 2 thumbnail: Ranking table -->
      <div style="background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 12px 40px rgba(0,0,0,.4);border:1px solid rgba(255,255,255,.06);">
        <div style="background:#f1f3f5;padding:.4rem .7rem;display:flex;gap:.35rem;align-items:center;">
          <span style="width:8px;height:8px;border-radius:50%;background:#ef4444;display:inline-block;"></span>
          <span style="width:8px;height:8px;border-radius:50%;background:#f59e0b;display:inline-block;"></span>
          <span style="width:8px;height:8px;border-radius:50%;background:#10b981;display:inline-block;"></span>
          <span style="font-size:.6rem;color:#94a3b8;margin-left:.5rem;">Page 2 — Full Rankings</span>
        </div>
        <div style="padding:.75rem;color:#0b1120;font-family:'DM Sans',sans-serif;">
          <div style="font-size:.6rem;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.5rem;">All 415 Micro-Areas Ranked</div>
          <table style="width:100%;border-collapse:collapse;font-size:.52rem;">
            <thead><tr style="background:#0b1120;color:#fff;">
              <th style="padding:.25rem .3rem;text-align:left;">#</th>
              <th style="padding:.25rem .3rem;text-align:left;">Area</th>
              <th style="padding:.25rem .3rem;">Yield</th>
              <th style="padding:.25rem .3rem;">Growth</th>
              <th style="padding:.25rem .3rem;">RPZ</th>
              <th style="padding:.25rem .3rem;">Signal</th>
              <th style="padding:.25rem .3rem;">★</th>
            </tr></thead>
            <tbody>
              <tr style="border-bottom:1px solid #f1f5f9;"><td style="padding:.22rem .3rem;color:#475569;">1</td><td style="padding:.22rem .3rem;">Snugborough Rd</td><td style="padding:.22rem .3rem;text-align:center;color:#10b981;font-weight:700;">13.6%</td><td style="padding:.22rem .3rem;text-align:center;color:#10b981;">+6.4%</td><td style="padding:.22rem .3rem;text-align:center;color:#f97316;font-weight:700;">⚠</td><td style="padding:.22rem .3rem;text-align:center;font-size:.48rem;color:#10b981;font-weight:700;">HIGH POT.</td><td style="padding:.22rem .3rem;text-align:center;color:#f59e0b;font-size:.55rem;">★★★</td></tr>
              <tr style="border-bottom:1px solid #f1f5f9;background:#f8fafc;"><td style="padding:.22rem .3rem;color:#475569;">2</td><td style="padding:.22rem .3rem;">Ballymun D11</td><td style="padding:.22rem .3rem;text-align:center;color:#10b981;font-weight:700;">13.2%</td><td style="padding:.22rem .3rem;text-align:center;color:#10b981;">+16%</td><td style="padding:.22rem .3rem;text-align:center;color:#f97316;font-weight:700;">⚠</td><td style="padding:.22rem .3rem;text-align:center;font-size:.48rem;color:#10b981;font-weight:700;">HIGH POT.</td><td style="padding:.22rem .3rem;text-align:center;color:#f59e0b;font-size:.55rem;">★★★</td></tr>
              <tr style="border-bottom:1px solid #f1f5f9;"><td style="padding:.22rem .3rem;color:#475569;">3</td><td style="padding:.22rem .3rem;">Clondalkin D22</td><td style="padding:.22rem .3rem;text-align:center;color:#10b981;font-weight:700;">11.9%</td><td style="padding:.22rem .3rem;text-align:center;color:#10b981;">+3.9%</td><td style="padding:.22rem .3rem;text-align:center;color:#f97316;font-weight:700;">⚠</td><td style="padding:.22rem .3rem;text-align:center;font-size:.48rem;color:#10b981;font-weight:700;">HIGH POT.</td><td style="padding:.22rem .3rem;text-align:center;color:#f59e0b;font-size:.55rem;">★★★</td></tr>
              <tr style="border-bottom:1px solid #f1f5f9;background:#f8fafc;filter:blur(2.5px);user-select:none;"><td style="padding:.22rem .3rem;">4</td><td style="padding:.22rem .3rem;">██████████</td><td style="padding:.22rem .3rem;text-align:center;">██%</td><td style="padding:.22rem .3rem;text-align:center;">+█%</td><td style="padding:.22rem .3rem;text-align:center;">█</td><td style="padding:.22rem .3rem;text-align:center;font-size:.48rem;">███ POT.</td><td style="padding:.22rem .3rem;text-align:center;">███</td></tr>
              <tr style="border-bottom:1px solid #f1f5f9;filter:blur(2.5px);user-select:none;"><td style="padding:.22rem .3rem;">5</td><td style="padding:.22rem .3rem;">██████████</td><td style="padding:.22rem .3rem;text-align:center;">██%</td><td style="padding:.22rem .3rem;text-align:center;">+█%</td><td style="padding:.22rem .3rem;text-align:center;">█</td><td style="padding:.22rem .3rem;text-align:center;font-size:.48rem;">███ POT.</td><td style="padding:.22rem .3rem;text-align:center;">███</td></tr>
              <tr style="border-bottom:1px solid #f1f5f9;background:#f8fafc;filter:blur(2.5px);user-select:none;"><td style="padding:.22rem .3rem;">6</td><td style="padding:.22rem .3rem;">██████████</td><td style="padding:.22rem .3rem;text-align:center;">██%</td><td style="padding:.22rem .3rem;text-align:center;">+█%</td><td style="padding:.22rem .3rem;text-align:center;">█</td><td style="padding:.22rem .3rem;text-align:center;font-size:.48rem;">███ POT.</td><td style="padding:.22rem .3rem;text-align:center;">███</td></tr>
              <tr style="filter:blur(2.5px);user-select:none;"><td style="padding:.22rem .3rem;">7</td><td style="padding:.22rem .3rem;">██████████</td><td style="padding:.22rem .3rem;text-align:center;">██%</td><td style="padding:.22rem .3rem;text-align:center;">+█%</td><td style="padding:.22rem .3rem;text-align:center;">█</td><td style="padding:.22rem .3rem;text-align:center;font-size:.48rem;">███ POT.</td><td style="padding:.22rem .3rem;text-align:center;">███</td></tr>
            </tbody>
          </table>
          <div style="text-align:center;margin-top:.5rem;font-size:.55rem;color:#94a3b8;">+ 408 more areas · all scored &amp; ranked</div>
        </div>
      </div>

      <!-- Page 3 thumbnail: Methodology -->
      <div style="background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 12px 40px rgba(0,0,0,.4);border:1px solid rgba(255,255,255,.06);">
        <div style="background:#f1f3f5;padding:.4rem .7rem;display:flex;gap:.35rem;align-items:center;">
          <span style="width:8px;height:8px;border-radius:50%;background:#ef4444;display:inline-block;"></span>
          <span style="width:8px;height:8px;border-radius:50%;background:#f59e0b;display:inline-block;"></span>
          <span style="width:8px;height:8px;border-radius:50%;background:#10b981;display:inline-block;"></span>
          <span style="font-size:.6rem;color:#94a3b8;margin-left:.5rem;">Page 3 — Methodology</span>
        </div>
        <div style="padding:.75rem;color:#0b1120;font-family:'DM Sans',sans-serif;">
          <div style="font-size:.6rem;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.6rem;">How Each Score is Calculated</div>
          <div style="display:flex;flex-direction:column;gap:.5rem;">
            <div style="padding:.4rem .5rem;background:#f0fdf4;border-left:2px solid #10b981;border-radius:2px;">
              <div style="font-size:.58rem;font-weight:700;color:#10b981;margin-bottom:.15rem;">📈 Growth Score</div>
              <div style="font-size:.52rem;color:#64748b;line-height:1.4;">5yr CAGR at micro-area level, volume-weighted to penalise thin markets with fewer than 10 transactions.</div>
            </div>
            <div style="padding:.4rem .5rem;background:#fffbeb;border-left:2px solid #f59e0b;border-radius:2px;">
              <div style="font-size:.58rem;font-weight:700;color:#f59e0b;margin-bottom:.15rem;">⚖️ Risk Score</div>
              <div style="font-size:.52rem;color:#64748b;line-height:1.4;">CV of yearly median prices combined with avg. annual transaction volume. Low CV + high volume = Low risk.</div>
            </div>
            <div style="padding:.4rem .5rem;background:#eff6ff;border-left:2px solid #3b82f6;border-radius:2px;">
              <div style="font-size:.58rem;font-weight:700;color:#3b82f6;margin-bottom:.15rem;">💰 Yield Estimate</div>
              <div style="font-size:.52rem;color:#64748b;line-height:1.4;">RTB Q2 2025 official rents × 0.4 dampening factor ÷ PPR median sale price. Gross estimate only.</div>
            </div>
            <div style="padding:.4rem .5rem;background:#fff7ed;border-left:2px solid #f97316;border-radius:2px;">
              <div style="font-size:.58rem;font-weight:700;color:#f97316;margin-bottom:.15rem;">⚠ RPZ Flag</div>
              <div style="font-size:.52rem;color:#64748b;line-height:1.4;">Each area cross-checked against official RTB 2024 Rent Pressure Zone list. Rent capped at 2%/yr in RPZ areas.</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- What's included checklist -->
    <div style="background:rgba(16,185,129,.06);border:1px solid rgba(16,185,129,.2);border-radius:14px;padding:2rem 2.5rem;max-width:760px;margin:0 auto 2rem;" class="fade-in">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:.75rem 2rem;">
        <div style="font-size:.85rem;color:var(--t2);display:flex;align-items:flex-start;gap:.6rem;"><span style="color:var(--green);font-weight:700;flex-shrink:0;">✓</span>All micro-areas in your county ranked by signal</div>
        <div style="font-size:.85rem;color:var(--t2);display:flex;align-items:flex-start;gap:.6rem;"><span style="color:var(--green);font-weight:700;flex-shrink:0;">✓</span>RPZ flag on every single area</div>
        <div style="font-size:.85rem;color:var(--t2);display:flex;align-items:flex-start;gap:.6rem;"><span style="color:var(--green);font-weight:700;flex-shrink:0;">✓</span>Gross yield estimate (RTB Q2 2025 rents)</div>
        <div style="font-size:.85rem;color:var(--t2);display:flex;align-items:flex-start;gap:.6rem;"><span style="color:var(--green);font-weight:700;flex-shrink:0;">✓</span>Data confidence rating (★★★ / ★★☆ / ★☆☆)</div>
        <div style="font-size:.85rem;color:var(--t2);display:flex;align-items:flex-start;gap:.6rem;"><span style="color:var(--green);font-weight:700;flex-shrink:0;">✓</span>5-year CAGR growth per micro-area</div>
        <div style="font-size:.85rem;color:var(--t2);display:flex;align-items:flex-start;gap:.6rem;"><span style="color:var(--green);font-weight:700;flex-shrink:0;">✓</span>Risk classification (Low / Medium / High)</div>
        <div style="font-size:.85rem;color:var(--t2);display:flex;align-items:flex-start;gap:.6rem;"><span style="color:var(--green);font-weight:700;flex-shrink:0;">✓</span>Price trend chart (2010–2025)</div>
        <div style="font-size:.85rem;color:var(--t2);display:flex;align-items:flex-start;gap:.6rem;"><span style="color:var(--green);font-weight:700;flex-shrink:0;">✓</span>Full methodology appendix included</div>
      </div>
    </div>

    <!-- CTA -->
    <div style="text-align:center;" class="fade-in">
      <p style="color:var(--t3);font-size:.88rem;margin-bottom:1rem;">Based on 727,000+ PPR transactions · Updated March 2026 · Instant PDF download</p>
      <a href="#reports" class="bp" style="font-size:1.05rem;padding:1rem 2.5rem;">Get the Full Report — €29 →</a>
      <p style="font-size:.78rem;color:var(--t3);margin-top:.75rem;">Or <a href="#snap" style="color:var(--green);text-decoration:none;">get the free snapshot first</a> — top 3 areas, no card needed</p>
    </div>

  </div>
</section>
<!-- ── END FULL REPORT PREVIEW ── -->

<!-- ── COMPARE COUNTIES ── -->
<section id="compare" style="padding:5rem 2rem;background:var(--bg2);border-top:1px solid var(--border);">
<style>
#compare .cc-wrap{max-width:1000px;margin:0 auto;}
#compare .cc-selectors{display:flex;gap:1rem;justify-content:center;flex-wrap:wrap;margin-bottom:2.5rem;}
#compare .cc-sel{padding:.7rem 1.2rem;background:var(--bg);border:1px solid var(--border);border-radius:10px;color:var(--t1);font-family:var(--fb);font-size:.92rem;cursor:pointer;flex:1;max-width:220px;}
#compare .cc-sel:focus{outline:none;border-color:var(--green);}
#compare .cc-add{background:none;border:1px dashed rgba(16,185,129,.4);color:var(--green);border-radius:10px;padding:.7rem 1.2rem;font-family:var(--fb);font-size:.88rem;cursor:pointer;flex:1;max-width:220px;transition:background .2s;}
#compare .cc-add:hover{background:rgba(16,185,129,.06);}
#compare .cc-table-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;}
#compare .cc-table{width:100%;border-collapse:collapse;min-width:500px;}
#compare .cc-table th{padding:.75rem 1rem;font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--t3);text-align:left;border-bottom:1px solid var(--border);}
#compare .cc-table th.cc-metric{text-align:right;}
#compare .cc-table td{padding:.9rem 1rem;border-bottom:1px solid rgba(255,255,255,.04);font-size:.9rem;vertical-align:middle;}
#compare .cc-table td.cc-metric{text-align:right;}
#compare .cc-table tr:last-child td{border-bottom:none;}
#compare .cc-table tr:hover td{background:rgba(255,255,255,.02);}
#compare .cc-county-head{font-weight:700;color:var(--t1);}
#compare .cc-winner{color:var(--green);font-weight:700;}
#compare .cc-bar-wrap{display:flex;align-items:center;gap:.5rem;justify-content:flex-end;}
#compare .cc-bar{height:6px;border-radius:3px;background:var(--green);transition:width .4s ease;}
#compare .cc-bar.amber{background:#f59e0b;}
#compare .cc-bar.red{background:#ef4444;}
#compare .cc-sig{display:inline-block;font-size:.65rem;font-weight:700;padding:.2rem .55rem;border-radius:4px;}
#compare .cc-sig.hp{background:rgba(26,107,60,.3);color:#4ade80;}
#compare .cc-sig.mo{background:rgba(245,158,11,.15);color:#f59e0b;}
#compare .cc-sig.av{background:rgba(239,68,68,.15);color:#ef4444;}
#compare .cc-risk-low{color:#4ade80;}
#compare .cc-risk-med{color:#f59e0b;}
#compare .cc-risk-high{color:#ef4444;}
#compare .cc-rpz-yes{color:#f97316;font-size:.75rem;font-weight:700;}
#compare .cc-rpz-no{color:var(--t3);font-size:.75rem;}
#compare .cc-empty{text-align:center;padding:3rem;color:var(--t3);font-size:.9rem;}
#compare .cc-remove{background:none;border:none;color:var(--t3);cursor:pointer;font-size:1rem;padding:0 .3rem;line-height:1;margin-left:.4rem;vertical-align:middle;}
#compare .cc-remove:hover{color:#ef4444;}
#compare .cc-hint{text-align:center;font-size:.8rem;color:var(--t3);margin-bottom:1.5rem;}
#compare .cc-cta-row{text-align:center;margin-top:2rem;}
@media(max-width:600px){#compare .cc-selectors{flex-direction:column;align-items:stretch;}#compare .cc-sel,#compare .cc-add{max-width:100%;}}
</style>
<div class="cc-wrap">
  <div class="sh fade-in" style="margin-bottom:2rem;">
    <div class="ol">Compare</div>
    <h2>Compare counties side-by-side</h2>
    <p>Pick up to 4 counties and see yield, growth, risk and price compared instantly.</p>
  </div>
  <div class="cc-hint">Select counties below — the best value on each metric is highlighted in green</div>
  <div class="cc-selectors" id="ccSelectors">
    <select class="cc-sel" onchange="ccUpdate()">
      <option value="">— County 1 —</option>
    </select>
    <select class="cc-sel" onchange="ccUpdate()">
      <option value="">— County 2 —</option>
    </select>
    <button class="cc-add" onclick="ccAddSlot()" id="ccAddBtn">+ Add county</button>
  </div>
  <div class="cc-table-wrap">
    <div id="ccOutput" class="cc-empty">Select at least one county above to begin comparing.</div>
  </div>
  <div class="cc-cta-row" id="ccCta" style="display:none;">
    <a href="#reports" class="bp" style="font-size:.95rem;padding:.85rem 2rem;">Get the Full Report — €29 →</a>
    <p style="font-size:.78rem;color:var(--t3);margin-top:.6rem;">Full micro-area rankings, yield estimates &amp; RPZ flags for your chosen county</p>
  </div>
</div>
<script>
(function(){
  // Populate all selects with county names from hmD
  var counties=Object.keys(hmD).sort();
  function populateSel(sel){
    var cur=sel.value;
    // keep blank option
    while(sel.options.length>1) sel.remove(1);
    counties.forEach(function(c){
      var o=document.createElement('option');
      o.value=c; o.textContent=c;
      sel.appendChild(o);
    });
    if(cur) sel.value=cur;
  }
  document.querySelectorAll('#ccSelectors .cc-sel').forEach(populateSel);

  window.ccAddSlot=function(){
    var wrap=document.getElementById('ccSelectors');
    var sels=wrap.querySelectorAll('.cc-sel');
    if(sels.length>=4){showToast('Maximum 4 counties at once.');return;}
    var sel=document.createElement('select');
    sel.className='cc-sel';
    sel.onchange=ccUpdate;
    populateSel(sel);
    // Insert before the add button
    var btn=document.getElementById('ccAddBtn');
    wrap.insertBefore(sel,btn);
    if(sels.length+1>=4) btn.style.display='none';
  };

  window.ccUpdate=function(){
    var sels=document.querySelectorAll('#ccSelectors .cc-sel');
    var chosen=[];
    sels.forEach(function(s){if(s.value) chosen.push(s.value);});
    var out=document.getElementById('ccOutput');
    var cta=document.getElementById('ccCta');
    if(chosen.length===0){
      out.className='cc-empty';
      out.innerHTML='Select at least one county above to begin comparing.';
      cta.style.display='none';
      return;
    }
    cta.style.display='block';

    // Find best value per metric for highlighting
    var best={yield:-Infinity,growth:-Infinity,price:Infinity,risk:{'Low':0,'Medium':1,'High':2}};
    var bestYield='',bestGrowth='',bestPrice='',bestRisk='';
    chosen.forEach(function(c){
      var d=hmD[c];
      if(d.yield>best.yield){best.yield=d.yield;bestYield=c;}
      if(d.growth>best.growth){best.growth=d.growth;bestGrowth=c;}
      if(d.price<best.price){best.price=d.price;bestPrice=c;}
      if(best.risk[d.risk]<best.risk[bestRisk]||bestRisk===''){bestRisk=c;}
    });

    // Max values for bar scaling
    var maxYield=Math.max.apply(null,chosen.map(function(c){return hmD[c].yield;}));
    var maxGrowth=Math.max.apply(null,chosen.map(function(c){return hmD[c].growth;}));
    var maxPrice=Math.max.apply(null,chosen.map(function(c){return hmD[c].price;}));

    // Build table
    var rows=[
      {label:'Gross Yield',key:'yield',fmt:function(v){return v+'%';},bar:true,barMax:maxYield,barColor:function(v){return v>=6?'red':v>=5?'amber':''},winner:bestYield},
      {label:'5yr Growth',key:'growth',fmt:function(v){return '+'+v+'%';},bar:true,barMax:maxGrowth,barColor:function(){return''},winner:bestGrowth},
      {label:'Median Price',key:'price',fmt:function(v){return'€'+v.toLocaleString();},bar:false,winner:bestPrice},
      {label:'Risk',key:'risk',fmt:null,bar:false,winner:bestRisk},
      {label:'Signal',key:'signal',fmt:null,bar:false,winner:''},
      {label:'RPZ Status',key:'rpz',fmt:null,bar:false,winner:''},
    ];

    var html='<table class="cc-table"><thead><tr><th>Metric</th>';
    chosen.forEach(function(c){html+='<th class="cc-metric cc-county-head">'+c+'</th>';});
    html+='</tr></thead><tbody>';

    rows.forEach(function(row){
      html+='<tr><td style="color:var(--t3);font-size:.8rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;">'+row.label+'</td>';
      chosen.forEach(function(c){
        var d=hmD[c];
        var v=d[row.key];
        var isWinner=(row.winner===c);
        var cell='';

        if(row.key==='risk'){
          var rc=v==='Low'?'cc-risk-low':v==='Medium'?'cc-risk-med':'cc-risk-high';
          cell='<span class="'+rc+'">'+v+'</span>';
        } else if(row.key==='signal'){
          var sc=v==='HIGH POTENTIAL'?'hp':v==='MODERATE'||v==='MODERATE POTENTIAL'?'mo':'av';
          var sl=v==='HIGH POTENTIAL'?'HIGH POT.':v==='MODERATE'||v==='MODERATE POTENTIAL'?'MODERATE':'AVOID';
          cell='<span class="cc-sig '+sc+'">'+sl+'</span>';
        } else if(row.key==='rpz'){
          cell=v?'<span class="cc-rpz-yes">⚠ RPZ</span>':'<span class="cc-rpz-no">No</span>';
        } else if(row.bar){
          var pct=maxYield>0?(v/row.barMax*100):0;
          var bc=row.barColor(v);
          cell='<div class="cc-bar-wrap"><span'+(isWinner?' class="cc-winner"':'')+'>'+row.fmt(v)+'</span><div class="cc-bar'+(bc?' '+bc:'')+'" style="width:'+pct+'px;max-width:80px;"></div></div>';
        } else {
          cell='<span'+(isWinner?' class="cc-winner"':'')+'>'+row.fmt(v)+'</span>';
        }
        html+='<td class="cc-metric">'+cell+'</td>';
      });
      html+='</tr>';
    });
    html+='</tbody></table>';
    out.className='';
    out.innerHTML=html;
  };

  // Init
  document.querySelectorAll('#ccSelectors .cc-sel').forEach(populateSel);
})();
</script>
</section>
<!-- ── END COMPARE COUNTIES ── -->

<section class="rs" id="reports"><div class="sh fade-in"><div class="ol">Full Reports</div><h2>Unlock the full county report</h2><p>Every micro-area in your chosen county — ranked by yield, growth, and risk. Built for investors who want data, not guesswork.</p><div style="margin-top:1.25rem;display:inline-flex;align-items:baseline;gap:.5rem"><span style="font-family:var(--fd);font-size:2.25rem;font-weight:700;color:var(--green)">€29</span><span style="font-size:.88rem;color:var(--t3)">per county · instant PDF download</span></div><p style="font-size:.82rem;color:var(--gold);margin-top:.5rem;font-weight:600">🚀 Launch price — €29 while counties are being added</p></div><div class="fade-in" style="max-width:480px;margin:0 auto;text-align:center"><div style="margin-bottom:1.5rem"><label style="display:block;font-size:.85rem;color:var(--t3);margin-bottom:.6rem;text-transform:uppercase;letter-spacing:.08em">Select your county</label><select id="countyBuySelect" style="width:100%;padding:1rem 1.2rem;background:var(--bg);border:1px solid var(--border);border-radius:10px;color:var(--t1);font-family:var(--fb);font-size:1rem;cursor:pointer"><option value="">— Choose a county —</option><optgroup label="✅ Available Now"><option value="https://diourielouafi.gumroad.com/l/dqfeno">Dublin</option><option value="https://diourielouafi.gumroad.com/l/nsofqi">Cork</option><option value="https://diourielouafi.gumroad.com/l/khbhp">Galway</option><option value="https://diourielouafi.gumroad.com/l/qzexsg">Kildare</option><option value="https://diourielouafi.gumroad.com/l/pqllej">Kerry</option><option value="https://diourielouafi.gumroad.com/l/jlixrl">Meath</option><option value="https://diourielouafi.gumroad.com/l/qjecas">Wicklow</option></optgroup><optgroup label="⏳ Coming Soon"><option value="coming">Carlow</option><option value="coming">Cavan</option><option value="coming">Clare</option><option value="coming">Donegal</option><option value="coming">Kilkenny</option><option value="coming">Laois</option><option value="coming">Leitrim</option><option value="coming">Limerick</option><option value="coming">Longford</option><option value="coming">Louth</option><option value="coming">Mayo</option><option value="coming">Monaghan</option><option value="coming">Offaly</option><option value="coming">Roscommon</option><option value="coming">Sligo</option><option value="coming">Tipperary</option><option value="coming">Waterford</option><option value="coming">Westmeath</option><option value="coming">Wexford</option></optgroup></select></div><button id="countyBuyBtn" onclick="(function(){var s=document.getElementById(\'countyBuySelect\');if(!s.value)return;if(s.value===\'coming\'){var n=s.options[s.selectedIndex].text;document.getElementById(\'reqCounty\').value=n;document.querySelector(\'#countyRequestForm input[type=email]\').focus();document.getElementById(\'countyRequestForm\').scrollIntoView({behavior:\'smooth\'});showToast(\'Enter your email below to be notified when \'+n+\' launches!\');return;}window.open(s.value,\'_blank\');})()" class="bp" style="width:100%;justify-content:center;padding:1rem 2rem;font-size:1.1rem">Get Instant Access — €29 →</button><p style="font-size:.82rem;color:var(--t3);margin-top:.75rem">7 counties live now — more added weekly. Can\'t see yours?</p><form class="ef" style="margin-top:.75rem" id="countyRequestForm"><input type="email" placeholder="your@email.com" required id="reqEmail" style="flex:1;padding:.85rem 1.2rem;background:var(--bg);border:1px solid var(--border);border-radius:10px;color:var(--t1);font-family:var(--fb);font-size:.95rem"><select id="reqCounty" style="padding:.85rem;background:var(--bg);border:1px solid var(--border);border-radius:10px;color:var(--t1);font-family:var(--fb);font-size:.9rem">%COUNTY_OPTIONS_FULL%</select><button type="submit" class="bs" style="white-space:nowrap">Request County</button></form><p style="font-size:.78rem;color:var(--t3);margin-top:.5rem">We'll email you when your county report is ready.</p></div></section>
<section id="meth"><div class="sh fade-in"><div class="ol">Methodology</div><h2>Transparent, data-driven scoring</h2><p>No black boxes. Here's exactly how we analyse the market.</p></div><div class="mg fade-in"><div class="mc"><h4>📊 Property Price Register</h4><p>Every residential transaction since 2010 — cleaned, deduplicated, and analysed.</p></div><div class="mc"><h4>🏠 RTB Rental Data</h4><p>Official Q2 2025 rent figures providing the most current yield data available.</p></div><div class="mc"><h4>📐 Growth Scoring</h4><p>CAGR at micro-area level with volume weighting to penalise thin markets.</p></div><div class="mc"><h4>⚖️ Risk Model</h4><p>Coefficient of variation, transaction frequency, and price consistency combined.</p></div></div></section>
<section style="padding:5rem 2rem;background:var(--bg2);border-top:1px solid var(--border)">
  <div style="max-width:680px;margin:0 auto">
    <div style="font-size:.75rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--green);margin-bottom:1rem">The Story</div>
    <h2 style="font-family:var(--fd);font-size:clamp(1.6rem,3vw,2.2rem);font-weight:700;line-height:1.2;margin-bottom:1.5rem">Why I built this</h2>
    <div style="display:grid;grid-template-columns:1fr;gap:1.5rem">
      <div style="padding:1.5rem;background:var(--card);border:1px solid var(--border);border-radius:12px;border-left:3px solid var(--green)">
        <div style="font-size:.82rem;font-weight:700;color:var(--green);margin-bottom:.6rem;text-transform:uppercase;letter-spacing:.08em">The Problem</div>
        <p style="color:var(--t2);font-size:.95rem;line-height:1.7">As anyone watching the Irish property market knows, county-level averages are misleading. A "6% yield in Dublin" tells you nothing about whether a specific street in Dublin 15 is a solid investment versus a cul-de-sac in Dublin 6 that hasn't moved in a decade.</p>
      </div>
      <div style="padding:1.5rem;background:var(--card);border:1px solid var(--border);border-radius:12px;border-left:3px solid var(--gold)">
        <div style="font-size:.82rem;font-weight:700;color:var(--gold);margin-bottom:.6rem;text-transform:uppercase;letter-spacing:.08em">The Goal</div>
        <p style="color:var(--t2);font-size:.95rem;line-height:1.7">I built this tool to surface the micro-data that mainstream listing sites hide. By connecting the Property Price Register with RTB rental data, the aim is to give individual buyers and local investors the same granular insight that institutional funds already use — without the €500/month price tag.</p>
      </div>
      <div style="padding:1.5rem;background:var(--card);border:1px solid var(--border);border-radius:12px;border-left:3px solid #3B82F6">
        <div style="font-size:.82rem;font-weight:700;color:#3B82F6;margin-bottom:.6rem;text-transform:uppercase;letter-spacing:.08em">The Philosophy</div>
        <p style="color:var(--t2);font-size:.95rem;line-height:1.7">Data should be transparent, not a black box. This is not a financial advice tool — it is a data analysis tool built on publicly available government records. Every signal, every yield estimate, and every confidence score is explained on the <a href="/methodology" style="color:var(--green);text-decoration:none">Methodology page</a>. No guesswork, no hidden model.</p>
      </div>
    </div>
    <p style="font-size:.82rem;color:var(--t3);margin-top:1.5rem;text-align:center">All data from <a href="https://www.propertypriceregister.ie" target="_blank" style="color:var(--t2);text-decoration:none">Property Price Register</a> &amp; <a href="https://www.rtb.ie" target="_blank" style="color:var(--t2);text-decoration:none">Residential Tenancies Board</a> — official Irish government sources.</p>
  </div>
</section>
<!-- ── FINAL CTA ── -->
<section style="padding:6rem 2rem;background:linear-gradient(135deg,#0b1120 0%,#0f1a2e 50%,#0b1120 100%);border-top:1px solid var(--border);text-align:center;">
  <div style="max-width:640px;margin:0 auto;">
    <div style="font-size:.72rem;font-weight:700;letter-spacing:.15em;text-transform:uppercase;color:var(--green);margin-bottom:1.25rem;">Ready to invest smarter?</div>
    <h2 style="font-family:var(--fd);font-size:clamp(1.8rem,4vw,2.8rem);font-weight:700;line-height:1.15;margin-bottom:1.25rem;color:var(--t1);">Find Ireland's Best Rental<br>Areas — Starting Free</h2>
    <p style="color:var(--t3);font-size:.95rem;line-height:1.65;max-width:440px;margin:0 auto 2.5rem;">Get your free county snapshot now. Upgrade to the full report when you're ready — 500+ micro-areas, ranked by yield, growth & risk.</p>
    <div style="display:flex;gap:1rem;justify-content:center;flex-wrap:wrap;margin-bottom:1rem;">
      <a href="#snap" class="bp" style="font-size:1.05rem;padding:1rem 2.4rem;">Get Free Snapshot →</a>
      <a href="#reports" class="bs" style="padding:1rem 2rem;">Full Report — €29</a>
    </div>
    <p style="font-size:.78rem;color:var(--t3);">No credit card · Based on 727,000+ verified transactions · Official government data</p>
  </div>
</section>
<!-- ── END FINAL CTA ── -->

<script>
document.querySelectorAll('.fqq').forEach(function(q){
  q.addEventListener('click',function(){
    var fi=this.closest('.fi');
    document.querySelectorAll('.fi.open').forEach(function(o){if(o!==fi)o.classList.remove('open');});
    fi.classList.toggle('open');
  });
});
</script>
<footer>
  <p>© 2026 IrishPropertyInsights · Data: <a href="https://www.propertypriceregister.ie" target="_blank">PPR</a> &amp; <a href="https://www.rtb.ie" target="_blank">RTB</a> · <a href="/methodology">Methodology</a> · <a href="/privacy">Privacy Policy</a> · <a href="mailto:hello@irishpropertyinsights.ie">hello@irishpropertyinsights.ie</a></p>
  <p style="margin-top:.4rem;font-size:.76rem;color:var(--t3)">IrishPropertyInsights provides data analysis based on public records. It is not financial advice. Always consult a qualified advisor before making investment decisions.</p>
</footer>
<div class="toast" id="toast"></div>

<!-- ── BACK TO TOP ── -->
<button id="btt" onclick="window.scrollTo({top:0,behavior:'smooth'})" title="Back to top" aria-label="Back to top">
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="18 15 12 9 6 15"/></svg>
</button>
<style>
#btt{position:fixed;bottom:5.5rem;right:1.5rem;z-index:190;width:42px;height:42px;border-radius:50%;background:var(--bg2);border:1px solid var(--border);color:var(--t2);cursor:pointer;display:flex;align-items:center;justify-content:center;opacity:0;transform:translateY(12px);transition:opacity .3s,transform .3s,background .2s,border-color .2s;pointer-events:none;}
#btt.visible{opacity:1;transform:translateY(0);pointer-events:auto;}
#btt:hover{background:rgba(16,185,129,.12);border-color:rgba(16,185,129,.4);color:var(--green);}
@media(max-width:480px){#btt{bottom:4.5rem;right:1rem;width:38px;height:38px;}}
</style>
<script>
(function(){
  var b=document.getElementById('btt');
  window.addEventListener('scroll',function(){
    window.scrollY>400?b.classList.add('visible'):b.classList.remove('visible');
  },{passive:true});
})();
</script>
<script>
const o=new IntersectionObserver(e=>{e.forEach(e=>{e.isIntersecting&&e.target.classList.add('visible')})},{threshold:.15});
document.querySelectorAll('.fade-in').forEach(e=>o.observe(e));
function showToast(m){const t=document.getElementById('toast');t.textContent=m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),3500)}
const rf=document.getElementById('countyRequestForm');if(rf){rf.addEventListener('submit',async function(e){e.preventDefault();const em=document.getElementById('reqEmail').value;const co=document.getElementById('reqCounty').value;try{const res=await fetch('https://formspree.io/f/xdalrzrn',{method:'POST',headers:{'Content-Type':'application/json','Accept':'application/json'},body:JSON.stringify({email:em,county:co,message:'County report request: '+co+' from '+em})});if(res.ok){showToast('✓ Request received! We will email you when '+co+' is ready.');}else{showToast('✓ Request received! We will email you when '+co+' is ready.');}}catch(err){showToast('✓ Request received! We will email you when '+co+' is ready.');}rf.reset();})}\nfunction openSnapModal(){const c=document.getElementById('snapCounty').value;if(!c){showToast('Please select a county first.');return;}document.getElementById('modalCountyName').textContent=c;document.getElementById('snapModal').style.display='flex';document.getElementById('snapEmail').focus();}
function closeSnapModal(){document.getElementById('snapModal').style.display='none';document.getElementById('snapEmail').value='';}
async function submitSnapModal(){const em=document.getElementById('snapEmail').value;const co=document.getElementById('snapCounty').value;if(!em||!em.includes('@')){showToast('Please enter a valid email.');return;}try{await fetch('https://formspree.io/f/xdalrzrn',{method:'POST',headers:{'Content-Type':'application/json','Accept':'application/json'},body:JSON.stringify({email:em,county:co,type:'snapshot_download',message:'Free snapshot downloaded: '+co+' by '+em})});}catch(e){}closeSnapModal();showToast('✓ Downloading your '+co+' snapshot...');setTimeout(()=>{window.location.href='/snapshot?county='+encodeURIComponent(co);},600);setTimeout(()=>{const reportsEl=document.getElementById('reports');if(reportsEl){const sel=document.getElementById('countyBuySelect');if(sel){for(let i=0;i<sel.options.length;i++){if(sel.options[i].text===co){sel.value=sel.options[i].value;break;}}}showToast('📊 Want all micro-areas for '+co+'? Scroll to Full Reports — €29');reportsEl.scrollIntoView({behavior:'smooth'});}},4000);}
document.addEventListener('keydown',function(e){if(e.key==='Escape')closeSnapModal();});
</script>

<!-- ── COOKIE CONSENT BANNER ── -->
<div id="cookieBanner" style="display:none;">
  <div id="cookieBannerInner">
    <div id="cookieText">
      <strong style="color:var(--t1);display:block;margin-bottom:.3rem;">🍪 Cookie notice</strong>
      <span>We use minimal cookies — only session storage to remember your preferences (e.g. dismissed popups). No advertising or tracking cookies. Read our <a href="/privacy" style="color:var(--green);text-decoration:underline;">Privacy Policy</a>.</span>
    </div>
    <div id="cookieActions">
      <button id="cookieDecline" onclick="cookieRespond(false)">Decline</button>
      <button id="cookieAccept" onclick="cookieRespond(true)">Accept</button>
    </div>
  </div>
</div>
<style>
#cookieBanner{position:fixed;bottom:0;left:0;right:0;z-index:300;padding:.9rem 1.5rem;background:rgba(15,20,35,.97);backdrop-filter:blur(12px);border-top:1px solid rgba(16,185,129,.2);animation:slideUpCookie .35s ease forwards;}
@keyframes slideUpCookie{from{transform:translateY(100%);}to{transform:translateY(0);}}
#cookieBannerInner{max-width:900px;margin:0 auto;display:flex;align-items:center;gap:1.5rem;flex-wrap:wrap;}
#cookieText{flex:1;min-width:220px;font-size:.82rem;color:var(--t2);line-height:1.5;}
#cookieActions{display:flex;gap:.6rem;flex-shrink:0;}
#cookieDecline{background:none;border:1px solid var(--border);color:var(--t3);padding:.5rem 1.1rem;border-radius:8px;font-family:var(--fb);font-size:.82rem;cursor:pointer;transition:border-color .2s,color .2s;}
#cookieDecline:hover{border-color:var(--t2);color:var(--t1);}
#cookieAccept{background:var(--green);border:none;color:#0b1120;padding:.5rem 1.25rem;border-radius:8px;font-family:var(--fb);font-size:.82rem;font-weight:700;cursor:pointer;transition:opacity .2s;}
#cookieAccept:hover{opacity:.88;}
@media(max-width:500px){
  #cookieBanner{padding:.75rem 1rem;}
  #cookieBannerInner{gap:.75rem;}
  #cookieText{font-size:.78rem;}
  #cookieDecline,#cookieAccept{padding:.45rem .9rem;font-size:.78rem;}
}
</style>
<script>
(function(){
  // Show banner only if user hasn't responded yet
  if(!localStorage.getItem('cookieConsent')){
    // Small delay so it doesn't flash on load
    setTimeout(function(){
      document.getElementById('cookieBanner').style.display='block';
    }, 1200);
  }
})();
function cookieRespond(accepted){
  localStorage.setItem('cookieConsent', accepted ? 'accepted' : 'declined');
  var b=document.getElementById('cookieBanner');
  b.style.transition='transform .3s ease, opacity .3s ease';
  b.style.transform='translateY(100%)';
  b.style.opacity='0';
  setTimeout(function(){b.style.display='none';},320);
  if(accepted) showToast('✓ Preferences saved');
}
</script>
<div style="text-align:center;padding:1.5rem 2rem;border-top:1px solid #e8e4dc;margin-top:2rem;font-size:.76rem;color:#9a9690;line-height:1.6;">
  IrishPropertyInsights provides data analysis based on public records. It is not financial advice.<br>
  <a href="/" style="color:#9a9690">Home</a> · <a href="/methodology" style="color:#9a9690">Methodology</a>
</div>
</body></html>"""


COUNTIES = [
    "Carlow","Cavan","Clare","Cork","Donegal","Dublin","Galway","Kerry",
    "Kildare","Kilkenny","Laois","Leitrim","Limerick","Longford","Louth",
    "Mayo","Meath","Monaghan","Offaly","Roscommon","Sligo","Tipperary",
    "Waterford","Westmeath","Wexford","Wicklow"
]


def get_landing_html():
    opts = "\n".join(f'<option value="{c}">{c}</option>' for c in COUNTIES)
    full_opts = '<option value="" disabled selected>Select a county...</option>\n' + opts
    html = LANDING_HTML.replace("%COUNTY_OPTIONS%", opts)
    html = html.replace("%COUNTY_OPTIONS_FULL%", full_opts)
    return html


# ─── ROUTES ─────────────────────────────────────────────
@app.route("/")
def home():
    return get_landing_html()


@app.route("/report")
def report():
    county = request.args.get("county", "").strip()
    if county not in COUNTIES:
        return "Invalid county", 400

    try:
        analysis = analyse_county(county)
        if analysis is None:
            return f"Not enough data for {county}", 400

        pdf_path = build_pdf_report(analysis, is_snapshot=False)
        return send_file(pdf_path, as_attachment=True,
                         download_name=f"{county}_Investment_Report_2025.pdf")
    except Exception as e:
        print(f"Error generating report for {county}: {e}")
        import traceback
        traceback.print_exc()
        return f"Error generating report: {str(e)}", 500


@app.route("/snapshot")
def snapshot():
    county = request.args.get("county", "").strip()
    if county not in COUNTIES:
        return "Invalid county", 400

    try:
        analysis = analyse_county(county)
        if analysis is None:
            return f"Not enough data for {county}", 400

        pdf_path = build_pdf_report(analysis, is_snapshot=True)
        return send_file(pdf_path, as_attachment=True,
                         download_name=f"{county}_Free_Snapshot_2025.pdf")
    except Exception as e:
        print(f"Error generating snapshot for {county}: {e}")
        import traceback
        traceback.print_exc()
        return f"Error generating snapshot: {str(e)}", 500


# ─── RUN ────────────────────────────────────────────────








# ── DEAL CHECKER ──────────────────────────────────────────────
import threading
_model_cache = {}

def _load_or_train():
    import joblib, json, numpy as np
    import pandas as pd
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import LabelEncoder

    pkl = "deal_scorer_model.pkl"

    # Already trained?
    if os.path.exists(pkl):
        try:
            _model_cache["model"]    = joblib.load(pkl)
            _model_cache["le_county"] = joblib.load("le_county.pkl")
            _model_cache["le_desc"]   = joblib.load("le_desc.pkl")
            _model_cache["le_micro"]  = joblib.load("le_micro.pkl")
            with open("known_values.json") as f:
                _model_cache["known"] = json.load(f)
            _model_cache["ready"] = True
            print("Model loaded from disk.")
            return
        except Exception as e:
            print("Load failed, retraining:", e)

    # Download PPR CSV
    csv_path = "PPR-ALL.csv"
    if not os.path.exists(csv_path) and not os.path.exists("PPR-ALL.zip"):
        print("Downloading PPR CSV…")
        import urllib.request
        # Download from Google Drive
        url = "https://drive.google.com/uc?export=download&id=1_swvDrOfx66RHsDWwaGpn6Cifx3NLktV"
        try:
            # Use requests with timeout instead of urlretrieve
            import requests as req_lib
            import ssl
            # Google Drive large file download (handles virus scan confirmation)
            session = req_lib.Session()
            resp = session.get(url, stream=True, verify=False, timeout=300)
            # Check for Google Drive confirmation page
            token = None
            for key, value in resp.cookies.items():
                if key.startswith("download_warning"):
                    token = value
                    break
            if token:
                params = {"confirm": token, "id": "1_swvDrOfx66RHsDWwaGpn6Cifx3NLktV"}
                resp = session.get("https://drive.google.com/uc?export=download", 
                                   params=params, stream=True, verify=False, timeout=300)
            with open("PPR-ALL.csv", "wb") as cf:
                for chunk in resp.iter_content(chunk_size=32768):
                    if chunk:
                        cf.write(chunk)
            csv_path = "PPR-ALL.csv"  # Already a CSV, no zip extraction needed
            print("PPR CSV downloaded from Google Drive.")
        except Exception as e:
            print("Download failed:", e)
            _model_cache["ready"] = False
            _model_cache["error"] = str(e)
            return

    print("Training model…")
    try:
        df = pd.read_csv(csv_path, encoding="latin-1", low_memory=False)
        df.columns = ["date_of_sale","address","county","eircode","price",
                      "not_full_market_price","vat_exclusive","description",
                      "property_size_desc"]
        df["price"] = df["price"].astype(str).str.replace(r"[^\d.]","",regex=True)
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        df = df[df["not_full_market_price"].astype(str).str.strip() == "No"].copy()
        df = df.dropna(subset=["price","county","description"])
        df = df[(df["price"] >= 30000) & (df["price"] <= 3_000_000)]
        df["year"] = pd.to_datetime(df["date_of_sale"], dayfirst=True, errors="coerce").dt.year
        df["micro"] = df["address"].astype(str).str.split(",").str[-2].str.strip().str.title()

        le_county = LabelEncoder(); df["county_enc"] = le_county.fit_transform(df["county"].astype(str))
        le_desc   = LabelEncoder(); df["desc_enc"]   = le_desc.fit_transform(df["description"].astype(str))
        le_micro  = LabelEncoder(); df["micro_enc"]  = le_micro.fit_transform(df["micro"].astype(str))

        import numpy as np
        X = df[["county_enc","micro_enc","desc_enc","year"]]
        y = np.log1p(df["price"])

        model = RandomForestRegressor(n_estimators=50, n_jobs=-1, random_state=42)
        model.fit(X, y)

        joblib.dump(model,    "deal_scorer_model.pkl")
        joblib.dump(le_county,"le_county.pkl")
        joblib.dump(le_desc,  "le_desc.pkl")
        joblib.dump(le_micro, "le_micro.pkl")
        known = {"counties": sorted(df["county"].dropna().unique().tolist()),
                 "descriptions": sorted(df["description"].dropna().unique().tolist())}
        with open("known_values.json","w") as f:
            json.dump(known, f)

        _model_cache["model"]     = model
        _model_cache["le_county"] = le_county
        _model_cache["le_desc"]   = le_desc
        _model_cache["le_micro"]  = le_micro
        _model_cache["known"]     = known
        _model_cache["ready"]     = True
        print("Model trained and saved.")
    except Exception as e:
        print("Training failed:", e)
        _model_cache["ready"] = False
        _model_cache["error"] = str(e)

# Start training in background when app boots
threading.Thread(target=_load_or_train, daemon=True).start()


COUNTIES_LIST = [
    "Carlow","Cavan","Clare","Cork","Donegal","Dublin","Galway","Kerry",
    "Kildare","Kilkenny","Laois","Leitrim","Limerick","Longford","Louth",
    "Mayo","Meath","Monaghan","Offaly","Roscommon","Sligo","Tipperary",
    "Waterford","Westmeath","Wexford","Wicklow"
]

@app.route("/deal-checker", methods=["GET", "POST"])
def deal_checker():
    import numpy as np

    county_opts = "\n".join(
        f'<option value="{c}">{c}</option>' for c in COUNTIES_LIST
    )

    FORM_HTML = f"""<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Deal Checker | Irish Property Insights</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root{{--ink:#0f1014;--paper:#f5f2ec;--gold:#c9a84c;--muted:#6b6860;--border:#ddd8ce;}}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:var(--paper);color:var(--ink);font-family:'DM Sans',sans-serif;min-height:100vh;}}
nav{{border-bottom:1px solid var(--border);padding:1.2rem 2rem;display:flex;align-items:center;justify-content:space-between;background:var(--paper);}}
.nav-logo{{font-family:'Playfair Display',serif;font-size:1.2rem;font-weight:700;color:var(--ink);text-decoration:none;}}
.hero{{padding:4rem 2rem 2rem;max-width:700px;margin:0 auto;text-align:center;}}
.hero-tag{{display:inline-block;font-size:0.72rem;font-weight:500;letter-spacing:0.15em;text-transform:uppercase;color:var(--gold);border:1px solid var(--gold);padding:0.3rem 0.8rem;border-radius:2px;margin-bottom:1.5rem;}}
.hero h1{{font-family:'Playfair Display',serif;font-size:clamp(2rem,5vw,3rem);font-weight:900;line-height:1.1;margin-bottom:1rem;}}
.hero p{{color:var(--muted);font-size:1rem;font-weight:300;line-height:1.7;max-width:500px;margin:0 auto;}}
.form-wrapper{{max-width:620px;margin:2rem auto 4rem;padding:0 1.5rem;}}
.form-card{{background:white;border:1px solid var(--border);border-radius:4px;padding:2.5rem;box-shadow:0 4px 24px rgba(0,0,0,0.06);}}
.form-row{{display:grid;grid-template-columns:1fr 1fr;gap:1.2rem;margin-bottom:1.2rem;}}
.form-group{{display:flex;flex-direction:column;gap:0.4rem;}}
label{{font-size:0.78rem;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;color:var(--muted);}}
input,select{{font-family:'DM Sans',sans-serif;font-size:1rem;padding:0.75rem 1rem;border:1px solid var(--border);border-radius:3px;background:var(--paper);color:var(--ink);}}
.price-wrap{{position:relative;}}
.price-wrap span{{position:absolute;left:1rem;top:50%;transform:translateY(-50%);color:var(--muted);}}
.price-wrap input{{padding-left:1.8rem;}}
.submit-btn{{width:100%;padding:1rem;background:var(--ink);color:white;border:none;border-radius:3px;font-family:'DM Sans',sans-serif;font-size:0.9rem;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;cursor:pointer;margin-top:0.5rem;}}
.notice{{text-align:center;padding:2rem;color:var(--muted);font-size:0.9rem;}}
.disclaimer{{text-align:center;font-size:0.75rem;color:var(--muted);margin-top:1rem;}}
</style></head>
<body>
<nav><a href="/" class="nav-logo">IrishProperty<span style="color:#4ade80">Insights</span></a><a href="/" style="font-size:0.85rem;color:#6b6860;text-decoration:none;">← Back</a></nav>
<div class="hero">
  <div class="hero-tag">AI-Powered Analysis</div>
  <h1>Is This Property a Good Deal?</h1>
  <p>Trained on 700,000+ real Irish property transactions from the PPR.</p>
</div>
<div class="form-wrapper">
  <div class="form-card">
    <form method="POST" action="/deal-checker">
      <div class="form-row">
        <div class="form-group">
          <label>County</label>
          <select name="county" required>
            <option value="" disabled selected>Select county</option>
            {county_opts}
          </select>
        </div>
        <div class="form-group">
          <label>Area / Town</label>
          <input type="text" name="area" placeholder="e.g. Blackrock" required>
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Asking Price</label>
          <div class="price-wrap">
            <span>€</span>
            <input type="number" name="asking_price" placeholder="e.g. 350000" required>
          </div>
        </div>
      </div>
      <button type="submit" class="submit-btn">Analyse This Property</button>
    </form>
    <p class="disclaimer">Not financial advice. Based on PPR data 2010–2024.</p>
  </div>
</div>
</body></html>"""

    if request.method == "GET":
        return FORM_HTML

    # POST — score the property
    if not _model_cache.get("ready"):
        training = _model_cache.get("ready") is None or "model" not in _model_cache
        msg = "Model is still training, please try again in 60 seconds." if training else _model_cache.get("error","Unknown error")
        return f"""<!DOCTYPE html><html><body style="font-family:sans-serif;padding:2rem;">
        <h2>One moment...</h2><p>{msg}</p>
        <a href="/deal-checker">← Try again</a></body></html>"""

    county       = request.form.get("county","").strip().title()
    area         = request.form.get("area","").strip().title()
    asking_price = float(request.form.get("asking_price", 0))

    le_county = _model_cache["le_county"]
    le_desc   = _model_cache["le_desc"]
    le_micro  = _model_cache["le_micro"]
    model     = _model_cache["model"]

    try: county_enc = le_county.transform([county])[0]
    except: county_enc = 0
    try: micro_enc = le_micro.transform([area])[0]
    except: micro_enc = 0
    desc_enc = 0

    import pandas as pd
    X = pd.DataFrame({"county_enc":[county_enc],"micro_enc":[micro_enc],"desc_enc":[desc_enc],"year":[2024]})
    predicted  = np.expm1(model.predict(X)[0])
    diff_pct   = ((asking_price - predicted) / predicted) * 100

    if diff_pct <= -15: verdict,color,bg = "HIGH POTENTIAL","#1a6b3c","#f0faf4"
    elif diff_pct <= -5: verdict,color,bg = "GOOD DEAL","#1a6b3c","#f0faf4"
    elif diff_pct <= 5:  verdict,color,bg = "FAIR","#a07c10","#fffbf0"
    elif diff_pct <= 15: verdict,color,bg = "OVERPRICED","#d4821a","#fff8f0"
    else:                verdict,color,bg = "AVOID","#c0392b","#fdf2f2"

    return f"""<!DOCTYPE html>
<html><head>
<meta charset="UTF-8"><title>Deal Checker | Irish Property Insights</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:#f5f2ec;font-family:'DM Sans',sans-serif;}}
nav{{border-bottom:1px solid #ddd8ce;padding:1.2rem 2rem;display:flex;align-items:center;justify-content:space-between;background:#f5f2ec;}}
.nav-logo{{font-family:'Playfair Display',serif;font-size:1.2rem;font-weight:700;color:#0f1014;text-decoration:none;}}
.result-card{{max-width:620px;margin:3rem auto;padding:0 1.5rem;}}
.result-inner{{background:white;border:1px solid #ddd8ce;border-radius:4px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.06);}}
.verdict-banner{{padding:2rem 2.5rem;border-bottom:1px solid #ddd8ce;background:{bg};border-left:5px solid {color};}}
.verdict-label{{font-size:0.72rem;letter-spacing:0.15em;text-transform:uppercase;color:#6b6860;margin-bottom:0.5rem;}}
.verdict-text{{font-family:'Playfair Display',serif;font-size:2rem;font-weight:900;color:{color};}}
.verdict-diff{{margin-top:0.4rem;font-size:0.95rem;color:#6b6860;}}
.metrics{{display:grid;grid-template-columns:1fr 1fr;border-bottom:1px solid #ddd8ce;}}
.metric{{padding:1.5rem 2.5rem;border-right:1px solid #ddd8ce;}}
.metric:last-child{{border-right:none;}}
.metric-label{{font-size:0.72rem;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;margin-bottom:0.4rem;}}
.metric-value{{font-family:'Playfair Display',serif;font-size:1.6rem;font-weight:700;}}
.footer{{padding:1.2rem 2.5rem;background:#f5f2ec;font-size:0.8rem;color:#6b6860;}}
.try-again{{display:block;text-align:center;margin-top:1.5rem;color:#6b6860;text-decoration:underline;cursor:pointer;}}
</style></head>
<body>
<nav><a href="/" class="nav-logo">IrishProperty<span style="color:#4ade80">Insights</span></a><a href="/" style="font-size:0.85rem;color:#6b6860;text-decoration:none;">← Back</a></nav>
<div class="result-card">
  <div class="result-inner">
    <div class="verdict-banner">
      <div class="verdict-label">Our verdict for {area}, {county}</div>
      <div class="verdict-text">{verdict}</div>
      <div class="verdict-diff">{diff_pct:+.1f}% vs estimated market value</div>
    </div>
    <div class="metrics">
      <div class="metric">
        <div class="metric-label">Asking Price</div>
        <div class="metric-value">€{asking_price:,.0f}</div>
      </div>
      <div class="metric">
        <div class="metric-label">Estimated Value</div>
        <div class="metric-value">€{predicted:,.0f}</div>
      </div>
    </div>
    <div class="footer">Based on PPR data 2010–2024. Not financial advice. <a href="/" style="color:#0f1014">View full reports →</a></div>
  </div>
  <a class="try-again" href="/deal-checker">Check another property</a>
</div>
</body></html>"""
# ── END DEAL CHECKER ───────────────────────────────────────────

@app.route("/methodology")
def methodology():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Methodology | IrishPropertyInsights</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=Fraunces:wght@300;500;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'DM Sans',sans-serif;background:#0B1120;color:#F1F5F9;line-height:1.7}
nav{padding:1.2rem 2rem;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid rgba(148,163,184,.1);background:rgba(11,17,32,.9)}
.nl{font-family:'Fraunces',serif;font-size:1.2rem;font-weight:700;color:#F1F5F9;text-decoration:none}
.nl span{color:#10B981}
.back{font-size:.85rem;color:#94A3B8;text-decoration:none}
.back:hover{color:#F1F5F9}
main{max-width:760px;margin:0 auto;padding:4rem 2rem}
h1{font-family:'Fraunces',serif;font-size:2.4rem;font-weight:700;margin-bottom:.75rem;line-height:1.15}
.sub{color:#94A3B8;font-size:1.05rem;margin-bottom:3rem;max-width:560px}
.section{margin-bottom:2.5rem;padding:2rem;background:#1A2332;border:1px solid rgba(148,163,184,.1);border-radius:12px;border-left:3px solid #10B981}
.section.gold{border-left-color:#F59E0B}
.section.blue{border-left-color:#3B82F6}
.section.red{border-left-color:#EF4444}
h2{font-family:'Fraunces',serif;font-size:1.25rem;font-weight:600;margin-bottom:.75rem;color:#F1F5F9}
p{color:#94A3B8;font-size:.95rem;margin-bottom:.75rem}
p:last-child{margin-bottom:0}
strong{color:#CBD5E1}
.conf-table{width:100%;border-collapse:collapse;margin-top:1rem;font-size:.88rem}
.conf-table th{text-align:left;padding:.6rem 1rem;background:rgba(148,163,184,.08);color:#64748B;font-weight:600;font-size:.78rem;text-transform:uppercase;letter-spacing:.06em}
.conf-table td{padding:.6rem 1rem;border-top:1px solid rgba(148,163,184,.08);color:#94A3B8}
.conf-table tr:hover td{background:rgba(255,255,255,.02)}
.badge{display:inline-block;padding:.2rem .6rem;border-radius:4px;font-size:.75rem;font-weight:700}
.badge.gold{background:rgba(245,158,11,.15);color:#F59E0B}
.badge.silver{background:rgba(148,163,184,.15);color:#CBD5E1}
.badge.bronze{background:rgba(180,120,60,.15);color:#C97A3A}
.tip{position:relative;cursor:help;display:inline-block}
.tip .tiptext{visibility:hidden;opacity:0;width:260px;background:#1E293B;color:#CBD5E1;font-size:.78rem;line-height:1.6;padding:.7rem 1rem;border-radius:8px;border:1px solid rgba(148,163,184,.15);position:absolute;z-index:10;bottom:130%;left:50%;transform:translateX(-50%);transition:opacity .2s;pointer-events:none;text-align:left}
.tip .tiptext::after{content:"";position:absolute;top:100%;left:50%;transform:translateX(-50%);border:5px solid transparent;border-top-color:#1E293B}
.tip:hover .tiptext{visibility:visible;opacity:1}
.disclaimer{margin-top:3rem;padding:1.5rem;background:rgba(239,68,68,.06);border:1px solid rgba(239,68,68,.15);border-radius:8px;font-size:.85rem;color:#94A3B8}
footer{text-align:center;padding:2rem;border-top:1px solid rgba(148,163,184,.1);font-size:.8rem;color:#475569}
footer a{color:#64748B;text-decoration:none}
</style>
</head>
<body>
<nav>
  <a href="/" class="nl">Irish<span>Property</span>Insights</a>
  <a href="/" class="back">← Back to site</a>
</nav>
<main>
  <h1>Data Transparency &amp; Methodology</h1>
  <p class="sub">How we turn 727,000 raw property transactions into actionable investment signals — and how to read our confidence scores.</p>

  <div class="section">
    <h2>📊 Data Source 1 — Property Price Register (PPR)</h2>
    <p>We ingest every residential property transaction registered in Ireland since 2010 from the <strong>Property Services Regulatory Authority's Property Price Register</strong> — the official government record of all settled sale prices.</p>
    <p>Unlike asking prices on listing sites like Daft or MyHome, PPR data reflects <strong>actual completed transactions</strong>. We clean, deduplicate, and normalise this data to extract micro-area signals.</p>
    <p><strong>Coverage:</strong> 727,000+ transactions across all 26 counties, 2010–2024.</p>
  </div>

  <div class="section gold">
    <h2>🏠 Data Source 2 — RTB Rental Index</h2>
    <p>Rental yield estimates are cross-referenced with <strong>Residential Tenancies Board (RTB) Q2 2025 quarterly rent data</strong> — the official Irish government rental index.</p>
    <p>We map county-level RTB rents to micro-areas using a <strong>0.4× dampening factor</strong> that adjusts for the price difference between a micro-area and its county average. This prevents overstating yields in lower-priced areas.</p>
    <p><strong>Formula:</strong> Gross Yield = (Adjusted Annual Rent ÷ Micro-Area Median Price) × 100</p>
  </div>

  <div class="section blue">
    <h2>📈 Growth Calculation</h2>
    <p>5-year <strong>Compound Annual Growth Rate (CAGR)</strong> is calculated for each micro-area using yearly median sale prices. Only micro-areas with <strong>10+ transactions in the 5-year window</strong> are included — thin markets are excluded entirely.</p>
    <p><strong>Formula:</strong> CAGR = ((Latest Median ÷ Earliest Median) ^ (1 ÷ Years)) − 1</p>
  </div>

  <div class="section">
    <h2>⚖️ Risk Model</h2>
    <p>Risk is assessed using the <strong>Coefficient of Variation (CV)</strong> — price standard deviation divided by mean — combined with average annual transaction volume.</p>
    <p><strong>Low Risk:</strong> CV &lt; 15% and 5+ annual transactions.<br>
       <strong>Medium Risk:</strong> CV &lt; 25% or 3+ annual transactions.<br>
       <strong>High Risk:</strong> All others. Thinly-traded markets are penalised.</p>
  </div>

  <div class="section gold">
    <h2>🎯 Investment Signals</h2>
    <p>Each micro-area receives a composite data signal based on weighted scoring of growth rate, gross yield, and risk classification. These are <strong>data indicators, not financial advice</strong>.</p>
    <table class="conf-table">
      <tr><th>Signal</th><th>What it means</th></tr>
      <tr><td><strong>HIGH POTENTIAL</strong></td><td>Strong yield, strong growth, low-medium risk. Score ≥ 6. <em style="color:#F59E0B">Check RPZ status — yield assumes market rent.</em></td></tr>
      <tr><td><strong>GOOD PROSPECT</strong></td><td>Above-average on multiple dimensions. Score 4–5.</td></tr>
      <tr><td><strong>MODERATE POTENTIAL</strong></td><td>Some positive indicators but not across the board. Score 2–3.</td></tr>
      <tr><td><strong>HOLD</strong></td><td>Neutral — no strong positive or negative signals. Score 0–1.</td></tr>
      <tr><td><strong>CAUTION</strong></td><td>Negative growth, high risk, or poor yield combination. Score &lt; 0.</td></tr>
    </table>
  </div>

  <div class="section blue">
    <h2>🏅 Data Confidence Score</h2>
    <p>Every micro-area is assigned a confidence level based on the number of recent transactions. Low sample sizes can be skewed by a single high-value sale — the confidence score tells you how much weight to give the signal.</p>
    <table class="conf-table">
      <tr><th>Badge</th><th>Transactions</th><th>Meaning</th></tr>
      <tr><td><span class="tip"><span class="badge gold">🟡 High</span><span class="tiptext">Calculated from 15+ recent transactions. This area shows high liquidity and consistent price trends, making the projected yield statistically reliable.</span></span></td><td>15+ sales</td><td>Statistically significant. Trends are reliable.</td></tr>
      <tr><td><span class="tip"><span class="badge silver">⚪ Medium</span><span class="tiptext">Based on a moderate number of sales. While the trend is clear, we recommend checking for individual high-value outliers that may slightly skew the average.</span></span></td><td>6–14 sales</td><td>Good indicator. Check for 1–2 outliers that may skew the average.</td></tr>
      <tr><td><span class="tip"><span class="badge bronze">🟤 Low</span><span class="tiptext">Data is based on a small sample size (fewer than 6 sales). This signal should be used as an early-stage indicator rather than a definitive valuation. A single high-value sale can skew the average significantly.</span></span></td><td>1–5 sales</td><td>Small sample. Use as early-stage indicator only — not a final valuation.</td></tr>
    </table>
  </div>


  <div class="section red" style="border-left-color:#F59E0B">
    <h2>🏘️ Rent Pressure Zone (RPZ) Indicator</h2>
    <p>Every micro-area now shows an <strong>RPZ flag</strong> — indicating whether that area falls within an official <strong>Rent Pressure Zone</strong> as designated by the Irish Government and the Residential Tenancies Board (RTB).</p>
    <p>In RPZ areas, annual rent increases are <strong>capped at 2% or the rate of inflation (HICP), whichever is lower</strong>. This is a critical variable for any landlord or buy-to-let investor — a HIGH POTENTIAL signal based on current market rent may be misleading if the property already has a sitting tenant in an RPZ, since you cannot increase rent to market rate.</p>
    <table class="conf-table">
      <tr><th>RPZ Status</th><th>What it means for investors</th></tr>
      <tr><td><strong>⚠ Yes — RPZ</strong></td><td>Rent increases capped at 2%/HICP. Yield calculation reflects current market rent, not necessarily achievable rent for existing tenancies.</td></tr>
      <tr><td><strong>No — Non-RPZ</strong></td><td>No statutory rent cap. Rent can be set at market rate on a new tenancy.</td></tr>
    </table>
    <p style="margin-top:.75rem;font-size:.88rem;color:#64748B">RPZ boundaries are based on the RTB's official 2024 designations. Always verify current status at <a href="https://www.rtb.ie/registration-and-compliance/rent-pressure-zones" target="_blank" style="color:#94A3B8">rtb.ie</a> before making investment decisions. Micro-area matching uses keyword-based detection — verify manually for boundary areas.</p>
  </div>

  <div class="disclaimer">
    <strong>Important:</strong> All signals and scores are generated from historical public records for informational purposes only. They do not constitute financial advice. Gross yield estimates do not account for management fees, maintenance, LPT, vacancy, or financing costs. Always conduct independent due diligence and consult a qualified financial advisor before making any investment decision.
  </div>

  <div style="text-align:center;margin-top:3rem;padding:2.5rem;background:#1A2332;border:1px solid rgba(148,163,184,.1);border-radius:16px;">
    <p style="color:#94A3B8;font-size:.95rem;margin-bottom:1.25rem;">Ready to put this into practice?</p>
    <h3 style="font-family:'Fraunces',serif;font-size:1.4rem;font-weight:600;margin-bottom:1.5rem;color:#F1F5F9;">See the data for your county</h3>
    <div style="display:flex;gap:1rem;justify-content:center;flex-wrap:wrap;">
      <a href="/#snap" style="display:inline-block;padding:.85rem 1.8rem;background:#10B981;color:#fff;border-radius:10px;font-weight:600;font-size:.95rem;text-decoration:none;">Get Free County Snapshot →</a>
      <a href="/#reports" style="display:inline-block;padding:.85rem 1.8rem;background:transparent;color:#CBD5E1;border:1px solid rgba(148,163,184,.2);border-radius:10px;font-weight:500;font-size:.95rem;text-decoration:none;">View Full Reports — €29</a>
    </div>
    <p style="font-size:.78rem;color:#475569;margin-top:1rem;">No credit card required for the free snapshot</p>
  </div>
</main>
<footer><p>© 2025 IrishPropertyInsights · Data: <a href="https://www.propertypriceregister.ie" target="_blank">PPR</a> &amp; <a href="https://www.rtb.ie" target="_blank">RTB</a> · <a href="/">Back to site</a></p></footer>
</body>
</html>"""



@app.route("/privacy")
def privacy():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Privacy Policy — IrishPropertyInsights</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Serif+Display&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#0b1120;--bg2:#111827;--border:rgba(255,255,255,.08);--t1:#f1f5f9;--t2:#94a3b8;--t3:#475569;--green:#10b981;--gold:#c9a84c;--fd:'DM Serif Display',serif;--fb:'DM Sans',sans-serif}
body{font-family:var(--fb);background:var(--bg);color:var(--t1);line-height:1.7}
nav{position:sticky;top:0;z-index:100;background:rgba(11,17,32,.95);backdrop-filter:blur(12px);border-bottom:1px solid var(--border);padding:1rem 2rem;display:flex;align-items:center;justify-content:space-between}
nav a.logo{font-family:var(--fd);font-size:1.2rem;text-decoration:none;color:var(--t1)}
nav a.logo span{color:var(--green)}
nav a.back{font-size:.85rem;color:var(--t2);text-decoration:none;transition:color .2s}
nav a.back:hover{color:var(--green)}
main{max-width:720px;margin:0 auto;padding:4rem 2rem 6rem}
.badge{display:inline-block;background:rgba(16,185,129,.1);color:var(--green);font-size:.72rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;padding:.35rem .9rem;border-radius:20px;border:1px solid rgba(16,185,129,.2);margin-bottom:1.5rem}
h1{font-family:var(--fd);font-size:clamp(2rem,4vw,2.8rem);font-weight:700;line-height:1.2;margin-bottom:1rem;color:var(--t1)}
.meta{font-size:.82rem;color:var(--t3);margin-bottom:3rem;padding-bottom:2rem;border-bottom:1px solid var(--border)}
h2{font-family:var(--fd);font-size:1.25rem;font-weight:700;color:var(--t1);margin:2.5rem 0 .75rem}
p{color:var(--t2);margin-bottom:1rem;font-size:.95rem}
ul{color:var(--t2);font-size:.95rem;padding-left:1.5rem;margin-bottom:1rem}
ul li{margin-bottom:.4rem}
a{color:var(--green);text-decoration:none}
a:hover{text-decoration:underline}
.highlight{background:rgba(16,185,129,.06);border:1px solid rgba(16,185,129,.15);border-radius:10px;padding:1.25rem 1.5rem;margin:1.5rem 0}
.highlight p{margin-bottom:0;color:var(--t2)}
footer{text-align:center;padding:2rem;border-top:1px solid var(--border);font-size:.8rem;color:var(--t3)}
footer a{color:var(--t2)}
@media(max-width:600px){main{padding:2.5rem 1.25rem 4rem}}
</style>
</head>
<body>
<nav>
  <a href="/" class="logo">Irish<span>Property</span>Insights</a>
  <a href="/" class="back">← Back to site</a>
</nav>
<main>
  <div class="badge">Legal</div>
  <h1>Privacy Policy</h1>
  <div class="meta">
    Last updated: March 2026 &nbsp;·&nbsp; IrishPropertyInsights &nbsp;·&nbsp; Questions? <a href="mailto:diouri@outlook.com">diouri@outlook.com</a>
  </div>

  <div class="highlight">
    <p><strong style="color:var(--t1)">The short version:</strong> We collect only what we need (your email, when you request a report or snapshot), we never sell your data, we don't use advertising trackers, and you can ask us to delete your data at any time.</p>
  </div>

  <h2>1. Who We Are</h2>
  <p>IrishPropertyInsights is an independent data analysis service built on official Irish government records — the Property Price Register (PPR) and the Residential Tenancies Board (RTB). We provide property investment intelligence reports for the Irish market.</p>
  <p>For the purposes of data protection, the data controller is IrishPropertyInsights, operated as a sole trader based in Ireland.</p>

  <h2>2. What Data We Collect</h2>
  <p>We collect minimal personal data. Specifically:</p>
  <ul>
    <li><strong>Email address</strong> — when you request a free snapshot, purchase a full report, or sign up to be notified when a county launches. This is collected via our email form and processed through Formspree.</li>
    <li><strong>County selection</strong> — the Irish county you select when requesting a report or snapshot. This is not personally identifying on its own.</li>
    <li><strong>Usage data</strong> — basic server logs (IP address, browser type, pages visited) retained for up to 30 days for security and debugging. We do not use this for profiling.</li>
  </ul>
  <p>We do <strong>not</strong> collect: payment card details (handled entirely by Gumroad), names, addresses, phone numbers, or any sensitive personal data.</p>

  <h2>3. How We Use Your Data</h2>
  <ul>
    <li>To send you the free snapshot or full report you requested</li>
    <li>To notify you when a requested county report becomes available</li>
    <li>To send occasional product updates if you opted in (you can unsubscribe at any time)</li>
    <li>To understand how the site is used and improve it</li>
  </ul>
  <p>We do <strong>not</strong> use your data for advertising, profiling, or automated decision-making.</p>

  <h2>4. Legal Basis (GDPR)</h2>
  <p>We process your personal data under the following legal bases:</p>
  <ul>
    <li><strong>Contract performance</strong> — to deliver the snapshot or report you requested</li>
    <li><strong>Legitimate interests</strong> — to improve the service and prevent abuse</li>
    <li><strong>Consent</strong> — for any optional marketing emails (you can withdraw consent at any time)</li>
  </ul>

  <h2>5. Third-Party Services</h2>
  <p>We use a small number of trusted third-party services to operate this site:</p>
  <ul>
    <li><strong>Formspree</strong> — processes email form submissions. <a href="https://formspree.io/legal/privacy-policy" target="_blank">Formspree Privacy Policy →</a></li>
    <li><strong>Gumroad</strong> — processes payments for full reports. We never see your card details. <a href="https://gumroad.com/privacy" target="_blank">Gumroad Privacy Policy →</a></li>
    <li><strong>Railway</strong> — hosts this application. <a href="https://railway.app/legal/privacy" target="_blank">Railway Privacy Policy →</a></li>
    <li><strong>Google Fonts</strong> — loads fonts from Google's CDN. This may log your IP address. <a href="https://policies.google.com/privacy" target="_blank">Google Privacy Policy →</a></li>
  </ul>
  <p>We do not use Google Analytics, Facebook Pixel, or any advertising trackers.</p>

  <h2>6. Data Sources</h2>
  <p>The property and rental data used in our reports comes entirely from official Irish government sources:</p>
  <ul>
    <li><a href="https://www.propertypriceregister.ie" target="_blank">Property Price Register</a> — published by the Revenue Commissioners and Property Services Regulatory Authority</li>
    <li><a href="https://www.rtb.ie" target="_blank">Residential Tenancies Board (RTB)</a> — official rental market data</li>
  </ul>
  <p>This data is publicly available and used in accordance with its open data licence. No personal data of property buyers or tenants is included in our reports.</p>

  <h2>7. Data Retention</h2>
  <ul>
    <li>Email addresses collected via Formspree: retained until you request deletion</li>
    <li>Server logs: deleted after 30 days</li>
    <li>Gumroad purchase records: governed by Gumroad's own retention policy</li>
  </ul>

  <h2>8. Your Rights (GDPR)</h2>
  <p>If you are based in the EU or EEA, you have the following rights under GDPR:</p>
  <ul>
    <li><strong>Access</strong> — request a copy of the personal data we hold about you</li>
    <li><strong>Rectification</strong> — ask us to correct inaccurate data</li>
    <li><strong>Erasure</strong> — ask us to delete your data ("right to be forgotten")</li>
    <li><strong>Restriction</strong> — ask us to limit how we use your data</li>
    <li><strong>Portability</strong> — request your data in a machine-readable format</li>
    <li><strong>Objection</strong> — object to processing based on legitimate interests</li>
  </ul>
  <p>To exercise any of these rights, email us at <a href="mailto:diouri@outlook.com">diouri@outlook.com</a>. We will respond within 30 days.</p>
  <p>You also have the right to lodge a complaint with the <a href="https://www.dataprotection.ie" target="_blank">Data Protection Commission (DPC)</a>, Ireland's supervisory authority.</p>

  <h2>9. Cookies</h2>
  <p>This site uses minimal cookies:</p>
  <ul>
    <li><strong>Session storage</strong> — used to remember if you've dismissed the exit popup (stored in your browser only, not sent to our servers, cleared when you close the tab)</li>
    <li><strong>No advertising or tracking cookies</strong> — we do not use any third-party tracking cookies</li>
  </ul>
  <p>You can clear cookies at any time via your browser settings.</p>

  <h2>10. Children's Privacy</h2>
  <p>This service is intended for adults making property investment decisions. We do not knowingly collect data from anyone under 18. If you believe we have inadvertently collected data from a minor, please contact us immediately.</p>

  <h2>11. Changes to This Policy</h2>
  <p>We may update this policy from time to time. When we do, we'll update the "Last updated" date at the top of this page. We encourage you to review this page periodically.</p>

  <h2>12. Contact</h2>
  <p>If you have any questions about this privacy policy or how we handle your data, please contact us:</p>
  <div class="highlight">
    <p>📧 <a href="diouri@outlook.com">diouri@outlook.com</a><br>
    🌐 <a href="/">www.irishpropertyinsights.ie</a><br>
    🏢 IrishPropertyInsights, Ireland</p>
  </div>
</main>
<footer>
  <p>© 2025 IrishPropertyInsights · <a href="/">Home</a> · <a href="/methodology">Methodology</a> · <a href="/privacy">Privacy Policy</a></p>
</footer>
</body>
</html>"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
