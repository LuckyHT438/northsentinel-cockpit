import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd
import pytz

# --- FUSEAU HORAIRE DE MONTRÉAL (AMERICA/TORONTO) ---
MONTREAL_TZ = pytz.timezone('America/Toronto')

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="NorthSentinel CORE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PERSONNALISÉ POUR LA SIDEBAR ---
st.markdown(
    """
    <style>
        /* Réduit la taille de la police dans toute la sidebar */
        .css-1d391kg, .css-12oz5g7, .css-1v3fvcr, .css-1v0mbdj {
            font-size: 0.85rem !important;
        }
        /* Réduit la taille des métriques */
        [data-testid="stMetricValue"] {
            font-size: 1.2rem !important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.8rem !important;
        }
        /* Réduit le titre de la sidebar */
        .css-1v3fvcr h3 {
            font-size: 1rem !important;
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
    st.title("🔐 Accès restreint")
    password_input = st.text_input("Entrez le mot de passe", type="password")
    if st.button("Se connecter"):
        if password_input == st.secrets["password"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Mot de passe incorrect")
    return False

if not check_password():
    st.stop()

# --- HEADER AVEC LOGO ---
col1, col2 = st.columns([1, 5])
with col1:
    st.image("assets/logo_northsentinel_core.png", width=120)
with col2:
    st.markdown("<h1 style='color: #F5A623; margin-bottom: 0;'>NorthSentinel CORE</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #AAAAAA; margin-top: 0;'>Cockpit de supervision — Signaux en temps réel</p>", unsafe_allow_html=True)

st.divider()

# --- BARRE LATÉRALE (PARAMÈTRES) ---
with st.sidebar:
    st.image("assets/logo_northsentinel_core.png", width=80)
    st.markdown("---")
    st.markdown("### ⚙️ Paramètres de risque")
    st.metric("Capital", "1 000 000 $")
    st.metric("Risque / trade", "2 %")
    st.metric("SL max", "2.5 %")
    st.metric("R/R min", "1:2")
    st.markdown("---")
    st.caption(f"Session ouverte – {datetime.now(MONTREAL_TZ).strftime('%Y-%m-%d %H:%M:%S')}")

# --- LECTURE DES SIGNAUX ---
SIGNAL_FILE = "core_signals_today.json"
signals = []
if os.path.exists(SIGNAL_FILE):
    with open(SIGNAL_FILE, "r") as f:
        try:
            signals = json.load(f)
        except:
            signals = []
else:
    st.warning("⚠️ Aucun fichier de signaux trouvé.")

# --- MÉTRIQUES PRINCIPALES ---
if signals:
    signals = signals[-10:][::-1]
    total = len(signals)
    avg_score = sum(s.get("score", 0) for s in signals) / total if total > 0 else 0
    
    col_met1, col_met2, col_met3, col_met4 = st.columns(4)
    col_met1.metric("📊 Signaux récents", total)
    col_met2.metric("⭐ Score moyen", f"{avg_score:.1f}/9" if avg_score > 0 else "N/A")
    col_met3.metric("📈 Meilleur score", max([s.get("score", 0) for s in signals]) if signals else "N/A")
    col_met4.metric("🔄 Dernier signal", signals[0].get("ticker", "N/A") if signals else "N/A")
else:
    st.info("Aucun signal sauvegardé pour le moment. Les signaux apparaîtront après la première exécution du script Core.")

st.divider()

# --- TABLEAU DES SIGNAUX ---
st.markdown("### 📋 Derniers setups")

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
    st.markdown("### 🔍 Détail du dernier signal")
    last = signals[0]
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Ticker", last.get("ticker", "N/A"))
        st.metric("Type", last.get("type", "STOCK"))
    with col2:
        st.metric("Prix d'entrée", f"${last.get('entry_price', 0):.2f}")
        st.metric("Score", f"{last.get('score', 0)}/9" if last.get("type")=="STOCK" else f"{last.get('score', 0)}/5")
    with col3:
        st.metric("GAP", f"{last.get('gap', 0):.1f}%")
        st.metric("Trailing Stop", f"{last.get('trail_percent', 0):.2f}%")
    if last.get("cap_category"):
        st.caption(f"Capitalisation : {last.get('cap_category')}")
    if last.get("market_bias"):
        st.caption(f"Biais : {last.get('market_bias')}")
else:
    st.info("En attente des premiers signaux...")

# --- PIED DE PAGE ---
st.divider()
st.markdown(
    "<p style='text-align: center; color: #666; font-size: 0.8rem;'>NorthSentinel CORE – Cockpit v2.0 – © NorthSentinel Trading</p>",
    unsafe_allow_html=True
)
