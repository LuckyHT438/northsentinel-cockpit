import streamlit as st
import json
import os
from datetime import datetime, timedelta
import pandas as pd
import pytz
import time  # ← ajout pour l'auto‑refresh

# --- MONTREAL TIMEZONE (AMERICA/TORONTO) ---
MONTREAL_TZ = pytz.timezone('America/Toronto')

# --- FILE DEFINITIONS (BEFORE ROTATION) ---
SIGNAL_FILE = "core_signals_today.json"
LOG_FILE = "core.log"

# --- AUTOMATIC LOG ROTATION (once/day at midnight) ---
if os.path.exists(LOG_FILE):
    mtime = os.path.getmtime(LOG_FILE)
    last_mod = datetime.fromtimestamp(mtime, MONTREAL_TZ)
    now = datetime.now(MONTREAL_TZ)
    today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if last_mod < today_midnight:
        archive_name = f"core_log_archive_{last_mod.strftime('%Y%m%d_%H%M%S')}.log"
        os.rename(LOG_FILE, archive_name)
        with open(LOG_FILE, 'w') as f:
            pass
        print(f"✅ Log archived: {archive_name}")

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="NorthSentinel CORE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS (buttons, sidebar, etc.) ---
st.markdown(
    """
    <style>
        /* Reduce font size in sidebar */
        .css-1d391kg, .css-12oz5g7, .css-1v3fvcr, .css-1v0mbdj {
            font-size: 0.85rem !important;
        }
        /* Reduce metric font size */
        [data-testid="stMetricValue"] {
            font-size: 0.95rem !important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.8rem !important;
        }
        /* Titres des métriques en orange dans la sidebar */
        section[data-testid="stSidebar"] [data-testid="stMetricLabel"] {
            color: #F5A623 !important;
        }
        /* Reduce sidebar title */
        .css-1v3fvcr h3 {
            font-size: 1rem !important;
        }

        /* --- BUTTON STYLES --- */
        /* "Sign in" button (login page) */
        .stButton button {
            font-weight: bold !important;
            background-color: #F5A623 !important;
            color: #0E1117 !important;
            border: none !important;
            border-radius: 4px !important;
            padding: 0.5rem 1rem !important;
            font-size: 1rem !important;
        }
        .stButton button:hover {
            background-color: #e0951a !important;
            color: #0E1117 !important;
        }
        /* "Sign out" button in sidebar (auto width) */
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
        .sidebar-signout button:hover {
            background-color: #e0951a !important;
            color: #0E1117 !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# --- AUTHENTICATION ---
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

# --- HEADER WITH LOGO (fallback si fichier absent) ---
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

# --- LIVE EXECUTION SECTION ---
st.markdown("### 📡 Live Execution")

# --- READ CURRENT RUN STATUS ---
RUN_STATUS_FILE = "run_status.json"

def get_run_status():
    if os.path.exists(RUN_STATUS_FILE):
        try:
            with open(RUN_STATUS_FILE, "r") as f:
                return json.load(f)
        except:
            return None
    return None

run_status = get_run_status()

if run_status and run_status.get("run_active", False):
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
    
    # Progress bar (if progress is "X/Y" format)
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
    time.sleep(3)
    st.rerun()
else:
    st.info("🔹 No run in progress. Next run is scheduled at the usual times (10:00, 10:30, 14:55, 15:55).")
    st.caption("Updates will appear automatically once a run starts.")

# --- SYSTEM STATUS FUNCTION (2 states - CORRECTED) ---
def get_system_status():
    now = datetime.now(MONTREAL_TZ)
    
    # Run times (local time)
    run_times = [
        now.replace(hour=10, minute=0, second=0, microsecond=0),
        now.replace(hour=10, minute=30, second=0, microsecond=0),
        now.replace(hour=14, minute=55, second=0, microsecond=0),
        now.replace(hour=15, minute=55, second=0, microsecond=0)
    ]
    
    # Find next run
    next_run = None
    for rt in run_times:
        if rt > now:
            next_run = rt
            break
    if next_run is None:
        next_run = run_times[0] + timedelta(days=1)
    
    # Read last signal (with robust error handling)
    last_signal_time = None
    if os.path.exists(SIGNAL_FILE):
        try:
            with open(SIGNAL_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    signals = json.loads(content)
                    if signals and isinstance(signals, list) and len(signals) > 0:
                        last_ts = signals[-1].get('timestamp')
                        if last_ts:
                            last_signal_time = datetime.strptime(last_ts, '%Y-%m-%d %H:%M')
                            last_signal_time = MONTREAL_TZ.localize(last_signal_time)
        except (json.JSONDecodeError, ValueError, IndexError):
            # File is empty or malformed → ignore
            pass
    
    # Determine status (only 2 states)
    if last_signal_time:
        delta_minutes = (now - last_signal_time).total_seconds() / 60
        if delta_minutes < 3:
            return "🟢", "Run in progress"
    
    # If no run in progress, show next run
    delta_next = next_run - now
    hours = delta_next.seconds // 3600
    minutes = (delta_next.seconds % 3600) // 60
    return "🔵", f"Next run in {hours}h {minutes:02d}min"

# --- SIDEBAR (PARAMETERS + STATUS) ---
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
    
    # --- SIGN OUT BUTTON ---
    st.markdown('<div class="sidebar-signout">', unsafe_allow_html=True)
    if st.button("Sign out"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.caption(f"Session started – {datetime.now(MONTREAL_TZ).strftime('%Y-%m-%d %H:%M:%S')}")

# --- READ SIGNALS (for main display) ---
signals = []
if os.path.exists(SIGNAL_FILE):
    with open(SIGNAL_FILE, "r") as f:
        try:
            signals = json.load(f)
        except:
            signals = []
else:
    st.warning("⚠️ No signal file found.")

# --- MAIN METRICS ---
if signals:
    signals = signals[-10:][::-1]
    total = len(signals)
    avg_score = sum(s.get("score", 0) for s in signals) / total if total > 0 else 0
    
    col_met1, col_met2, col_met3, col_met4 = st.columns(4)
    col_met1.metric("📊 Recent signals", total)
    col_met2.metric("⭐ Average score", f"{avg_score:.1f}/9" if avg_score > 0 else "N/A")
    col_met3.metric("📈 Best score", max([s.get("score", 0) for s in signals]) if signals else "N/A")
    col_met4.metric("🔄 Last signal", signals[0].get("ticker", "N/A") if signals else "N/A")
else:
    st.info("No signals saved yet. Signals will appear after the first Core script execution.")

st.divider()

# --- SIGNALS TABLE ---
st.markdown("### 📋 Latest setups")

if signals:
    data = []
    for s in signals:
        data.append({
            "Ticker": s.get("ticker", "N/A"),
            "Type": s.get("type", "STOCK"),
            "Entry": f"${s.get('entry_price', 0):.2f}",
            "Score": s.get("score", 0),
            "Gap": f"{s.get('gap', 0):.1f}%",
            "Vol Ratio": f"{s.get('vol_ratio', 0):.1f}x",
            "Trail": f"{s.get('trail_percent', 0):.2f}%",
            "Timestamp": s.get("timestamp", "N/A")
        })
    df = pd.DataFrame(data)
    
    def color_score(val):
        if val >= 7:
            return 'background-color: #1a5e1a; color: white;'
        elif val >= 5:
            return 'background-color: #b8860b; color: white;'
        else:
            return 'background-color: #5e1a1a; color: white;'
    
    styled_df = df.style.applymap(color_score, subset=['Score'])
    st.dataframe(styled_df, use_container_width=True, height=400)

    st.markdown("---")
    st.markdown("### 🔍 Last signal details")
    last = signals[0]
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
    st.info("Awaiting the first signals...")

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
    st.info("📭 No logs available yet. Logs will appear after the first Core script execution.")
    st.caption("Tip: redirect Core script output to `core.log` to see logs here.")

# --- FOOTER ---
st.divider()
st.markdown(
    "<p style='text-align: center; color: #666; font-size: 0.9rem;'>NorthSentinel CORE – Cockpit v2.0 – July, 2026 © NorthSentinel Trading</p>",
    unsafe_allow_html=True
)
