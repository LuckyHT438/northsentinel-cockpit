import streamlit as st
import json
import os
from datetime import datetime, timedelta
import pandas as pd
import pytz
import requests
import base64
from streamlit_autorefresh import st_autorefresh

MONTREAL_TZ = pytz.timezone('America/Toronto')
GITHUB_REPO = "LuckyHT438/northsentinel-data"
GITHUB_PATH = "core_signals_today.json"
RUN_STATUS_URL = "https://raw.githubusercontent.com/LuckyHT438/northsentinel-data/main/run_status.json"

st.set_page_config(page_title="NorthSentinel CORE", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")

# --- AUTH ---
def check_password():
    if "authenticated" in st.session_state and st.session_state.authenticated:
        return True
    st.title("🔐 Restricted Access")
    pw = st.text_input("Enter password", type="password")
    if st.button("Sign in"):
        if pw == st.secrets["password"]:
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
        st.markdown("### 🏔️")
with col2:
    st.markdown("<h1 style='color: #F5A623;'>NorthSentinel CORE</h1>", unsafe_allow_html=True)
    st.markdown("Real‑time system monitoring cockpit — Beta")

st.divider()

# --- FUNCTIONS ---
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
    except:
        pass
    return []

def fetch_run_status():
    try:
        r = requests.get(RUN_STATUS_URL, timeout=3)
        if r.status_code == 200:
            return r.json()
    except:
        pass
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
    st.metric("Phase", f"{run_status.get('phase', '')} ({run_status.get('progress', '0/0')})")
    st.metric("Current Ticker", run_status.get('current_ticker', '—'))
    st.metric("Status", run_status.get('last_action', '—'))
    st.metric("Score", run_status.get('current_score', 0))
else:
    st.info("No run in progress. Auto‑refresh: 30s")
st.divider()

# --- TABLEAU DES SIGNAUX (EXACT) ---
st.markdown("### 📋 Latest setups")

signals = fetch_signals()

if signals and isinstance(signals, list) and len(signals) > 0:
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
    # Pas de colonne d'index, pas de bordures, pas de couleur
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### 🔍 Last signal details")
    last = signals[-1]
    st.metric("Ticker", last.get("ticker", "N/A"))
    st.metric("Entry Price", f"${last.get('entry_price', 0):.2f}")
    st.metric("Score", last.get("score", 0))
else:
    st.info("Aucun signal pour le moment.")

st.divider()
st.caption("NorthSentinel CORE – Cockpit v2.0 – July, 2026")
