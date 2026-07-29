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

# --- FONCTIONS DE CALCUL (reproduites depuis le Core) ---
def get_market_bias_adjustment(bias_text):
    if "Risk-on" in bias_text:
        return {"tp": 0.005, "sl": 0.005, "trail": 0.5}
    elif "Risk-off" in bias_text:
        return {"tp": -0.005, "sl": -0.005, "trail": -0.5}
    else:
        return {"tp": 0.0, "sl": 0.0, "trail": 0.0}

def get_cap_adjustment(cap_category):
    adjustments = {
        "Mega Cap": {"tp": 0.0, "sl": 0.0, "trail": 0.0},
        "Large Cap": {"tp": 0.0, "sl": 0.0, "trail": 0.0},
        "Mid Cap": {"tp": -0.002, "sl": 0.002, "trail": 0.005},
        "Small Cap": {"tp": -0.005, "sl": 0.005, "trail": 0.010},
        "Micro Cap": {"tp": -0.010, "sl": 0.010, "trail": 0.015},
        "N/A": {"tp": 0.0, "sl": 0.0, "trail": 0.0}
    }
    return adjustments.get(cap_category, {"tp": 0.0, "sl": 0.0, "trail": 0.0})

def get_tp_multiplier(score, gap, cap_category="Large Cap", market_bias=None, spread_pct=0.0):
    if score < 6:
        if score == 5:
            base = 1.010
        else:
            base = 1.005
    elif gap >= 20:
        base = 1.02 + (score - 4) * 0.006
    elif gap >= 10:
        base = 1.015 + (score - 4) * 0.004
    else:
        base = 1.005 + (score - 4) * 0.002
    cap_adj = get_cap_adjustment(cap_category)
    bias_adj = get_market_bias_adjustment(market_bias) if market_bias else {"tp": 0.0}
    spread_adj = spread_pct / 100.0
    base = base + cap_adj["tp"] + bias_adj["tp"] - spread_adj
    return round(base, 3)

def get_sl_multiplier(score, cap_category="Large Cap", market_bias=None, spread_pct=0.0):
    if score >= 8:
        base = 0.97
    elif score >= 6:
        base = 0.96
    else:
        base = 0.95
    cap_adj = get_cap_adjustment(cap_category)
    bias_adj = get_market_bias_adjustment(market_bias) if market_bias else {"sl": 0.0}
    spread_adj = spread_pct / 200.0
    return round(base - cap_adj["sl"] - bias_adj["sl"] - spread_adj, 3)

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="NorthSentinel CORE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS (suppression des bordures, espacements réduits) ---
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
            padding: 0.5rem 1rem !important;
            font-size: 0.9rem !important;
            width: auto !important;
        }
        .sidebar-signout button:hover { background-color: #e0951a !important; color: #0E1117 !important; }

        /* Supprimer les bordures des dataframes */
        .stDataFrame {
            border: none !important;
        }
        .stDataFrame td, .stDataFrame th {
            border: none !important;
        }
        .stDataFrame th {
            font-weight: bold !important;
        }

        /* Réduire les marges entre les sections */
        .block-container {
            padding-top: 1.4rem !important;
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
col1, col2 = st.columns([1, 5])
with col1:
    try:
        st.image("assets/logo_northsentinel_core.png", width=120)
    except:
        st.markdown("### 🏔️ NS")
with col2:
    st.markdown("<h1 style='color: #F5A623; margin-bottom: 0;'>NorthSentinel CORE</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #AAAAAA; margin-top: 0; font-size: 1.2rem;'>Real‑time system monitoring cockpit — Beta</p>", unsafe_allow_html=True)

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

# 🔧 RÉDUCTION DU CACHE : de 10s à 1s pour une détection plus rapide du début de run
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

# --- AUTO-REFRESH INTELLIGENT ---
run_status = fetch_run_status()
run_active = run_status and run_status.get("run_active", False)

if run_active:
    st_autorefresh(interval=3000, key="live_refresh")
else:
    st_autorefresh(interval=30000, key="idle_refresh")

# --- LIVE EXECUTION (corrigé pour gérer "initialisation") ---
st.markdown("### 📡 Live Execution")

if run_active:
    phase = run_status.get("phase", "")
    progress = run_status.get("progress", "0/0")
    current_ticker = run_status.get("current_ticker", "")
    last_action = run_status.get("last_action", "")
    score = run_status.get("current_score", 0)
    timestamp = run_status.get("timestamp", "")

    # Déterminer le libellé de la phase
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

    # Barre de progression (gère le cas total=0)
    try:
        prog_parts = progress.split('/')
        if len(prog_parts) == 2:
            current = int(prog_parts[0])
            total = int(prog_parts[1])
            if total > 0:
                st.progress(current / total)
            else:
                st.progress(0.0)  # total=0, progression à 0%
    except:
        pass

    st.caption(f"Last update: {timestamp}")
    st.caption("🔄 Auto‑refresh: 3s")
else:
    st.info("🔹 No run in progress. Auto‑refresh toutes les 30s pour détecter les nouveaux signaux.")
    st.caption("🔄 Auto‑refresh: 30s")

# --- SYSTEM STATUS (pour la sidebar) ---
def get_system_status():
    now = datetime.now(MONTREAL_TZ)
    run_times = [
        now.replace(hour=10, minute=0, second=0, microsecond=0),
        now.replace(hour=10, minute=30, second=0, microsecond=0),
        now.replace(hour=14, minute=55, second=0, microsecond=0),
        now.replace(hour=15, minute=55, second=0, microsecond=0)
    ]
    next_run = None
    for rt in run_times:
        if rt > now:
            next_run = rt
            break
    if next_run is None:
        next_run = run_times[0] + timedelta(days=1)

    signals = fetch_signals()
    last_signal_time = None
    if signals and isinstance(signals, list) and len(signals) > 0:
        last_ts = signals[-1].get('timestamp')
        if last_ts:
            try:
                last_signal_time = datetime.strptime(last_ts, '%Y-%m-%d %H:%M')
                last_signal_time = MONTREAL_TZ.localize(last_signal_time)
            except:
                pass

    if last_signal_time and (now - last_signal_time).total_seconds() / 60 < 3:
        return "🟢", "Run in progress (latest signal recent)"

    delta_next = next_run - now
    hours = delta_next.seconds // 3600
    minutes = (delta_next.seconds % 3600) // 60
    return "🔵", f"Next run in {hours}h {minutes:02d}min"

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
# TODAY VALIDATED SETUPS (tableau complet avec colonnes spécifiques)
# ============================================================================
st.markdown("### 📋 Today validated setups")

signals = fetch_signals()

if signals and isinstance(signals, list) and len(signals) > 0:
    data_latest = []
    for s in signals:
        entry = s.get('entry_price', 0)
        spread_pct = s.get('spread_pct', 0)
        spread_usd = round((spread_pct / 100) * entry, 2) if entry > 0 else 0
        score = s.get('score', 0)
        gap = s.get('gap', 0)
        market_bias = s.get('market_bias', '')
        cap_cat = s.get('cap_category', 'Large Cap')
        tp_mult = get_tp_multiplier(score, gap, cap_cat, market_bias, spread_pct)
        sl_mult = get_sl_multiplier(score, cap_cat, market_bias, spread_pct)
        tp_price = round(entry * tp_mult, 2)
        sl_price = round(entry * sl_mult, 2)
        trail_pct = s.get('trail_percent', 0)
        trail_price = round(entry * (1 - trail_pct/100), 2) if trail_pct > 0 else 0

        data_latest.append({
            "Ticker": s.get('ticker', 'N/A'),
            "Exchange": s.get('exchange', 'N/A'),
            "Spread": f"{spread_pct:.2f}% (${spread_usd:.2f})",
            "Entry": f"${entry:.2f}",
            "TP": f"${tp_price:.2f}",
            "SL": f"${sl_price:.2f}",
            "Trailing Stop": f"${trail_price:.2f} ({trail_pct:.2f}%)"
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

else:
    st.info("Aucun signal trouvé dans le dépôt de données. Les signaux apparaîtront après le premier run programmé.")
    st.caption("💡 L'interface se met à jour automatiquement toutes les 30 secondes.")

# ============================================================================
# TODAY RELATED SIGNALS DETAILS (avec Cap./AUM dynamique)
# ============================================================================
st.markdown("---")
st.markdown("### 🔍 Today related signals details")

if signals and isinstance(signals, list) and len(signals) > 0:
    last = signals[-1]

    # --- Déterminer la valeur Cap./AUM pour le dernier signal ---
    asset_type_last = last.get('type', 'STOCK')
    if asset_type_last == 'ETF':
        aum_m = last.get('aum_m', 0)
        if aum_m >= 1000:
            cap_aum_last = f"{aum_m/1000:.1f}B$"
        elif aum_m > 0:
            cap_aum_last = f"{aum_m:.1f}M$"
        else:
            cap_aum_last = "N/A"
    else:
        cap_aum_last = last.get('cap_category', 'N/A')

    detail_data = [{
        "Score": last.get('score', 0),
        "Cap./AUM": cap_aum_last,
        "Gap": f"{last.get('gap', 0):.1f}%",
        "Vol. ratio": f"{last.get('vol_ratio', 0):.1f}x",
        "Market bias": last.get('market_bias', 'N/A'),
        "Run time": last.get('timestamp', 'N/A')
    }]
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
else:
    st.info("📭 Aucun détail de signal disponible pour le moment.")

# --- FOOTER ---
st.markdown(
    "<p style='text-align: center; color: #666; font-size: 0.8rem; margin-top: 1rem;'>NorthSentinel CORE – Cockpit v2.0 – July, 2026 © NorthSentinel Trading</p>",
    unsafe_allow_html=True
)
