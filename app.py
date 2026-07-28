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
GITHUB_PATH = "core_signals_today.json"
RUN_STATUS_URL = "https://raw.githubusercontent.com/LuckyHT438/northsentinel-data/main/run_status.json"
LOG_FILE = "core.log"

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="NorthSentinel CORE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS ---
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

# --- FONCTIONS DE LECTURE ---
@st.cache_data(ttl=10)
def fetch_signals():
    token = st.secrets.get("GITHUB_TOKEN", "")
    if not token:
        return []
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_PATH}"
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

def fetch_run_status():
    try:
        r = requests.get(RUN_STATUS_URL, timeout=3)
        if r.status_code == 200:
            return r.json()
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

# --- LIVE EXECUTION ---
st.markdown("### 📡 Live Execution")

if run_active:
    phase = "📈 Stocks" if run_status.get("phase") == "stocks" else "📊 ETFs"
    progress = run_status.get("progress", "0/0")
    current_ticker = run_status.get("current_ticker", "")
    last_action = run_status.get("last_action", "")
    score = run_status.get("current_score", 0)
    timestamp = run_status.get("timestamp", "")
    
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    col1.metric("Phase", f"{phase} ({progress})")
    col2.metric("Current Ticker", current_ticker if current_ticker else "—")
    col3.metric("Status", last_action)
    col4.metric("Score", f"{score}/9" if score > 0 else "—")
    
    try:
        prog_parts = progress.split('/')
        if len(prog_parts) == 2:
            current = int(prog_parts[0])
            total = int(prog_parts[1])
            st.progress(current / total if total > 0 else 0)
    except:
        pass
    
    st.caption(f"Last update: {timestamp}")
    st.caption("🔄 Auto‑refresh: 3s")
else:
    st.info("🔹 No run in progress. Auto‑refresh toutes les 30s pour détecter les nouveaux signaux.")
    st.caption("🔄 Auto‑refresh: 30s")

st.divider()

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

# --- LATEST SETUPS (TABLEAU SANS BORDURES) ---
st.markdown("### 📋 Latest setups")

signals = fetch_signals()

if signals and isinstance(signals, list) and len(signals) > 0:
    # Préparer les données
    data = []
    for s in signals:
        data.append({
            "Ticker": s.get("ticker", "N/A"),
            "Score": s.get("score", 0),
            "Gap": f"{s.get('gap', 0):.1f}%",
            "Vol Ratio": f"{s.get('vol_ratio', 0):.1f}x",
            "Market Bias": s.get("market_bias", "N/A"),
            "Run Time": s.get("timestamp", "N/A")
        })
    df = pd.DataFrame(data)

    # CSS pour supprimer les bordures et mettre le titre en gras
    st.markdown(
        """
        <style>
        .no-border-table {
            border: none !important;
        }
        .no-border-table td, .no-border-table th {
            border: none !important;
        }
        .no-border-table th {
            font-weight: bold !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Afficher le tableau sans bordures
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker", width="small"),
            "Score": st.column_config.NumberColumn("Score", width="small"),
            "Gap": st.column_config.TextColumn("Gap", width="small"),
            "Vol Ratio": st.column_config.TextColumn("Vol Ratio", width="small"),
            "Market Bias": st.column_config.TextColumn("Market Bias", width="medium"),
            "Run Time": st.column_config.TextColumn("Run Time", width="medium")
        }
    )

    # --- Détail du dernier signal (inchangé) ---
    st.markdown("---")
    st.markdown("### 🔍 Last signal details")
    last = signals[-1]
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Ticker", last.get("ticker", "N/A"))
        st.metric("Type", last.get("type", "STOCK"))
    with col2:
        st.metric("Entry Price", f"${last.get('entry_price', 0):.2f}")
        st.metric("Score", f"{last.get('score', 0)}/9" if last.get("type")=="STOCK" else f"{last.get('score', 0)}/5")
    with col3:
        st.metric("GAP", f"{last.get('gap', 0):.1f}%")
        st.metric("Trailing Stop", f"{last.get('trail_percent', 0):.2f}%")
    if last.get("cap_category"):
        st.caption(f"Capitalization: {last.get('cap_category')}")
    if last.get("market_bias"):
        st.caption(f"Market bias: {last.get('market_bias')}")

else:
    st.info("Aucun signal trouvé dans le dépôt de données. Les signaux apparaîtront après le premier run programmé.")
    st.caption("💡 L'interface se met à jour automatiquement toutes les 30 secondes.")

st.divider()

# --- LOGS SECTION ---
st.markdown("### 📋 Run logs")
if os.path.exists(LOG_FILE):
    try:
        with open(LOG_FILE, "r") as f:
            log_lines = f.readlines()
            if len(log_lines) > 50:
                log_lines = log_lines[-50:]
            log_text = "".join(log_lines)
            st.code(log_text, language="log", line_numbers=False)
            st.caption(f"Showing last {len(log_lines)} lines from {LOG_FILE}")
    except Exception as e:
        st.error(f"Error reading log file: {e}")
else:
    st.info("📭 No logs available yet.")
    st.caption("Logs are stored locally and only visible when running in the same environment as the Core script.")

# --- FOOTER ---
st.divider()
st.markdown(
    "<p style='text-align: center; color: #666; font-size: 0.9rem;'>NorthSentinel CORE – Cockpit v2.0 – July, 2026 © NorthSentinel Trading</p>",
    unsafe_allow_html=True
)
