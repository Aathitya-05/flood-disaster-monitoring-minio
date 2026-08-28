"""
Flood Disaster Monitoring System - Streamlit Interactive Operations Dashboard
Provides interactive visualization and query interface over MinIO Object Storage.
"""

import io
import os
import json
import time
import platform
import subprocess
import urllib.request
import streamlit as st
import pandas as pd
from minio import Minio
from PIL import Image
from crypto_utils import decrypt_bytes

st.set_page_config(
    page_title="Flood Disaster Monitoring System | MinIO",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------------------
# Design system - validated status palette (colorblind-safe),
# dark surfaces, Apple-style glass cards, gradients, motion.
# -------------------------------------------------------------
STATUS_COLORS = {
    "normal":   {"hex": "#0ca30c", "glow": "rgba(12,163,12,0.35)", "label": "Normal"},
    "moderate": {"hex": "#fab219", "glow": "rgba(250,178,25,0.35)", "label": "Moderate"},
    "severe":   {"hex": "#ec835a", "glow": "rgba(236,131,90,0.35)", "label": "Severe"},
    "critical": {"hex": "#d03b3b", "glow": "rgba(208,59,59,0.40)", "label": "Critical"},
    "low":      {"hex": "#0ca30c", "glow": "rgba(12,163,12,0.35)", "label": "Low"},
    "medium":   {"hex": "#fab219", "glow": "rgba(250,178,25,0.35)", "label": "Medium"},
    "high":     {"hex": "#ec835a", "glow": "rgba(236,131,90,0.35)", "label": "High"},
    "extreme":  {"hex": "#d03b3b", "glow": "rgba(208,59,59,0.40)", "label": "Extreme"},
}


def badge(value):
    """Renders a colored status pill for a flood-level or severity value."""
    if not value:
        return ""
    key = str(value).strip().lower()
    c = STATUS_COLORS.get(key, {"hex": "#3987e5", "glow": "rgba(57,135,229,0.35)", "label": value})
    icon = {"normal": "✓", "low": "✓", "moderate": "●", "medium": "●",
            "severe": "▲", "high": "▲", "critical": "⚠", "extreme": "⚠"}.get(key, "•")
    return (
        f'<span style="display:inline-flex;align-items:center;gap:5px;'
        f'background:{c["hex"]}22;color:{c["hex"]};border:1px solid {c["hex"]}55;'
        f'padding:3px 12px;border-radius:999px;font-size:0.78rem;font-weight:600;'
        f'letter-spacing:0.02em;box-shadow:0 0 12px {c["glow"]};">'
        f'{icon} {c["label"]}</span>'
    )


def section_title(icon, title, subtitle=None):
    sub = f'<div class="fdm-section-sub">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f'<div class="fdm-section"><div class="fdm-section-title">{icon} {title}</div>{sub}</div>',
        unsafe_allow_html=True
    )


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg-plane: #06070a;
    --bg-surface: #101218;
    --glass: rgba(255,255,255,0.045);
    --glass-border: rgba(255,255,255,0.09);
    --ink: #f5f6f8;
    --ink-secondary: #b7bac3;
    --ink-muted: #7c7f89;
    --accent-blue: #3987e5;
    --accent-violet: #9085e9;
    --accent-aqua: #199e70;
}

html, body, [class*="css"], .stApp, .stApp * :not(code):not(pre):not(kbd):not([data-testid="stIconMaterial"]) {
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
}
code, pre, kbd, .stCodeBlock, [data-testid="stCodeBlock"] * {
    font-family: 'SF Mono', 'Menlo', ui-monospace, monospace !important;
}
/* Material Symbols icons (sidebar collapse arrow, expander chevrons, etc.) must
   keep Streamlit's own icon font - the broad Inter override above turns their
   ligature text (e.g. "keyboard_double_arrow_left") into literal visible text
   instead of rendering the icon glyph. */
[data-testid="stIconMaterial"] {
    font-family: 'Material Symbols Rounded' !important;
    font-weight: normal !important;
    -webkit-font-feature-settings: 'liga';
    font-feature-settings: 'liga';
}

.stApp {
    background: var(--bg-plane);
    color: var(--ink);
    position: relative;
}
.stApp::before {
    content: "";
    position: fixed;
    inset: -10%;
    z-index: 0;
    pointer-events: none;
    background:
        radial-gradient(1200px 600px at 15% -10%, rgba(57,135,229,0.16), transparent 60%),
        radial-gradient(1000px 500px at 100% 0%, rgba(144,133,233,0.14), transparent 55%),
        radial-gradient(900px 700px at 50% 120%, rgba(25,158,112,0.10), transparent 60%);
    animation: fdmAmbientDrift 26s ease-in-out infinite alternate;
    will-change: transform;
}
@keyframes fdmAmbientDrift {
    0%   { transform: translate(0, 0) scale(1) rotate(0deg); }
    50%  { transform: translate(-1.5%, 2%) scale(1.06) rotate(1.5deg); }
    100% { transform: translate(2%, -1.5%) scale(1.03) rotate(-1deg); }
}
.stApp > * { position: relative; z-index: 1; }

.main .block-container {
    padding-top: 2.2rem;
    animation: fdmFadeIn 0.55s cubic-bezier(.2,.8,.2,1);
}

@keyframes fdmFadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* Hero header */
.fdm-hero {
    padding: 8px 0 6px 0;
}
.fdm-hero h1 {
    font-size: 2.9rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    margin: 0;
    line-height: 1.08;
    background: linear-gradient(100deg, #ffffff 10%, var(--accent-blue) 45%, var(--accent-violet) 75%, var(--accent-aqua) 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
}
.fdm-hero p {
    color: var(--ink-secondary);
    font-size: 1.08rem;
    font-weight: 500;
    margin-top: 6px;
}
.fdm-divider {
    height: 1px;
    border: none;
    margin: 22px 0 26px 0;
    background: linear-gradient(90deg, transparent, var(--glass-border) 20%, var(--glass-border) 80%, transparent);
}

/* Section titles used across pages */
.fdm-section { margin: 4px 0 18px 0; }
.fdm-section-title {
    font-size: 1.5rem;
    font-weight: 700;
    letter-spacing: -0.01em;
    background: linear-gradient(95deg, #ffffff, var(--accent-blue) 90%);
    -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
}
.fdm-section-sub { color: var(--ink-muted); font-size: 0.92rem; margin-top: 2px; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0b0d12 0%, #06070a 100%);
    border-right: 1px solid var(--glass-border);
}
[data-testid="stSidebar"] .fdm-brand {
    font-size: 1.35rem; font-weight: 800; letter-spacing: -0.01em;
    background: linear-gradient(95deg, var(--accent-blue), var(--accent-violet));
    -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 2px;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
    color: var(--ink-muted); font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.08em;
    font-weight: 700; margin-top: 4px;
}

/* Sidebar nav (radio) styled as pill tabs */
[data-testid="stSidebar"] div[role="radiogroup"] { gap: 4px; display: flex; flex-direction: column; }
[data-testid="stSidebar"] div[role="radiogroup"] label {
    background: transparent;
    border-radius: 12px;
    padding: 9px 12px !important;
    transition: all 0.18s ease;
    border: 1px solid transparent;
}
[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: var(--glass);
    border-color: var(--glass-border);
    transform: translateX(2px);
}
[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"],
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
    background: linear-gradient(95deg, rgba(57,135,229,0.22), rgba(144,133,233,0.18));
    border-color: rgba(57,135,229,0.4);
    box-shadow: 0 0 18px rgba(57,135,229,0.15);
}
[data-testid="stSidebar"] div[role="radiogroup"] label p { font-weight: 600; font-size: 0.92rem; }

/* Glass cards: metrics, expanders, dataframes - real 3D depth on hover */
.main .block-container { perspective: 1400px; }

[data-testid="stMetric"] {
    background: var(--glass);
    border: 1px solid var(--glass-border);
    border-radius: 18px;
    padding: 16px 18px 14px 18px;
    backdrop-filter: blur(14px);
    box-shadow: 0 1px 2px rgba(0,0,0,0.4), 0 8px 16px rgba(0,0,0,0.25);
    transform-style: preserve-3d;
    transition: transform 0.35s cubic-bezier(.2,.8,.2,1), box-shadow 0.35s, border-color 0.35s;
    will-change: transform;
}
[data-testid="stMetric"]:hover {
    transform: perspective(800px) rotateX(6deg) rotateY(-6deg) translateY(-6px) translateZ(14px) scale(1.02);
    border-color: rgba(57,135,229,0.5);
    box-shadow:
        0 2px 4px rgba(0,0,0,0.35),
        0 14px 24px rgba(0,0,0,0.35),
        0 26px 46px rgba(57,135,229,0.20),
        0 0 0 1px rgba(57,135,229,0.15) inset;
}
[data-testid="stMetricLabel"] { color: var(--ink-muted) !important; font-weight: 600 !important; }
[data-testid="stMetricValue"] {
    background: linear-gradient(95deg, #ffffff, var(--accent-blue));
    -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
    font-weight: 800 !important;
}

[data-testid="stExpander"] {
    background: var(--glass);
    border: 1px solid var(--glass-border) !important;
    border-radius: 16px !important;
    overflow: hidden;
    box-shadow: 0 1px 2px rgba(0,0,0,0.35), 0 6px 14px rgba(0,0,0,0.22);
    transition: border-color 0.25s, box-shadow 0.25s, transform 0.25s cubic-bezier(.2,.8,.2,1);
}
[data-testid="stExpander"]:hover {
    border-color: rgba(57,135,229,0.4) !important;
    transform: translateY(-2px) translateZ(4px);
    box-shadow: 0 2px 4px rgba(0,0,0,0.3), 0 16px 30px rgba(57,135,229,0.14);
}

[data-testid="stDataFrame"] {
    border-radius: 16px;
    overflow: hidden;
    border: 1px solid var(--glass-border);
    box-shadow: 0 10px 26px rgba(0,0,0,0.30);
}

/* Images: rounded, elevated, real depth + tilt on hover */
[data-testid="stImage"] { border-radius: 16px; overflow: hidden; perspective: 900px; }
[data-testid="stImage"] img {
    border-radius: 16px;
    transition: transform 0.45s cubic-bezier(.2,.8,.2,1), filter 0.45s, box-shadow 0.45s;
    box-shadow: 0 2px 4px rgba(0,0,0,0.4), 0 14px 30px rgba(0,0,0,0.45);
    will-change: transform;
}
[data-testid="stImage"] img:hover {
    transform: perspective(900px) rotateX(3deg) rotateY(-4deg) scale(1.045) translateZ(10px);
    filter: brightness(1.08) saturate(1.08);
    box-shadow: 0 4px 8px rgba(0,0,0,0.4), 0 26px 50px rgba(57,135,229,0.30);
}

/* Buttons - raised 3D pill with press-down feedback */
.stButton > button {
    background: linear-gradient(160deg, var(--accent-blue), var(--accent-violet));
    color: #ffffff;
    border: none;
    border-radius: 999px;
    padding: 10px 26px;
    font-weight: 700;
    letter-spacing: 0.01em;
    box-shadow:
        0 1px 0 rgba(255,255,255,0.25) inset,
        0 -2px 6px rgba(0,0,0,0.25) inset,
        0 8px 18px rgba(57,135,229,0.35);
    transition: transform 0.18s cubic-bezier(.2,.8,.2,1), box-shadow 0.18s ease;
}
.stButton > button:hover {
    transform: translateY(-3px) scale(1.02);
    box-shadow:
        0 1px 0 rgba(255,255,255,0.3) inset,
        0 -2px 6px rgba(0,0,0,0.25) inset,
        0 16px 32px rgba(144,133,233,0.45);
}
.stButton > button:active {
    transform: translateY(0px) scale(0.97);
    box-shadow: 0 1px 0 rgba(255,255,255,0.15) inset, 0 4px 10px rgba(57,135,229,0.3);
}

/* Selects, inputs */
[data-baseweb="select"] > div {
    background: var(--glass) !important;
    border-color: var(--glass-border) !important;
    border-radius: 12px !important;
}

/* Tabs - pill-style, matches sidebar nav language */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 6px;
    background: var(--glass);
    border: 1px solid var(--glass-border);
    border-radius: 14px;
    padding: 6px;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 8px 18px;
    font-weight: 600;
    transition: all 0.2s ease;
}
[data-testid="stTabs"] [data-baseweb="tab"]:hover { background: rgba(255,255,255,0.06); }
[data-testid="stTabs"] [aria-selected="true"] {
    background: linear-gradient(95deg, rgba(57,135,229,0.28), rgba(144,133,233,0.22)) !important;
    box-shadow: 0 0 16px rgba(57,135,229,0.18);
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { display: none; }
[data-testid="stTabs"] [data-baseweb="tab-border"] { display: none; }

/* Alerts (st.info/st.success/st.warning) */
[data-testid="stAlert"] {
    border-radius: 14px;
    backdrop-filter: blur(10px);
    border: 1px solid var(--glass-border);
    box-shadow: 0 1px 2px rgba(0,0,0,0.3), 0 8px 18px rgba(0,0,0,0.22);
}

/* Staggered entrance for column-based card/image grids across every page */
[data-testid="column"] {
    animation: fdmCardIn 0.5s cubic-bezier(.2,.8,.2,1) backwards;
}
[data-testid="column"]:nth-child(1) { animation-delay: 0.04s; }
[data-testid="column"]:nth-child(2) { animation-delay: 0.11s; }
[data-testid="column"]:nth-child(3) { animation-delay: 0.18s; }
[data-testid="column"]:nth-child(4) { animation-delay: 0.25s; }
[data-testid="column"]:nth-child(5) { animation-delay: 0.32s; }
@keyframes fdmCardIn {
    from { opacity: 0; transform: translateY(16px) scale(0.98); }
    to   { opacity: 1; transform: translateY(0) scale(1); }
}

/* Scrollbar */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, var(--accent-blue), var(--accent-violet));
    border-radius: 999px;
}

/* Alert bulletin cards (Task 5.3) - raised panel with press-toward-viewer tilt */
.fdm-alert-card {
    border-radius: 16px;
    padding: 18px 22px;
    margin-bottom: 14px;
    background: var(--glass);
    border: 1px solid var(--glass-border);
    border-left: 4px solid var(--accent-color, var(--accent-blue));
    backdrop-filter: blur(12px);
    box-shadow: 0 1px 2px rgba(0,0,0,0.35), 0 8px 18px rgba(0,0,0,0.25);
    transform-style: preserve-3d;
    transition: transform 0.3s cubic-bezier(.2,.8,.2,1), box-shadow 0.3s ease;
    will-change: transform;
}
.fdm-alert-card:hover {
    transform: perspective(1000px) rotateX(2deg) rotateY(-2deg) translateX(6px) translateZ(8px);
    box-shadow: 0 2px 4px rgba(0,0,0,0.3), 0 18px 34px rgba(0,0,0,0.4), 0 0 40px var(--accent-color, rgba(57,135,229,0.15));
}
.fdm-alert-card h4 { margin: 0 0 8px 0; font-size: 1.08rem; }
.fdm-alert-card p { margin: 4px 0; color: var(--ink-secondary); font-size: 0.93rem; line-height: 1.5; }

/* Generic content card used for drone/sensor headers - same raised-panel depth */
.fdm-card {
    background: var(--glass);
    border: 1px solid var(--glass-border);
    border-radius: 18px;
    padding: 18px 22px;
    margin-bottom: 16px;
    backdrop-filter: blur(12px);
    box-shadow: 0 1px 2px rgba(0,0,0,0.35), 0 10px 22px rgba(0,0,0,0.25);
    transform-style: preserve-3d;
    transition: border-color 0.3s ease, transform 0.3s cubic-bezier(.2,.8,.2,1), box-shadow 0.3s ease;
    will-change: transform;
}
.fdm-card:hover {
    border-color: rgba(57,135,229,0.4);
    transform: perspective(1200px) rotateX(1.5deg) translateY(-4px) translateZ(10px);
    box-shadow: 0 2px 4px rgba(0,0,0,0.3), 0 22px 40px rgba(0,0,0,0.35), 0 0 44px rgba(57,135,229,0.10);
}
.fdm-card h3 { margin: 0 0 10px 0; font-size: 1.15rem; }
.fdm-card ul { margin: 0; padding-left: 18px; color: var(--ink-secondary); }
.fdm-card li { margin: 4px 0; }

/* Hero: layered 3D text-shadow for a lifted, engraved look */
.fdm-hero h1 {
    filter: drop-shadow(0 4px 18px rgba(57,135,229,0.25));
}

/* Sidebar nav pills: subtle raised depth, pressed-in when active */
[data-testid="stSidebar"] div[role="radiogroup"] label {
    box-shadow: none;
    transition: all 0.2s cubic-bezier(.2,.8,.2,1);
}
[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    transform: translateX(3px) translateZ(4px);
}
[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"],
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
    box-shadow:
        0 1px 0 rgba(255,255,255,0.08) inset,
        0 -1px 0 rgba(0,0,0,0.3) inset,
        0 0 18px rgba(57,135,229,0.15);
}

/* Hide the default "Made with Streamlit" footer for a cleaner, finished
   look - this is inside the app's own DOM so it's actually reachable,
   unlike the separate Streamlit Cloud owner toolbar. */
footer[data-testid="stFooter"], footer { display: none !important; }
</style>
""", unsafe_allow_html=True)

# Connect to MinIO
# Root credentials come from Streamlit's encrypted secrets store when
# configured (Settings -> Secrets on share.streamlit.io), so the real
# deployed instance never has to run on the well-known "minioadmin"
# default. Falls back to that default for local development, where
# MinIO is bound to loopback-only anyway (see bootstrap_minio_if_needed
# below) and start_project.bat already uses the same default locally.
try:
    ACCESS_KEY = st.secrets.get("MINIO_ROOT_USER", "minioadmin")
    SECRET_KEY = st.secrets.get("MINIO_ROOT_PASSWORD", "minioadmin")
except Exception:
    ACCESS_KEY, SECRET_KEY = "minioadmin", "minioadmin"

# Same pattern for the object-body encryption key (crypto_utils.py) - a
# secret set here must match whatever key the data was actually
# encrypted under (minio_uploader.py), otherwise decryption fails.
try:
    _OBJECT_ENC_KEY_B64 = st.secrets.get("OBJECT_ENC_KEY", None)
except Exception:
    _OBJECT_ENC_KEY_B64 = None

import base64 as _base64
OBJECT_ENC_KEY = _base64.b64decode(_OBJECT_ENC_KEY_B64) if _OBJECT_ENC_KEY_B64 else None  # None -> crypto_utils default


def decrypt_object(blob: bytes) -> bytes:
    return decrypt_bytes(blob, key=OBJECT_ENC_KEY)


MINIO_ENDPOINT = "127.0.0.1:9100"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LINUX_MINIO_BIN = os.path.join(BASE_DIR, "minio_bin_linux", "minio")
MINIO_DATA_DIR = os.path.join(BASE_DIR, "minio_data")


def _minio_is_up():
    try:
        with urllib.request.urlopen(f"http://{MINIO_ENDPOINT}/minio/health/live", timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


@st.cache_resource
def bootstrap_minio_if_needed():
    """On a hosted deployment (e.g. Streamlit Community Cloud) there is no
    separately-running MinIO server to connect to - unlike local development,
    where start_project.bat launches minio_bin/minio.exe beforehand. In that
    case, launch the bundled Linux MinIO binary as a background subprocess,
    pointed at the dataset already committed in minio_data/, so the exact
    same real dataset this project ships with is served with no live API
    calls needed at startup. No-op if MinIO is already reachable (local dev)
    or if not running on Linux (this binary won't execute on Windows)."""
    if _minio_is_up():
        return "already-running"
    if platform.system() != "Linux":
        return "not-linux"
    if not os.path.exists(LINUX_MINIO_BIN):
        return "binary-missing"

    os.chmod(LINUX_MINIO_BIN, 0o755)
    env = os.environ.copy()
    env["MINIO_ROOT_USER"] = ACCESS_KEY
    env["MINIO_ROOT_PASSWORD"] = SECRET_KEY
    subprocess.Popen(
        [LINUX_MINIO_BIN, "server", MINIO_DATA_DIR,
         "--address", MINIO_ENDPOINT, "--console-address", "127.0.0.1:9101"],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    for _ in range(30):
        if _minio_is_up():
            return "bootstrapped"
        time.sleep(1)
    return "bootstrap-timeout"


_bootstrap_status = bootstrap_minio_if_needed()
if _bootstrap_status in ("binary-missing", "bootstrap-timeout"):
    st.error(
        f"Could not start the bundled MinIO server (status: {_bootstrap_status}). "
        "If you're running this locally on Windows, start it first via `start_project.bat`."
    )
    st.stop()


@st.cache_resource
def get_client():
    return Minio(
        MINIO_ENDPOINT,
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        secure=False
    )

client = get_client()

# Header
st.markdown(
    '<div class="fdm-hero">'
    '<h1>🌊 Flood Disaster Monitoring System</h1>'
    '<p>High-performance multi-modal object storage architecture powered by <strong>MinIO</strong></p>'
    '</div>',
    unsafe_allow_html=True
)
st.markdown('<hr class="fdm-divider"/>', unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown('<div class="fdm-brand">🌊🛰️ MinIO</div>', unsafe_allow_html=True)
st.sidebar.markdown("### Control Center")
menu = st.sidebar.radio(
    "Navigation",
    [
        "📊 Storage Overview & Buckets",
        "🛰️ Satellite Flood Maps",
        "🚁 Drone Aerial Surveillance",
        "🌊 IoT Sensor Telemetry",
        "🌦️ Weather Radar Reports",
        "🚨 Emergency Alert Bulletins",
        "🔍 Custom Query Workbench"
    ],
    label_visibility="collapsed"
)


# -------------------------------------------------------------
# 1. Storage Overview & Buckets
# -------------------------------------------------------------
if menu == "📊 Storage Overview & Buckets":
    section_title("📦", "MinIO Bucket Architecture & Storage Footprint")

    buckets = ["satellite-images", "drone-videos", "sensor-data", "weather-reports", "emergency-alerts"]
    bucket_icons = {"satellite-images": "🛰️", "drone-videos": "🚁", "sensor-data": "🌊", "weather-reports": "🌦️", "emergency-alerts": "🚨"}
    # Fixed categorical order (never cycled/re-ranked) - validated CVD-safe slots
    bucket_colors = {
        "satellite-images": "#3987e5", "drone-videos": "#d95926", "sensor-data": "#199e70",
        "weather-reports": "#c98500", "emergency-alerts": "#d55181"
    }

    # Gather all bucket stats up front - render order is decoupled from fetch order
    stats = []
    for b in buckets:
        objs = list(client.list_objects(b, recursive=True))
        stats.append({"bucket": b, "count": len(objs), "size": sum(o.size for o in objs)})

    grand_total_objs = sum(s["count"] for s in stats)
    grand_total_size = sum(s["size"] for s in stats)

    # 1. Hero KPIs - the two numbers that matter most, first
    hc1, hc2 = st.columns(2)
    hc1.metric("🗄️ Total Objects Across All Buckets", f"{grand_total_objs}")
    hc2.metric("💾 Total Storage Footprint", f"{grand_total_size / (1024*1024):.2f} MB")

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # 2. Per-bucket breakdown
    st.markdown('<p style="color:var(--ink-muted);font-size:0.82rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px;">Per-Bucket Breakdown</p>', unsafe_allow_html=True)
    cols = st.columns(len(buckets))
    for i, s in enumerate(stats):
        with cols[i]:
            st.metric(
                label=f"{bucket_icons.get(s['bucket'], '📦')} {s['bucket']}",
                value=f"{s['count']} Objects",
                delta=f"{s['size'] / 1024:.1f} KB"
            )

    # 3. Relative distribution visualization
    st.markdown('<p style="color:var(--ink-muted);font-size:0.82rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;margin:20px 0 8px 0;">Relative Distribution</p>', unsafe_allow_html=True)
    bar_rows = ""
    max_count = max((s["count"] for s in stats), default=1) or 1
    for s in stats:
        pct = round((s["count"] / max_count) * 100, 1)
        color = bucket_colors.get(s["bucket"], "#3987e5")
        bar_rows += (
            f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:10px;">'
            f'<div style="width:150px;font-size:0.85rem;color:var(--ink-secondary);">{bucket_icons.get(s["bucket"],"📦")} {s["bucket"]}</div>'
            f'<div style="flex:1;background:rgba(255,255,255,0.06);border-radius:8px;height:14px;overflow:hidden;">'
            f'<div style="width:{pct}%;height:100%;background:linear-gradient(90deg,{color}aa,{color});border-radius:8px;'
            f'box-shadow:0 0 12px {color}66;transition:width 0.6s cubic-bezier(.2,.8,.2,1);"></div></div>'
            f'<div style="width:56px;text-align:right;font-size:0.85rem;font-weight:700;color:{color};">{s["count"]}</div>'
            f'</div>'
        )
    st.markdown(f'<div class="fdm-card">{bar_rows}</div>', unsafe_allow_html=True)

    st.markdown('<hr class="fdm-divider"/>', unsafe_allow_html=True)

    # 4. Full inventory - a distinct section, since it's a different task (browse vs. summarize)
    section_title("📋", "Bucket Inventory & Sample Objects")
    with st.container():
        st.markdown('<div class="fdm-card">', unsafe_allow_html=True)
        selected_bucket = st.selectbox("Select Bucket to Inspect:", buckets)
        st.markdown('</div>', unsafe_allow_html=True)

    objs = list(client.list_objects(selected_bucket, recursive=True))
    table_data = []
    for o in objs:
        stat = client.stat_object(selected_bucket, o.object_name)
        meta = stat.metadata
        table_data.append({
            "Object Key": o.object_name,
            "Size (Bytes)": o.size,
            "ETag Checksum": o.etag,
            "District": meta.get("x-amz-meta-district", "N/A"),
            "Flood Level": meta.get("x-amz-meta-flood-level", "N/A"),
            "Severity": meta.get("x-amz-meta-severity", "N/A"),
            "Sensor / Source ID": meta.get("x-amz-meta-sensor-id", "N/A"),
            "Last Modified": o.last_modified.strftime("%Y-%m-%d %H:%M:%S")
        })
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True)

# -------------------------------------------------------------
# 2. Satellite Flood Maps
# -------------------------------------------------------------
elif menu == "🛰️ Satellite Flood Maps":
    section_title("🛰️", "Satellite Inundation & Geospatial Imagery")

    with st.container():
        st.markdown('<div class="fdm-card">', unsafe_allow_html=True)
        district = st.selectbox("Select District:", ["All", "Cuttack", "Wayanad", "Patna", "Guwahati", "Kolhapur"])
        st.markdown('</div>', unsafe_allow_html=True)
    prefix = "" if district == "All" else f"raw/{district}/"

    objs = [o for o in client.list_objects("satellite-images", prefix=prefix, recursive=True) if o.object_name.endswith(".jpg")]

    st.markdown(f'<p style="color:var(--ink-muted);font-size:0.88rem;margin-bottom:14px;">Displaying <strong style="color:var(--ink);">{len(objs)}</strong> satellite scenes</p>', unsafe_allow_html=True)
    cols = st.columns(3)
    for idx, o in enumerate(objs):
        stat = client.stat_object("satellite-images", o.object_name)
        meta = stat.metadata

        # Read and decrypt image (stored as AES-256-GCM ciphertext, not a real JPEG)
        response = client.get_object("satellite-images", o.object_name)
        img_bytes = decrypt_object(response.read())
        response.close()
        response.release_conn()
        img = Image.open(io.BytesIO(img_bytes))

        with cols[idx % 3]:
            st.image(img, use_container_width=True)
            st.markdown(f"**Key:** `{o.object_name.split('/')[-1]}`")
            st.markdown(
                f"📍 **Location:** {meta.get('x-amz-meta-location')}<br/>"
                f"🛰️ **Sensor:** {meta.get('x-amz-meta-sensor-id')} · ☁️ **Cloud:** {meta.get('x-amz-meta-cloud-cover')}%<br/>"
                f"{badge(meta.get('x-amz-meta-flood-level'))}",
                unsafe_allow_html=True
            )
            st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 3. Drone Aerial Surveillance (Task 5.1 Demo)
# -------------------------------------------------------------
elif menu == "🚁 Drone Aerial Surveillance":
    section_title("🚁", "Drone Aerial Reconnaissance Footage", "Task 5.1 — retrieval of drone footage by district with S3 pre-signed URLs and keyframes")

    with st.container():
        st.markdown('<div class="fdm-card">', unsafe_allow_html=True)
        district = st.selectbox("Select Surveillance District:", ["Cuttack", "Wayanad", "Patna", "Guwahati", "Kolhapur"])
        st.markdown('</div>', unsafe_allow_html=True)

    prefix = f"aerial/{district}/"
    objs = [o for o in client.list_objects("drone-videos", prefix=prefix, recursive=True) if o.object_name.endswith(".mp4")]

    st.markdown(f'<p style="color:var(--ink-muted);font-size:0.88rem;margin-bottom:14px;">Found <strong style="color:var(--ink);">{len(objs)}</strong> drone missions in <strong style="color:var(--ink);">{district}</strong></p>', unsafe_allow_html=True)

    grid = st.columns(2)
    for idx, o in enumerate(objs):
        stat = client.stat_object("drone-videos", o.object_name)
        meta = stat.metadata
        frame_key = o.object_name + ".jpg"

        with grid[idx % 2]:
            st.markdown('<div class="fdm-card">', unsafe_allow_html=True)
            try:
                frame_res = client.get_object("drone-videos", frame_key)
                fimg = Image.open(io.BytesIO(decrypt_object(frame_res.read())))
                frame_res.close()
                frame_res.release_conn()
                st.image(fimg, caption="Mission Reconnaissance Keyframe", use_container_width=True)
            except Exception:
                st.write("Frame preview unavailable")

            st.markdown(
                f"<h3>🚁 {meta.get('x-amz-meta-sensor-id', 'Drone')}</h3>"
                f"<ul>"
                f"<li><strong>UAV Model:</strong> {meta.get('x-amz-meta-model')} &nbsp;·&nbsp; <strong>Altitude:</strong> {meta.get('x-amz-meta-altitude-m')} m</li>"
                f"<li><strong>District:</strong> {meta.get('x-amz-meta-district')} (Coords: <code>{meta.get('x-amz-meta-coordinates')}</code>)</li>"
                f"<li><strong>Severity:</strong> {badge(meta.get('x-amz-meta-severity'))} &nbsp; <strong>Flood Level:</strong> {badge(meta.get('x-amz-meta-flood-level'))}</li>"
                f"</ul>",
                unsafe_allow_html=True
            )
            # Proxied through Streamlit's own server rather than a presigned
            # MinIO URL - MinIO stays bound to localhost/loopback and is
            # never exposed to the internet, on this deployment or any future
            # one; all object bytes flow through this one audited surface.
            try:
                video_res = client.get_object("drone-videos", o.object_name)
                video_bytes = decrypt_object(video_res.read())
                video_res.close()
                video_res.release_conn()
                st.download_button(
                    "⬇️ Download Mission Video", data=video_bytes,
                    file_name=o.object_name.split("/")[-1], mime="video/mp4",
                    key=f"dl_{o.object_name}"
                )
            except Exception:
                st.caption("Video download unavailable")
            st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------------
# 4. IoT Sensor Telemetry (Task 5.2 Demo)
# -------------------------------------------------------------
elif menu == "🌊 IoT Sensor Telemetry":
    section_title("🌊", "IoT Water Level Sensor Telemetry", "Task 5.2 — real-time streaming and threshold filtering of river water levels directly from MinIO")

    with st.container():
        st.markdown('<div class="fdm-card">', unsafe_allow_html=True)
        district = st.selectbox("Select River Basin District:", ["Cuttack", "Wayanad", "Patna", "Guwahati", "Kolhapur"])
        st.markdown('</div>', unsafe_allow_html=True)
    prefix = f"telemetry/{district}/"
    objs = [o for o in client.list_objects("sensor-data", prefix=prefix, recursive=True) if o.object_name.endswith(".csv")]

    for o in objs:
        stat = client.stat_object("sensor-data", o.object_name)
        meta = stat.metadata

        res = client.get_object("sensor-data", o.object_name)
        df = pd.read_csv(io.BytesIO(decrypt_object(res.read())))
        res.close()
        res.release_conn()

        sensor_id = meta.get("x-amz-meta-sensor-id")
        danger_mark = float(meta.get("x-amz-meta-danger-mark", 14.0))
        max_level = float(meta.get("x-amz-meta-max-water-level", df["water_level_meters"].max()))

        st.markdown(
            f'<div class="fdm-card"><h3>📡 Sensor Station: {sensor_id} '
            f'<span style="color:var(--ink-muted);font-weight:500;font-size:0.9rem;">'
            f'({meta.get("x-amz-meta-location")} · {meta.get("x-amz-meta-river-basin")})</span></h3></div>',
            unsafe_allow_html=True
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("Current Danger Mark", f"{danger_mark:.1f} m")
        c2.metric("Peak Water Level", f"{max_level:.2f} m", delta=f"{max_level - danger_mark:+.2f} m vs Danger")
        critical_count = (df["water_level_meters"] >= danger_mark).sum()
        c3.metric("Critical Inundation Readings", f"{critical_count} / {len(df)}")

        # Plot time series chart
        st.line_chart(df.set_index("timestamp")[["water_level_meters", "danger_mark_meters"]])

        with st.expander("View Raw Telemetry Stream"):
            st.dataframe(df, use_container_width=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 5. Weather Radar Reports
# -------------------------------------------------------------
elif menu == "🌦️ Weather Radar Reports":
    section_title("🌦️", "Weather Reports — Live Data (Open-Meteo)", "Real, live weather data fetched from the Open-Meteo public API for each district's actual coordinates")
    objs = [o for o in client.list_objects("weather-reports", recursive=True) if o.object_name.endswith(".json") and not o.object_name.endswith(".meta.json")]

    # Group by district first so each district's 3 reports live under one tab
    # instead of 15 reports flattened into one long expander list.
    by_district = {}
    for o in objs:
        res = client.get_object("weather-reports", o.object_name)
        data = json.loads(decrypt_object(res.read()).decode("utf-8"))
        res.close()
        res.release_conn()
        by_district.setdefault(data.get("district", "Unknown"), []).append(data)

    report_order = {"Live Current Conditions": 0, "3-Day Precipitation Forecast": 1, "Wind Synoptic Outlook": 2}
    districts_present = sorted(by_district.keys())

    if districts_present:
        tabs = st.tabs([f"📍 {d}" for d in districts_present])
        for tab, dist_name in zip(tabs, districts_present):
            with tab:
                reports = sorted(by_district[dist_name], key=lambda d: report_order.get(d.get("report_type", ""), 9))
                for data in reports:
                    report_type = data.get("report_type", "Weather Report")
                    with st.expander(f"📡 {report_type}", expanded=(report_type == "Live Current Conditions")):
                        if report_type == "Live Current Conditions":
                            c1, c2, c3 = st.columns(3)
                            c1.metric("Temperature", f"{data.get('temperature_c')} °C")
                            c2.metric("Precipitation (current)", f"{data.get('precipitation_mm')} mm")
                            c3.metric("Wind Speed", f"{data.get('wind_speed_kmph')} km/h")
                            c4, c5, c6 = st.columns(3)
                            c4.metric("Humidity", f"{data.get('relative_humidity_pct')} %")
                            c5.metric("Cloud Cover", f"{data.get('cloud_cover_pct')} %")
                            c6.metric("Pressure (MSL)", f"{data.get('pressure_msl_hpa')} hPa")
                        elif report_type == "3-Day Precipitation Forecast":
                            dates = data.get("dates") or []
                            precip = data.get("precipitation_sum_mm") or []
                            prob = data.get("precipitation_probability_max_pct") or []
                            if dates and precip:
                                forecast_df = pd.DataFrame({"Date": dates, "Precipitation (mm)": precip, "Max Probability (%)": prob})
                                st.dataframe(forecast_df, use_container_width=True, hide_index=True)
                                precip_valid = [p for p in precip if p is not None]
                                if precip_valid:
                                    st.metric("Peak Forecast Precipitation", f"{max(precip_valid):.1f} mm")
                        elif report_type == "Wind Synoptic Outlook":
                            dates = data.get("dates") or []
                            wind = data.get("windspeed_10m_max_kmph") or []
                            if dates and wind:
                                wind_df = pd.DataFrame({"Date": dates, "Max Wind Speed (km/h)": wind})
                                st.dataframe(wind_df, use_container_width=True, hide_index=True)
                                wind_valid = [w for w in wind if w is not None]
                                if wind_valid:
                                    st.metric("Peak Wind Speed", f"{max(wind_valid):.1f} km/h")
                        st.caption(f"Fetched {data.get('fetched_at_utc', 'N/A')} · Source: {data.get('data_source', 'N/A')}")

# -------------------------------------------------------------
# 6. Emergency Alert Bulletins (Task 5.3 Demo)
# -------------------------------------------------------------
elif menu == "🚨 Emergency Alert Bulletins":
    section_title("🚨", "State Emergency Operation Center Alert Bulletins", "Task 5.3 — query retrieval of emergency alerts filtered by specific issuance dates")

    dates = ["2026-08-23", "2026-08-22", "2026-08-21", "2026-08-20"]
    with st.container():
        st.markdown('<div class="fdm-card">', unsafe_allow_html=True)
        target_date = st.selectbox("Select Alert Issuance Date:", dates)
        st.markdown('</div>', unsafe_allow_html=True)

    prefix = f"bulletins/{target_date}/"
    objs = list(client.list_objects("emergency-alerts", prefix=prefix, recursive=True))

    st.markdown(f'<p style="color:var(--ink-muted);font-size:0.88rem;margin-bottom:14px;">Retrieved <strong style="color:var(--ink);">{len(objs)}</strong> official alert bulletins for <strong style="color:var(--ink);">{target_date}</strong></p>', unsafe_allow_html=True)
    for o in objs:
        res = client.get_object("emergency-alerts", o.object_name)
        payload = json.loads(decrypt_object(res.read()).decode("utf-8"))
        res.close()
        res.release_conn()

        sev_key = str(payload["severity"]).strip().lower()
        accent = STATUS_COLORS.get(sev_key, STATUS_COLORS["moderate"])["hex"]

        st.markdown(f"""
        <div class="fdm-alert-card" style="--accent-color:{accent};">
            <h4>🚨 {payload['alert_id']} — <span style="color:{accent};">{payload['alert_code']}</span></h4>
            <p>{badge(payload['severity'])} &nbsp; <strong>Authority:</strong> {payload['issuing_authority']} &nbsp;|&nbsp; <strong>District:</strong> {payload['district']}, {payload['state']} (Basin: {payload['river_basin']})</p>
            <p><strong>Action Protocol:</strong> {payload['action_protocol']}</p>
            <p><strong>Estimated Affected Population:</strong> {payload['affected_population_est']:,} &nbsp;|&nbsp; <strong>Active Shelters:</strong> {payload['shelters_active']}</p>
        </div>
        """, unsafe_allow_html=True)

# -------------------------------------------------------------
# 7. Custom Query Workbench
# -------------------------------------------------------------
elif menu == "🔍 Custom Query Workbench":
    section_title("🔍", "MinIO S3 Metadata & Object Query Workbench", "Execute live multi-criteria queries across MinIO buckets using custom metadata tags")

    with st.container():
        st.markdown('<div class="fdm-card">', unsafe_allow_html=True)
        qc1, qc2, qc3 = st.columns(3)
        q_bucket = qc1.selectbox("Select Target Bucket:", ["satellite-images", "drone-videos", "sensor-data", "weather-reports", "emergency-alerts"])
        q_district = qc2.selectbox("Filter District:", ["Any", "Cuttack", "Wayanad", "Patna", "Guwahati", "Kolhapur"])
        q_flood_level = qc3.selectbox("Filter Flood Level:", ["Any", "Critical", "Severe", "Moderate", "Normal"])
        run_query = st.button("🚀 Execute MinIO Query")
        st.markdown('</div>', unsafe_allow_html=True)

    if run_query:
        objs = list(client.list_objects(q_bucket, recursive=True))
        results = []
        for o in objs:
            if o.object_name.endswith(".meta.json"):
                continue
            stat = client.stat_object(q_bucket, o.object_name)
            meta = stat.metadata
            dist = meta.get("x-amz-meta-district", "")
            flevel = meta.get("x-amz-meta-flood-level", "")

            if q_district != "Any" and dist.lower() != q_district.lower():
                continue
            if q_flood_level != "Any" and flevel.lower() != q_flood_level.lower():
                continue

            results.append({
                "Object Key": o.object_name,
                "Size (Bytes)": o.size,
                "District": dist,
                "Flood Level": flevel,
                "Severity": meta.get("x-amz-meta-severity", ""),
                "Sensor ID": meta.get("x-amz-meta-sensor-id", ""),
                "Timestamp": meta.get("x-amz-meta-timestamp", "")
            })

        st.success(f"Query returned {len(results)} matching objects.")
        if results:
            st.dataframe(pd.DataFrame(results), use_container_width=True)
