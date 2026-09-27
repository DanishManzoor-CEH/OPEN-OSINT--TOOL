import streamlit as st
from config import load_config
from ui import configure_page, render_sidebar, render_header

configure_page(); render_sidebar()
render_header("Settings", "Deployment and integration status.")
cfg = load_config()
c1, c2 = st.columns(2)
with c1:
    st.metric("Groq API", "Configured" if cfg.groq_api_key else "Missing")
    st.metric("HIBP API", "Configured" if cfg.hibp_api_key else "Not configured")
with c2:
    st.metric("Model", cfg.groq_model)
    st.metric("Agent steps", cfg.max_iterations)
st.subheader("Streamlit Secrets")
st.code('GROQ_API_KEY = "gsk_your_key"\nGROQ_MODEL = "openai/gpt-oss-120b"\n# HIBP_API_KEY = "your_key"', language="toml")
st.info("Keep real secrets in Streamlit Cloud Secrets; never commit them to GitHub.")
