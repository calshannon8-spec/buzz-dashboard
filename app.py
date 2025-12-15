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
        --accent: #7AA2FF;
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
        color: #7AA2FF !important;
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

    /* Market Value Cell - White, Bold */
    .dark-market-value {
        font-family: 'SF Mono', 'Consolas', 'Monaco', monospace;
        font-variant-numeric: tabular-nums;
        font-size: 0.875rem;
        font-weight: 700;
        color: #ffffff;
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
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px !important;
        margin-top: 0.5rem !important;
        margin-bottom: -0.5rem !important;
        padding-bottom: 0 !important;
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

    /* Hide default Streamlit sidebar toggle */
    [data-testid="collapsedControl"] {
        display: none !important;
    }

    /* ========== SIDEBAR STYLING ========== */
    section[data-testid="stSidebar"] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        width: 280px !important;
        min-width: 280px !important;
        transform: none !important;
        margin-left: 0 !important;
        position: relative !important;
        background: #0a0e14 !important;
        border-right: 1px solid rgba(255,255,255,0.06) !important;
    }
    section[data-testid="stSidebar"] > div {
        width: 280px !important;
        padding: 1.5rem 1.25rem !important;
        background: #0a0e14 !important;
    }
    section[data-testid="stSidebar"] > div > div {
        background: transparent !important;
    }

    /* Sidebar section headers */
    .sidebar-section-header {
        font-size: 0.65rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 1.2px !important;
        color: #5a6775 !important;
        margin-bottom: 12px !important;
        padding-left: 2px !important;
    }
    .sidebar-divider {
        height: 1px;
        background: rgba(255,255,255,0.06);
        margin: 20px 0;
    }

    /* Sidebar selectbox styling */
    section[data-testid="stSidebar"] [data-testid="stSelectbox"] {
        margin-bottom: 12px !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSelectbox"] label {
        font-size: 0.7rem !important;
        color: #6b7a8a !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        margin-bottom: 6px !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 6px !important;
        color: var(--text) !important;
        font-size: 0.85rem !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div:hover {
        border-color: rgba(122, 162, 255, 0.3) !important;
        background: rgba(255,255,255,0.05) !important;
    }

    /* Sidebar text input styling */
    section[data-testid="stSidebar"] [data-testid="stTextInput"] {
        margin-bottom: 8px !important;
    }
    section[data-testid="stSidebar"] [data-testid="stTextInput"] label {
        font-size: 0.7rem !important;
        color: #6b7a8a !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        margin-bottom: 6px !important;
    }
    section[data-testid="stSidebar"] [data-testid="stTextInput"] input {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 6px !important;
        color: var(--text) !important;
        font-size: 0.85rem !important;
        padding: 10px 12px !important;
    }
    section[data-testid="stSidebar"] [data-testid="stTextInput"] input:focus {
        border-color: rgba(122, 162, 255, 0.5) !important;
        box-shadow: 0 0 0 1px rgba(122, 162, 255, 0.2) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stTextInput"] input::placeholder {
        color: #4a5568 !important;
        font-size: 0.8rem !important;
    }

    /* Sidebar caption styling */
    section[data-testid="stSidebar"] .stCaption {
        font-size: 0.7rem !important;
        color: #5a6775 !important;
    }

    /* Sidebar radio (view navigation) styling */
    section[data-testid="stSidebar"] [data-testid="stRadio"] > label {
        font-size: 0.7rem !important;
        color: #6b7a8a !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        margin-bottom: 8px !important;
        display: none !important;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div {
        gap: 4px !important;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label {
        display: flex !important;
        align-items: center !important;
        padding: 10px 12px !important;
        margin: 0 !important;
        border-radius: 6px !important;
        background: transparent !important;
        border: 1px solid transparent !important;
        transition: all 0.15s ease !important;
        cursor: pointer !important;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label:hover {
        background: rgba(255,255,255,0.04) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label[data-checked="true"] {
        background: rgba(122, 162, 255, 0.08) !important;
        border-color: rgba(122, 162, 255, 0.2) !important;
        border-left: 3px solid #7AA2FF !important;
        padding-left: 9px !important;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label span {
        font-size: 0.82rem !important;
        color: #8a96a3 !important;
        font-weight: 400 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label[data-checked="true"] span {
        color: #e8edf5 !important;
        font-weight: 500 !important;
    }
    /* Hide radio circle */
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label > div:first-child {
        display: none !important;
    }

    /* Sidebar button styling (for search matches) */
    section[data-testid="stSidebar"] .stButton > button {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 6px !important;
        color: var(--text) !important;
        font-size: 0.8rem !important;
        padding: 6px 12px !important;
        width: 100% !important;
        text-align: left !important;
        transition: all 0.15s ease !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(122, 162, 255, 0.1) !important;
        border-color: rgba(122, 162, 255, 0.3) !important;
    }

    /* ========== SNAPSHOT PAGE REDESIGN v2 ========== */

    /* Hide duplicate Streamlit header on snapshot pages */
    [data-testid="stMainBlockContainer"] > div:first-child > div:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }

    /* Main Container - left-aligned */
    .snap-wrap {
        max-width: 1280px;
        margin: 0;
        padding: 0;
    }

    /* ===== HERO SECTION ===== */
    .snap-hero {
        margin-bottom: 20px;
        padding-bottom: 16px;
        border-bottom: 1px solid rgba(255,255,255,0.06);
    }
    .snap-hero-top {
        display: flex;
        align-items: baseline;
        gap: 10px;
        margin-bottom: 4px;
    }
    .snap-ticker {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--text);
        letter-spacing: -0.5px;
    }
    .snap-company {
        font-size: 0.95rem;
        color: var(--muted);
        font-weight: 400;
    }
    .snap-price-row {
        display: flex;
        align-items: baseline;
        gap: 12px;
        margin-bottom: 10px;
    }
    .snap-price {
        font-size: 2.2rem;
        font-weight: 700;
        color: var(--text);
        letter-spacing: -0.5px;
    }
    .snap-change {
        font-size: 1rem;
        font-weight: 600;
    }
    .snap-change.up { color: #22c55e; }
    .snap-change.down { color: #ef4444; }
    .snap-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 2px;
    }
    .snap-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 8px 14px;
        background: rgba(255,255,255,0.05);
        border-radius: 8px;
        font-size: 0.82rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.15);
    }
    .snap-chip-lbl {
        color: var(--muted);
        font-size: 0.75rem;
        font-weight: 400;
    }
    .snap-chip-val {
        color: var(--text);
        font-weight: 600;
        font-size: 0.85rem;
    }

    /* ===== MAIN GRID (Chart + Sidebar) ===== */
    .snap-grid {
        display: grid;
        grid-template-columns: 1fr 280px;
        gap: 20px;
        align-items: start;
        margin-bottom: 20px;
    }
    @media (max-width: 900px) {
        .snap-grid {
            grid-template-columns: 1fr;
        }
    }

    /* ===== CHART AREA ===== */
    .snap-chart-wrap {
        background: rgba(255,255,255,0.015);
        border-radius: 10px;
        padding: 12px 16px 16px;
    }

    /* Timeframe Pills */
    .snap-tf-bar {
        display: flex;
        gap: 4px;
        margin-bottom: 12px;
    }
    .snap-tf-btn {
        padding: 5px 12px;
        font-size: 0.75rem;
        font-weight: 500;
        color: var(--muted);
        background: transparent;
        border: 1px solid transparent;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.15s ease;
    }
    .snap-tf-btn:hover {
        color: var(--text);
        background: rgba(255,255,255,0.04);
    }
    .snap-tf-btn.active {
        color: var(--text);
        background: rgba(255,255,255,0.08);
        border-color: rgba(255,255,255,0.1);
    }

    /* Stats Strip (OHLC / Period) */
    .snap-stats-strip {
        margin-top: 24px;
        border-top: 1px solid rgba(255,255,255,0.06);
        padding-top: 12px;
    }
    .snap-stats-hdr {
        font-size: 0.85rem;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
        opacity: 0.7;
    }
    .snap-ohlc {
        display: flex;
        justify-content: space-between;
        gap: 16px;
    }
    .snap-ohlc-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 2px;
        flex: 1;
    }
    .snap-ohlc-lbl {
        font-size: 0.8rem;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }
    .snap-ohlc-val {
        font-size: 0.95rem;
        color: var(--text);
        font-weight: 600;
    }

    /* ===== SIDEBAR ===== */
    .snap-sidebar {
        display: flex;
        flex-direction: column;
        gap: 16px;
    }
    .snap-card {
        background: rgba(255,255,255,0.02);
        border-radius: 10px;
        padding: 14px;
    }
    .snap-card-hdr {
        font-size: 0.85rem;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
        margin-bottom: 8px;
        padding-bottom: 8px;
        border-bottom: 1px solid rgba(255,255,255,0.06);
    }
    .snap-rows {
        display: flex;
        flex-direction: column;
    }
    .snap-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 4px;
        border-bottom: 1px solid rgba(255,255,255,0.04);
        transition: background 0.1s ease;
    }
    .snap-row:last-child {
        border-bottom: none;
    }
    .snap-row:hover {
        background: rgba(255,255,255,0.02);
    }
    .snap-row-lbl {
        font-size: 0.9rem;
        color: var(--muted);
        flex-shrink: 0;
    }
    .snap-row-val {
        font-size: 0.95rem;
        color: var(--text);
        font-weight: 600;
        text-align: right;
        min-width: 70px;
    }
    .snap-row-val.na {
        color: var(--muted);
        opacity: 0.6;
        font-weight: 400;
    }

    /* ===== ABOUT/DESCRIPTION TEXT ===== */
    .snap-about-txt {
        font-size: 0.9rem;
        color: var(--text);
        line-height: 1.5;
        opacity: 0.85;
        max-height: 150px;
        overflow-y: auto;
        padding-right: 4px;
    }
    .snap-about-txt::-webkit-scrollbar {
        width: 4px;
    }
    .snap-about-txt::-webkit-scrollbar-track {
        background: transparent;
    }
    .snap-about-txt::-webkit-scrollbar-thumb {
        background: rgba(255,255,255,0.1);
        border-radius: 2px;
    }

    /* ===== SPACING TOKENS ===== */
    :root {
        --section-gap: 24px;
        --header-content-gap: 12px;
        --item-gap: 0;
    }

    /* ===== NEWS SECTION ===== */
    .snap-news-section {
        display: block;
        clear: both;
        width: 100%;
        margin-top: 12px;
        padding-top: 16px;
        border-top: 1px solid rgba(255,255,255,0.06);
    }

    /* Force news container to break out of column flow */
    [data-testid="stMarkdown"]:has(.snap-news-section) {
        display: block !important;
        width: 100% !important;
        clear: both !important;
    }
    .snap-news-hdr {
        font-size: 0.85rem;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
        margin: 0 0 var(--header-content-gap) 0;
    }
    .snap-news-list {
        display: flex;
        flex-direction: column;
    }
    .snap-news-item {
        padding: 10px 0;
        border-bottom: 1px solid rgba(255,255,255,0.04);
    }
    .snap-news-item:first-child { padding-top: 0; }
    .snap-news-item:last-child { border-bottom: none; padding-bottom: 0; }
    .snap-news-title {
        font-size: 0.85rem;
        color: var(--text);
        font-weight: 500;
        line-height: 1.4;
        margin-bottom: 3px;
    }
    .snap-news-title a {
        color: var(--text);
        text-decoration: none;
    }
    .snap-news-title a:hover { color: var(--accent); }
    .snap-news-meta {
        font-size: 0.7rem;
        color: var(--muted);
    }
    .snap-news-empty {
        font-size: 0.8rem;
        color: var(--muted);
    }

    /* ===== STREAMLIT OVERRIDES FOR SNAPSHOT PAGE ===== */

    /* Timeframe selector - minimal compact tabs */
    [data-testid="stHorizontalBlock"] [data-testid="stRadio"] > div {
        gap: 0 !important;
        background: transparent !important;
        padding: 0 !important;
    }
    [data-testid="stHorizontalBlock"] [data-testid="stRadio"] label {
        padding: 3px 8px !important;
        font-size: 0.65rem !important;
        font-weight: 500 !important;
        border-radius: 4px !important;
        border: none !important;
        background: transparent !important;
        transition: all 0.1s ease !important;
        min-height: auto !important;
        line-height: 1.2 !important;
    }
    [data-testid="stHorizontalBlock"] [data-testid="stRadio"] label:hover {
        background: rgba(255,255,255,0.05) !important;
    }
    [data-testid="stHorizontalBlock"] [data-testid="stRadio"] label[data-checked="true"] {
        background: rgba(255,255,255,0.08) !important;
    }
    [data-testid="stHorizontalBlock"] [data-testid="stRadio"] label span {
        color: var(--muted) !important;
        font-size: 0.65rem !important;
    }
    [data-testid="stHorizontalBlock"] [data-testid="stRadio"] label[data-checked="true"] span {
        color: var(--text) !important;
    }

    /* Hide radio circles */
    [data-testid="stHorizontalBlock"] [data-testid="stRadio"] input[type="radio"] {
        display: none !important;
    }

    /* Tighter column gaps and remove extra space after columns */
    .stColumns,
    [data-testid="stHorizontalBlock"] {
        gap: 20px !important;
        margin-bottom: 0 !important;
    }

    /* Remove excessive vertical space between elements */
    [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"] {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }

    /* Reduce default element spacing in main container */
    .stMainBlockContainer [data-testid="stVerticalBlock"] > div {
        margin-bottom: 0 !important;
    }

    /* Clean up expander styling */
    [data-testid="stExpander"] {
        border: none !important;
        background: transparent !important;
    }
    [data-testid="stExpander"] summary {
        font-size: 0.7rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        font-weight: 600 !important;
        color: var(--muted) !important;
        padding: 8px 0 !important;
    }
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
        padding: 12px 0 16px 16px !important;
    }
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] p,
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] li,
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] strong {
        font-size: 0.8rem !important;
        line-height: 1.5 !important;
    }

    /* Small action buttons (show more/toggle) */
    .snap-card + div button,
    .snap-news + div button,
    [data-testid="stButton"] button {
        font-size: 0.72rem !important;
        padding: 6px 12px !important;
        border-radius: 6px !important;
    }

    /* ===== CONVICTION RANKING PAGE ===== */
    .conv-wrap {
        max-width: 1280px;
        margin: 0;
        padding: 0;
    }

    /* Hero - simpler, just title */
    .conv-hero {
        margin-bottom: 8px;
    }
    .conv-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--text);
        margin-bottom: 2px;
        letter-spacing: -0.5px;
    }
    .conv-subtitle {
        font-size: 0.85rem;
        color: var(--muted);
        margin-bottom: 4px;
    }
    .conv-viewing {
        font-size: 0.85rem;
        color: var(--muted);
        margin-bottom: 16px;
    }

    /* Toolbar row - compact navigation */
    .conv-toolbar {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 14px;
        background: rgba(255,255,255,0.02);
        border-radius: 8px;
        margin-bottom: 16px;
        border: 1px solid rgba(255,255,255,0.04);
    }

    /* KPI Strip - clean metrics row */
    .conv-kpi-strip {
        display: flex;
        gap: 8px;
        margin-bottom: 20px;
        padding-bottom: 16px;
        border-bottom: 1px solid rgba(255,255,255,0.06);
    }
    .conv-kpi {
        display: flex;
        flex-direction: column;
        gap: 2px;
        padding: 10px 16px;
        background: rgba(255,255,255,0.03);
        border-radius: 8px;
        min-width: 0;
    }
    .conv-kpi.primary {
        background: rgba(255,255,255,0.05);
        flex: 1.2;
    }
    .conv-kpi.secondary {
        flex: 0.8;
    }
    .conv-kpi-lbl {
        font-size: 0.65rem;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.3px;
        white-space: nowrap;
    }
    .conv-kpi-val {
        font-size: 0.95rem;
        color: var(--text);
        font-weight: 600;
        white-space: nowrap;
    }
    .conv-kpi-val.accent {
        color: #7AA2FF;
    }

    /* Chart Card - contained, polished */
    .conv-chart-card {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.04);
        border-radius: 10px;
        padding: 16px 20px 12px 20px;
        margin-bottom: -8px;
    }
    .conv-chart-header {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        margin-bottom: 0;
    }
    .conv-chart-title {
        font-size: 0.7rem;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .conv-chart-subtitle {
        font-size: 0.7rem;
        color: var(--muted);
        opacity: 0.7;
    }

    /* ===== SLIDER - Two-Tone Blue ===== */
    /* Remove overlay on container */
    [data-testid="stSlider"] {
        background: transparent !important;
        box-shadow: none !important;
    }
    /* Hide the value label above thumb */
    [data-testid="stSlider"] [data-testid="stThumbValue"],
    [data-testid="stSlider"] [class*="ThumbValue"],
    [data-testid="stSlider"] [class*="thumbValue"] {
        display: none !important;
    }
    /* Slider thumb - accent blue */
    [data-testid="stSlider"] [role="slider"] {
        background-color: #7AA2FF !important;
        border-color: #7AA2FF !important;
        box-shadow: none !important;
    }
    /* Track base (deselected portion) - lighter blue */
    [data-testid="stSlider"] [data-baseweb="slider"] > div > div {
        background: rgba(122, 162, 255, 0.3) !important;
        box-shadow: none !important;
    }
    /* Inner track (selected portion) - full blue - catch all nested divs */
    [data-testid="stSlider"] [data-baseweb="slider"] > div > div > div,
    [data-testid="stSlider"] [data-baseweb="slider"] > div > div > div:first-child,
    [data-testid="stSlider"] [data-baseweb="slider"] div[style*="background"] {
        background: #7AA2FF !important;
        background-color: #7AA2FF !important;
    }

    /* Button overrides for toolbar */
    .conv-toolbar [data-testid="stButton"] button {
        padding: 4px 10px !important;
        font-size: 0.75rem !important;
        min-height: 28px !important;
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 6px !important;
    }
    .conv-toolbar [data-testid="stButton"] button:hover {
        background: rgba(255,255,255,0.08) !important;
        border-color: rgba(255,255,255,0.12) !important;
    }

    /* Expander styling for conviction page */
    .conv-wrap [data-testid="stExpander"] {
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 8px !important;
        background: rgba(255,255,255,0.01) !important;
        margin-top: 20px;
    }
    .conv-wrap [data-testid="stExpander"] summary {
        font-size: 0.8rem !important;
        color: var(--muted) !important;
        padding: 12px 16px !important;
    }
    .conv-wrap [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
        padding: 0 16px 16px 16px !important;
    }

    /* ===== TURNOVER PAGE - Snapshot-style ===== */
    .turn-wrap {
        max-width: 1280px;
        margin: 0;
        padding: 0;
    }
    .turn-hero {
        margin-bottom: 20px;
        padding-bottom: 16px;
        border-bottom: 1px solid rgba(255,255,255,0.06);
    }
    .turn-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--text);
        margin-bottom: 4px;
        letter-spacing: -0.5px;
    }
    .turn-subtitle {
        font-size: 0.85rem;
        color: var(--muted);
    }
    /* KPI Chips - matching Snapshot */
    .turn-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 20px;
    }
    .turn-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 10px 16px;
        background: rgba(255,255,255,0.03);
        border-radius: 8px;
        border: 1px solid rgba(255,255,255,0.04);
    }
    .turn-chip-lbl {
        color: var(--muted);
        font-size: 0.7rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }
    .turn-chip-val {
        color: var(--text);
        font-weight: 600;
        font-size: 0.95rem;
    }
    /* Chart Card */
    .turn-chart-card {
        background: rgba(255,255,255,0.015);
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 16px;
    }
    .turn-chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    .turn-chart-title {
        font-size: 0.7rem;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
    }
    .turn-chart-date {
        font-size: 0.7rem;
        color: var(--muted);
        opacity: 0.7;
    }
    /* Timeframe Pills */
    .turn-tf-bar {
        display: flex;
        gap: 4px;
        margin-bottom: 16px;
    }
    .turn-tf-btn {
        padding: 5px 12px;
        font-size: 0.75rem;
        font-weight: 500;
        color: var(--muted);
        background: transparent;
        border: 1px solid transparent;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.15s ease;
    }
    .turn-tf-btn:hover {
        color: var(--text);
        background: rgba(255,255,255,0.04);
    }
    .turn-tf-btn.active {
        color: var(--text);
        background: rgba(255,255,255,0.08);
        border-color: rgba(255,255,255,0.1);
    }
    /* Hide default Streamlit radio styling for turnover page */
    .turn-wrap [data-testid="stRadio"] > label {
        display: none !important;
    }
    .turn-wrap [data-testid="stRadio"] > div {
        gap: 4px !important;
    }
    .turn-wrap [data-testid="stRadio"] [role="radiogroup"] {
        gap: 4px !important;
    }
    .turn-wrap [data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {
        font-size: 0.75rem !important;
        padding: 5px 12px !important;
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


@st.cache_data(ttl=300)  # Cache for 5 minutes for fresher data
def get_daily_changes_batch(tickers: tuple[str, ...]) -> dict[str, float]:
    """Fetch daily % change for multiple tickers using batch download."""
    changes = {t: 0.0 for t in tickers}  # Default all to 0
    try:
        # Use 1-minute interval for last 2 days to get current price vs previous close
        data = yf.download(
            list(tickers),
            period="2d",
            interval="1m",
            progress=False,
            threads=True,
            group_by="ticker",
            prepost=False
        )

        for ticker in tickers:
            try:
                if len(tickers) == 1:
                    hist = data["Close"]
                else:
                    hist = data[ticker]["Close"]

                hist = hist.dropna()
                if len(hist) >= 2:
                    # Get current price (last data point)
                    curr = hist.iloc[-1]
                    # Get previous day's close (first data point of today or last of yesterday)
                    # Find where today starts
                    today = hist.index[-1].date()
                    yesterday_data = hist[hist.index.date < today]
                    if len(yesterday_data) > 0:
                        prev = yesterday_data.iloc[-1]  # Previous day's close
                    else:
                        prev = hist.iloc[0]  # Fallback to earliest available
                    changes[ticker] = ((curr - prev) / prev * 100) if prev else 0
            except Exception:
                pass  # Keep default 0
    except Exception:
        # Rate limited or other error - return zeros (cached data will be used next time)
        st.warning("Price data temporarily unavailable. Showing cached or default values.")
    return changes


@st.cache_data(ttl=600)  # Cache for 10 minutes to avoid rate limits
def get_ticker_info_cached(ticker: str) -> dict:
    """Fetch ticker info with caching. Raises exception on failure (won't be cached)."""
    ticker_obj = yf.Ticker(ticker)
    info = ticker_obj.info
    # Validate we got real data (not empty or error response)
    if not info or "regularMarketPrice" not in info:
        raise ValueError("Invalid ticker info response")
    return info


def get_ticker_info(ticker: str) -> dict:
    """Wrapper that handles errors gracefully."""
    try:
        return get_ticker_info_cached(ticker)
    except Exception:
        return {}


@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_ticker_calendar_cached(ticker: str) -> dict:
    """Fetch ticker calendar. Raises exception on failure (won't be cached)."""
    ticker_obj = yf.Ticker(ticker)
    calendar = ticker_obj.calendar
    if calendar is None:
        raise ValueError("No calendar data")
    return calendar


def get_ticker_calendar(ticker: str) -> dict | None:
    """Wrapper that handles errors gracefully."""
    try:
        return get_ticker_calendar_cached(ticker)
    except Exception:
        return None


@st.cache_data(ttl=300)  # Cache for 5 minutes for fresher data
def get_ticker_price_data_cached(ticker: str) -> dict:
    """Fetch ticker price using intraday data for live prices."""
    ticker_obj = yf.Ticker(ticker)
    # Use 1-minute interval to get current price
    hist = ticker_obj.history(period="2d", interval="1m", prepost=False)
    if hist.empty or "Close" not in hist.columns:
        raise ValueError("No price data")

    hist = hist.dropna(subset=["Close"])
    if len(hist) < 2:
        raise ValueError("Insufficient price data")

    # Current price is the last available data point
    live_price = hist["Close"].iloc[-1]

    # Get previous day's close
    today = hist.index[-1].date()
    yesterday_data = hist[hist.index.date < today]
    if len(yesterday_data) > 0:
        prev_close = yesterday_data["Close"].iloc[-1]
    else:
        prev_close = hist["Close"].iloc[0]  # Fallback

    pct_change = ((live_price - prev_close) / prev_close * 100) if prev_close else 0
    return {"price": live_price, "pct_change": pct_change, "valid": True}


def get_ticker_price_data(ticker: str) -> dict:
    """Wrapper that handles errors gracefully."""
    try:
        return get_ticker_price_data_cached(ticker)
    except Exception:
        return {"price": None, "pct_change": 0.0, "valid": False}


@st.cache_data(ttl=600)  # Cache for 10 minutes
def _get_ticker_news_cached(ticker: str) -> list:
    """Fetch ticker news from yfinance. Raises on failure so empty results aren't cached."""
    t = yf.Ticker(ticker)
    news = t.news
    if news and isinstance(news, list) and len(news) > 0:
        return news
    raise ValueError("No news available")


def get_ticker_news(ticker: str) -> list:
    """Wrapper that handles errors gracefully."""
    try:
        return _get_ticker_news_cached(ticker)
    except Exception:
        return []


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
# Global Helper Formatters
# -----------------------------
def fmt_big(val):
    """Format large numbers with T/B/M suffix"""
    if val is None: return None
    if val >= 1e12: return f"${val/1e12:,.1f}T"
    if val >= 1e9: return f"${val/1e9:,.1f}B"
    if val >= 1e6: return f"${val/1e6:,.1f}M"
    return f"${val:,.0f}"

def fmt_vol(val):
    """Format volume with B/M/K suffix"""
    if val is None: return None
    if val >= 1e9: return f"{val/1e9:,.1f}B"
    if val >= 1e6: return f"{val/1e6:,.1f}M"
    if val >= 1e3: return f"{val/1e3:,.0f}K"
    return f"{val:,.0f}"

def fmt_pct(val):
    """Format percentage"""
    if val is None: return None
    return f"{val:.2f}%"

def fmt_price(val):
    """Format price with dollar sign"""
    if val is None: return None
    return f"${val:,.2f}"

def fmt_ratio(val):
    """Format ratio to 2 decimals"""
    if val is None: return None
    return f"{val:.2f}"


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

# Ticker section header
st.sidebar.markdown('<div class="sidebar-section-header">Ticker</div>', unsafe_allow_html=True)

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

# Views section
st.sidebar.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="sidebar-section-header">Views</div>', unsafe_allow_html=True)

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

# Dynamic title based on view/ticker (Snapshot, BUZZ Performance, and Conviction Ranking have hero headers)
if st.session_state.view_mode_state == "All Holdings":
    st.title("All Holdings")
elif st.session_state.view_mode_state == "Monthly Turnover":
    pass  # Hero header rendered in turnover section
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
    # ===== FETCH DATA =====
    buzz_info = get_ticker_info("BUZZ")
    buzz_price_data = get_ticker_price_data("BUZZ")

    # Get total net assets from CSV holdings sum
    total_assets = df["MarketValueUSD"].sum() if "MarketValueUSD" in df.columns else 0

    # Get current price and daily change
    current_price = buzz_price_data.get("price") if buzz_price_data.get("valid") else None
    daily_pct_change = buzz_price_data.get("pct_change", 0) or 0
    prev_close = current_price / (1 + daily_pct_change / 100) if current_price and daily_pct_change != 0 else current_price
    daily_change_abs = current_price - prev_close if current_price and prev_close else 0

    # ===== BUILD HERO (matches Stock Detail style) =====
    change_cls = "up" if daily_pct_change >= 0 else "down"
    sign = "+" if daily_pct_change >= 0 else ""
    price_str = f"${current_price:,.2f}" if current_price else "—"
    change_str = f"{sign}{daily_pct_change:.2f}%"
    if daily_change_abs:
        change_str += f" ({sign}${abs(daily_change_abs):.2f})"

    # Chips data for BUZZ
    chips = []
    if total_assets > 0:
        chips.append(("Total Assets", fmt_big(total_assets)))
    expense = buzz_info.get("annualReportExpenseRatio") or buzz_info.get("expenseRatio")
    if expense:
        chips.append(("Expense", f"{expense*100:.2f}%"))
    w_lo, w_hi = buzz_info.get("fiftyTwoWeekLow"), buzz_info.get("fiftyTwoWeekHigh")
    if w_lo and w_hi:
        chips.append(("52W", f"${w_lo:.0f}–${w_hi:.0f}"))
    vol = fmt_vol(buzz_info.get("volume"))
    if vol:
        chips.append(("Vol", vol))

    chips_html = "".join([
        f'<span class="snap-chip"><span class="snap-chip-lbl">{lbl}</span><span class="snap-chip-val">{val}</span></span>'
        for lbl, val in chips
    ])

    # Render hero
    st.markdown(f'''
        <div class="snap-wrap">
            <div class="snap-hero">
                <div class="snap-hero-top">
                    <span class="snap-ticker">BUZZ</span>
                    <span class="snap-company">VanEck Social Sentiment ETF</span>
                </div>
                <div class="snap-price-row">
                    <span class="snap-price">{price_str}</span>
                    <span class="snap-change {change_cls}">{change_str}</span>
                </div>
                <div class="snap-chips">{chips_html}</div>
            </div>
        </div>
    ''', unsafe_allow_html=True)

    # ===== TIMEFRAME CONFIG =====
    tf_map = {
        "1D": ("1d", "5m"), "5D": ("5d", "30m"), "1M": ("1mo", "1h"),
        "6M": ("6mo", "1d"), "1Y": ("1y", "1d"), "ALL": ("max", "1d"),
    }
    tf_opts = list(tf_map.keys())

    tf_key = "buzz_tf"
    if tf_key not in st.session_state:
        st.session_state[tf_key] = "1M"

    # ===== CHART TOOLBAR (timeframe + S&P 500 toggle) =====
    toolbar_col1, toolbar_col2 = st.columns([3, 1])

    with toolbar_col1:
        selected_tf = st.radio(
            "tf", tf_opts, horizontal=True,
            index=tf_opts.index(st.session_state[tf_key]),
            key="buzz_tf_radio",
            label_visibility="collapsed"
        )
        st.session_state[tf_key] = selected_tf

    with toolbar_col2:
        compare_sp500 = st.checkbox("vs S&P 500", key='buzz_compare_sp500', label_visibility="visible")

    # ===== FETCH CHART DATA =====
    @st.cache_data(ttl=300)
    def fetch_buzz_chart(period, interval, include_sp500):
        t_buzz = yf.Ticker("BUZZ")
        hist = t_buzz.history(period=period, interval=interval)
        if include_sp500:
            t_sp = yf.Ticker("^GSPC")
            sp_hist = t_sp.history(period=period, interval=interval)
            hist["SP500"] = sp_hist["Close"]
        return hist

    period, interval = tf_map[selected_tf]
    try:
        hist = fetch_buzz_chart(period, interval, compare_sp500)
    except:
        hist = pd.DataFrame()

    if hist.empty or "Close" not in hist.columns:
        st.warning("No historical data available for BUZZ.")
        st.stop()

    # Calculate period metrics
    start_price = hist["Close"].iloc[0]
    end_price = hist["Close"].iloc[-1]
    period_change = end_price - start_price
    period_pct = (period_change / start_price * 100) if start_price else 0

    # Normalize for comparison mode
    if compare_sp500 and "SP500" in hist.columns:
        hist["BUZZ_Idx"] = (hist["Close"] / hist["Close"].iloc[0]) * 100
        hist["SP500_Idx"] = (hist["SP500"] / hist["SP500"].iloc[0]) * 100

    # ===== RENDER CHART (matching Stock Detail style) =====
    import plotly.graph_objects as go

    if not hist.empty and "Close" in hist.columns:
        fig = go.Figure()

        if compare_sp500 and "SP500_Idx" in hist.columns:
            # Indexed comparison mode
            fig.add_trace(go.Scatter(
                x=hist.index, y=hist["BUZZ_Idx"],
                mode="lines", line=dict(color="#60a5fa", width=2),
                name="BUZZ",
                hovertemplate="BUZZ: %{y:.1f}<extra></extra>"
            ))
            fig.add_trace(go.Scatter(
                x=hist.index, y=hist["SP500_Idx"],
                mode="lines", line=dict(color="#a78bfa", width=2),
                name="S&P 500",
                hovertemplate="S&P 500: %{y:.1f}<extra></extra>"
            ))
        else:
            # Standard price mode (matching stock page style)
            fig.add_trace(go.Scatter(
                x=hist.index, y=hist["Close"],
                mode="lines",
                line=dict(color="#60a5fa", width=2),
                fill="tozeroy",
                fillcolor="rgba(96,165,250,0.08)",
                hovertemplate="%{x|%b %d, %Y}<br>$%{y:.2f}<extra></extra>"
            ))

        fig.update_layout(
            height=480,
            margin=dict(l=0, r=0, t=8, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, showline=False, zeroline=False,
                       tickfont=dict(color="#6b7a8a", size=10)),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)",
                       showline=False, zeroline=False,
                       tickfont=dict(color="#6b7a8a", size=10),
                       tickprefix="" if compare_sp500 else "$"),
            hovermode="x unified",
            showlegend=compare_sp500,
            legend=dict(
                yanchor="top", y=0.99, xanchor="left", x=0.01,
                bgcolor="rgba(0,0,0,0.5)", font=dict(size=11)
            ) if compare_sp500 else None,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "staticPlot": True})

        # ===== PERIOD METRICS STRIP (matching Stock Detail style) =====
        if selected_tf == "1D":
            strip_header = "Today"
            stats = [
                ("Open", fmt_price(buzz_info.get("open") or buzz_info.get("regularMarketOpen"))),
                ("High", fmt_price(buzz_info.get("dayHigh") or buzz_info.get("regularMarketDayHigh"))),
                ("Low", fmt_price(buzz_info.get("dayLow") or buzz_info.get("regularMarketDayLow"))),
                ("Prev Close", fmt_price(buzz_info.get("previousClose") or buzz_info.get("regularMarketPreviousClose"))),
                ("Volume", fmt_vol(buzz_info.get("volume"))),
            ]
        else:
            strip_header = f"Period ({selected_tf})"
            period_high = hist["High"].max() if "High" in hist.columns else hist["Close"].max()
            period_low = hist["Low"].min() if "Low" in hist.columns else hist["Close"].min()
            avg_vol = None
            if "Volume" in hist.columns:
                daily_vol = hist["Volume"].groupby(hist.index.date).sum()
                avg_vol = daily_vol.mean() if len(daily_vol) > 0 else None
            stats = [
                ("Period High", fmt_price(period_high)),
                ("Period Low", fmt_price(period_low)),
                ("Return", f"{period_pct:+.2f}%"),
                ("Avg Daily Vol", fmt_vol(avg_vol)),
            ]

        stats_html = "".join([
            f'<div class="snap-ohlc-item"><span class="snap-ohlc-lbl">{lbl}</span><span class="snap-ohlc-val">{val or "—"}</span></div>'
            for lbl, val in stats
        ])
        st.markdown(f'''
            <div class="snap-stats-strip">
                <div class="snap-stats-hdr">{strip_header}</div>
                <div class="snap-ohlc">{stats_html}</div>
            </div>
        ''', unsafe_allow_html=True)
    else:
        st.caption("Chart data unavailable")

    # ===== NEWS SECTION (matching Stock Detail style) =====
    news_data = []
    try:
        t = yf.Ticker("BUZZ")
        if hasattr(t, 'news'):
            raw_news = t.news
            if isinstance(raw_news, list):
                news_data = raw_news
            elif isinstance(raw_news, dict) and 'news' in raw_news:
                news_data = raw_news.get('news', [])
    except:
        news_data = []

    news_items_html = ""
    if news_data and len(news_data) > 0:
        for item in news_data[:5]:
            if not isinstance(item, dict):
                continue
            content = item.get("content", item)
            title = content.get("title") or ""
            link = "#"
            if content.get("canonicalUrl"):
                link = content["canonicalUrl"].get("url", "#") if isinstance(content["canonicalUrl"], dict) else content["canonicalUrl"]
            provider = content.get("provider", {})
            publisher = provider.get("displayName") or provider.get("name") or "" if isinstance(provider, dict) else ""
            pub_date = content.get("pubDate") or ""
            if not title:
                continue
            time_ago = ""
            if pub_date:
                try:
                    from datetime import datetime, timezone
                    dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                    now = datetime.now(timezone.utc)
                    delta = now - dt
                    if delta.days > 0:
                        time_ago = f"{delta.days}d ago"
                    elif delta.seconds // 3600 > 0:
                        time_ago = f"{delta.seconds // 3600}h ago"
                    else:
                        time_ago = f"{max(1, delta.seconds // 60)}m ago"
                except:
                    pass
            meta = f"{publisher} · {time_ago}" if publisher and time_ago else publisher or time_ago or ""
            news_items_html += f'''
                <div class="snap-news-item">
                    <div class="snap-news-title"><a href="{link}" target="_blank">{title}</a></div>
                    <div class="snap-news-meta">{meta}</div>
                </div>'''

    if not news_items_html:
        news_items_html = '<div class="snap-news-empty">No recent news available.</div>'

    st.markdown(f'''
        <div class="snap-news-section">
            <div class="snap-news-hdr">Recent News</div>
            <div class="snap-news-list">{news_items_html}</div>
        </div>
    ''', unsafe_allow_html=True)

    st.stop()

# Conviction Ranking view
if st.session_state.view_mode_state == "Conviction Ranking":

    try:
        # Load dominance history data
        leaders_df = load_dominance_history()

        if not leaders_df.empty:
            # Create list of unique dates for slider
            unique_dates = sorted(leaders_df["date"].dropna().unique())
            date_labels = [d.strftime("%b %Y") for d in unique_dates]

            # Initialize session state for slider index
            if "dominance_idx" not in st.session_state:
                st.session_state.dominance_idx = len(date_labels) - 1

            # Clamp index to valid range
            st.session_state.dominance_idx = max(0, min(st.session_state.dominance_idx, len(date_labels) - 1))

            # ===== HERO HEADER =====
            st.markdown(f'''
                <div class="conv-wrap">
                    <div class="conv-hero">
                        <div class="conv-title">Most Dominant Stocks</div>
                        <div class="conv-subtitle">Historical #1 sentiment rankings by month</div>
                        <div class="conv-viewing">Viewing: {date_labels[st.session_state.dominance_idx]}</div>
                    </div>
                </div>
            ''', unsafe_allow_html=True)

            # ===== TOOLBAR NAVIGATION =====
            col_prev, col_slider, col_next = st.columns([0.5, 9, 0.5])

            with col_prev:
                if st.button("◀", key="prev_month", use_container_width=True):
                    if st.session_state.dominance_idx > 0:
                        st.session_state.dominance_idx -= 1
                        st.rerun()

            with col_slider:
                selected_idx = st.slider(
                    "Select Month",
                    min_value=0,
                    max_value=len(date_labels) - 1,
                    value=st.session_state.dominance_idx,
                    format=" ",
                    label_visibility="collapsed",
                )
                if selected_idx != st.session_state.dominance_idx:
                    st.session_state.dominance_idx = selected_idx
                    st.rerun()

            with col_next:
                if st.button("▶", key="next_month", use_container_width=True):
                    if st.session_state.dominance_idx < len(date_labels) - 1:
                        st.session_state.dominance_idx += 1
                        st.rerun()

            # Get data for selected date
            selected_idx = st.session_state.dominance_idx
            selected_date = unique_dates[selected_idx]
            current_month_leader = leaders_df[leaders_df["date"] == selected_date]["leader"].iloc[0] if not leaders_df[leaders_df["date"] == selected_date].empty else "N/A"
            top_data = get_cumulative_dominance(leaders_df, selected_date, top_n=15)

            if not top_data.empty:
                # Calculate stats
                current_leader = top_data.iloc[0]["ticker"]
                current_count = top_data.iloc[0]["months_at_top"]
                total_unique = len(leaders_df[leaders_df["date"] <= selected_date]["leader"].unique())
                total_periods = len(leaders_df[leaders_df["date"] <= selected_date])

                # ===== KPI STRIP =====
                kpi_html = f'''
                <div class="conv-kpi-strip">
                    <div class="conv-kpi primary">
                        <span class="conv-kpi-lbl">#1 in {date_labels[selected_idx]}</span>
                        <span class="conv-kpi-val accent">{current_month_leader}</span>
                    </div>
                    <div class="conv-kpi primary">
                        <span class="conv-kpi-lbl">Cumulative Leader</span>
                        <span class="conv-kpi-val accent">{current_leader} <span style="opacity:0.6;font-weight:400;">({current_count}mo)</span></span>
                    </div>
                    <div class="conv-kpi secondary">
                        <span class="conv-kpi-lbl">Unique #1s</span>
                        <span class="conv-kpi-val">{total_unique}</span>
                    </div>
                    <div class="conv-kpi secondary">
                        <span class="conv-kpi-lbl">Months Tracked</span>
                        <span class="conv-kpi-val">{total_periods}</span>
                    </div>
                </div>
                '''
                st.markdown(kpi_html, unsafe_allow_html=True)

                # ===== CHART SECTION =====
                # Reverse for horizontal bar chart (top at top)
                top_data = top_data.iloc[::-1].reset_index(drop=True)

                # Color gradient - opacity-based for cleaner look
                def get_bar_color(rank, total):
                    # Base blue #60a5fa, fade opacity for lower ranks
                    opacity = 1.0 - (rank - 1) / max(total - 1, 1) * 0.5
                    return f"rgba(96, 165, 250, {opacity})"

                colors = [get_bar_color(r, 15) for r in top_data["rank"]]

                import plotly.graph_objects as go
                fig_race = go.Figure(go.Bar(
                    x=top_data["months_at_top"],
                    y=top_data["ticker"],
                    orientation="h",
                    marker=dict(
                        color=colors,
                        line=dict(width=0),
                        cornerradius=3,
                    ),
                    text=top_data["months_at_top"],
                    textposition="outside",
                    textfont=dict(color="#94a3b8", size=12),
                    hovertemplate="<b>%{y}</b><br>Months at #1: %{x}<extra></extra>",
                ))

                max_months = top_data["months_at_top"].max()
                x_max = max(max_months * 1.12, 5)

                fig_race.update_layout(
                    height=480,
                    margin=dict(t=4, l=70, r=40, b=36),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="white"),
                    dragmode=False,
                    xaxis=dict(
                        title=dict(text="Months at #1", font=dict(color="#64748b", size=11)),
                        tickfont=dict(color="#64748b", size=10),
                        gridcolor="rgba(255,255,255,0.03)",
                        range=[0, x_max],
                        showline=False,
                        dtick=max(1, max_months // 5),
                        tickmode="linear",
                        fixedrange=True,
                    ),
                    yaxis=dict(
                        title="",
                        tickfont=dict(color="#e2e8f0", size=11),
                        gridcolor="rgba(255,255,255,0.02)",
                        showline=False,
                        fixedrange=True,
                    ),
                    bargap=0.3,
                )

                # Render in card container with header
                st.markdown(f'''
                <div class="conv-chart-card">
                    <div class="conv-chart-header">
                        <span class="conv-chart-title">All-Time #1 Months</span>
                        <span class="conv-chart-subtitle">as of {date_labels[selected_idx]}</span>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
                st.plotly_chart(fig_race, use_container_width=True, config={"displayModeBar": False, "staticPlot": True})

                # ===== EXPLANATION (collapsible) =====
                with st.expander("About this chart", expanded=False):
                    st.markdown('''
**How to read this chart:**
- Each bar shows how many months a stock has held the **#1 position** in the BUZZ Index
- **Brighter bars** = higher cumulative months | **Fainter bars** = fewer months
- Use the slider to see how rankings evolved over time

**Metrics explained:**
- **#1 in [Month]** — The stock with the highest sentiment score that month
- **Cumulative Leader** — Most total months at #1 up to selected date
- **Unique #1s** — Different stocks that have ever reached #1
- **Months Tracked** — Total monthly rebalances covered
                    ''')

    except Exception as e:
        st.warning(f"Could not load dominance history: {e}")

    st.stop()

# Monthly Turnover view
if st.session_state.view_mode_state == "Monthly Turnover":

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
        latest_date = turnover_df['Rebalance_date'].max().strftime('%b %Y')

        # ===== HERO HEADER =====
        st.markdown(f'''
            <div class="turn-wrap">
                <div class="turn-hero">
                    <div class="turn-title">Portfolio Turnover</div>
                    <div class="turn-subtitle">Monthly rebalancing activity for the BUZZ Index</div>
                </div>
            </div>
        ''', unsafe_allow_html=True)

        # ===== KPI CHIPS =====
        st.markdown(f'''
            <div class="turn-wrap">
                <div class="turn-chips">
                    <div class="turn-chip">
                        <span class="turn-chip-lbl">Historical Avg</span>
                        <span class="turn-chip-val">{avg_turnover:.2f}%</span>
                    </div>
                    <div class="turn-chip">
                        <span class="turn-chip-lbl">Period Avg ({timeframe})</span>
                        <span class="turn-chip-val">{period_avg:.2f}%</span>
                    </div>
                    <div class="turn-chip">
                        <span class="turn-chip-lbl">Min</span>
                        <span class="turn-chip-val">{min_turnover:.2f}%</span>
                    </div>
                    <div class="turn-chip">
                        <span class="turn-chip-lbl">Max</span>
                        <span class="turn-chip-val">{max_turnover:.2f}%</span>
                    </div>
                </div>
            </div>
        ''', unsafe_allow_html=True)

        # ===== TIMEFRAME SELECTOR =====
        st.markdown('<div class="turn-wrap">', unsafe_allow_html=True)
        st.radio("Timeframe", ["6M", "1Y", "YTD", "3Y", "5Y", "ALL"], index=5, horizontal=True, key='turnover_timeframe', label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)


        # Create line chart using plotly
        try:
            import plotly.graph_objects as go

            fig = go.Figure()

            # Add main turnover line - BLUE to match Snapshot
            fig.add_trace(
                go.Scatter(
                    x=turnover_df['Rebalance_date'],
                    y=turnover_df['Monthly_Turnover_Rate_Percent'],
                    mode='lines',
                    line=dict(color='#7AA2FF', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(122,162,255,0.08)',
                    name='Monthly Turnover',
                    hovertemplate="<b>%{x|%b %Y}</b><br>" +
                                  "Turnover: %{y:.2f}%<br>" +
                                  "<extra></extra>",
                )
            )

            # Add average line - muted gray-blue to match Snapshot
            fig.add_hline(
                y=avg_turnover,
                line_dash="dash",
                line_color="rgba(159,178,204,0.5)",
                line_width=1.5,
                annotation_text=f"Avg ({avg_turnover}%)",
                annotation_position="right",
                annotation_font_size=10,
                annotation_font_color="rgba(159,178,204,0.7)",
            )

            # Update layout - Snapshot style
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#9fb2cc", size=10),
                height=400,
                xaxis=dict(
                    showgrid=True,
                    gridcolor="rgba(255,255,255,0.04)",
                    showline=False,
                    tickfont=dict(color="#6b7a8a", size=10),
                    fixedrange=True,
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor="rgba(255,255,255,0.04)",
                    showline=False,
                    tickfont=dict(color="#6b7a8a", size=10),
                    ticksuffix="%",
                    range=[0, max(turnover_df['Monthly_Turnover_Rate_Percent'].max() * 1.1, avg_turnover * 1.2)],
                    fixedrange=True,
                ),
                hovermode='x unified',
                hoverlabel=dict(
                    bgcolor="rgba(0,0,0,0.8)",
                    bordercolor="rgba(122,162,255,0.5)",
                    font=dict(color="white", size=11),
                ),
                margin=dict(l=0, r=0, t=0, b=0),
                showlegend=False,
            )

            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "staticPlot": True})

            # ===== ABOUT SECTION - Accordion style =====
            with st.expander("About This Chart", expanded=False):
                st.markdown("""
**What is Portfolio Turnover?**

Measures the percentage of the portfolio that changes each month. Calculated as: (Sum of Absolute Weight Changes) ÷ 2. Higher values indicate more active rebalancing.

**Interpreting the Chart:**
- **Above Average Line** — More aggressive month with higher portfolio changes
- **Below Average Line** — More stable month with fewer portfolio adjustments
- **Spikes** — Major market events or significant sentiment shifts
- **Stable Periods** — Consistent market sentiment and holdings
                """)

        except Exception as e:
            st.line_chart(turnover_df.set_index('Rebalance_date')['Monthly_Turnover_Rate_Percent'])
            st.error(f"Note: Using simplified chart. Error: {e}")

    except FileNotFoundError:
        st.error("BUZZ_Monthly_Turnover_Time_Series.csv not found.")
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


def render_snapshot_page(ticker: str, df: pd.DataFrame, desc_map: dict):
    """
    Render the redesigned snapshot page - v2 with all layout/UX fixes.
    Clean hierarchy, no duplicate headers, tight spacing, aligned grid.
    """
    import plotly.graph_objects as go
    from datetime import datetime

    # ===== HELPER FORMATTERS =====
    def fmt_big(val):
        if val is None: return None
        if val >= 1e12: return f"${val/1e12:,.1f}T"
        if val >= 1e9: return f"${val/1e9:,.1f}B"
        if val >= 1e6: return f"${val/1e6:,.1f}M"
        return f"${val:,.0f}"

    def fmt_vol(val):
        if val is None: return None
        if val >= 1e9: return f"{val/1e9:,.1f}B"
        if val >= 1e6: return f"{val/1e6:,.1f}M"
        if val >= 1e3: return f"{val/1e3:,.0f}K"
        return f"{val:,.0f}"

    def fmt_pct(val):
        if val is None: return None
        return f"{val:.2f}%"

    def fmt_price(val):
        if val is None: return None
        return f"${val:,.2f}"

    def fmt_ratio(val):
        if val is None or val < 0 or val > 1000: return None
        return f"{val:.2f}"

    def fmt_time_ago(ts):
        if not ts: return ""
        try:
            dt = datetime.fromtimestamp(ts)
            delta = datetime.now() - dt
            if delta.days > 0: return f"{delta.days}d ago"
            if delta.seconds // 3600 > 0: return f"{delta.seconds // 3600}h ago"
            return f"{max(1, delta.seconds // 60)}m ago"
        except: return ""

    # ===== FETCH DATA =====
    info = get_ticker_info(ticker)
    price_data = get_ticker_price_data(ticker)

    company_name = info.get("shortName") or info.get("longName") or ""
    current_price = price_data.get("price") if price_data.get("valid") else None
    pct_change = price_data.get("pct_change", 0) or 0

    price_change_abs = None
    if current_price and pct_change:
        price_change_abs = current_price - (current_price / (1 + pct_change / 100))

    # ===== BUILD HERO =====
    change_cls = "up" if pct_change >= 0 else "down"
    sign = "+" if pct_change >= 0 else ""
    price_str = fmt_price(current_price) or "—"
    change_str = f"{sign}{pct_change:.2f}%"
    if price_change_abs is not None:
        change_str += f" ({sign}${abs(price_change_abs):.2f})"

    # Chips data
    chips = []
    mkt_cap = fmt_big(info.get("marketCap"))
    if mkt_cap: chips.append(("Mkt Cap", mkt_cap))
    w_lo, w_hi = info.get("fiftyTwoWeekLow"), info.get("fiftyTwoWeekHigh")
    if w_lo and w_hi: chips.append(("52W", f"${w_lo:.0f}–${w_hi:.0f}"))
    vol = fmt_vol(info.get("volume"))
    if vol: chips.append(("Vol", vol))
    # Relative volume (current volume / average volume)
    cur_vol, avg_vol = info.get("volume"), info.get("averageVolume")
    if cur_vol and avg_vol and avg_vol > 0:
        rel_vol = cur_vol / avg_vol
        chips.append(("Rel Vol", f"{rel_vol:.2f}x"))

    chips_html = "".join([
        f'<span class="snap-chip"><span class="snap-chip-lbl">{lbl}</span><span class="snap-chip-val">{val}</span></span>'
        for lbl, val in chips
    ])

    # Render hero
    st.markdown(f'''
        <div class="snap-wrap">
            <div class="snap-hero">
                <div class="snap-hero-top">
                    <span class="snap-ticker">{ticker}</span>
                    <span class="snap-company">{company_name}</span>
                </div>
                <div class="snap-price-row">
                    <span class="snap-price">{price_str}</span>
                    <span class="snap-change {change_cls}">{change_str}</span>
                </div>
                <div class="snap-chips">{chips_html}</div>
            </div>
        </div>
    ''', unsafe_allow_html=True)

    # ===== TWO-COLUMN GRID =====
    col_chart, col_side = st.columns([7, 3], gap="medium")

    with col_chart:
        # Timeframe config
        tf_map = {
            "1D": ("1d", "5m"), "5D": ("5d", "30m"), "1M": ("1mo", "1h"),
            "6M": ("6mo", "1d"), "1Y": ("1y", "1d"), "ALL": ("max", "1d"),
        }
        tf_opts = list(tf_map.keys())

        tf_key = f"snap_tf_{ticker}"
        if tf_key not in st.session_state:
            st.session_state[tf_key] = "1M"

        # Render timeframe pills using radio with custom styling
        selected_tf = st.radio(
            "tf", tf_opts, horizontal=True,
            index=tf_opts.index(st.session_state[tf_key]),
            key=f"tf_radio_{ticker}",
            label_visibility="collapsed"
        )
        st.session_state[tf_key] = selected_tf

        # Fetch chart data
        @st.cache_data(ttl=300)
        def fetch_chart(tkr, period, interval):
            return yf.Ticker(tkr).history(period=period, interval=interval)

        period, interval = tf_map[selected_tf]
        try:
            hist = fetch_chart(ticker, period, interval)
        except:
            hist = pd.DataFrame()

        if not hist.empty and "Close" in hist.columns:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist.index, y=hist["Close"],
                mode="lines",
                line=dict(color="#60a5fa", width=2),
                fill="tozeroy",
                fillcolor="rgba(96,165,250,0.08)",
                hovertemplate="%{x|%b %d, %Y}<br>$%{y:.2f}<extra></extra>"
            ))
            fig.update_layout(
                height=480,
                margin=dict(l=0, r=0, t=8, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False, showline=False, zeroline=False,
                           tickfont=dict(color="#6b7a8a", size=10)),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)",
                           showline=False, zeroline=False,
                           tickfont=dict(color="#6b7a8a", size=10), tickprefix="$"),
                hovermode="x unified", showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "staticPlot": True})

            # Stats strip - changes based on timeframe
            if selected_tf == "1D":
                # Daily stats from quote data
                strip_header = "Today"
                stats = [
                    ("Open", fmt_price(info.get("open") or info.get("regularMarketOpen"))),
                    ("High", fmt_price(info.get("dayHigh") or info.get("regularMarketDayHigh"))),
                    ("Low", fmt_price(info.get("dayLow") or info.get("regularMarketDayLow"))),
                    ("Prev Close", fmt_price(info.get("previousClose") or info.get("regularMarketPreviousClose"))),
                    ("Volume", fmt_vol(info.get("volume"))),
                ]
            else:
                # Period stats computed from chart data
                strip_header = f"Period ({selected_tf})"

                # Compute period high/low from chart data
                if "High" in hist.columns:
                    period_high = hist["High"].max()
                else:
                    period_high = hist["Close"].max() if "Close" in hist.columns else None

                if "Low" in hist.columns:
                    period_low = hist["Low"].min()
                else:
                    period_low = hist["Close"].min() if "Close" in hist.columns else None

                # Compute average DAILY volume (aggregate intraday bars by day, then average)
                avg_daily_volume = None
                if "Volume" in hist.columns:
                    vol_series = hist["Volume"].dropna()
                    if len(vol_series) > 0:
                        # Group by date and sum volume per day, then take the mean
                        daily_vol = vol_series.groupby(vol_series.index.date).sum()
                        avg_daily_volume = daily_vol.mean() if len(daily_vol) > 0 else None

                # Compute period return
                period_return = None
                if "Close" in hist.columns and len(hist) > 1:
                    first_close = hist["Close"].iloc[0]
                    last_close = hist["Close"].iloc[-1]
                    if first_close and first_close != 0:
                        period_return = ((last_close - first_close) / first_close) * 100

                stats = [
                    ("Period High", fmt_price(period_high)),
                    ("Period Low", fmt_price(period_low)),
                    ("Return", f"{period_return:+.2f}%" if period_return is not None else "—"),
                    ("Avg Daily Vol", fmt_vol(avg_daily_volume)),
                ]

            stats_html = "".join([
                f'<div class="snap-ohlc-item"><span class="snap-ohlc-lbl">{lbl}</span><span class="snap-ohlc-val">{val or "—"}</span></div>'
                for lbl, val in stats
            ])
            st.markdown(f'''
                <div class="snap-stats-strip">
                    <div class="snap-stats-hdr">{strip_header}</div>
                    <div class="snap-ohlc">{stats_html}</div>
                </div>
            ''', unsafe_allow_html=True)
        else:
            st.caption("Chart data unavailable")

    with col_side:
        # Holdings Snapshot
        max_months = get_max_consecutive_months(ticker)
        latest_row = get_latest_ticker_row(df, ticker)

        pct_val, mv_val = None, None
        if latest_row is not None:
            if "PercentNetAssets" in latest_row and pd.notna(latest_row.get("PercentNetAssets")):
                pct_val = float(latest_row["PercentNetAssets"])
            elif "Weight" in latest_row and pd.notna(latest_row.get("Weight")):
                pct_val = float(latest_row["Weight"]) * 100
            if "MarketValueUSD" in latest_row and pd.notna(latest_row.get("MarketValueUSD")):
                mv_val = float(latest_row["MarketValueUSD"])
            elif "MarketValue" in latest_row and pd.notna(latest_row.get("MarketValue")):
                mv_val = float(latest_row["MarketValue"])

        # Get first appearance date
        first_appearance = get_first_appearance_date(ticker)

        # Helper to render a row with proper styling for missing values
        def render_row(lbl, val):
            if val is None or val == "N/A":
                return f'<div class="snap-row"><span class="snap-row-lbl">{lbl}</span><span class="snap-row-val na">—</span></div>'
            return f'<div class="snap-row"><span class="snap-row-lbl">{lbl}</span><span class="snap-row-val">{val}</span></div>'

        holdings = [
            ("Months Held", str(max_months)),
            ("% Net Assets", fmt_pct(pct_val)),
            ("Market Value", fmt_big(mv_val)),
            ("First in BUZZ", first_appearance),
        ]
        holdings_html = "".join([render_row(lbl, val) for lbl, val in holdings])

        st.markdown(f'''
            <div class="snap-card">
                <div class="snap-card-hdr">Holdings Snapshot</div>
                <div class="snap-rows">{holdings_html}</div>
            </div>
        ''', unsafe_allow_html=True)

        # Key Metrics - show all (volume metrics moved to chart strip)
        beta_val = info.get("beta")
        all_metrics = [
            ("Beta", f"{beta_val:.2f}" if beta_val else None),
            ("Trailing P/E", fmt_ratio(info.get("trailingPE"))),
            ("Forward P/E", fmt_ratio(info.get("forwardPE"))),
            ("P/S Ratio", fmt_ratio(info.get("priceToSalesTrailing12Months"))),
            ("P/B Ratio", fmt_ratio(info.get("priceToBook"))),
            ("EPS (TTM)", fmt_price(info.get("trailingEps"))),
            ("Div Yield", fmt_pct(info.get("dividendYield") * 100) if info.get("dividendYield") else None),
        ]

        metrics_html = "".join([render_row(lbl, val) for lbl, val in all_metrics])

        st.markdown(f'''
            <div class="snap-card">
                <div class="snap-card-hdr">Key Metrics</div>
                <div class="snap-rows">{metrics_html}</div>
            </div>
        ''', unsafe_allow_html=True)

        # Description card in sidebar
        desc_text = desc_map.get(ticker, "No description available for this ticker.")
        st.markdown(f'''
            <div class="snap-card">
                <div class="snap-card-hdr">About {ticker}</div>
                <div class="snap-about-txt">{desc_text}</div>
            </div>
        ''', unsafe_allow_html=True)

    # ===== NEWS SECTION (full width, outside columns) =====
    # Fetch news - try multiple yfinance methods
    news_data = []
    try:
        t = yf.Ticker(ticker)
        if hasattr(t, 'news'):
            raw_news = t.news
            if isinstance(raw_news, list):
                news_data = raw_news
            elif isinstance(raw_news, dict) and 'news' in raw_news:
                news_data = raw_news.get('news', [])
            elif isinstance(raw_news, dict):
                news_data = list(raw_news.values()) if raw_news else []
        if not news_data and hasattr(t, 'get_news'):
            news_data = t.get_news() or []
    except Exception:
        news_data = []

    # Build news items HTML
    news_items_html = ""
    if news_data and len(news_data) > 0:
        for item in news_data[:5]:
            if not isinstance(item, dict):
                continue

            content = item.get("content", item)
            title = content.get("title") or ""

            link = "#"
            if content.get("canonicalUrl"):
                link = content["canonicalUrl"].get("url", "#") if isinstance(content["canonicalUrl"], dict) else content["canonicalUrl"]
            elif content.get("clickThroughUrl"):
                link = content["clickThroughUrl"].get("url", "#") if isinstance(content["clickThroughUrl"], dict) else content["clickThroughUrl"]

            provider = content.get("provider", {})
            publisher = provider.get("displayName") or provider.get("name") or "" if isinstance(provider, dict) else ""
            pub_date = content.get("pubDate") or ""

            if not title:
                continue

            time_ago = ""
            if pub_date:
                try:
                    from datetime import datetime, timezone
                    dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                    now = datetime.now(timezone.utc)
                    delta = now - dt
                    if delta.days > 0:
                        time_ago = f"{delta.days}d ago"
                    elif delta.seconds // 3600 > 0:
                        time_ago = f"{delta.seconds // 3600}h ago"
                    else:
                        time_ago = f"{max(1, delta.seconds // 60)}m ago"
                except:
                    pass

            meta = f"{publisher} · {time_ago}" if publisher and time_ago else publisher or time_ago or ""
            news_items_html += f'''
                <div class="snap-news-item">
                    <div class="snap-news-title"><a href="{link}" target="_blank">{title}</a></div>
                    <div class="snap-news-meta">{meta}</div>
                </div>'''

    if not news_items_html:
        news_items_html = '<div class="snap-news-empty">No recent news available.</div>'

    # Render entire news section as single block
    st.markdown(f'''
        <div class="snap-news-section">
            <div class="snap-news-hdr">Recent News</div>
            <div class="snap-news-list">{news_items_html}</div>
        </div>
    ''', unsafe_allow_html=True)


def render_key_metrics(ticker: str):
    """
    Render seven key metrics for the given ticker below the description.
    Uses yfinance.info and calendar; falls back to N/A when data is missing.
    """
    info = get_ticker_info(ticker)  # Uses cached function to avoid rate limits

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

    def fmt_vol(val):
        """Format volume with K/M suffix"""
        if val is None:
            return "N/A"
        if val >= 1e6:
            return f"{val/1e6:,.1f}M"
        if val >= 1e3:
            return f"{val/1e3:,.0f}K"
        return f"{val:,.0f}"

    market_cap = fmt_bil(info.get("marketCap"))
    pe_trailing = fmt_pe(info.get("trailingPE"))
    pe_forward = fmt_pe(info.get("forwardPE"))
    ps_ratio = fmt_ps(info.get("priceToSalesTrailing12Months"))
    beta = fmt_2(info.get("beta"))

    # Volume metrics
    daily_vol_raw = info.get("volume")
    avg_vol_raw = info.get("averageVolume")
    daily_vol = fmt_vol(daily_vol_raw)
    avg_vol = fmt_vol(avg_vol_raw)
    if daily_vol_raw and avg_vol_raw and avg_vol_raw > 0:
        rel_vol = f"{daily_vol_raw / avg_vol_raw:.2f}x"
    else:
        rel_vol = "N/A"

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

        calendar = get_ticker_calendar(ticker)  # Uses cached function to avoid rate limits
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
            <div class="metric-card">
                <div class="metric-label">Daily Volume</div>
                <div class="metric-value">{daily_vol}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Avg Volume</div>
                <div class="metric-value">{avg_vol}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Relative Volume</div>
                <div class="metric-value">{rel_vol}</div>
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

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "staticPlot": True})


def render_news_section(ticker: str):
    """
    Render up to 5 recent news items for the ticker.
    Shows headline (clickable) and publisher/date underneath.
    """
    # Use cached function to avoid rate limits
    news_items = get_ticker_news(ticker)

    if not news_items:
        st.info("No recent news found.")
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
# Render Redesigned Snapshot Page
# -----------------------------
render_snapshot_page(selected_ticker, df, desc_map)


# -----------------------------
# Middle/Bottom sections removed per request; focus only on snapshot above.
