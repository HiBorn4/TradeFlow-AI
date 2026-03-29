"""
TradeFlow AI - Logistics Document Processor
Enhanced Streamlit Frontend
"""

import streamlit as st
import requests
import json
from pathlib import Path

BACKEND = "http://localhost:8001"

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TradeFlow AI",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Import fonts */
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg: #0a0e1a;
    --surface: #111827;
    --border: #1e2d45;
    --accent: #00d4ff;
    --accent2: #7c3aed;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
    --text: #e2e8f0;
    --muted: #64748b;
}

/* Global */
.stApp { background-color: var(--bg); font-family: 'DM Sans', sans-serif; }
.stApp * { color: var(--text); }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: var(--surface);
    border-right: 1px solid var(--border);
}

/* Main header */
.hero-header {
    background: linear-gradient(135deg, #0a0e1a 0%, #111827 50%, #0d1f35 100%);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 32px 40px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}
.hero-header::before {
    content: '';
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: radial-gradient(circle at 70% 30%, rgba(0,212,255,0.06) 0%, transparent 60%);
    pointer-events: none;
}
.hero-title {
    font-family: 'Space Mono', monospace;
    font-size: 2.2rem;
    font-weight: 700;
    background: linear-gradient(90deg, #00d4ff, #7c3aed);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 8px 0;
}
.hero-sub {
    font-size: 1rem;
    color: var(--muted);
    margin: 0;
    font-weight: 300;
}
.hero-badge {
    display: inline-block;
    background: rgba(0,212,255,0.12);
    border: 1px solid rgba(0,212,255,0.3);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.75rem;
    font-family: 'Space Mono', monospace;
    color: var(--accent);
    margin-top: 12px;
    letter-spacing: 0.05em;
}

/* Status cards */
.status-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px;
    margin-bottom: 24px;
}
.status-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
    text-align: center;
}
.status-card .icon { font-size: 1.5rem; }
.status-card .label { font-size: 0.7rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.1em; margin-top: 4px; }
.status-card .value { font-family: 'Space Mono', monospace; font-size: 1.1rem; font-weight: 700; color: var(--accent); }

/* Upload zone */
.upload-label {
    font-family: 'Space Mono', monospace;
    font-size: 0.85rem;
    color: var(--accent);
    letter-spacing: 0.05em;
    margin-bottom: 8px;
}

/* Log output */
.log-box {
    background: #060a12;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px;
    font-family: 'Space Mono', monospace;
    font-size: 0.8rem;
    line-height: 1.7;
    max-height: 400px;
    overflow-y: auto;
    white-space: pre-wrap;
    color: #a8c0d6;
}
.log-box .log-success { color: #10b981; }
.log-box .log-info    { color: #00d4ff; }
.log-box .log-warn    { color: #f59e0b; }
.log-box .log-err     { color: #ef4444; }

/* Results panel */
.result-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 12px;
}
.result-card .doc-type {
    font-family: 'Space Mono', monospace;
    font-size: 0.75rem;
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: 0.1em;
}
.result-card .doc-count {
    font-size: 1.8rem;
    font-weight: 600;
    color: var(--text);
    line-height: 1;
    margin: 4px 0;
}
.result-card .doc-sub { font-size: 0.8rem; color: var(--muted); }

/* Section headers */
.section-title {
    font-family: 'Space Mono', monospace;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: var(--muted);
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #00d4ff22, #7c3aed22) !important;
    border: 1px solid var(--accent) !important;
    color: var(--accent) !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.05em !important;
    border-radius: 6px !important;
    padding: 8px 20px !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #00d4ff44, #7c3aed44) !important;
    transform: translateY(-1px) !important;
}

/* Chat messages */
.chat-msg {
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 8px;
    font-size: 0.9rem;
    line-height: 1.6;
}
.chat-user {
    background: rgba(124,58,237,0.15);
    border: 1px solid rgba(124,58,237,0.3);
    text-align: right;
}
.chat-agent {
    background: rgba(0,212,255,0.08);
    border: 1px solid rgba(0,212,255,0.2);
}

/* Divider */
hr { border-color: var(--border) !important; margin: 20px 0 !important; }

/* Info/success/error boxes */
.stSuccess { background: rgba(16,185,129,0.1) !important; border-color: var(--success) !important; }
.stError   { background: rgba(239,68,68,0.1) !important; border-color: var(--danger) !important; }
.stInfo    { background: rgba(0,212,255,0.08) !important; border-color: var(--accent) !important; }
.stWarning { background: rgba(245,158,11,0.1) !important; border-color: var(--warning) !important; }
</style>
""", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "backend_url" not in st.session_state:
    st.session_state.backend_url = BACKEND

# ── Helpers ───────────────────────────────────────────────────────────────────
def check_backend(url: str) -> bool:
    try:
        r = requests.get(f"{url}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False

def send_chat(url: str, message: str, session_id: str | None, timeout: int = 1800):
    resp = requests.post(
        f"{url}/chat",
        json={"message": message, "session_id": session_id},
        headers={"Content-Type": "application/json"},
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()

def upload_pdf(url: str, file) -> dict:
    resp = requests.post(
        f"{url}/upload",
        files={"file": (file.name, file, "application/pdf")},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()

DOC_ICONS = {
    "Packing List": "📦",
    "Commercial Invoice": "🧾",
    "Tax Invoice": "🏛️",
    "Import Declaration": "📋",
    "Package Declaration": "📝",
    "Bill of Lading": "🚢",
    "Certificate of Origin": "🌐",
    "Unclassified": "❓",
}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-title">⚙️ Configuration</div>', unsafe_allow_html=True)
    backend_input = st.text_input("Backend URL", st.session_state.backend_url, key="backend_input")
    st.session_state.backend_url = backend_input

    alive = check_backend(st.session_state.backend_url)
    if alive:
        st.success("● Backend connected", icon="✅")
    else:
        st.error("● Backend offline", icon="❌")

    st.markdown("---")
    st.markdown('<div class="section-title">📡 MCP Tools</div>', unsafe_allow_html=True)
    tools = [
        "classify_document",
        "extract_data_from_classified_pages",
        "process_document_end_to_end",
        "get_extracted_json",
        "get_all_extracted_data",
        "get_processing_status",
        "cleanup_workspace",
    ]
    for t in tools:
        st.markdown(f"<span style='font-family:monospace;font-size:0.75rem;color:#64748b'>› {t}</span>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="section-title">ℹ️ About</div>', unsafe_allow_html=True)
    st.markdown("""
<span style='font-size:0.8rem;color:#64748b'>
TradeFlow AI processes logistics PDFs using a multi-step AI pipeline:<br><br>
<b style='color:#94a3b8'>1</b> OCR + LLM page classification<br>
<b style='color:#94a3b8'>2</b> GPT-4.1 Vision extraction<br>
<b style='color:#94a3b8'>3</b> ERPNext JSON schema mapping<br><br>
Built with Google ADK + MCP + FastAPI
</span>
""", unsafe_allow_html=True)

# ── Hero Header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-header">
  <div class="hero-title">🚢 TradeFlow AI</div>
  <p class="hero-sub">Intelligent Logistics Document Processing Pipeline</p>
  <span class="hero-badge">Google ADK · MCP · GPT-4.1 Vision · FastAPI</span>
</div>
""", unsafe_allow_html=True)

# ── Main Layout ───────────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2], gap="large")

with col_left:
    # ── Upload Section ────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">📎 Document Upload</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Drop a logistics PDF - invoices, bills of lading, declarations...",
        type=["pdf"],
        label_visibility="visible",
    )

    if uploaded_file is not None:
        st.info(f"**{uploaded_file.name}** - {uploaded_file.size / 1024:.1f} KB")

        if st.button("🚀 Process Document", use_container_width=True):
            with st.spinner("Uploading..."):
                try:
                    up = upload_pdf(st.session_state.backend_url, uploaded_file)
                    file_path = up.get("file_path")
                    st.success(f"Uploaded → `{file_path}`")
                except Exception as e:
                    st.error(f"Upload failed: {e}")
                    file_path = None

            if file_path:
                st.markdown('<div class="section-title" style="margin-top:16px">⚡ Processing Log</div>', unsafe_allow_html=True)
                log_placeholder = st.empty()
                result_placeholder = st.empty()

                with st.spinner("Running AI pipeline... (this may take 3–5 minutes)"):
                    try:
                        data = send_chat(
                            st.session_state.backend_url,
                            f"Process this document: {file_path}",
                            st.session_state.session_id,
                        )
                        st.session_state.session_id = data.get("session_id")
                        response_text = data.get("response", "")
                        st.session_state.last_result = response_text

                        log_placeholder.markdown(
                            f'<div class="log-box">{response_text}</div>',
                            unsafe_allow_html=True,
                        )
                        result_placeholder.success("✅ Pipeline complete!")

                        st.session_state.chat_history.append({
                            "role": "user",
                            "content": f"Process: {uploaded_file.name}",
                        })
                        st.session_state.chat_history.append({
                            "role": "agent",
                            "content": response_text,
                        })

                    except Exception as e:
                        st.error(f"Processing error: {e}")

    # ── Chat Interface ────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="section-title">💬 Command Interface</div>', unsafe_allow_html=True)

    # Chat history
    if st.session_state.chat_history:
        for msg in st.session_state.chat_history[-6:]:
            css_class = "chat-user" if msg["role"] == "user" else "chat-agent"
            icon = "👤" if msg["role"] == "user" else "🤖"
            st.markdown(
                f'<div class="chat-msg {css_class}">{icon} {msg["content"][:500]}</div>',
                unsafe_allow_html=True,
            )

    cmd_input = st.text_input(
        "Command",
        placeholder="e.g. 'Show all extracted data' or 'cleanup workspace'",
        label_visibility="collapsed",
    )

    c1, c2 = st.columns([4, 1])
    with c1:
        send_btn = st.button("Send →", use_container_width=True)
    with c2:
        clear_btn = st.button("Clear", use_container_width=True)

    if clear_btn:
        st.session_state.chat_history = []
        st.session_state.session_id = None
        st.rerun()

    if send_btn and cmd_input.strip():
        with st.spinner("Thinking..."):
            try:
                data = send_chat(
                    st.session_state.backend_url,
                    cmd_input.strip(),
                    st.session_state.session_id,
                    timeout=120,
                )
                st.session_state.session_id = data.get("session_id")
                reply = data.get("response", "No reply.")
                st.session_state.chat_history.append({"role": "user", "content": cmd_input.strip()})
                st.session_state.chat_history.append({"role": "agent", "content": reply})
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

with col_right:
    # ── Quick Actions ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">⚡ Quick Actions</div>', unsafe_allow_html=True)

    actions = {
        "📊 View All Results": "Show me all extracted data in a summary",
        "🔍 Processing Status": "What is the current processing status?",
        "📦 Packing List JSON": "Show extracted Packing List data",
        "🧾 Invoice JSON": "Show extracted Commercial Invoice data",
        "🗂️ Import Declaration": "Show extracted Import Declaration data",
        "🧹 Cleanup Workspace": "cleanup workspace",
    }

    for label, cmd in actions.items():
        if st.button(label, use_container_width=True, key=f"qa_{label}"):
            if check_backend(st.session_state.backend_url):
                with st.spinner("Running..."):
                    try:
                        data = send_chat(
                            st.session_state.backend_url, cmd,
                            st.session_state.session_id, timeout=60,
                        )
                        st.session_state.session_id = data.get("session_id")
                        reply = data.get("response", "")
                        st.session_state.chat_history.append({"role": "user", "content": cmd})
                        st.session_state.chat_history.append({"role": "agent", "content": reply})
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
            else:
                st.error("Backend offline - start FastAPI server first.")

    # ── Document Types Reference ──────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="section-title">📑 Supported Document Types</div>', unsafe_allow_html=True)

    for doc_type, icon in DOC_ICONS.items():
        if doc_type != "Unclassified":
            st.markdown(
                f"<div style='padding:6px 0;font-size:0.85rem;border-bottom:1px solid #1e2d45'>"
                f"{icon} <span style='color:#e2e8f0'>{doc_type}</span></div>",
                unsafe_allow_html=True,
            )

    # ── Last Result Preview ───────────────────────────────────────────────────
    if st.session_state.last_result:
        st.markdown("---")
        st.markdown('<div class="section-title">📋 Last Output</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="log-box" style="max-height:200px;font-size:0.72rem">'
            f'{st.session_state.last_result[:800]}{"..." if len(st.session_state.last_result) > 800 else ""}'
            f'</div>',
            unsafe_allow_html=True,
        )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style='text-align:center;padding:8px 0'>
  <span style='font-family:Space Mono,monospace;font-size:0.7rem;color:#334155'>
    🚢 TradeFlow AI &nbsp;·&nbsp; Google ADK + MCP + FastAPI + Streamlit &nbsp;·&nbsp;
    <a href='https://github.com' style='color:#00d4ff;text-decoration:none'>GitHub</a>
  </span>
</div>
""", unsafe_allow_html=True)
