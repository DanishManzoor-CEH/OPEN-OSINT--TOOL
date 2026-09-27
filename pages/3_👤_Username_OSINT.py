import streamlit as st
from config import load_config
from ui import configure_page, render_sidebar, render_header
from tools import configure, check_public_username

configure_page(); render_sidebar()
render_header("Username OSINT", "Check public profile availability on selected platforms.")
cfg = load_config(); configure(cfg.timeout, cfg.hibp_api_key)
username = st.text_input("Username", placeholder="exampleuser")
if st.button("Search public profiles", type="primary"):
    if not username.strip(): st.warning("Enter a username."); st.stop()
    result = check_public_username(username)
    cols = st.columns(len(result.get("profiles", {})) or 1)
    for col, (site, data) in zip(cols, result.get("profiles", {}).items()):
        with col: st.metric(site, "Found" if data.get("found") else "Not found")
    st.json(result)
    st.info("A matching username is not proof of identity or account ownership.")
