import streamlit as st
import json
import os
from datetime import datetime, timedelta
import pandas as pd
import pytz

# --- FUSEAU HORAIRE DE MONTRÉAL (AMERICA/TORONTO) ---
MONTREAL_TZ = pytz.timezone('America/Toronto')

# --- DÉFINITION DES FICHIERS (AVANT LA ROTATION) ---
SIGNAL_FILE = "core_signals_today.json"
LOG_FILE = "core.log"

# --- ROTATION AUTOMATIQUE DU FICHIER DE LOG (1x/jour à minuit) ---
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
        print(f"✅ Log archivé : {archive_name}")

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="NorthSentinel CORE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PERSONNALISÉ (boutons, sidebar, etc.) ---
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

        /* --- STYLE DES BOUTONS --- */
        /* Bouton "Se connecter" (page de login) */
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
        /* Bouton "Se déconnecter" dans la sidebar (sans largeur pleine) */
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
    st.markdown("<p style='color: #AAAAAA; margin-top: 0; font-size: 1.2rem;'>Cockpit de supervision — Signaux en temps réel</p>", unsafe_allow_html=True)

st.divider()

# --- FONCTION DE STATUT (SIMPLIFIÉE : 2 ÉTATS) ---
def get_system_status():
    now = datetime.now(MONTREAL_TZ)
    
    # Horaires des runs (heure locale)
    run_times = [
        now.replace(hour=10, minute=0, second=0, microsecond=0),
        now.replace(hour=10, minute=30, second=0, microsecond=0),
        now.replace(hour=14, minute=55, second=0, microsecond=0),
        now.replace(hour=15, minute=55, second=0, microsecond=0)
    ]
    
    # Trouver le prochain run
    next_run = None
    for rt in run_times:
        if rt > now:
            next_run = rt
            break
    if next_run is None:
        next_run = run_times[0] + timedelta(days=1)
    
    # Lire le dernier signal
    last_signal_time = None
    if os.path.exists(SIGNAL_FILE):
        try:
            with open(SIGNAL_FILE, 'r') as f:
                signals = json.load(f)
                if signals:
                    last_ts = signals[-1].get('timestamp')
                    if last_ts:
                        last_signal_time = datetime.strptime(last_ts, '%Y-%m-%d %H:%M')
                        last_signal_time = MONTREAL_TZ.localize(last_signal_time)
        except:
            pass
    
    # Déterminer le statut (uniquement 2 états)
    if last_signal_time:
        delta_minutes = (now - last_signal_time).total_seconds() / 60
        if delta_minutes < 3:
            return "🟢", "Run en cours"
    
    # Si pas de run en cours, on affiche le prochain run
    delta_next = next_run - now
    hours = delta_next.seconds // 3600
    minutes = (delta_next.seconds % 3600) // 60
    return "🔵", f"Prochain run dans {hours}h {minutes:02d}min"

# --- BARRE LATÉRALE (PARAMÈTRES + STATUT) ---
with st.sidebar:
    status_emoji, status_msg = get_system_status()
    st.markdown(f"### {status_emoji} Statut")
    st.markdown(f"*{status_msg}*")
    st.markdown("---")
    st.markdown("<h3 style='color: #F5A623;'>⚙️ Paramètres de risque</h3>", unsafe_allow_html=True)
    st.metric("Capital", "1 000 000 $")
    st.metric("Exposition max / trade", "100 000 $")
    st.metric("Risque / trade", "2 %")
    st.metric("SL max", "2.5 %")
    st.metric("R/R min", "1:2")
    st.markdown("---")
    
    # --- BOUTON DE DÉCONNEXION (avec classe CSS pour largeur auto) ---
    st.markdown('<div class="sidebar-signout">', unsafe_allow_html=True)
    if st.button("Se déconnecter"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.caption(f"Session ouverte – {datetime.now(MONTREAL_TZ).strftime('%Y-%m-%d %H:%M:%S')}")

# --- LECTURE DES SIGNAUX (pour l'affichage principal) ---
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

st.divider()

# --- SECTION LOGS ---
st.markdown("### 📋 Logs des runs")

if os.path.exists(LOG_FILE):
    try:
        with open(LOG_FILE, "r") as f:
            log_lines = f.readlines()
            if len(log_lines) > 50:
                log_lines = log_lines[-50:]
            log_text = "".join(log_lines)
            st.code(log_text, language="log", line_numbers=False)
            st.caption(f"Affichage des {len(log_lines)} dernières lignes du fichier {LOG_FILE}")
    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier de log : {e}")
else:
    st.info("📭 Aucun log disponible pour le moment. Les logs apparaîtront après la première exécution du script Core.")
    st.caption("Astuce : redirige la sortie du script Core vers un fichier `core.log` pour voir les logs ici.")

# --- PIED DE PAGE ---
st.divider()
st.markdown(
    "<p style='text-align: center; color: #666; font-size: 0.9rem;'>NorthSentinel CORE – Cockpit v2.0 – July, 2026 © NorthSentinel Trading</p>",
    unsafe_allow_html=True
)
