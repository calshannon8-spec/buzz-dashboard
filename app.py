import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import datetime
from pathlib import Path
import yfinance as yf

# Helper setters (no rerun inside callbacks)
def set_ticker_state(ticker_symbol: str):
    st.session_state.selected_ticker = ticker_symbol
    st.session_state.view_mode_state = "Snapshot"

def go_all_holdings_state():
    st.session_state.view_mode_state = "All Holdings"

# New function: Updates state ONLY when the radio button is clicked
def update_view_mode_callback():
    st.session_state.view_mode_state = st.session_state.view_mode_widget
# -----------------------------
# CALLBACK FUNCTION FOR DATA EDITOR
# -----------------------------
def process_holdings_selection(holdings_df):
    if st.session_state.holdings_editor_output and st.session_state.holdings_editor_output.get("selection", {}).get("rows"):
        selected_row_index = st.session_state.holdings_editor_output["selection"]["rows"][0]
        new_ticker = holdings_df.iloc[selected_row_index]["Ticker"]
        if new_ticker != st.session_state.selected_ticker:
            st.session_state.selected_ticker = new_ticker
            st.rerun()


# -----------------------------
# Page Config & Basic Styling
# -----------------------------
st.set_page_config(
    page_title="BUZZ Media Prep Dashboard",
    layout="wide",
)

# init session state for view mode (ticker defaults set after data loads)
if "view_mode_state" not in st.session_state:
    st.session_state.view_mode_state = "Snapshot"
if "view_mode_widget" not in st.session_state:
    st.session_state.view_mode_widget = st.session_state.view_mode_state

st.markdown(
    """
    <style>
    :root {
        --bg: #0c1119;
        --panel: #0f1623;
        --border: #1d2a3a;
        --text: #e8edf5;
        --muted: #9fb2cc;
        --accent: #5da0ff;
    }
    .main {
        background-color: var(--bg);
        color: var(--text);
    }
    .fp-section-title {
        margin: 0 0 0.4rem 0;
        font-size: 1.05rem;
        letter-spacing: 0.2px;
        color: var(--muted);
        text-transform: uppercase;
    }
    .fp-card {
        background: radial-gradient(circle at 20% 20%, rgba(93,160,255,0.05), rgba(15,22,35,0.9));
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 16px 18px 6px 18px;
        margin-bottom: 16px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.25);
    }
    .stMetric {
        background-color: rgba(255,255,255,0.03) !important;
        padding: 10px !important;
        border-radius: 10px !important;
        border: 1px solid var(--border) !important;
    }
    .fp-holdings {
        margin-top: 10px;
    }
    .fp-holding-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 12px;
        border: 1px solid var(--border);
        border-radius: 10px;
        background: rgba(255,255,255,0.03);
        margin-bottom: 8px;
    }
    .fp-holding-name {
        color: var(--text);
        font-weight: 600;
        letter-spacing: 0.2px;
    }
    .fp-holding-meta {
        color: var(--muted);
        font-size: 0.9rem;
    }
    .fp-holdings .stButton>button {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        color: #5da0ff !important;
        text-decoration: underline;
        font-weight: 700;
        cursor: pointer;
    }
    .fp-holdings .stButton>button:hover {
        color: #7cb8ff !important;
    }
    .fp-holding-header {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 12px;
        padding: 6px 12px;
        margin-bottom: 6px;
        color: var(--muted);
        font-size: 0.9rem;
        letter-spacing: 0.2px;
    }
    .fp-desc-box {
        background: rgba(255,255,255,0.03);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 12px 14px;
        margin-top: 10px;
        color: var(--text);
        line-height: 1.5;
    }
    /* link-style buttons for holdings tickers */
    .fp-linkbtn button {
        background: none !important;
        border: none !important;
        padding: 0 4px !important;
        color: var(--text) !important;
        text-decoration: none !important;
        font-weight: 700;
        cursor: pointer;
    }
    hr.fp-divider {
        border: none;
        border-top: 1px solid var(--border);
        margin: 0.5rem 0 1rem 0;
    }
    /* Holdings Table Styles (legacy - used by old Top 20, kept for compatibility) */
    .holdings-table-container {
        background: var(--panel);
        border: none !important;
        border-radius: 12px;
        padding: 0 !important;
        margin-top: 0;
        border-collapse: collapse;
    }

    /* Remove extra spacing from columns inside table container */
    .holdings-table-container [data-testid="column"] {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        gap: 0 !important;
        border: none !important;
        border-spacing: 0 !important;
        min-height: 0 !important;
        height: auto !important;
    }

    /* Target first child specifically to ensure no top spacing */
    .holdings-table-container > div:first-child,
    .holdings-table-container [data-testid="column"]:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }

    /* Force remove gaps between rows - target Streamlit's horizontal blocks */
    .holdings-table-container > div,
    .holdings-table-container [data-testid="stHorizontalBlock"],
    .holdings-table-container [data-testid="stVerticalBlock"] {
        gap: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        border: none !important;
        border-spacing: 0 !important;
    }

    /* Remove spacing before table container - target the caption above */
    [data-testid="stCaptionContainer"] {
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
        border-bottom: none !important;
        border: none !important;
    }

    /* Nuclear option: remove ALL spacing from ALL elements inside table */
    .holdings-table-container * {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        border-top: none !important;
        border-bottom: none !important;
        border-spacing: 0 !important;
        border-collapse: collapse !important;
    }

    /* Table header cells */
    .table-header-cell {
        font-weight: 600;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: rgba(159,178,204,0.7);
        padding-bottom: 0;
        border-bottom: none !important;
        margin-bottom: 0;
        border: none !important;
    }

    /* Data cell styles */
    .rank-cell {
        text-align: center;
        color: rgba(159,178,204,0.6);
        font-weight: 500;
        font-size: 0.9rem;
        padding: 0.5rem 0;
        border-top: none !important;
        border: none !important;
        margin-top: 0;
        margin: 0;
    }

    .weight-cell {
        text-align: center;
        font-weight: 500;
        color: var(--text);
        padding: 0.5rem 0;
        border-top: none !important;
        border: none !important;
        margin-top: 0;
        margin: 0;
    }

    .value-cell {
        text-align: right;
        color: #9fb2cc;
        font-family: 'SF Mono', 'Consolas', 'Monaco', monospace;
        font-size: 0.9rem;
        padding: 0.5rem 0;
        border-top: none !important;
        border: none !important;
        margin-top: 0;
        margin: 0;
    }

    /* Style the ticker buttons to look clean and uniform */
    .holdings-table-container .stButton > button {
        width: 100%;
        background: transparent;
        border: none !important;
        border-top: none !important;
        color: var(--accent);
        font-weight: 600;
        font-size: 1rem;
        padding: 0.5rem 0.75rem;
        text-align: left;
        transition: all 0.15s ease;
        margin-top: 0;
    }

    .holdings-table-container .stButton > button:hover {
        background: rgba(93,160,255,0.1);
        border-radius: 6px;
    }

    /* Force remove any borders from button containers */
    .holdings-table-container .stButton {
        border-top: none !important;
        margin-top: 0;
    }
    /* BUZZ Performance Info Box */
    .buzz-info-box {
        background: rgba(255,255,255,0.03);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 24px;
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 24px;
    }
    .buzz-info-item {
        display: flex;
        flex-direction: column;
    }
    .buzz-info-label {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--muted);
        margin-bottom: 8px;
        font-weight: 600;
    }
    .buzz-info-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--text);
        font-family: 'SF Mono', 'Consolas', 'Monaco', monospace;
    }
    .buzz-change-positive {
        color: #26d97a;
    }
    .buzz-change-negative {
        color: #ff4757;
    }
    .buzz-arrow {
        font-size: 1.8rem;
        margin-right: 6px;
    }
    /* Key Metrics Grid */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
        margin-top: 12px;
    }
    .metric-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 16px 18px;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .metric-label {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--muted);
        font-weight: 600;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--text);
        font-family: 'SF Mono', 'Consolas', 'Monaco', monospace;
        word-break: break-word;
    }

    /* Dark Financial Card Container */
    .dark-card {
        background: #1a1f2e;
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 24px;
        margin-top: 16px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3), 0 1px 3px rgba(0,0,0,0.2);
    }

    /* Card Title - Dark Theme */
    .dark-card-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #f8fafc;
        margin: 0 0 4px 0;
    }
    .dark-card-subtitle {
        font-size: 0.8rem;
        color: #94a3b8;
        margin: 0;
    }

    /* Search Input - Dark Theme */
    .dark-card .stTextInput > div > div > input {
        background: #0f1419 !important;
        border: 1px solid #374151 !important;
        border-radius: 8px !important;
        color: #f1f5f9 !important;
        padding: 10px 14px !important;
        font-size: 0.875rem !important;
    }
    .dark-card .stTextInput > div > div > input:focus {
        border-color: #10b981 !important;
        box-shadow: 0 0 0 3px rgba(16,185,129,0.15) !important;
    }
    .dark-card .stTextInput > div > div > input::placeholder {
        color: #64748b !important;
    }

    /* Scrollable Table Container - Dark */
    .dark-table-container {
        max-height: 450px;
        overflow-y: auto;
        border: 1px solid #2d3748;
        border-radius: 8px;
        background: #111827;
    }

    /* Custom Scrollbar - Dark Theme */
    .dark-table-container::-webkit-scrollbar {
        width: 8px;
    }
    .dark-table-container::-webkit-scrollbar-track {
        background: #1a1f2e;
    }
    .dark-table-container::-webkit-scrollbar-thumb {
        background: #374151;
        border-radius: 4px;
    }
    .dark-table-container::-webkit-scrollbar-thumb:hover {
        background: #4b5563;
    }

    /* Dark Table Header */
    .dark-table-header {
        display: flex;
        align-items: center;
        padding: 14px 20px;
        background: #0f1419;
        border-bottom: 1px solid #2d3748;
        position: sticky;
        top: 0;
        z-index: 10;
    }
    .dark-th {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #64748b;
    }
    .dark-th.text-right {
        text-align: right;
    }

    /* Dark Row Styles */
    .dark-row {
        display: flex;
        align-items: center;
        padding: 0 20px;
        border-bottom: 1px solid #1e293b;
        cursor: pointer;
        transition: background 0.15s ease;
        background: #111827;
    }
    .dark-row:hover {
        background: #1e293b;
    }
    .dark-row:last-child {
        border-bottom: none;
    }

    /* Ticker button - Bright White, Bold */
    .dark-row .stButton > button {
        background: transparent !important;
        border: none !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        padding: 14px 0 !important;
        text-align: left !important;
        width: auto !important;
        min-width: 0 !important;
    }
    .dark-row .stButton > button:hover {
        color: #10b981 !important;
        background: transparent !important;
    }

    /* Company Name - Light Gray, Subtle */
    .dark-company-name {
        font-size: 0.8rem;
        color: #94a3b8;
        padding: 14px 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* Weight Cell - Bold White */
    .dark-weight {
        font-family: 'SF Mono', 'Consolas', 'Monaco', monospace;
        font-variant-numeric: tabular-nums;
        font-size: 0.875rem;
        font-weight: 600;
        color: #f1f5f9;
        padding: 14px 0;
        text-align: right;
    }

    /* Market Value Cell - Emerald Green, Bold */
    .dark-market-value {
        font-family: 'SF Mono', 'Consolas', 'Monaco', monospace;
        font-variant-numeric: tabular-nums;
        font-size: 0.875rem;
        font-weight: 700;
        color: #10b981;
        padding: 14px 0;
        text-align: right;
    }

    /* Footer caption - Dark Theme */
    .dark-card .stCaption {
        color: #64748b !important;
    }

    /* Override Streamlit default blue accents */
    .stSelectbox [data-baseweb="select"] {
        border-color: var(--border) !important;
    }
    .stSelectbox [data-baseweb="select"]:focus-within {
        border-color: #10b981 !important;
        box-shadow: none !important;
    }

    /* Hide any stray Streamlit elements */
    .element-container:empty {
        display: none !important;
    }

    /* Override any blue focus indicators */
    *:focus {
        outline-color: #10b981 !important;
    }
    [data-baseweb] {
        --accent-color: #10b981 !important;
    }

    /* Override Streamlit primary button color */
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="baseButton-primary"] {
        background-color: #10b981 !important;
        border-color: #10b981 !important;
    }
    .stButton > button {
        background-color: transparent !important;
        border-color: var(--border) !important;
    }
    .stButton > button:hover {
        border-color: #10b981 !important;
        background-color: rgba(16, 185, 129, 0.1) !important;
    }

    /* Hide color indicator squares */
    .stColorBlock,
    [data-testid="stColorBlock"],
    .color-block {
        display: none !important;
    }

    /* Hide any potential blue squares/blocks */
    [style*="background-color: rgb(0, 0, 255)"],
    [style*="background-color: blue"],
    [style*="background: rgb(0, 0, 255)"],
    [style*="background: blue"] {
        display: none !important;
    }

    /* Force all divs to not have blue backgrounds */
    div[style*="background-color: rgb(49, 51, 63)"] {
        background-color: transparent !important;
    }

    /* Override Streamlit's default decoration elements */
    .stDeployButton,
    [data-testid="stDeployButton"],
    .stDecoration,
    [data-testid="stDecoration"] {
        display: none !important;
    }

    /* Hide the blue status bar/header that Streamlit sometimes shows */
    header[data-testid="stHeader"] {
        background: var(--bg) !important;
    }
    .stApp > header {
        background: transparent !important;
    }

    /* Completely hide Streamlit's top bar and decorations */
    [data-testid="stToolbar"],
    [data-testid="stStatusWidget"],
    .stToolbar,
    footer,
    #MainMenu {
        display: none !important;
        visibility: hidden !important;
    }

    /* Override any potential blue backgrounds on main elements */
    .main .block-container {
        background: transparent !important;
    }

    /* Target Streamlit's skeleton loader (sometimes shows as blue) */
    .stSkeleton,
    [data-testid="stSkeleton"] {
        background: var(--bg) !important;
    }

    /* Hide any empty stMarkdown containers that might show */
    .stMarkdown:empty,
    .element-container .stMarkdown:empty {
        display: none !important;
    }

    /* Remove any border or background from title area */
    h1, .stTitle, [data-testid="stTitle"] {
        border: none !important;
        background: transparent !important;
    }
    h1::before, h1::after {
        display: none !important;
    }

    /* Autocomplete suggestion buttons - styled as dropdown items */
    .stButton > button[kind="secondary"] {
        background: #1e293b !important;
        border: 1px solid #374151 !important;
        border-radius: 6px !important;
        color: #e2e8f0 !important;
        text-align: left !important;
        padding: 8px 12px !important;
        font-size: 0.85rem !important;
        margin-bottom: 4px !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background: #334155 !important;
        border-color: #10b981 !important;
        color: #ffffff !important;
    }

    /* Make sidebar permanent and always visible */
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    section[data-testid="stSidebar"] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        width: 300px !important;
        min-width: 300px !important;
        transform: none !important;
        margin-left: 0 !important;
        position: relative !important;
    }
    section[data-testid="stSidebar"] > div {
        width: 300px !important;
        padding: 2rem 1.5rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Data Loading (from data/ folder)
# -----------------------------
def _get_data_dir() -> Path:
    """
    Get the data directory path.
    - Local dev: BUZZ DASHBOARD/data/ (parent.parent / "data")
    - Streamlit Cloud: same folder as app.py (parent)
    """
    script_dir = Path(__file__).resolve().parent

    # First check: files in same folder as app.py (Streamlit Cloud)
    if (script_dir / "current_holdings.csv").exists():
        return script_dir

    # Second check: files in ../data/ folder (local dev)
    data_dir = script_dir.parent / "data"
    if data_dir.exists():
        return data_dir

    # Fallback to same folder
    return script_dir


def _find_current_holdings_file() -> Path:
    """Find the current_holdings.csv file in the data directory"""
    data_dir = _get_data_dir()
    current_file = data_dir / "current_holdings.csv"
    if current_file.exists():
        return current_file
    # Fallback: look for BUZZ_asof_*.csv pattern
    candidates = list(data_dir.glob("BUZZ_asof_*.csv"))
    if candidates:
        return max(candidates, key=lambda p: p.stat().st_mtime)
    st.error(f"No current_holdings.csv or BUZZ_asof_*.csv files found in {data_dir}")
    st.stop()


def _extract_date_from_file(path: Path) -> pd.Timestamp:
    """Extract date from filename or use file modification time"""
    # Try to extract from BUZZ_asof_YYYYMMDD pattern
    match = re.search(r"BUZZ_asof_(\d{8})", path.name)
    if match:
        return pd.to_datetime(match.group(1), format="%Y%m%d")
    # For current_holdings.csv, use file modification date
    return pd.Timestamp(datetime.fromtimestamp(path.stat().st_mtime))


@st.cache_data
def load_buzz_data(csv_path: str | None = None) -> pd.DataFrame:
    # Pick file: explicit override or current_holdings.csv from data/
    data_dir = _get_data_dir()
    if csv_path:
        explicit = (data_dir / csv_path).resolve()
        if not explicit.exists():
            st.error(f"CSV file not found at: {explicit}")
            st.stop()
        path = explicit
    else:
        path = _find_current_holdings_file()

    # Try loading - first check if it's the new format (header on line 1)
    # or old BUZZ format (2 line preamble)
    try:
        # Peek at first line to detect format
        with open(path, 'r') as f:
            first_line = f.readline().strip()

        # New format has "Ticker,Company,Weight,MarketValue" header
        if first_line.startswith("Ticker,"):
            df = pd.read_csv(path)
        else:
            # Old format with 2 line preamble
            df = pd.read_csv(path, skiprows=2)
    except Exception as exc:
        st.error(f"Failed to read {path.name}: {exc}")
        st.stop()

    # Clean ticker (strip country suffix), add Date from filename
    if "Ticker" not in df.columns:
        st.error(f"'Ticker' column missing in {path.name}")
        st.stop()
    df["Ticker"] = df["Ticker"].astype(str).str.split().str[0]

    file_date = _extract_date_from_file(path)
    df["Date"] = file_date

    # Normalize column names we care about
    rename_map = {
        "Market Value (US$)": "MarketValueUSD",
        "% of Net Assets": "PercentNetAssets",
        "MarketValue": "MarketValueUSD",  # New format column name
    }
    for old, new in rename_map.items():
        if old in df.columns and new not in df.columns:
            df = df.rename(columns={old: new})

    # Ensure Sentiment_Score exists; if missing, fill with NaN so UI shows N/A
    if "Sentiment_Score" not in df.columns:
        df["Sentiment_Score"] = pd.NA
    else:
        df["Sentiment_Score"] = pd.to_numeric(df["Sentiment_Score"], errors="coerce")

    # Normalize Weight if present
    if "Weight" in df.columns:
        df["Weight"] = pd.to_numeric(df["Weight"], errors="coerce")

    # Normalize MarketValueUSD if present (strip $ and commas)
    if "MarketValueUSD" in df.columns:
        df["MarketValueUSD"] = (
            df["MarketValueUSD"]
            .astype(str)
            .str.replace(r"[$,]", "", regex=True)
        )
        df["MarketValueUSD"] = pd.to_numeric(df["MarketValueUSD"], errors="coerce")

    # Normalize PercentNetAssets if present (strip % and commas)
    if "PercentNetAssets" in df.columns:
        df["PercentNetAssets"] = (
            df["PercentNetAssets"]
            .astype(str)
            .str.replace(r"[%,]", "", regex=True)
        )
        df["PercentNetAssets"] = pd.to_numeric(df["PercentNetAssets"], errors="coerce")

    return df


df = load_buzz_data()


@st.cache_data
def load_latest_holdings_from_historical():
    """
    Load holdings from BuzzIndex_historical.csv, filtered to most recent Rebalance_date.
    Calculates Market Value based on Weight × Total Fund Value.
    """
    TOTAL_FUND_VALUE = 100_000_000  # $100M default

    try:
        csv_path = _get_data_dir() / "BuzzIndex_historical.csv"
        hist_df = pd.read_csv(csv_path)

        # Normalize ticker names (FB -> META)
        hist_df['Ticker'] = hist_df['Ticker'].replace({'FB': 'META'})

        # Parse dates (DD/MM/YYYY format)
        hist_df['Rebalance_date'] = pd.to_datetime(hist_df['Rebalance_date'], format='%d/%m/%Y')

        # Get most recent rebalance date
        latest_date = hist_df['Rebalance_date'].max()
        latest_df = hist_df[hist_df['Rebalance_date'] == latest_date].copy()

        # Parse Weight as float
        latest_df['Weight'] = pd.to_numeric(latest_df['Weight'], errors='coerce')
        latest_df = latest_df[latest_df['Weight'].notna() & (latest_df['Weight'] > 0)]

        # Calculate Market Value
        latest_df['MarketValue'] = latest_df['Weight'] * TOTAL_FUND_VALUE

        # Sort by Weight descending
        latest_df = latest_df.sort_values('Weight', ascending=False)

        return latest_df, latest_date, TOTAL_FUND_VALUE

    except Exception:
        return pd.DataFrame(), None, TOTAL_FUND_VALUE


@st.cache_data
def load_company_descriptions() -> dict[str, str]:
    """
    Load ticker -> description mapping from a CSV.
    Looks for company_description.csv or company_descriptions.csv in data/ folder.
    Expected columns: Ticker, Company, Description (3 columns).
    """
    data_dir = _get_data_dir()
    names = ["company_description.csv", "company_descriptions.csv"]
    paths = [data_dir / name for name in names]
    target = next((p for p in paths if p.exists()), None)
    if target is None:
        return {}
    # Use pandas for proper CSV parsing (handles quoted fields with commas)
    try:
        df_desc = pd.read_csv(target)
        mapping: dict[str, str] = {}
        for _, row in df_desc.iterrows():
            ticker = str(row.get("Ticker", "")).strip()
            company = str(row.get("Company", "")).strip()
            description = str(row.get("Description", "")).strip()
            if ticker and description:
                # Capitalize first letter of description and combine with company name
                desc_formatted = description[0].upper() + description[1:] if description else ""
                mapping[ticker] = f"{company} {desc_formatted}".strip()
        return mapping
    except Exception:
        return {}


desc_map = load_company_descriptions()

# Sector mapping for BUZZ Heatmap
SECTOR_MAP = {
    # Technology (29 stocks)
    "APLD": "Technology", "RGTI": "Technology", "NBIS": "Technology", "INTC": "Technology",
    "PLTR": "Technology", "NVDA": "Technology", "IREN": "Technology", "MSTR": "Technology",
    "AMD": "Technology", "SOUN": "Technology", "AAPL": "Technology", "SMCI": "Technology",
    "QS": "Technology", "QBTS": "Technology", "IONQ": "Technology", "PATH": "Technology",
    "MSFT": "Technology", "ORCL": "Technology", "DUOL": "Technology", "MU": "Technology",
    "AVGO": "Technology", "TTD": "Technology", "U": "Technology", "APP": "Technology",
    "CRM": "Technology", "ADBE": "Technology", "QCOM": "Technology", "GRAB": "Technology",
    "IBM": "Technology",

    # Communication Services (9 stocks)
    "ASTS": "Communication Services", "META": "Communication Services", "GOOGL": "Communication Services",
    "NFLX": "Communication Services", "RDDT": "Communication Services", "SNAP": "Communication Services",
    "LUMN": "Communication Services", "DIS": "Communication Services", "T": "Communication Services",

    # Consumer Discretionary (14 stocks)
    "TSLA": "Consumer Discretionary", "GME": "Consumer Discretionary", "AMZN": "Consumer Discretionary",
    "DKNG": "Consumer Discretionary", "RIVN": "Consumer Discretionary", "LULU": "Consumer Discretionary",
    "DASH": "Consumer Discretionary", "CVNA": "Consumer Discretionary", "CMG": "Consumer Discretionary",
    "GM": "Consumer Discretionary", "TGT": "Consumer Discretionary", "UBER": "Consumer Discretionary",
    "DECK": "Consumer Discretionary", "F": "Consumer Discretionary",

    # Financials (6 stocks)
    "SOFI": "Financials", "HOOD": "Financials", "PYPL": "Financials", "COIN": "Financials",
    "RKT": "Financials", "RIOT": "Financials",

    # Healthcare (6 stocks)
    "HIMS": "Healthcare", "UNH": "Healthcare", "PFE": "Healthcare", "LLY": "Healthcare",
    "TEM": "Healthcare", "MRNA": "Healthcare",

    # Industrials (5 stocks)
    "RKLB": "Industrials", "ACHR": "Industrials", "BA": "Industrials", "BE": "Industrials",
    "JOBY": "Industrials",

    # Real Estate (1 stock)
    "OPEN": "Real Estate",

    # Utilities (1 stock)
    "OKLO": "Utilities",

    # Materials (3 stocks)
    "MP": "Materials", "AG": "Materials", "B": "Materials",

    # Consumer Staples (1 stock)
    "CELH": "Consumer Staples",
}


@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_daily_changes_batch(tickers: tuple[str, ...]) -> dict[str, float]:
    """Fetch daily % change for multiple tickers using batch download."""
    changes = {t: 0.0 for t in tickers}  # Default all to 0
    try:
        # Batch download is more efficient and less likely to hit rate limits
        data = yf.download(
            list(tickers),
            period="5d",
            interval="1d",
            progress=False,
            threads=True,
            group_by="ticker"
        )

        for ticker in tickers:
            try:
                if len(tickers) == 1:
                    # Single ticker returns different structure
                    hist = data["Close"]
                else:
                    hist = data[ticker]["Close"]

                hist = hist.dropna()
                if len(hist) >= 2:
                    prev = hist.iloc[-2]
                    curr = hist.iloc[-1]
                    changes[ticker] = ((curr - prev) / prev * 100) if prev else 0
            except Exception:
                pass  # Keep default 0
    except Exception:
        # Rate limited or other error - return zeros (cached data will be used next time)
        st.warning("Price data temporarily unavailable. Showing cached or default values.")
    return changes


@st.cache_data
def load_dominance_history() -> pd.DataFrame:
    """
    Load historical data and extract the #1 holding (highest Score) for each rebalance date.
    Returns DataFrame with columns: date, leader
    """
    try:
        csv_path = _get_data_dir() / "BuzzIndex_historical.csv"
        hist_df = pd.read_csv(csv_path)

        # Parse dates (format: DD/MM/YYYY)
        hist_df["Rebalance_date"] = pd.to_datetime(hist_df["Rebalance_date"], format="%d/%m/%Y", errors="coerce")

        # For each rebalance date, get the ticker with highest Score (that's the #1 holding)
        leaders = hist_df.loc[hist_df.groupby("Rebalance_date")["Score"].idxmax()][["Rebalance_date", "Ticker"]].copy()
        leaders.columns = ["date", "leader"]
        leaders = leaders.sort_values("date").reset_index(drop=True)

        return leaders
    except Exception as e:
        st.error(f"Error loading dominance history: {e}")
        return pd.DataFrame(columns=["date", "leader"])


def get_cumulative_dominance(leaders_df: pd.DataFrame, selected_date: pd.Timestamp, top_n: int = 15) -> pd.DataFrame:
    """
    Calculate cumulative "months at #1" up to the selected date.
    Returns top N tickers sorted by count descending.
    """
    # Filter to dates <= selected_date
    filtered = leaders_df[leaders_df["date"] <= selected_date]

    # Count occurrences per ticker
    counts = filtered["leader"].value_counts().reset_index()
    counts.columns = ["ticker", "months_at_top"]

    # Take top N
    top = counts.head(top_n).copy()

    # Add rank for coloring
    top["rank"] = range(1, len(top) + 1)

    return top


# -----------------------------
# Sidebar selection + view toggle
# -----------------------------
# Sort tickers by Weight descending (same order as All Holdings)
if "Weight" in df.columns:
    all_tickers = df.sort_values("Weight", ascending=False)["Ticker"].dropna().unique().tolist()
elif "PercentNetAssets" in df.columns:
    all_tickers = df.sort_values("PercentNetAssets", ascending=False)["Ticker"].dropna().unique().tolist()
else:
    all_tickers = sorted(df["Ticker"].dropna().unique().tolist())

# Set default ticker to the top-weighted one (first in list)
if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = all_tickers[0] if all_tickers else "META"
if "ticker_selectbox_widget" not in st.session_state:
    st.session_state.ticker_selectbox_widget = st.session_state.selected_ticker

if not all_tickers:
    st.error("No tickers available in the latest BUZZ file.")
    st.stop()

# Process pending search selection BEFORE rendering selectbox
if "pending_ticker_selection" in st.session_state:
    pending = st.session_state.pending_ticker_selection
    del st.session_state.pending_ticker_selection
    if pending in all_tickers:
        st.session_state.selected_ticker = pending
        st.session_state.ticker_selectbox_widget = pending
        st.session_state.view_mode_state = "Snapshot"
        st.session_state.view_mode_widget = "Snapshot"
        st.session_state.ticker_search = ""  # Clear search after navigation

# Callback for when user changes ticker via selectbox
def on_ticker_selectbox_change():
    st.session_state.selected_ticker = st.session_state.ticker_selectbox_widget
    # Always go to Snapshot page when a ticker is selected
    st.session_state.view_mode_state = "Snapshot"
    st.session_state.view_mode_widget = "Snapshot"

# Ensure selectbox widget state is valid (ticker exists in options)
if st.session_state.ticker_selectbox_widget not in all_tickers:
    st.session_state.ticker_selectbox_widget = all_tickers[0] if all_tickers else "META"
    st.session_state.selected_ticker = st.session_state.ticker_selectbox_widget

selected_ticker = st.sidebar.selectbox(
    "Select Ticker",
    options=all_tickers,
    key="ticker_selectbox_widget",
    on_change=on_ticker_selectbox_change,
)
# Use session state as the source of truth
selected_ticker = st.session_state.selected_ticker

# Search ticker input
search_query = st.sidebar.text_input("Search Ticker", placeholder="Type ticker symbol...", key="ticker_search")
if search_query:
    search_upper = search_query.upper().strip()
    # Exact match first, then partial matches
    matches = [t for t in all_tickers if t == search_upper]
    if not matches:
        matches = [t for t in all_tickers if search_upper in t]

    if matches:
        st.sidebar.caption(f"Found: {', '.join(matches[:5])}")
        if len(matches) == 1 or matches[0] == search_upper:
            # Auto-select on exact match or single result
            # Navigate to Snapshot if ticker changed OR if not already on Snapshot
            if st.session_state.selected_ticker != matches[0] or st.session_state.view_mode_state != "Snapshot":
                st.session_state.pending_ticker_selection = matches[0]
                st.rerun()
        else:
            # Show buttons for multiple matches
            for match in matches[:5]:
                if st.sidebar.button(match, key=f"search_match_{match}"):
                    st.session_state.pending_ticker_selection = match
                    st.rerun()
    else:
        st.sidebar.caption("No matches found")

# keep the radio default in sync with our state before rendering
view_options = ["Snapshot", "All Holdings", "BUZZ Performance", "Conviction Ranking", "Monthly Turnover", "BUZZ Heatmap"]
current_index = view_options.index(st.session_state.view_mode_state) if st.session_state.view_mode_state in view_options else 0
view_mode = st.sidebar.radio(
    "View",
    options=view_options,
    index=current_index,
    key="view_mode_widget",
    on_change=update_view_mode_callback,
)
st.session_state.view_mode_state = view_mode


# Dynamic title based on view/ticker
if st.session_state.view_mode_state == "Snapshot":
    st.title(selected_ticker)

    # Fetch live price for snapshot view
    try:
        ticker_obj = yf.Ticker(selected_ticker)
        ticker_hist = ticker_obj.history(period="5d", interval="1d")

        if not ticker_hist.empty and "Close" in ticker_hist.columns:
            # Get the most recent closing price
            live_price = ticker_hist["Close"].iloc[-1]

            # Calculate percentage change from previous close
            if len(ticker_hist) >= 2:
                prev_close = ticker_hist["Close"].iloc[-2]
                pct_change = ((live_price - prev_close) / prev_close * 100)

                # Format display string
                if pct_change >= 0:
                    color = "#26d97a"  # green
                    sign = "+"
                else:
                    color = "#ff4757"  # red
                    sign = ""

                # Display using st.write with HTML
                st.write(f'<div style="font-size: 1.8rem; margin-bottom: 1rem;"><span style="font-weight: 700;">${live_price:,.2f}</span> <span style="color: {color}; font-size: 1.2rem;">({sign}{pct_change:.2f}%)</span></div>', unsafe_allow_html=True)
            else:
                # Only one price point available
                st.write(f'<div style="font-size: 1.8rem; font-weight: 700; margin-bottom: 1rem;">${live_price:,.2f}</div>', unsafe_allow_html=True)
    except Exception as e:
        # If price fetch fails, show nothing or a fallback
        pass

elif st.session_state.view_mode_state == "All Holdings":
    st.title("All Holdings")
elif st.session_state.view_mode_state == "BUZZ Performance":
    st.title("BUZZ Performance")
elif st.session_state.view_mode_state == "Conviction Ranking":
    st.title("Most Dominant Stocks")
elif st.session_state.view_mode_state == "Monthly Turnover":
    st.title("BUZZ Index: Monthly Portfolio Turnover Rate (2016 - Present)")
elif st.session_state.view_mode_state == "BUZZ Heatmap":
    st.title("BUZZ Heatmap")

# If user wants the All Holdings page, render that and exit early
if st.session_state.view_mode_state == "All Holdings":

    # Use the already-loaded df from current_holdings.csv
    # Filter to only Stock asset class if column exists (old format)
    if "Asset Class" in df.columns:
        holdings_df = df[df["Asset Class"] == "Stock"].copy()
    else:
        holdings_df = df.copy()

    # Get date from the loaded data
    file_date = holdings_df["Date"].iloc[0] if not holdings_df.empty and "Date" in holdings_df.columns else None

    # Sort by Weight descending (works for both old and new format)
    if "Weight" in holdings_df.columns:
        holdings_df = holdings_df.sort_values("Weight", ascending=False)
    elif "PercentNetAssets" in holdings_df.columns:
        holdings_df = holdings_df.sort_values("PercentNetAssets", ascending=False)

    # Create callback factory for ticker selection
    def make_ticker_callback(ticker_value):
        """Creates a callback function that selects a specific ticker"""
        def callback():
            st.session_state.selected_ticker = ticker_value
            st.session_state.ticker_selectbox_widget = ticker_value
            st.session_state.view_mode_state = "Snapshot"
            st.session_state.view_mode_widget = "Snapshot"
        return callback

    # Card header with title and search
    col_title, col_search = st.columns([2, 1])
    with col_title:
        date_str = file_date.strftime("%b %d, %Y") if file_date else "N/A"
        st.markdown(f'<p class="dark-card-title">Portfolio Holdings</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="dark-card-subtitle">As of {date_str}</p>', unsafe_allow_html=True)
    with col_search:
        search_query = st.text_input(
            "Search",
            placeholder="Search ticker or company...",
            label_visibility="collapsed",
            key="holdings_search_input"
        )

    # Filter by search (search both ticker and holding name/company)
    filtered_df = holdings_df.copy()
    if search_query:
        ticker_mask = filtered_df['Ticker'].str.contains(search_query, case=False, na=False)
        # Support both old "Holding Name" and new "Company" column names
        company_col = 'Company' if 'Company' in filtered_df.columns else 'Holding Name'
        name_mask = filtered_df[company_col].str.contains(search_query, case=False, na=False) if company_col in filtered_df.columns else pd.Series([False] * len(filtered_df))
        filtered_df = filtered_df[ticker_mask | name_mask]

    # Table header
    st.markdown('''
        <div class="dark-table-header">
            <div class="dark-th" style="flex: 1.2;">Ticker</div>
            <div class="dark-th" style="flex: 2.5;">Company</div>
            <div class="dark-th text-right" style="flex: 1;">Weight</div>
            <div class="dark-th text-right" style="flex: 1.5;">Market Value</div>
        </div>
    ''', unsafe_allow_html=True)

    # Scrollable data rows container
    st.markdown('<div class="dark-table-container">', unsafe_allow_html=True)

    for row_num, (idx, row) in enumerate(filtered_df.iterrows()):
        ticker = str(row["Ticker"])
        # Support both old "Holding Name" and new "Company" column names
        company_name = str(row.get("Company", row.get("Holding Name", ""))) if pd.notna(row.get("Company", row.get("Holding Name"))) else ""

        # Support both old "PercentNetAssets" (percentage) and new "Weight" (decimal) formats
        if "Weight" in row and pd.notna(row.get("Weight")):
            weight_pct = row["Weight"] * 100  # Convert decimal to percentage
        elif "PercentNetAssets" in row and pd.notna(row.get("PercentNetAssets")):
            weight_pct = row["PercentNetAssets"]  # Already a percentage
        else:
            weight_pct = 0

        market_val = row.get("MarketValueUSD", 0) if pd.notna(row.get("MarketValueUSD")) else 0

        # Format values
        weight_str = f"{weight_pct:.2f}%"
        mv_str = f"${market_val:,.0f}"

        st.markdown('<div class="dark-row">', unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns([1.2, 2.5, 1, 1.5])
        with c1:
            st.button(
                ticker,
                key=f"ticker_btn_{row_num}",
                on_click=make_ticker_callback(ticker),
                help=f"View {ticker} snapshot"
            )
        with c2:
            st.markdown(f'<div class="dark-company-name">{company_name}</div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="dark-weight">{weight_str}</div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="dark-market-value">{mv_str}</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # Close table container

    # Footer with count
    total_value = filtered_df["MarketValueUSD"].sum() if "MarketValueUSD" in filtered_df.columns else 0
    st.caption(f"Showing {len(filtered_df)} holdings · Total: ${total_value:,.0f}")

    st.stop()

# BUZZ performance view
if st.session_state.view_mode_state == "BUZZ Performance":
    # Fetch BUZZ ETF info for total net assets and daily change
    buzz_ticker = yf.Ticker("BUZZ")
    buzz_info = buzz_ticker.info

    # Get total net assets
    total_assets = buzz_info.get("totalAssets")
    if total_assets:
        assets_display = f"${total_assets:,.0f}"
    else:
        assets_display = "N/A"

    # Get daily change
    # Initialize variables for reuse in metric cards
    info_box_prev_close = None
    info_box_current_price = None
    info_box_daily_change = None
    info_box_change_pct = None

    try:
        day_hist = buzz_ticker.history(period="2d", interval="1d")
        if len(day_hist) >= 2:
            prev_close = day_hist["Close"].iloc[-2]
            current_price = day_hist["Close"].iloc[-1]
            daily_change = current_price - prev_close
            change_pct = (daily_change / prev_close * 100) if prev_close else 0

            # Store these values for reuse in metric cards
            info_box_prev_close = prev_close
            info_box_current_price = current_price
            info_box_daily_change = daily_change
            info_box_change_pct = change_pct

            if daily_change >= 0:
                arrow = "↑"
                change_class = "buzz-change-positive"
                change_display = f'<span class="{change_class}"><span class="buzz-arrow">{arrow}</span>${daily_change:,.2f} ({change_pct:+.2f}%)</span>'
            else:
                arrow = "↓"
                change_class = "buzz-change-negative"
                change_display = f'<span class="{change_class}"><span class="buzz-arrow">{arrow}</span>${daily_change:,.2f} ({change_pct:.2f}%)</span>'
        else:
            change_display = '<span class="buzz-change-neutral">N/A</span>'
    except Exception:
        change_display = '<span class="buzz-change-neutral">N/A</span>'

    # Render info box
    st.markdown(f'''
        <div class="buzz-info-box">
            <div class="buzz-info-item">
                <div class="buzz-info-label" style="font-size: 0.7rem; opacity: 0.7;">Total Net Assets</div>
                <div class="buzz-info-value" style="font-size: 1.8rem; opacity: 0.75;">{assets_display}</div>
            </div>
            <div class="buzz-info-item">
                <div class="buzz-info-label">Daily Share Price Change</div>
                <div class="buzz-info-value">{change_display}</div>
            </div>
        </div>
    ''', unsafe_allow_html=True)

    # Timeframe configuration
    tf_map = {
        "1D": dict(period="1d", interval="5m", start=None),
        "5D": dict(period="5d", interval="30m", start=None),
        "1M": dict(period="1mo", interval="1h", start=None),
        "6M": dict(period="6mo", interval="1d", start=None),
        "1Y": dict(period="1y", interval="1d", start=None),
        "YTD": dict(period=None, interval="1d", start=pd.Timestamp.today().replace(month=1, day=1)),
        "ALL": dict(period="max", interval="1d", start=None),
    }

    # Get current control values (using session state for persistence across renders)
    compare_sp500 = st.session_state.get('buzz_compare_sp500', False)
    tf_choice = st.session_state.get('buzz_timeframe', "1M")

    tf_sel = tf_map[tf_choice]
    period, interval, start = tf_sel["period"], tf_sel["interval"], tf_sel["start"]

    # Data fetching function
    @st.cache_data
    def get_buzz_history(period: str | None, interval: str, start: pd.Timestamp | None, include_sp500: bool) -> pd.DataFrame:
        t_buzz = yf.Ticker("BUZZ")
        if start is not None:
            hist = t_buzz.history(start=start, interval=interval)
        else:
            hist = t_buzz.history(period=period, interval=interval)

        # Fetch S&P 500 data if requested
        if include_sp500:
            t_sp500 = yf.Ticker("^GSPC")
            if start is not None:
                sp500_hist = t_sp500.history(start=start, interval=interval)
            else:
                sp500_hist = t_sp500.history(period=period, interval=interval)

            # Merge S&P 500 close prices into main dataframe
            hist["SP500"] = sp500_hist["Close"]

        return hist

    # Fetch and calculate data
    try:
        hist = get_buzz_history(period, interval, start, compare_sp500)
    except Exception as exc:
        st.error(f"Failed to load BUZZ data: {exc}")
        st.stop()

    if hist.empty or "Close" not in hist.columns:
        st.warning("No historical data available for BUZZ.")
        st.stop()

    # Normalize data to indexed values (base 100)
    hist["BUZZ_Indexed"] = (hist["Close"] / hist["Close"].iloc[0]) * 100
    hist["BUZZ_Return"] = ((hist["BUZZ_Indexed"] - 100).round(1))  # Percentage return rounded to 1 decimal
    if compare_sp500 and "SP500" in hist.columns:
        hist["SP500_Indexed"] = (hist["SP500"] / hist["SP500"].iloc[0]) * 100
        hist["SP500_Return"] = ((hist["SP500_Indexed"] - 100).round(1))  # Percentage return rounded to 1 decimal

    # Calculate metrics
    # For 1D timeframe, use the same calculation as the info box for consistency
    if tf_choice == "1D" and info_box_prev_close is not None:
        # Use the same values from the info box calculation to ensure identical display
        start_price = info_box_prev_close
        end_price = info_box_current_price
        abs_change = info_box_daily_change
        pct_change = info_box_change_pct
    else:
        # For all other timeframes (or if info box data unavailable), use hist data
        start_price = hist["Close"].iloc[0]
        end_price = hist["Close"].iloc[-1]
        abs_change = end_price - start_price
        pct_change = (abs_change / start_price * 100) if start_price else 0

    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Price Change", f"${abs_change:,.2f}")
    with col2:
        st.metric("Return", f"{pct_change:,.2f}%")
    with col3:
        st.metric("Last Price", f"${end_price:,.2f}")

    # Control panel (checkbox and timeframe selector)
    st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)
    st.checkbox("Compare to S&P 500", key='buzz_compare_sp500')
    st.radio("Timeframe", list(tf_map.keys()), index=2, horizontal=True, key='buzz_timeframe')

    # Step 5: Update subtitle to reflect indexed data when comparing
    if compare_sp500:
        st.subheader(f"Indexed Price Performance ({tf_choice})")
    else:
        st.subheader(f"Price ({tf_choice})")
    try:
        import plotly.graph_objects as go

        fig = go.Figure()

        # Step 4: Conditional plotting based on comparison mode
        if compare_sp500:
            # Use indexed data when comparing
            y_data_buzz = hist["BUZZ_Indexed"]

            # Add BUZZ trace (no fill when comparing)
            fig.add_trace(
                go.Scatter(
                    x=hist.index,
                    y=y_data_buzz,
                    mode="lines",
                    line=dict(color="#00C805", width=3),
                    name="BUZZ",
                    customdata=hist["BUZZ_Return"],
                    hovertemplate="BUZZ: %{customdata:+.1f}%<extra></extra>",
                )
            )

            # Add S&P 500 trace if data exists
            if "SP500_Indexed" in hist.columns:
                fig.add_trace(
                    go.Scatter(
                        x=hist.index,
                        y=hist["SP500_Indexed"],
                        mode="lines",
                        line=dict(color="#7b9cc4", width=2, dash="solid"),
                        name="S&P 500",
                        customdata=hist["SP500_Return"],
                        hovertemplate="S&P 500: %{customdata:+.1f}%<extra></extra>",
                    )
                )

            # Calculate range for indexed data
            all_values = [y_data_buzz.min(), y_data_buzz.max()]
            if "SP500_Indexed" in hist.columns:
                all_values.extend([hist["SP500_Indexed"].min(), hist["SP500_Indexed"].max()])
            y_min, y_max = min(all_values), max(all_values)
            y_range = [y_min * 0.99, y_max * 1.01]

        else:
            # Use raw price data when not comparing
            y_data_buzz = hist["Close"]

            fig.add_trace(
                go.Scatter(
                    x=hist.index,
                    y=y_data_buzz,
                    mode="lines+markers",
                    line=dict(color="#00C805", width=3),
                    fill="tozeroy",
                    fillcolor="rgba(0,200,5,0.2)",
                    marker=dict(
                        size=7,
                        color="#00C805",
                        line=dict(color="#0f1623", width=1),
                        opacity=0
                    ),
                    name="BUZZ",
                    hovertemplate="Price: $%{y:,.2f}<extra></extra>",
                )
            )

            min_price = hist["Close"].min()
            max_price = hist["Close"].max()
            y_range = [min_price * 0.999, max_price * 1.001]

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            xaxis=dict(
                fixedrange=True,
                showspikes=True,
                spikemode="across",
                spikethickness=1,
                spikedash="dash",
                spikecolor="rgba(255,255,255,0.3)",
                showgrid=False,
                showline=False,
            ),
            yaxis=dict(
                fixedrange=True,
                showgrid=True,
                gridcolor="rgba(255,255,255,0.1)",
                griddash="dot",
                showline=False,
                side="right",
                range=y_range,
                title="Indexed (Base 100)" if compare_sp500 else None,
            ),
            hovermode="x unified",
            hoverlabel=dict(
                bgcolor="rgba(15,22,35,0.92)",
                bordercolor="#26d97a",
                font=dict(color="white"),
            ),
            margin=dict(l=10, r=10, t=10, b=10),
            showlegend=compare_sp500,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(15,22,35,0.8)",
                bordercolor="rgba(255,255,255,0.2)",
                borderwidth=1,
            ) if compare_sp500 else None,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    except Exception:
        if compare_sp500:
            st.line_chart(hist[["BUZZ_Indexed", "SP500_Indexed"]])
        else:
            st.line_chart(hist["Close"])

    st.stop()

# Conviction Ranking view
if st.session_state.view_mode_state == "Conviction Ranking":

    try:
        # Load dominance history data
        leaders_df = load_dominance_history()

        if not leaders_df.empty:
            # Create list of unique dates for slider
            unique_dates = sorted(leaders_df["date"].dropna().unique())

            # Format dates for display in select_slider
            date_labels = [d.strftime("%b %Y") for d in unique_dates]

            # Initialize session state for slider index
            if "dominance_idx" not in st.session_state:
                st.session_state.dominance_idx = len(date_labels) - 1  # Default to latest

            # Clamp index to valid range (in case date_labels changed)
            st.session_state.dominance_idx = max(0, min(st.session_state.dominance_idx, len(date_labels) - 1))

            # Create 3-column layout: [< button] [slider] [> button]
            col_left, col_slider, col_right = st.columns([1, 10, 1])

            with col_left:
                if st.button("◀", key="prev_month", use_container_width=True):
                    if st.session_state.dominance_idx > 0:
                        st.session_state.dominance_idx -= 1
                        st.rerun()

            with col_slider:
                # Use index-based slider for reliability
                selected_idx = st.slider(
                    "Select Month",
                    min_value=0,
                    max_value=len(date_labels) - 1,
                    value=st.session_state.dominance_idx,
                    format=date_labels[st.session_state.dominance_idx],
                    label_visibility="collapsed",
                )
                # Update if changed
                if selected_idx != st.session_state.dominance_idx:
                    st.session_state.dominance_idx = selected_idx
                    st.rerun()

            with col_right:
                if st.button("▶", key="next_month", use_container_width=True):
                    if st.session_state.dominance_idx < len(date_labels) - 1:
                        st.session_state.dominance_idx += 1
                        st.rerun()

            # Show current month label
            st.markdown(f"**{date_labels[st.session_state.dominance_idx]}**", unsafe_allow_html=True)

            # Get the actual date from the index
            selected_idx = st.session_state.dominance_idx
            selected_date = unique_dates[selected_idx]

            # Get who was #1 at this specific date
            current_month_leader = leaders_df[leaders_df["date"] == selected_date]["leader"].iloc[0] if not leaders_df[leaders_df["date"] == selected_date].empty else "N/A"

            # Get cumulative dominance data up to selected date
            top_data = get_cumulative_dominance(leaders_df, selected_date, top_n=15)

            if not top_data.empty:
                # Calculate stats
                current_leader = top_data.iloc[0]["ticker"]  # Top of the list (before reversing)
                current_count = top_data.iloc[0]["months_at_top"]
                total_unique = len(leaders_df[leaders_df["date"] <= selected_date]["leader"].unique())
                total_periods = len(leaders_df[leaders_df["date"] <= selected_date])

                # Header showing the selected month's #1 and cumulative leader
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 12px;">
                    <div style="background: rgba(30,41,59,0.5); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 16px 24px; flex: 1; min-width: 200px;">
                        <div style="color: #9ca3af; font-size: 0.85rem; margin-bottom: 4px;">#1 in {date_labels[st.session_state.dominance_idx]}</div>
                        <div style="color: #00C805; font-size: 1.8rem; font-weight: 700;">{current_month_leader}</div>
                    </div>
                    <div style="background: rgba(30,41,59,0.5); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 16px 24px; flex: 1; min-width: 200px;">
                        <div style="color: #9ca3af; font-size: 0.85rem; margin-bottom: 4px;">Cumulative Leader</div>
                        <div style="color: #00C805; font-size: 1.8rem; font-weight: 700;">{current_leader} <span style="font-size: 1rem; color: #9ca3af;">({current_count} months)</span></div>
                    </div>
                    <div style="background: rgba(30,41,59,0.5); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 16px 24px; text-align: center;">
                        <div style="color: #9ca3af; font-size: 0.85rem; margin-bottom: 4px;">Unique #1s</div>
                        <div style="color: #f1f5f9; font-size: 1.8rem; font-weight: 700;">{total_unique}</div>
                    </div>
                    <div style="background: rgba(30,41,59,0.5); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 16px 24px; text-align: center;">
                        <div style="color: #9ca3af; font-size: 0.85rem; margin-bottom: 4px;">Months Tracked</div>
                        <div style="color: #f1f5f9; font-size: 1.8rem; font-weight: 700;">{total_periods}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Reverse for horizontal bar chart (top at top)
                top_data = top_data.iloc[::-1].reset_index(drop=True)

                # Create color gradient (Yellow to Purple based on rank)
                def get_gradient_color(rank, total):
                    t = (rank - 1) / max(total - 1, 1)
                    r = int(255 - t * (255 - 139))
                    g = int(215 - t * (215 - 92))
                    b = int(0 + t * (246 - 0))
                    return f"rgb({r},{g},{b})"

                colors = [get_gradient_color(r, 15) for r in top_data["rank"]]

                # Create horizontal bar chart
                import plotly.graph_objects as go
                fig_race = go.Figure(go.Bar(
                    x=top_data["months_at_top"],
                    y=top_data["ticker"],
                    orientation="h",
                    marker=dict(color=colors, line=dict(width=0)),
                    text=top_data["months_at_top"],
                    textposition="outside",
                    textfont=dict(color="white", size=14),
                    hovertemplate="<b>%{y}</b><br>Months at #1: %{x}<extra></extra>",
                ))

                max_months = top_data["months_at_top"].max()
                x_max = max(max_months * 1.15, 5)

                fig_race.update_layout(
                    height=520,
                    margin=dict(t=10, l=80, r=50, b=40),
                    paper_bgcolor="#0c1119",
                    plot_bgcolor="#0c1119",
                    font=dict(color="white"),
                    xaxis=dict(
                        title=dict(text="Months as Top Holding", font=dict(color="#9ca3af")),
                        tickfont=dict(color="white"),
                        gridcolor="rgba(255,255,255,0.1)",
                        range=[0, x_max],
                    ),
                    yaxis=dict(
                        title="",
                        tickfont=dict(color="white", size=13),
                        gridcolor="rgba(255,255,255,0.05)",
                    ),
                    bargap=0.25,
                )

                st.plotly_chart(fig_race, use_container_width=True, config={"displayModeBar": False})

                # Explanation
                st.markdown("---")
                st.markdown("""
**How to read this chart:**
- Each bar shows how many months a stock has held the **#1 position** (highest sentiment score) in the BUZZ Index
- **Yellow bars** = top ranked | **Purple bars** = lower ranked
- Use the slider above to travel back in time and watch rankings evolve

**Metrics explained:**
- **#1 in [Month]** — The stock with the highest sentiment score during that specific month
- **Cumulative Leader** — The stock with the most total months at #1 up to the selected date
- **Unique #1s** — How many different stocks have ever reached the top spot
- **Months Tracked** — Total number of monthly rebalances covered up to the selected date
                """)

    except Exception as e:
        st.warning(f"Could not load dominance history: {e}")

    st.stop()

# Monthly Turnover view
if st.session_state.view_mode_state == "Monthly Turnover":
    st.caption("Portfolio churn rate showing percentage of holdings that change each month")

    # Load monthly turnover data
    try:
        turnover_path = _get_data_dir() / "BUZZ_Monthly_Turnover_Time_Series.csv"
        turnover_df_full = pd.read_csv(turnover_path)

        # Convert date to datetime
        turnover_df_full['Rebalance_date'] = pd.to_datetime(turnover_df_full['Rebalance_date'])

        # Get selected timeframe from session state
        timeframe = st.session_state.get('turnover_timeframe', 'ALL')

        # Filter data based on timeframe
        if timeframe == '6M':
            cutoff_date = pd.Timestamp.today() - pd.DateOffset(months=6)
            turnover_df = turnover_df_full[turnover_df_full['Rebalance_date'] >= cutoff_date].copy()
        elif timeframe == '1Y':
            cutoff_date = pd.Timestamp.today() - pd.DateOffset(years=1)
            turnover_df = turnover_df_full[turnover_df_full['Rebalance_date'] >= cutoff_date].copy()
        elif timeframe == 'YTD':
            cutoff_date = pd.Timestamp.today().replace(month=1, day=1)
            turnover_df = turnover_df_full[turnover_df_full['Rebalance_date'] >= cutoff_date].copy()
        elif timeframe == '3Y':
            cutoff_date = pd.Timestamp.today() - pd.DateOffset(years=3)
            turnover_df = turnover_df_full[turnover_df_full['Rebalance_date'] >= cutoff_date].copy()
        elif timeframe == '5Y':
            cutoff_date = pd.Timestamp.today() - pd.DateOffset(years=5)
            turnover_df = turnover_df_full[turnover_df_full['Rebalance_date'] >= cutoff_date].copy()
        else:  # ALL
            turnover_df = turnover_df_full.copy()

        # Calculate statistics for selected period
        avg_turnover = 22.91  # User-specified historical average (all-time)
        period_avg = turnover_df['Monthly_Turnover_Rate_Percent'].mean()
        min_turnover = turnover_df['Monthly_Turnover_Rate_Percent'].min()
        max_turnover = turnover_df['Monthly_Turnover_Rate_Percent'].max()

        # Display summary stats in metric boxes
        st.markdown(f'''
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Historical Average</div>
                <div class="metric-value">{avg_turnover}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Period Average ({timeframe})</div>
                <div class="metric-value">{period_avg:.2f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Min Turnover</div>
                <div class="metric-value">{min_turnover:.2f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Max Turnover</div>
                <div class="metric-value">{max_turnover:.2f}%</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        st.markdown('<div style="margin-top: 8px; margin-bottom: 8px; color: rgba(159,178,204,0.8); font-size: 0.85rem; font-style: italic;">Higher turnover indicates more aggressive rebalancing and portfolio changes.</div>', unsafe_allow_html=True)

        # Timeframe selector
        st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)
        st.radio("Timeframe", ["6M", "1Y", "YTD", "3Y", "5Y", "ALL"], index=5, horizontal=True, key='turnover_timeframe')

        # Create line chart using plotly
        try:
            import plotly.graph_objects as go

            fig = go.Figure()

            # Add main turnover line
            fig.add_trace(
                go.Scatter(
                    x=turnover_df['Rebalance_date'],
                    y=turnover_df['Monthly_Turnover_Rate_Percent'],
                    mode='lines',
                    line=dict(color='#00C805', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(0,200,5,0.1)',
                    name='Monthly Turnover',
                    hovertemplate="<b>%{x|%b %Y}</b><br>" +
                                  "Turnover: %{y:.2f}%<br>" +
                                  "<extra></extra>",
                )
            )

            # Add average line at 22.91%
            fig.add_hline(
                y=avg_turnover,
                line_dash="dash",
                line_color="rgba(255,165,0,0.7)",
                line_width=2,
                annotation_text=f"Historical Avg ({avg_turnover}%)",
                annotation_position="right",
                annotation_font_size=11,
                annotation_font_color="rgba(255,165,0,0.9)",
            )

            # Update layout
            fig.update_layout(
                xaxis_title="Rebalance Date",
                yaxis_title="Monthly Turnover Rate (%)",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"),
                height=600,
                xaxis=dict(
                    showgrid=True,
                    gridcolor="rgba(255,255,255,0.1)",
                    griddash="dot",
                    showline=False,
                    fixedrange=True,  # Disable zoom
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor="rgba(255,255,255,0.1)",
                    griddash="dot",
                    showline=False,
                    range=[0, max(turnover_df['Monthly_Turnover_Rate_Percent'].max() * 1.1, avg_turnover * 1.2)],
                    fixedrange=True,  # Disable zoom
                ),
                hovermode='x unified',
                hoverlabel=dict(
                    bgcolor="rgba(15,22,35,0.92)",
                    bordercolor="#26d97a",
                    font=dict(color="white"),
                ),
                margin=dict(l=10, r=10, t=10, b=10),
                showlegend=False,
            )

            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            # Add interpretation guide
            st.markdown("""
            ### Understanding Portfolio Turnover

            **What is Portfolio Turnover?**
            - Measures the percentage of the portfolio that changes each month
            - Calculated as: (Sum of Absolute Weight Changes) ÷ 2
            - Higher values indicate more active rebalancing

            **Interpreting the Chart:**
            - **Above Average Line:** More aggressive month with higher portfolio changes
            - **Below Average Line:** More stable month with fewer portfolio adjustments
            - **Spikes:** Major market events or significant sentiment shifts
            - **Stable Periods:** Consistent market sentiment and holdings
            """)

        except Exception as e:
            # Fallback to simple line chart if plotly fails
            st.line_chart(turnover_df.set_index('Rebalance_date')['Monthly_Turnover_Rate_Percent'])
            st.error(f"Note: Using simplified chart. Error: {e}")

    except FileNotFoundError:
        st.error("BUZZ_Monthly_Turnover_Time_Series.csv not found. Please run generate_monthly_turnover.py first.")
    except Exception as e:
        st.error(f"Error loading monthly turnover data: {e}")

    st.stop()

# BUZZ Heatmap view
if st.session_state.view_mode_state == "BUZZ Heatmap":
    st.caption("Daily price change by sector • Click a sector to drill down • Use pathbar to navigate back")

    try:
        import plotly.graph_objects as go

        # Reload fresh data for heatmap (don't use filtered df)
        heatmap_df = load_buzz_data()
        tickers_list = heatmap_df["Ticker"].tolist()

        # Show loading message while fetching data
        with st.spinner("Loading price data for 75 holdings..."):
            # Fetch daily changes for all tickers
            changes = get_daily_changes_batch(tuple(tickers_list))

        # Build hierarchical data structure for treemap
        # Structure: Sectors (top level) -> Tickers (leaves)
        ids = []
        labels = []
        parents = []
        values = []
        colors = []

        # Track sector totals for aggregation
        sector_data = {}

        # First pass: collect ticker data by sector
        for ticker in tickers_list:
            sector = SECTOR_MAP.get(ticker, "Other")
            weight = heatmap_df[heatmap_df["Ticker"] == ticker]["Weight"].iloc[0] * 100 if ticker in heatmap_df["Ticker"].values else 0.01
            change = changes.get(ticker, 0)

            if sector not in sector_data:
                sector_data[sector] = {"tickers": [], "total_weight": 0, "weighted_change": 0}

            sector_data[sector]["tickers"].append({
                "ticker": ticker,
                "weight": weight,
                "change": change
            })
            sector_data[sector]["total_weight"] += weight
            sector_data[sector]["weighted_change"] += change * weight

        # Second pass: add sectors and tickers to hierarchy
        # PRE-FORMATTED STRATEGY: Build label_text and custom_hover with hardcoded strings
        label_text = []    # Pre-formatted display text for each node
        custom_hover = []  # Pre-formatted hover text for each node

        # Add root node "Heatmap" for pathbar
        total_weight = sum(d["total_weight"] for d in sector_data.values())
        ids.append("Heatmap")
        labels.append("Heatmap")
        parents.append("")  # Root has no parent
        values.append(total_weight)
        colors.append(0)  # Neutral color for root
        label_text.append("<b>Heatmap</b>")
        custom_hover.append("Heatmap")  # Clean hover text for pathbar

        for sector, data in sector_data.items():
            # Calculate sector's weighted average change (ensure no NaN)
            sector_change = data["weighted_change"] / data["total_weight"] if data["total_weight"] > 0 else 0.0
            sector_change = round(sector_change, 2) if sector_change == sector_change else 0.0  # NaN check
            sector_weight = round(data["total_weight"], 2)

            # Add sector node (parent is root "Heatmap")
            ids.append(sector)
            labels.append(sector)
            parents.append("Heatmap")  # Parent is root
            values.append(data["total_weight"])
            colors.append(sector_change)
            label_text.append(f"<b>{sector}</b>")
            custom_hover.append(f"<b>{sector}</b><br>Weight: {sector_weight:.2f}%")

            # Add ticker nodes (parent is sector)
            for t_data in data["tickers"]:
                ticker_id = f"{sector}/{t_data['ticker']}"  # Unique ID
                ticker_change = round(t_data["change"], 2) if t_data["change"] == t_data["change"] else 0.0
                ticker_weight = round(t_data["weight"], 2)

                ids.append(ticker_id)
                labels.append(t_data["ticker"])
                parents.append(sector)
                values.append(t_data["weight"])
                colors.append(ticker_change)
                label_text.append(f"<b>{t_data['ticker']}</b><br>{ticker_change:+.2f}%")
                custom_hover.append(f"<b>{t_data['ticker']}</b><br>Weight: {ticker_weight:.2f}%")

        # Create the treemap with drill-down navigation
        fig = go.Figure(go.Treemap(
            ids=ids,
            labels=labels,
            parents=parents,
            values=values,
            text=label_text,  # Pre-formatted text for display
            customdata=custom_hover,  # Pre-formatted hover text
            marker=dict(
                colors=colors,
                colorscale=[
                    [0.0, "#FF0000"],      # Deep red for -5% or worse
                    [0.25, "#FF6B6B"],     # Light red
                    [0.5, "#1a1a2e"],      # Dark neutral (matches background)
                    [0.75, "#4ade80"],     # Light green
                    [1.0, "#00C805"],      # Deep green for +5% or better
                ],
                cmid=0,  # Center the colorscale at 0%
                cmin=-5,
                cmax=5,
                showscale=False,
                line=dict(width=2, color="#0f1623"),
            ),
            texttemplate="%{text}",  # Just print the pre-formatted text
            insidetextfont=dict(color="white", size=28),
            textposition="middle center",
            hovertemplate="%{customdata}<extra></extra>",  # Just print pre-formatted hover
            branchvalues="total",
            maxdepth=3,  # Show root + sectors + tickers all at once
            pathbar=dict(
                visible=True,
                thickness=32,
                textfont=dict(size=13, color="white", family="Arial"),
                edgeshape=">",
                side="top",
            ),
            root=dict(color="#0c1119"),  # Dark background for root area
            tiling=dict(
                packing="squarify",
                pad=3,
            ),
        ))

        # Update layout for dark theme
        fig.update_layout(
            height=900,
            margin=dict(t=50, l=10, r=10, b=10),
            paper_bgcolor="#0c1119",
            plot_bgcolor="#0c1119",
            font=dict(color="white"),
            treemapcolorway=["#1a1a2e"],
        )

        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # CSS to disable hover on pathbar only
        st.markdown("""
        <style>
        .js-plotly-plot .pathbar { pointer-events: none !important; }
        </style>
        """, unsafe_allow_html=True)

        # Summary metrics below the heatmap
        gainers = sum(1 for c in changes.values() if c > 0)
        losers = sum(1 for c in changes.values() if c < 0)

        # Find best and worst performers
        best_ticker = max(changes, key=changes.get) if changes else "N/A"
        best_change = changes.get(best_ticker, 0)
        worst_ticker = min(changes, key=changes.get) if changes else "N/A"
        worst_change = changes.get(worst_ticker, 0)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f'''
                <div style="background: rgba(30,41,59,0.5); border-radius: 12px; padding: 20px 24px; text-align: center; min-height: 100px; display: flex; flex-direction: column; justify-content: center;">
                    <div style="color: #9ca3af; font-size: 1rem;">Best Performer</div>
                    <div style="color: #00C805; font-size: 1.6rem; font-weight: 600;">{best_ticker} ({best_change:+.2f}%)</div>
                </div>
            ''', unsafe_allow_html=True)
        with col2:
            st.markdown(f'''
                <div style="background: rgba(30,41,59,0.5); border-radius: 12px; padding: 20px 24px; text-align: center; min-height: 100px; display: flex; flex-direction: column; justify-content: center;">
                    <div style="color: #9ca3af; font-size: 1rem;">Worst Performer</div>
                    <div style="color: #FF5252; font-size: 1.6rem; font-weight: 600;">{worst_ticker} ({worst_change:+.2f}%)</div>
                </div>
            ''', unsafe_allow_html=True)
        with col3:
            st.markdown(f'''
                <div style="background: rgba(30,41,59,0.5); border-radius: 12px; padding: 20px 24px; text-align: center; min-height: 100px; display: flex; flex-direction: column; justify-content: center;">
                    <div style="color: #9ca3af; font-size: 1rem;">Gainers</div>
                    <div style="color: #00C805; font-size: 1.6rem; font-weight: 600;">{gainers}</div>
                </div>
            ''', unsafe_allow_html=True)
        with col4:
            st.markdown(f'''
                <div style="background: rgba(30,41,59,0.5); border-radius: 12px; padding: 20px 24px; text-align: center; min-height: 100px; display: flex; flex-direction: column; justify-content: center;">
                    <div style="color: #9ca3af; font-size: 1rem;">Losers</div>
                    <div style="color: #FF5252; font-size: 1.6rem; font-weight: 600;">{losers}</div>
                </div>
            ''', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error loading heatmap: {e}")
        import traceback
        st.code(traceback.format_exc())

    st.stop()

# -----------------------------
# Helper functions for metrics
# -----------------------------

@st.cache_data
def load_historical_weight_data():
    """
    Load BuzzIndex_historical.csv and return the full DataFrame for weight calculations.
    Weight column is parsed as float. Only rows with non-zero weights are included.
    """
    try:
        csv_path = _get_data_dir() / "BuzzIndex_historical.csv"
        df = pd.read_csv(csv_path)

        # Normalize ticker names (FB -> META)
        df['Ticker'] = df['Ticker'].replace({'FB': 'META'})

        # Parse Weight as float and filter out zero/null values
        df['Weight'] = pd.to_numeric(df['Weight'], errors='coerce')
        df = df[df['Weight'].notna() & (df['Weight'] > 0)]

        # Parse Rebalance_date (DD/MM/YYYY format)
        df['Rebalance_date'] = pd.to_datetime(df['Rebalance_date'], format='%d/%m/%Y')

        return df
    except Exception as e:
        return pd.DataFrame()


def get_first_appearance_date(ticker: str) -> str:
    """
    Get the first date a ticker appeared in the BUZZ Index.
    Returns formatted date string (e.g., "Aug 18, 2016") or "N/A" if not found.
    """
    df = load_historical_weight_data()

    if df.empty:
        return "N/A"

    # Filter for this ticker only
    ticker_df = df[df['Ticker'] == ticker].copy()

    if ticker_df.empty:
        return "N/A"

    # Find the earliest rebalance date
    first_date = ticker_df['Rebalance_date'].min()

    return first_date.strftime("%b %d, %Y")


def get_historical_weight_range(ticker: str) -> dict:
    """
    Calculate the all-time min and max Weight values for a ticker.

    Returns a dict with:
        - min_weight: float (as percentage, e.g., 0.50 for 0.50%)
        - max_weight: float (as percentage, e.g., 3.00 for 3.00%)
        - min_date: str (date when min occurred, e.g., "Aug 18, 2016")
        - max_date: str (date when max occurred)
        - range_str: str (formatted display string, e.g., "0.50% – 3.00%")
    """
    df = load_historical_weight_data()

    if df.empty:
        return {'range_str': 'N/A', 'min_weight': None, 'max_weight': None,
                'min_date': None, 'max_date': None}

    # Filter for this ticker only
    ticker_df = df[df['Ticker'] == ticker].copy()

    if ticker_df.empty:
        return {'range_str': 'N/A', 'min_weight': None, 'max_weight': None,
                'min_date': None, 'max_date': None}

    # Find min and max weights (Weight is stored as decimal, e.g., 0.03 = 3%)
    min_idx = ticker_df['Weight'].idxmin()
    max_idx = ticker_df['Weight'].idxmax()

    min_weight = ticker_df.loc[min_idx, 'Weight']
    max_weight = ticker_df.loc[max_idx, 'Weight']
    min_date = ticker_df.loc[min_idx, 'Rebalance_date']
    max_date = ticker_df.loc[max_idx, 'Rebalance_date']

    # Convert decimal to percentage (0.03 -> 3.00)
    min_pct = min_weight * 100
    max_pct = max_weight * 100

    # Format dates
    min_date_str = min_date.strftime("%b %d, %Y")
    max_date_str = max_date.strftime("%b %d, %Y")

    # Create display string with en-dash
    range_str = f"{min_pct:.2f}% – {max_pct:.2f}%"

    return {
        'range_str': range_str,
        'min_weight': min_pct,
        'max_weight': max_pct,
        'min_date': min_date_str,
        'max_date': max_date_str
    }


@st.cache_data
def load_historical_buzz_data():
    """
    Load and process BuzzIndex_historical.csv for calculating max consecutive months.
    Returns a dictionary mapping ticker -> max consecutive months held.
    """
    try:
        csv_path = _get_data_dir() / "BuzzIndex_historical.csv"
        df = pd.read_csv(csv_path)

        # Normalize ticker names for companies that changed names
        # FB -> META (Facebook rebranded to Meta in 2021)
        df['Ticker'] = df['Ticker'].replace({'FB': 'META'})

        # Convert Rebalance_date to datetime (format is DD/MM/YYYY)
        df['Rebalance_date'] = pd.to_datetime(df['Rebalance_date'], format='%d/%m/%Y')

        # Sort by ticker and date
        df = df.sort_values(['Ticker', 'Rebalance_date'])

        # Calculate max consecutive months for each ticker
        results = {}
        for ticker in df['Ticker'].unique():
            ticker_df = df[df['Ticker'] == ticker]
            max_months = calculate_max_consecutive_months_for_ticker(ticker_df)
            results[ticker] = max_months

        return results
    except Exception as e:
        st.warning(f"Could not load historical BUZZ data: {e}")
        return {}

def calculate_max_consecutive_months_for_ticker(ticker_df):
    """
    Calculate the CURRENT consecutive months a ticker has been held.
    Counts backwards from the most recent date until hitting a gap.
    """
    if len(ticker_df) == 0:
        return 0

    # Get sorted dates for this ticker
    dates = ticker_df['Rebalance_date'].sort_values().values

    if len(dates) == 1:
        return 1

    # Start from the most recent date and count backwards
    current_consecutive = 1

    # Count backwards from the most recent date
    for i in range(len(dates) - 1, 0, -1):
        current_date = pd.Timestamp(dates[i])
        prev_date = pd.Timestamp(dates[i-1])
        days_diff = (current_date - prev_date).days

        # Consider it consecutive if difference is between 25 and 35 days (approximately 1 month)
        if 25 <= days_diff <= 35:
            current_consecutive += 1
        else:
            # Hit a gap - stop counting
            break

    return current_consecutive

def get_max_consecutive_months(ticker: str) -> int:
    """
    Get the CURRENT consecutive months held for a ticker from historical data.
    Counts backwards from the most recent month until hitting a gap.
    """
    historical_data = load_historical_buzz_data()
    return historical_data.get(ticker, 0)

def compute_consecutive_months(df_all: pd.DataFrame, ticker: str) -> int:
    """
    Compute number of consecutive months (from the latest month in the index)
    that `ticker` has appeared in the index.

    If the ticker does *not* appear in the latest index month, tenure = 0.
    """
    if df_all.empty or "Date" not in df_all.columns:
        return "N/A"
    df_all = df_all.copy()
    df_all["YearMonth"] = pd.to_datetime(df_all["Date"]).dt.to_period("M")

    ticker_months = set(df_all.loc[df_all["Ticker"] == ticker, "YearMonth"].unique())
    if not ticker_months:
        return "N/A"

    all_months = np.sort(df_all["YearMonth"].unique())
    # If we only have one month/day of data, count as 1
    if len(all_months) <= 1:
        return 1

    tenure = 0
    for month in all_months[::-1]:  # start from latest month
        if month in ticker_months:
            tenure += 1
        else:
            break

    return tenure


def get_latest_ticker_row(df_all: pd.DataFrame, ticker: str) -> pd.Series | None:
    """
    Get the latest row for this ticker (by Date).
    """
    ticker_df = df_all[df_all["Ticker"] == ticker].copy()
    if ticker_df.empty:
        return None

    latest_date = ticker_df["Date"].max()
    latest_rows = ticker_df[ticker_df["Date"] == latest_date]
    if "Rank" in latest_rows.columns:
        latest_rows = latest_rows.sort_values("Rank")
    return latest_rows.iloc[0]


def render_key_metrics(ticker: str):
    """
    Render seven key metrics for the given ticker below the description.
    Uses yfinance.info and calendar; falls back to N/A when data is missing.
    """
    ticker_obj = yf.Ticker(ticker)
    info = ticker_obj.info

    def fmt_bil(val):
        if val is None:
            return "N/A"
        if val >= 1e12:
            return f"${val/1e12:,.1f}T"
        return f"${val/1e9:,.1f}B"

    def fmt_2(val):
        return f"{val:.2f}" if val is not None else "N/A"

    def fmt_pe(val):
        """Format P/E ratio with outlier handling: negative or > 1000 = N/A"""
        if val is None:
            return "N/A"
        if val < 0 or val > 1000:
            return "N/A"
        return f"{val:.2f}"

    def fmt_ps(val):
        """Format P/S ratio with outlier handling: negative or > 500 = N/A"""
        if val is None:
            return "N/A"
        if val < 0 or val > 500:
            return "N/A"
        return f"{val:.2f}"

    market_cap = fmt_bil(info.get("marketCap"))
    pe_trailing = fmt_pe(info.get("trailingPE"))
    pe_forward = fmt_pe(info.get("forwardPE"))
    ps_ratio = fmt_ps(info.get("priceToSalesTrailing12Months"))
    beta = fmt_2(info.get("beta"))

    # 52-week range
    week_low = info.get("fiftyTwoWeekLow")
    week_high = info.get("fiftyTwoWeekHigh")
    if week_low is not None and week_high is not None:
        week_range = f"${week_low:.2f} - ${week_high:.2f}"
    else:
        week_range = "N/A"

    # Next earnings date
    earnings_date = "N/A"
    try:
        from datetime import datetime

        calendar = ticker_obj.calendar
        if calendar is not None and 'Earnings Date' in calendar:
            earnings_dates = calendar['Earnings Date']
            if isinstance(earnings_dates, list) and len(earnings_dates) > 0:
                # Get today's date for comparison
                today = datetime.now().date()

                # Filter for future dates only
                future_dates = [d for d in earnings_dates if d > today]

                if future_dates:
                    # Get the nearest future earnings date (minimum = soonest)
                    next_earnings = min(future_dates)
                    earnings_date = next_earnings.strftime("%b %d, %Y")
                # If no future dates exist, leave as N/A (don't show past dates)
            elif hasattr(earnings_dates, 'strftime'):
                # Single date object (fallback) - only show if future
                if earnings_dates > today:
                    earnings_date = earnings_dates.strftime("%b %d, %Y")
    except Exception:
        earnings_date = "N/A"

    # Historical Weight Range from BUZZ Index history
    weight_range_data = get_historical_weight_range(ticker)
    weight_range_str = weight_range_data['range_str']
    # Build tooltip text with min/max dates for verification
    if weight_range_data['min_date'] and weight_range_data['max_date']:
        weight_tooltip = f"Min: {weight_range_data['min_weight']:.2f}% on {weight_range_data['min_date']} | Max: {weight_range_data['max_weight']:.2f}% on {weight_range_data['max_date']}"
    else:
        weight_tooltip = ""

    # First Appearance within BUZZ
    first_appearance = get_first_appearance_date(ticker)

    # Render custom grid layout
    st.markdown(f'''
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Market Cap</div>
                <div class="metric-value">{market_cap}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Trailing P/E</div>
                <div class="metric-value">{pe_trailing}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Forward P/E</div>
                <div class="metric-value">{pe_forward}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">P/S Ratio</div>
                <div class="metric-value">{ps_ratio}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Beta</div>
                <div class="metric-value">{beta}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">52-Week Range</div>
                <div class="metric-value">{week_range}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Next Earnings Date</div>
                <div class="metric-value">{earnings_date}</div>
            </div>
            <div class="metric-card" title="{weight_tooltip}">
                <div class="metric-label">Historical Weight Range</div>
                <div class="metric-value">{weight_range_str}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">First Appearance within BUZZ</div>
                <div class="metric-value">{first_appearance}</div>
            </div>
        </div>
    ''', unsafe_allow_html=True)


def render_stock_chart(ticker: str):
    """
    Render a live stock price chart with timeframe selector.
    """
    import plotly.graph_objects as go

    # Timeframe configuration (same as BUZZ Performance chart)
    tf_map = {
        "1D": dict(period="1d", interval="5m"),
        "5D": dict(period="5d", interval="30m"),
        "1M": dict(period="1mo", interval="1h"),
        "6M": dict(period="6mo", interval="1d"),
        "1Y": dict(period="1y", interval="1d"),
        "YTD": dict(period="ytd", interval="1d"),
        "ALL": dict(period="max", interval="1d"),
    }

    # Session state key unique to this ticker's chart
    tf_key = f"stock_chart_tf_{ticker}"
    if tf_key not in st.session_state:
        st.session_state[tf_key] = "1D"

    tf_choice = st.session_state[tf_key]
    tf_sel = tf_map[tf_choice]

    # Fetch stock data
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_stock_history(tkr: str, period: str, interval: str) -> pd.DataFrame:
        t = yf.Ticker(tkr)
        hist = t.history(period=period, interval=interval)
        return hist

    @st.cache_data(ttl=300)
    def get_daily_prices(tkr: str) -> tuple[float | None, float | None]:
        """Get yesterday's close and today's price from daily data to match title area."""
        t = yf.Ticker(tkr)
        hist = t.history(period="1mo", interval="1d")
        if len(hist) >= 2:
            return hist["Close"].iloc[-2], hist["Close"].iloc[-1]
        return None, None

    try:
        hist = get_stock_history(ticker, tf_sel["period"], tf_sel["interval"])
    except Exception as exc:
        st.error(f"Failed to load stock data: {exc}")
        return

    if hist.empty or "Close" not in hist.columns:
        st.warning(f"No historical data available for {ticker}.")
        return

    # Calculate metrics
    # For 1D timeframe, use daily data to match the title area display exactly
    if tf_choice == "1D":
        prev_close, current_price = get_daily_prices(ticker)
        if prev_close and current_price:
            start_price = prev_close
            end_price = current_price
        else:
            start_price = hist["Close"].iloc[0]
            end_price = hist["Close"].iloc[-1]
    else:
        start_price = hist["Close"].iloc[0]
        end_price = hist["Close"].iloc[-1]

    abs_change = end_price - start_price
    pct_change = (abs_change / start_price * 100) if start_price else 0

    # Determine color based on performance
    line_color = "#00C805" if pct_change >= 0 else "#FF5252"
    fill_color = "rgba(0, 200, 5, 0.1)" if pct_change >= 0 else "rgba(255, 82, 82, 0.1)"

    # Timeframe selector
    st.radio("Timeframe", list(tf_map.keys()), index=list(tf_map.keys()).index(tf_choice), horizontal=True, key=tf_key)

    # Display metrics row with custom styling for percentage
    pct_color = "#00C805" if pct_change >= 0 else "#FF5252"

    # Format price change properly (handle negative sign before dollar sign)
    if abs_change >= 0:
        change_str = f"+${float(abs_change):.2f}"
    else:
        change_str = f"-${abs(float(abs_change)):.2f}"

    st.markdown(f'''
        <div style="display: flex; gap: 1rem; margin-bottom: 1rem;">
            <div style="flex: 1; background: rgba(30,41,59,0.5); border-radius: 8px; padding: 12px 16px;">
                <div style="color: #9ca3af; font-size: 0.85rem; margin-bottom: 4px;">Price Change</div>
                <div style="color: #f1f5f9; font-size: 1.5rem; font-weight: 600;">
                    {change_str} <span style="color: {pct_color}; font-size: 0.9rem;">({pct_change:+.2f}%)</span>
                </div>
            </div>
            <div style="flex: 1; background: rgba(30,41,59,0.5); border-radius: 8px; padding: 12px 16px;">
                <div style="color: #9ca3af; font-size: 0.85rem; margin-bottom: 4px;">Open Price</div>
                <div style="color: #f1f5f9; font-size: 1.5rem; font-weight: 600;">${float(start_price):.2f}</div>
            </div>
        </div>
    ''', unsafe_allow_html=True)

    # Create chart
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=hist.index,
            y=hist["Close"],
            mode="lines",
            line=dict(color=line_color, width=2),
            fill="tozeroy",
            fillcolor=fill_color,
            name=ticker,
            hovertemplate=f"{ticker}: $%{{y:,.2f}}<extra></extra>",
        )
    )

    # Chart layout
    fig.update_layout(
        height=350,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(128,128,128,0.1)",
            showline=False,
            tickfont=dict(color="#9ca3af"),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(128,128,128,0.1)",
            showline=False,
            tickfont=dict(color="#9ca3af"),
            tickprefix="$",
        ),
        hovermode="x unified",
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_news_section(ticker: str):
    """
    Render up to 5 recent news items for the ticker.
    Shows headline (clickable) and publisher/date underneath.
    """
    news_items = []
    fetch_errors: list[str] = []
    try:
        t = yf.Ticker(ticker)
        # Try both APIs; some yfinance versions use .news, others .get_news()
        news_items = (t.news or []) if hasattr(t, "news") else []
        if not news_items and hasattr(t, "get_news"):
            news_items = t.get_news() or []
    except Exception as exc:
        fetch_errors.append(str(exc))

    if not news_items:
        st.info("No recent news found.")
        if fetch_errors:
            st.caption(f"(debug: {fetch_errors})")
        return

    # Present as simple hyperlinked titles only
    count = 0
    for item in news_items:
        title = item.get("title") or item.get("headline") or item.get("content", {}).get("title")
        if not title:
            continue
        raw_link = (
            item.get("link")
            or item.get("url")
            or item.get("content", {}).get("canonicalUrl")
            or item.get("content", {}).get("clickThroughUrl")
        )
        if isinstance(raw_link, dict):
            raw_link = raw_link.get("url") or raw_link.get("href")
        link = raw_link if isinstance(raw_link, str) else "#"
        st.markdown(f"- [{title}]({link})", unsafe_allow_html=True)
        count += 1
        if count >= 5:
            break

# -----------------------------
# Top Row: Media Prep Metrics
# -----------------------------
st.markdown('<div class="fp-section-title">Media Prep Snapshot</div>', unsafe_allow_html=True)
latest_row = get_latest_ticker_row(df, selected_ticker)

col1, col2, col3 = st.columns(3)
with col1:
    max_consecutive = get_max_consecutive_months(selected_ticker)
    st.metric("Consecutive Months Held", f"{max_consecutive}")

with col2:
    # Support both old "PercentNetAssets" and new "Weight" column formats
    pct_val = None
    if latest_row is not None:
        if "PercentNetAssets" in latest_row and pd.notna(latest_row.get("PercentNetAssets")):
            pct_val = float(latest_row["PercentNetAssets"])
        elif "Weight" in latest_row and pd.notna(latest_row.get("Weight")):
            # Weight is decimal (0.0382 = 3.82%), convert to percentage
            pct_val = float(latest_row["Weight"]) * 100
    if pct_val is not None:
        st.metric("% of Net Assets", f"{pct_val:.2f}%")
    else:
        st.metric("% of Net Assets", "N/A")

with col3:
    # Support both old "MarketValueUSD" and new "MarketValue" column formats
    mv_val = None
    if latest_row is not None:
        if "MarketValueUSD" in latest_row and pd.notna(latest_row.get("MarketValueUSD")):
            mv_val = float(latest_row["MarketValueUSD"])
        elif "MarketValue" in latest_row and pd.notna(latest_row.get("MarketValue")):
            mv_val = float(latest_row["MarketValue"])
    if mv_val is not None:
        st.metric("Market Value (USD)", f"${mv_val:,.0f}")
    else:
        st.metric("Market Value (USD)", "N/A")

# Description box
desc_text = desc_map.get(selected_ticker, "Description not available for this ticker.")
st.markdown('<div class="fp-section-title" style="margin-top:0.6rem;">Description</div>', unsafe_allow_html=True)
st.markdown(f'<div class="fp-desc-box">{desc_text}</div>', unsafe_allow_html=True)
st.markdown('<div style="margin-bottom: 24px;"></div>', unsafe_allow_html=True)
st.markdown('<div class="fp-section-title">Key Metrics</div>', unsafe_allow_html=True)
render_key_metrics(selected_ticker)
st.markdown('<div style="margin-bottom: 24px;"></div>', unsafe_allow_html=True)
st.markdown('<div class="fp-section-title">Stock Price</div>', unsafe_allow_html=True)
render_stock_chart(selected_ticker)
st.markdown('<div style="margin-bottom: 24px;"></div>', unsafe_allow_html=True)
st.markdown('<div class="fp-section-title">Recent News</div>', unsafe_allow_html=True)
render_news_section(selected_ticker)


# -----------------------------
# Middle/Bottom sections removed per request; focus only on snapshot above.
