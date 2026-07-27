import streamlit as st
import json
import os
from datetime import datetime
import pytz

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="NorthSentinel CORE", page_icon="📊", layout="wide")

# --- AUTHENTIFICATION ---
def check_password():
    """Return True if the user has entered the correct password."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    # Afficher le champ de mot de passe
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

# --- HEADER AVEC LOGO (PLACEHOLDER) ---
# Remplacer ce bloc quand le logo sera disponible
try:
    st.image("assets/logo_northsentinel_core.png", width=120)
except:
    st.markdown("### 🏔️ NorthSentinel CORE — Cockpit")

st.caption(f"Session ouverte – {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# --- PARAMÈTRES GLOBAUX (pour information) ---
# On peut les récupérer plus tard depuis un fichier de config si besoin
st.sidebar.title("⚙️ Paramètres")
st.sidebar.markdown("**Capital** : 1 000 000 $")
st.sidebar.markdown("**Risque/trade** : 2 %")
st.sidebar.markdown("**SL max** : 2.5 %")
st.sidebar.markdown("**R/R min** : 1:2")

# --- LECTURE DU FICHIER DES SIGNAUX ---
# On va chercher le fichier core_signals_today.json
# Il peut être dans le même dépôt ou dans un autre.
# On va d'abord chercher dans le répertoire courant, puis dans un chemin relatif.
# Adapte le chemin selon ta structure.

SIGNAL_FILE = "core_signals_today.json"  # par défaut, on le met à la racine
if not os.path.exists(SIGNAL_FILE):
    # On essaie un chemin alternatif (si tu l'as dans un dossier data/)
    alt_path = os.path.join("data", "core_signals_today.json")
    if os.path.exists(alt_path):
        SIGNAL_FILE = alt_path

signals = []
if os.path.exists(SIGNAL_FILE):
    with open(SIGNAL_FILE, "r") as f:
        try:
            signals = json.load(f)
        except:
            signals = []
else:
    st.warning("⚠️ Aucun fichier de signaux trouvé. Le fichier core_signals_today.json doit être présent pour afficher les setups.")

# --- AFFICHAGE DES DERNIERS SETUPS ---
st.header("📈 Derniers setups sauvegardés")

if signals:
    # On prend les 10 derniers signaux (les plus récents)
    signals = signals[-10:][::-1]  # inversion pour avoir du plus récent au plus ancien
    
    for s in signals:
        ticker = s.get("ticker", "N/A")
        signal_type = s.get("type", "STOCK")
        entry = s.get("entry_price", 0)
        score = s.get("score", 0)
        gap = s.get("gap", 0)
        vol_ratio = s.get("vol_ratio", 0)
        trail_pct = s.get("trail_percent", 0)
        timestamp = s.get("timestamp", "N/A")
        cap_category = s.get("cap_category", "")
        market_bias = s.get("market_bias", "")
        spread_pct = s.get("spread_pct", 0)
        
        # Pour calculer TP et SL, on va les reconstituer approximativement
        # En attendant, on peut juste les afficher tels quels
        # On va essayer de lire les champs TP/SL s'ils sont présents
        # Mais ils ne sont pas stockés directement dans le fichier actuel.
        # On peut soit les calculer à partir des données (si on a la formule)
        # soit les stocker plus tard. Ici on affiche ce qu'on a.
        
        with st.expander(f"🔹 {ticker} ({signal_type}) – Score: {score} – {timestamp}"):
            col1, col2, col3 = st.columns(3)
            col1.metric("Prix d'entrée", f"${entry:.2f}")
            col1.metric("Score", f"{score}/9" if signal_type=="STOCK" else f"{score}/5")
            col2.metric("GAP", f"{gap:.1f}%")
            col2.metric("Volume ratio", f"{vol_ratio:.1f}x")
            col3.metric("Trailing stop", f"{trail_pct:.2f}%")
            col3.metric("Spread", f"{spread_pct:.2f}%" if spread_pct else "N/A")
            if cap_category:
                st.caption(f"Capitalisation : {cap_category}")
            if market_bias:
                st.caption(f"Biais : {market_bias}")
else:
    st.info("Aucun signal sauvegardé pour le moment. Les signaux apparaîtront après la première exécution du script Core.")

# --- LOGS EN TEMPS RÉEL (optionnel) ---
st.header("📋 Journal des opérations")
# On peut éventuellement lire un fichier de log, mais pour l'instant on affiche un message.
st.text("Les logs en temps réel seront disponibles lorsque le cockpit sera connecté au flux du script Core.")

# --- PIED DE PAGE ---
st.markdown("---")
st.markdown("*NorthSentinel CORE – Cockpit v1.0 – © NorthSentinel Trading*")
