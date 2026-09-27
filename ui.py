import streamlit as st
from config import load_config

def configure_page():
    st.set_page_config(page_title="OpenOSINT AI", page_icon="🕵️", layout="wide")
    st.markdown("""
    <style>
    .block-container {max-width:1450px;padding-top:2rem}
    .hero {padding:1.5rem 1.7rem;border-radius:18px;background:linear-gradient(135deg,#07111f,#102a43);border:1px solid #203a55;color:white;margin-bottom:1.25rem}
    .hero h1 {margin:0;font-size:2.2rem}
    .hero p {margin:.45rem 0 0;color:#cbd5e1}
    </style>
    """, unsafe_allow_html=True)

def render_header(title, subtitle):
    st.markdown(f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)

def render_sidebar():
    cfg = load_config()
    with st.sidebar:
        st.title("🕵️ OpenOSINT AI")
        st.caption("V2 investigation workspace")
        st.page_link("app.py", label="Dashboard", icon="🏠")
        st.page_link("pages/1_🔎_Investigation.py", label="Investigation", icon="🔎")
        st.page_link("pages/2_📧_Email_OSINT.py", label="Email OSINT", icon="📧")
        st.page_link("pages/3_👤_Username_OSINT.py", label="Username OSINT", icon="👤")
        st.page_link("pages/4_🌐_Domain_OSINT.py", label="Domain OSINT", icon="🌐")
        st.page_link("pages/5_🌍_IP_OSINT.py", label="IP OSINT", icon="🌍")
        st.page_link("pages/6_📄_Reports.py", label="Reports", icon="📄")
        st.page_link("pages/7_🗂️_History.py", label="History", icon="🗂️")
        st.page_link("pages/8_⚙️_Settings.py", label="Settings", icon="⚙️")
        st.divider()
        st.success("Groq configured") if cfg.groq_api_key else st.error("Groq key missing")
        st.success("HIBP configured") if cfg.hibp_api_key else st.caption("HIBP not configured")
        st.caption("Authorized / public OSINT only.")
