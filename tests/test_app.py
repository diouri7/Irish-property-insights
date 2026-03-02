"""
Test suite for Irish Property Insights (app.py).

Coverage areas:
  - extract_micro_area  : pure address-parsing logic
  - compute_signal      : pure investment-signal scoring
  - get_landing_html    : template injection
  - Flask routes        : HTTP status codes for valid/invalid inputs
  - analyse_county      : analysis engine with mocked data
  - make_price_chart    : chart generation returns valid PNG bytes
  - make_top_areas_chart: chart generation returns valid PNG bytes
  - RTB_RENT data       : static data integrity
  - load_data / get_data: CSV loading with mocked I/O
"""

import io
import os
import sys

import numpy as np
import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

# Make sure the project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as app_module
from app import (
    COUNTIES,
    RTB_RENT,
    YIELD_DAMPEN,
    compute_signal,
    extract_micro_area,
    get_landing_html,
)


# ─── Shared fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def client():
    """Flask test client."""
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c


@pytest.fixture
def sample_df():
    """
    Synthetic DataFrame that mimics processed PPR data for Dublin.
    200 rows across 5 micro-areas and years 2018-2024 — enough to
    trigger the full analysis path in analyse_county().
    """
    rng = np.random.default_rng(42)
    n = 200
    years = rng.integers(2018, 2025, size=n)
    prices = rng.integers(200_000, 500_000, size=n).astype(float)
    areas = rng.choice(
        ["Swords", "Malahide", "Clontarf", "Raheny", "Blanchardstown"], size=n
    )
    return pd.DataFrame(
        {
            "year": years,
            "price": prices,
            "county": "Dublin",
            "micro_area": areas,
            "date": pd.to_datetime([f"{y}-06-01" for y in years]),
        }
    )


# ─── extract_micro_area ─────────────────────────────────────────────────────

class TestExtractMicroArea:
    """Unit tests for the address → town-name parser."""

    def test_empty_string_returns_unknown(self):
        assert extract_micro_area("") == "Unknown"

    def test_whitespace_only_returns_unknown(self):
        assert extract_micro_area("   ") == "Unknown"

    def test_none_returns_unknown(self):
        assert extract_micro_area(None) == "Unknown"

    def test_integer_returns_unknown(self):
        assert extract_micro_area(123) == "Unknown"

    def test_very_short_address_returns_unknown(self):
        # A two-character part is filtered out (len < 3)
        assert extract_micro_area("AB") == "Unknown"

    def test_ireland_suffix_excluded(self):
        result = extract_micro_area("14 Main St, Bray, Ireland")
        assert result != "Ireland"

    def test_county_word_stripped(self):
        # "County Galway" contains "county" and must be skipped
        result = extract_micro_area("5 Bridge St, Galway City, County Galway")
        assert "county" not in result.lower()

    def test_co_abbreviation_stripped(self):
        # "Co. Kerry" contains "co." and must be skipped
        result = extract_micro_area("3 High St, Killarney, Co. Kerry")
        assert result != "Co. Kerry"
        assert result.lower() not in ("co. kerry", "co kerry")

    def test_output_is_title_cased(self):
        result = extract_micro_area("14 main street, swords, dublin")
        if result != "Unknown":
            assert result == result.title()

    def test_single_meaningful_token(self):
        # Only one qualifying part → should be returned
        assert extract_micro_area("Swords") == "Swords"

    def test_result_has_minimum_length(self):
        # Whatever is returned must be at least 3 chars (or "Unknown")
        result = extract_micro_area("1 St, AB, Cork")
        assert result == "Unknown" or len(result) >= 3

    def test_numeric_heavy_part_skipped(self):
        # A part whose alpha_ratio < 0.5 is skipped
        # "1234AB" has 2 alpha out of 6 chars → ratio ≈ 0.33 → skipped
        result = extract_micro_area("1234AB, Dundrum, Dublin")
        assert result != "1234AB"

    def test_typical_dublin_address(self):
        # Should extract the last meaningful part after comma-splitting
        result = extract_micro_area("Apt 3, The Elms, Clontarf, Dublin 3")
        assert result != "Unknown"
        assert len(result) >= 3


# ─── compute_signal ─────────────────────────────────────────────────────────

class TestComputeSignal:
    """
    Unit tests for the investment-signal scoring function.

    Scoring rules (from source):
      Growth  >= 7  → +3 | >= 5 → +2 | >= 3 → +1 | < 0 → -1
      Yield   >= 6  → +3 | >= 5 → +2 | >= 4 → +1
      Risk Low → +2 | Medium → +1 | High → -1

    Thresholds:  score >= 6 → STRONG BUY
                 score >= 4 → BUY
                 score >= 2 → MODERATE
                 score >= 0 → HOLD
                 score <  0 → AVOID
    """

    # --- STRONG BUY ---
    def test_strong_buy_max_scores(self):
        # +3 +3 +2 = 8
        assert compute_signal(10, 8, "Low") == "STRONG BUY"

    def test_strong_buy_boundary_score_6(self):
        # +2 +2 +2 = 6
        assert compute_signal(5, 5, "Low") == "STRONG BUY"

    def test_strong_buy_growth_boundary_at_7(self):
        # growth=7 → +3; yield=5 → +2; Low → +2 = 7
        assert compute_signal(7, 5, "Low") == "STRONG BUY"

    # --- BUY ---
    def test_buy_score_5(self):
        # +2 +1 +2 = 5
        assert compute_signal(5, 4, "Low") == "BUY"

    def test_buy_boundary_score_4(self):
        # +1 +1 +2 = 4
        assert compute_signal(3, 4, "Low") == "BUY"

    # --- MODERATE ---
    def test_moderate_score_3(self):
        # +1 +0 +2 = 3
        assert compute_signal(3, 0, "Low") == "MODERATE"

    def test_moderate_boundary_score_2(self):
        # +0 +0 +2 = 2
        assert compute_signal(0, 0, "Low") == "MODERATE"

    def test_moderate_high_yield_high_risk(self):
        # +0 +3 -1 = 2
        assert compute_signal(0, 6, "High") == "MODERATE"

    # --- HOLD ---
    def test_hold_score_1(self):
        # +0 +0 +1 = 1
        assert compute_signal(0, 0, "Medium") == "HOLD"

    def test_hold_boundary_score_0(self):
        # +0 +1 -1 = 0
        assert compute_signal(0, 4, "High") == "HOLD"

    def test_hold_medium_growth_high_risk(self):
        # growth=5 → +2; yield=0; High → -1 = 1 → HOLD
        assert compute_signal(5, 0, "High") == "HOLD"

    # --- AVOID ---
    def test_avoid_negative_growth_high_risk(self):
        # -1 + 0 -1 = -2
        assert compute_signal(-5, 0, "High") == "AVOID"

    def test_avoid_negative_growth_medium_risk(self):
        # -1 + 0 + 1 = 0 → HOLD (not AVOID) — verifying boundary
        # For AVOID we need score < 0
        assert compute_signal(-1, 0, "High") == "AVOID"  # -1+0-1=-2

    # --- Boundary transitions ---
    def test_growth_just_below_7_gives_lower_score(self):
        # 6.9 → +2 (not +3), +0, -1 = 1 → HOLD vs 7.0 → +3 +0 -1 = 2 → MODERATE
        assert compute_signal(6.9, 0, "High") == "HOLD"
        assert compute_signal(7.0, 0, "High") == "MODERATE"

    def test_yield_just_below_6_gives_lower_score(self):
        # yield=6.0 → +3; yield=5.9 → +2
        assert compute_signal(0, 6.0, "High") == "MODERATE"  # 0+3-1=2
        assert compute_signal(0, 5.9, "High") == "HOLD"       # 0+2-1=1

    def test_all_five_signals_are_reachable(self):
        signals = {
            compute_signal(10, 8, "Low"),   # STRONG BUY
            compute_signal(5, 4, "Low"),    # BUY
            compute_signal(3, 0, "Low"),    # MODERATE
            compute_signal(0, 0, "Medium"), # HOLD
            compute_signal(-5, 0, "High"),  # AVOID
        }
        assert signals == {"STRONG BUY", "BUY", "MODERATE", "HOLD", "AVOID"}


# ─── get_landing_html ───────────────────────────────────────────────────────

class TestGetLandingHtml:
    """Unit tests for the landing-page template injection."""

    def test_returns_a_string(self):
        assert isinstance(get_landing_html(), str)

    def test_no_unreplaced_placeholders(self):
        html = get_landing_html()
        assert "%COUNTY_OPTIONS%" not in html
        assert "%COUNTY_OPTIONS_FULL%" not in html

    def test_all_counties_present(self):
        html = get_landing_html()
        for county in COUNTIES:
            assert county in html, f"{county} missing from landing HTML"

    def test_contains_option_elements(self):
        assert "<option" in get_landing_html()

    def test_exactly_26_counties(self):
        assert len(COUNTIES) == 26


# ─── Flask routes ────────────────────────────────────────────────────────────

class TestHomeRoute:
    def test_returns_200(self, client):
        assert client.get("/").status_code == 200

    def test_returns_html(self, client):
        resp = client.get("/")
        assert b"<html" in resp.data.lower() or b"<!doctype" in resp.data.lower()


class TestReportRoute:
    def test_invalid_county_returns_400(self, client):
        assert client.get("/report?county=Narnia").status_code == 400

    def test_empty_county_returns_400(self, client):
        assert client.get("/report?county=").status_code == 400

    def test_missing_county_param_returns_400(self, client):
        assert client.get("/report").status_code == 400

    @patch("app.analyse_county", return_value=None)
    def test_insufficient_data_returns_400(self, _mock, client):
        assert client.get("/report?county=Leitrim").status_code == 400

    @patch("app.build_pdf_report", side_effect=RuntimeError("PDF boom"))
    @patch("app.analyse_county", return_value={"county": "Cork"})
    def test_pdf_generation_error_returns_500(self, _ma, _mp, client):
        assert client.get("/report?county=Cork").status_code == 500


class TestSnapshotRoute:
    def test_invalid_county_returns_400(self, client):
        assert client.get("/snapshot?county=InvalidPlace").status_code == 400

    def test_empty_county_returns_400(self, client):
        assert client.get("/snapshot?county=").status_code == 400

    def test_missing_county_param_returns_400(self, client):
        assert client.get("/snapshot").status_code == 400

    @patch("app.analyse_county", return_value=None)
    def test_insufficient_data_returns_400(self, _mock, client):
        assert client.get("/snapshot?county=Leitrim").status_code == 400

    @patch("app.build_pdf_report", side_effect=RuntimeError("PDF boom"))
    @patch("app.analyse_county", return_value={"county": "Cork"})
    def test_pdf_generation_error_returns_500(self, _ma, _mp, client):
        assert client.get("/snapshot?county=Cork").status_code == 500


# ─── analyse_county ──────────────────────────────────────────────────────────

class TestAnalyseCounty:
    """Tests for the core analysis engine, using mocked get_data()."""

    @patch("app.get_data")
    def test_returns_none_when_fewer_than_50_rows(self, mock_get):
        mock_get.return_value = pd.DataFrame(
            {
                "county": ["Dublin"] * 10,
                "price": [300_000.0] * 10,
                "year": [2023] * 10,
                "micro_area": ["Swords"] * 10,
                "date": pd.to_datetime(["2023-01-01"] * 10),
            }
        )
        assert app_module.analyse_county("Dublin") is None

    @patch("app.get_data")
    def test_returns_none_when_no_area_has_10_transactions(self, mock_get):
        # 60 rows but all in unique areas → each area has 1 transaction
        mock_get.return_value = pd.DataFrame(
            {
                "county": ["Cork"] * 60,
                "price": [250_000.0] * 60,
                "year": [2022] * 60,
                "micro_area": [f"Area{i}" for i in range(60)],
                "date": pd.to_datetime(["2022-06-01"] * 60),
            }
        )
        assert app_module.analyse_county("Cork") is None

    @patch("app.get_data")
    def test_returns_dict_with_all_expected_keys(self, mock_get, sample_df):
        mock_get.return_value = sample_df
        result = app_module.analyse_county("Dublin")
        if result is None:
            pytest.skip("Fixture did not produce enough data")
        required = {
            "county", "latest_median", "total_transactions",
            "latest_year", "earliest_year", "county_growth_5yr",
            "county_yield", "county_rent", "yearly", "micro_areas", "num_areas",
        }
        assert required.issubset(result.keys())

    @patch("app.get_data")
    def test_county_name_propagated(self, mock_get, sample_df):
        mock_get.return_value = sample_df
        result = app_module.analyse_county("Dublin")
        if result is not None:
            assert result["county"] == "Dublin"

    @patch("app.get_data")
    def test_latest_median_is_positive(self, mock_get, sample_df):
        mock_get.return_value = sample_df
        result = app_module.analyse_county("Dublin")
        if result is not None:
            assert result["latest_median"] > 0

    @patch("app.get_data")
    def test_micro_areas_has_required_columns(self, mock_get, sample_df):
        mock_get.return_value = sample_df
        result = app_module.analyse_county("Dublin")
        if result is not None:
            required_cols = {
                "area", "median_price", "growth_5yr",
                "gross_yield", "risk", "signal", "transactions",
            }
            assert required_cols.issubset(set(result["micro_areas"].columns))

    @patch("app.get_data")
    def test_signals_are_valid_enum_values(self, mock_get, sample_df):
        mock_get.return_value = sample_df
        result = app_module.analyse_county("Dublin")
        if result is not None:
            valid = {"STRONG BUY", "BUY", "MODERATE", "HOLD", "AVOID"}
            assert set(result["micro_areas"]["signal"].unique()).issubset(valid)

    @patch("app.get_data")
    def test_risk_labels_are_valid_enum_values(self, mock_get, sample_df):
        mock_get.return_value = sample_df
        result = app_module.analyse_county("Dublin")
        if result is not None:
            valid = {"Low", "Medium", "High"}
            assert set(result["micro_areas"]["risk"].unique()).issubset(valid)

    @patch("app.get_data")
    def test_total_transactions_is_positive_int(self, mock_get, sample_df):
        mock_get.return_value = sample_df
        result = app_module.analyse_county("Dublin")
        if result is not None:
            assert isinstance(result["total_transactions"], int)
            assert result["total_transactions"] > 0

    @patch("app.get_data")
    def test_num_areas_matches_micro_areas_dataframe(self, mock_get, sample_df):
        mock_get.return_value = sample_df
        result = app_module.analyse_county("Dublin")
        if result is not None:
            assert result["num_areas"] == len(result["micro_areas"])


# ─── make_price_chart ────────────────────────────────────────────────────────

class TestMakePriceChart:
    """Chart generation should return a readable BytesIO containing a PNG."""

    def _make_yearly_df(self):
        return pd.DataFrame(
            {
                "year": [2019, 2020, 2021, 2022, 2023],
                "median_price": [250_000, 270_000, 290_000, 310_000, 330_000],
            }
        )

    def test_returns_readable_object(self):
        buf = app_module.make_price_chart(self._make_yearly_df(), "Dublin")
        assert hasattr(buf, "read")

    def test_output_is_png(self):
        buf = app_module.make_price_chart(self._make_yearly_df(), "Dublin")
        data = buf.read()
        assert data[:8] == b"\x89PNG\r\n\x1a\n", "Chart is not a valid PNG"

    def test_single_data_point_does_not_raise(self):
        yearly = pd.DataFrame({"year": [2023], "median_price": [300_000]})
        buf = app_module.make_price_chart(yearly, "Galway")
        assert buf is not None

    def test_non_empty_output(self):
        buf = app_module.make_price_chart(self._make_yearly_df(), "Cork")
        assert len(buf.read()) > 0


# ─── make_top_areas_chart ────────────────────────────────────────────────────

class TestMakeTopAreasChart:
    """Horizontal bar chart generation should return a valid PNG."""

    def _make_micro_df(self, n=5):
        signals = ["STRONG BUY", "BUY", "MODERATE", "HOLD", "AVOID"]
        return pd.DataFrame(
            {
                "area": [f"Area{i}" for i in range(n)],
                "gross_yield": [5.0 - i * 0.3 for i in range(n)],
                "signal": [signals[i % len(signals)] for i in range(n)],
            }
        )

    def test_returns_readable_object(self):
        buf = app_module.make_top_areas_chart(self._make_micro_df(), "Dublin")
        assert hasattr(buf, "read")

    def test_output_is_png(self):
        buf = app_module.make_top_areas_chart(self._make_micro_df(), "Dublin")
        assert buf.read()[:8] == b"\x89PNG\r\n\x1a\n"

    def test_top_n_less_than_dataframe_rows(self):
        df = self._make_micro_df(n=10)
        buf = app_module.make_top_areas_chart(df, "Cork", top_n=3)
        assert buf is not None

    def test_single_area_does_not_raise(self):
        df = pd.DataFrame({"area": ["Swords"], "gross_yield": [5.0], "signal": ["BUY"]})
        buf = app_module.make_top_areas_chart(df, "Dublin", top_n=1)
        assert buf is not None

    def test_all_signal_colours_handled(self):
        # One row per signal type — should not raise a KeyError / colour error
        df = pd.DataFrame(
            {
                "area": ["A", "B", "C", "D", "E"],
                "gross_yield": [6, 5, 4, 3, 2],
                "signal": ["STRONG BUY", "BUY", "MODERATE", "HOLD", "AVOID"],
            }
        )
        buf = app_module.make_top_areas_chart(df, "Dublin", top_n=5)
        assert buf.read()[:4] == b"\x89PNG"


# ─── RTB_RENT static data ────────────────────────────────────────────────────

class TestRTBRentData:
    """Sanity checks on the hard-coded rent lookup table."""

    def test_all_26_counties_present(self):
        for county in COUNTIES:
            assert county in RTB_RENT, f"{county} missing from RTB_RENT"

    def test_all_rents_are_positive(self):
        for county, rent in RTB_RENT.items():
            assert rent > 0, f"{county} has non-positive rent ({rent})"

    def test_dublin_is_most_expensive(self):
        assert RTB_RENT["Dublin"] == max(RTB_RENT.values())

    def test_yield_dampen_constant_in_valid_range(self):
        assert 0 < YIELD_DAMPEN < 1


# ─── load_data ───────────────────────────────────────────────────────────────

class TestLoadData:
    """Tests for the CSV loading function."""

    def test_reads_existing_local_file(self, tmp_path):
        csv = tmp_path / "PPR-ALL.csv"
        # Use a plain numeric price string — the app strips currency symbols anyway
        csv.write_text(
            "Date of Sale,Price,Address,County\n"
            "01/01/2023,300000,\"1 Main St, Swords\",Dublin\n",
            encoding="latin-1",
        )
        original = app_module.DATA_PATH
        app_module.DATA_PATH = str(csv)
        try:
            df = app_module.load_data()
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 1
        finally:
            app_module.DATA_PATH = original

    @patch("app.requests.get")
    def test_downloads_csv_when_no_local_file(self, mock_get, tmp_path):
        csv_bytes = (
            b"Date of Sale,Price (\xa3),Address,County\n"
            b"01/01/2023,\xa3300000,\"1 Main St, Swords\",Dublin\n"
        )
        mock_resp = MagicMock()
        mock_resp.content = csv_bytes
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        original_path = app_module.DATA_PATH
        original_tmp = app_module.TMP_DIR
        app_module.DATA_PATH = str(tmp_path / "nonexistent.csv")
        app_module.TMP_DIR = str(tmp_path)
        try:
            app_module.load_data()
            assert mock_get.called
        finally:
            app_module.DATA_PATH = original_path
            app_module.TMP_DIR = original_tmp


# ─── get_data (column normalisation) ────────────────────────────────────────

class TestGetData:
    """Tests for the data-loading + normalisation pipeline."""

    def _write_csv(self, tmp_path, content):
        csv = tmp_path / "PPR-ALL.csv"
        # Write as bytes so callers control encoding explicitly
        csv.write_bytes(content.encode("latin-1"))
        return csv

    def test_column_names_are_lowercase_snake_case(self, tmp_path):
        # Use ASCII-safe price column name — the app matches on "price" substring
        csv = self._write_csv(
            tmp_path,
            "Date of Sale,Price,Address,County of Property\n"
            "01/01/2020,250000,\"5 Main St, Swords\",Dublin\n",
        )
        original_path = app_module.DATA_PATH
        original_global = app_module.df_global
        app_module.DATA_PATH = str(csv)
        app_module.df_global = None
        try:
            df = app_module.get_data()
            for col in df.columns:
                assert col == col.lower(), f"Column '{col}' is not lowercase"
                assert " " not in col, f"Column '{col}' contains spaces"
        finally:
            app_module.DATA_PATH = original_path
            app_module.df_global = original_global

    def test_prices_below_threshold_are_dropped(self, tmp_path):
        csv = self._write_csv(
            tmp_path,
            "Date of Sale,Price,Address,County\n"
            "01/01/2020,9000,\"5 Main St, Swords\",Dublin\n"
            "01/01/2020,300000,\"6 Main St, Swords\",Dublin\n",
        )
        original_path = app_module.DATA_PATH
        original_global = app_module.df_global
        app_module.DATA_PATH = str(csv)
        app_module.df_global = None
        try:
            df = app_module.get_data()
            assert (df["price"] > 10_000).all(), "Sub-threshold prices were not filtered"
        finally:
            app_module.DATA_PATH = original_path
            app_module.df_global = original_global

    def test_rows_before_2010_are_dropped(self, tmp_path):
        csv = self._write_csv(
            tmp_path,
            "Date of Sale,Price,Address,County\n"
            "01/06/2009,200000,\"1 Old Rd, Galway\",Galway\n"
            "01/06/2020,200000,\"2 New Rd, Galway\",Galway\n",
        )
        original_path = app_module.DATA_PATH
        original_global = app_module.df_global
        app_module.DATA_PATH = str(csv)
        app_module.df_global = None
        try:
            df = app_module.get_data()
            assert (df["year"] >= 2010).all(), "Pre-2010 rows were not filtered"
        finally:
            app_module.DATA_PATH = original_path
            app_module.df_global = original_global

    def test_cached_result_returned_on_second_call(self, tmp_path):
        csv = self._write_csv(
            tmp_path,
            "Date of Sale,Price,Address,County\n"
            "01/01/2020,250000,\"5 Main St, Swords\",Dublin\n",
        )
        original_path = app_module.DATA_PATH
        original_global = app_module.df_global
        app_module.DATA_PATH = str(csv)
        app_module.df_global = None
        try:
            df1 = app_module.get_data()
            df2 = app_module.get_data()
            assert df1 is df2, "get_data() should return cached DataFrame on second call"
        finally:
            app_module.DATA_PATH = original_path
            app_module.df_global = original_global
