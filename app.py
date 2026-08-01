import streamlit as st
import json
import os
from datetime import datetime, timedelta
import pandas as pd
import pytz
import requests
import base64
from streamlit_autorefresh import st_autorefresh

# --- MONTREAL TIMEZONE ---
MONTREAL_TZ = pytz.timezone('America/Toronto')

# --- FICHIERS (via API GitHub avec token) ---
GITHUB_REPO = "LuckyHT438/northsentinel-data"
GITHUB_PATH_SIGNALS = "core_signals_today.json"
GITHUB_PATH_STATUS = "run_status.json"

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="NorthSentinel CORE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown(
    """
    <style>
        .css-1d391kg, .css-12oz5g7, .css-1v3fvcr, .css-1v0mbdj { font-size: 0.85rem !important; }
        [data-testid="stMetricValue"] { font-size: 0.95rem !important; }
        [data-testid="stMetricLabel"] { font-size: 0.8rem !important; }
        section[data-testid="stSidebar"] [data-testid="stMetricLabel"] { color: #F5A623 !important; }
        .css-1v3fvcr h3 { font-size: 1rem !important; }
        .stButton button {
            font-weight: bold !important;
            background-color: #F5A623 !important;
            color: #0E1117 !important;
            border: none !important;
            border-radius: 4px !important;
            padding: 0.5rem 1rem !important;
            font-size: 1rem !important;
        }
        .stButton button:hover { background-color: #e0951a !important; color: #0E1117 !important; }
        .sidebar-signout button {
            font-weight: bold !important;
            background-color: #F5A623 !important;
            color: #0E1117 !important;
            border: none !important;
            border-radius: 4px !important;
            padding: 0.2rem 0.6rem !important;
            font-size: 0.9rem !important;
            width: auto !important;
        }
        .sidebar-signout button:hover { background-color: #e0951a !important; color: #0E1117 !important; }

        .stDataFrame {
            border: none !important;
        }
        .stDataFrame td, .stDataFrame th {
            border: none !important;
        }
        .stDataFrame th {
            font-weight: bold !important;
        }

        .block-container {
            padding-top: 3rem !important;
            padding-bottom: 0.5rem !important;
        }
        .stMarkdown h3 {
            margin-bottom: 0.25rem !important;
        }
        .stMarkdown hr {
            margin: 0.5rem 0 !important;
        }
        .stDataFrame {
            margin-top: 0.25rem !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# --- AUTHENTIFICATION ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True
    st.title("🔐 Restricted Access")
    password_input = st.text_input("Enter password", type="password")
    if st.button("Sign in"):
        if password_input == st.secrets["password"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")
    return False

if not check_password():
    st.stop()

# --- HEADER ---
col1, col2 = st.columns([1, 5], vertical_alignment="center")
with col1:
    try:
        st.image("assets/logo_northsentinel_core.png", width=120)
    except:
        st.markdown("### 🏔️ NS")
with col2:
    st.markdown(
        """
        <div style="margin-top: -22px;">
            <h1 style='color: #F5A623; margin-bottom: 0;'>NorthSentinel CORE</h1>
            <p style='color: #AAAAAA; margin-top: 0; font-size: 1.2rem;'>Real‑time system monitoring cockpit — Beta</p>
        </div>
        """,
        unsafe_allow_html=True
    )

st.divider()

# --- FONCTIONS DE LECTURE (avec API GitHub) ---
@st.cache_data(ttl=5)
def fetch_signals():
    token = st.secrets.get("GITHUB_TOKEN", "")
    if not token:
        return []
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_PATH_SIGNALS}"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            content = base64.b64decode(data["content"]).decode("utf-8")
            signals = json.loads(content)
            return signals if isinstance(signals, list) else []
        return []
    except:
        return []

@st.cache_data(ttl=1)
def fetch_run_status():
    token = st.secrets.get("GITHUB_TOKEN", "")
    if not token:
        return None
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_PATH_STATUS}"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        r = requests.get(url, headers=headers, timeout=3)
        if r.status_code == 200:
            data = r.json()
            content = base64.b64decode(data["content"]).decode("utf-8")
            return json.loads(content)
        return None
    except:
        return None

# --- AUTO-REFRESH ---
run_status = fetch_run_status()
run_active = run_status and run_status.get("run_active", False)

if run_active:
    st_autorefresh(interval=3000, key="live_refresh")
else:
    st_autorefresh(interval=30000, key="idle_refresh")

# --- LIVE EXECUTION ---
st.markdown("### 📡 Live Execution")

if run_active:
    phase = run_status.get("phase", "")
    progress = run_status.get("progress", "0/0")
    current_ticker = run_status.get("current_ticker", "")
    last_action = run_status.get("last_action", "")
    score = run_status.get("current_score", 0)
    timestamp = run_status.get("timestamp", "")

    if phase == "initialisation":
        phase_label = "🔄 Initialisation"
    elif phase == "stocks":
        phase_label = "📈 Stocks"
    elif phase == "etfs":
        phase_label = "📊 ETFs"
    else:
        phase_label = "📡 En cours"

    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    col1.metric("Phase", f"{phase_label} ({progress})")
    col2.metric("Current Ticker", current_ticker if current_ticker else "—")
    col3.metric("Status", last_action)
    col4.metric("Score", f"{score}/9" if score > 0 else "—")

    try:
        prog_parts = progress.split('/')
        if len(prog_parts) == 2:
            current = int(prog_parts[0])
            total = int(prog_parts[1])
            if total > 0:
                st.progress(current / total)
            else:
                st.progress(0.0)
    except:
        pass

    st.caption(f"Last update: {timestamp}")
    st.caption("🔄 Auto‑refresh: 3s")
else:
    st.info("🔹 No run in progress. Auto-refreshes every 30s to detect new signals.")
    st.caption("🔄 Auto‑refresh: 30s")

# ============================================================
# SYSTEM STATUS (pour la sidebar)
# ============================================================
def get_system_status():
    run_status = fetch_run_status()
    if run_status and run_status.get("run_active", False):
        return "🟢", "Run in progress"
    return "🔵", "Idle until next run (auto/manual)"

# --- SIDEBAR ---
with st.sidebar:
    status_emoji, status_msg = get_system_status()
    st.markdown(f"### {status_emoji} Status")
    st.markdown(f"*{status_msg}*")
    st.markdown("---")
    st.markdown("<h3 style='color: #F5A623;'>⚙️ Risk Parameters</h3>", unsafe_allow_html=True)
    st.metric("Capital", "1 000 000 $")
    st.metric("Max exposure / trade", "100 000 $")
    st.metric("Risk / trade", "2 %")
    st.metric("Max Stop-Loss", "2.5 %")
    st.metric("Risk/Reward ratio", "1:2")
    st.markdown("---")
    st.markdown('<div class="sidebar-signout">', unsafe_allow_html=True)
    if st.button("Sign out"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.caption(f"Session started – {datetime.now(MONTREAL_TZ).strftime('%Y-%m-%d %H:%M:%S')}")

# ============================================================================
# RÈGLE D'AFFICHAGE : PAS DE SIGNAUX APRÈS 22h00 (Montréal)
# ============================================================================
now_mtl = datetime.now(MONTREAL_TZ)
current_hour = now_mtl.hour
today = now_mtl.strftime('%Y-%m-%d')

signals_raw = fetch_signals()

# Décision d'affichage avec messages distincts pour chaque section
if current_hour >= 22:
    signals = []
    display_message_setups = "📭 Setups are not displayed after 10:00 PM (Montreal time). Only new setups generated from the next successful run will appear here."
    display_message_details = "📭 Signal details are not displayed after 10:00 PM (Montreal time). Only new signal details generated from the next trading day first run will appear here."
else:
    signals = [s for s in signals_raw if s.get('date') == today] if isinstance(signals_raw, list) else []
    display_message_setups = None
    display_message_details = None

# ============================================================================
# TODAY VALIDATED SETUPS
# ============================================================================
st.markdown("### 📋 Today validated setups")

if not signals:
    if display_message_setups:
        st.info(display_message_setups)
    else:
        st.info("No validated setups, so far. Setups will appear after the first successful auto/manual run.")
    st.caption("💡 The interface refreshes automatically every 30 seconds.")
else:
    data_latest = []
    for s in signals:
        entry = s.get('entry_price', 0)
        spread_pct = s.get('spread_pct', 0)
        spread_usd = round((spread_pct / 100) * entry, 2) if entry > 0 else 0
        tp_price = s.get('tp_price', 0)
        sl_price = s.get('sl_price', 0)
        trailing_price = s.get('trailing_price', 0)
        trail_pct = s.get('trail_percent', 0)

        # Fallback pour les anciens signaux (si les niveaux ne sont pas stockés)
        if tp_price == 0 and entry > 0:
            tp_mult = s.get('tp_mult', 0)
            sl_mult = s.get('sl_mult', 0)
            trail_pct_stored = s.get('trail_pct', 0)
            if tp_mult > 0:
                tp_price = round(entry * tp_mult, 2)
                sl_price = round(entry * sl_mult, 2)
                trailing_price = round(entry * (1 - trail_pct_stored/100), 2) if trail_pct_stored > 0 else 0
                trail_pct = trail_pct_stored

        data_latest.append({
            "Ticker": s.get('ticker', 'N/A'),
            "Exchange": s.get('exchange', 'N/A'),
            "Spread": f"{spread_pct:.2f}% (${spread_usd:.2f})",
            "Entry": f"${entry:.2f}",
            "TP": f"${tp_price:.2f}",
            "SL": f"${sl_price:.2f}",
            "Trailing Stop": f"${trailing_price:.2f} ({trail_pct:.2f}%)"
        })

    df_latest = pd.DataFrame(data_latest)
    st.dataframe(
        df_latest,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker", width="small"),
            "Exchange": st.column_config.TextColumn("Exchange", width="small"),
            "Spread": st.column_config.TextColumn("Spread", width="small"),
            "Entry": st.column_config.TextColumn("Entry", width="small"),
            "TP": st.column_config.TextColumn("TP", width="small"),
            "SL": st.column_config.TextColumn("SL", width="small"),
            "Trailing Stop": st.column_config.TextColumn("Trailing Stop", width="medium")
        }
    )

# ============================================================================
# TODAY RELATED SIGNALS DETAILS
# ============================================================================
st.markdown("---")
st.markdown("### 🔍 Today related signals details")

if not signals:
    if display_message_details:
        st.info(display_message_details)
    else:
        st.info("📭 No signal details available yet. They will appear after the first successful auto/manual run.")
else:
    detail_data = []
    for s in signals:
        asset_type = s.get('type', 'STOCK')
        if asset_type == 'ETF':
            aum_m = s.get('aum_m', 0)
            if aum_m >= 1000:
                cap_aum = f"{aum_m/1000:.1f}B$"
            elif aum_m > 0:
                cap_aum = f"{aum_m:.1f}M$"
            else:
                cap_aum = "N/A"
        else:
            cap_aum = s.get('cap_category', 'N/A')

        detail_data.append({
            "Score": s.get('score', 0),
            "Cap./AUM": cap_aum,
            "Gap": f"{s.get('gap', 0):.1f}%",
            "Vol. ratio": f"{s.get('vol_ratio', 0):.1f}x",
            "Market bias": s.get('market_bias', 'N/A'),
            "Run time": s.get('timestamp', 'N/A')
        })

    df_detail = pd.DataFrame(detail_data)
    st.dataframe(
        df_detail,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Score": st.column_config.NumberColumn("Score", width="small", alignment="left"),
            "Cap./AUM": st.column_config.TextColumn("Cap./AUM", width="small"),
            "Gap": st.column_config.TextColumn("Gap", width="small"),
            "Vol. ratio": st.column_config.TextColumn("Vol. ratio", width="small"),
            "Market bias": st.column_config.TextColumn("Market bias", width="medium"),
            "Run time": st.column_config.TextColumn("Run time", width="medium")
        }
    )

# --- FOOTER ---
st.markdown(
    "<p style='text-align: center; color: #666; font-size: 0.8rem; margin-top: 1rem;'>NorthSentinel CORE – Cockpit v2.0 – July, 2026 © NorthSentinel Trading</p>",
    unsafe_allow_html=True
)
