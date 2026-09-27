import streamlit as st
from config import load_config
from ui import configure_page, render_sidebar, render_header
from tools import configure, validate_email_format, check_hibp

configure_page(); render_sidebar()
render_header("Email OSINT", "Passive email syntax and optional breach exposure lookup.")
cfg = load_config(); configure(cfg.timeout, cfg.hibp_api_key)
email = st.text_input("Email address", placeholder="you@example.com")
if st.button("Analyze email", type="primary"):
    if not email.strip(): st.warning("Enter an email."); st.stop()
    st.subheader("Email syntax"); st.json(validate_email_format(email))
    st.subheader("Breach exposure")
    st.json(check_hibp(email))
    st.warning("A breach record does not prove current compromise.")
