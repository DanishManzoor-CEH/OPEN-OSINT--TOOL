import streamlit as st
from config import load_config
from ui import configure_page, render_sidebar, render_header
from tools import configure, get_ip_info

configure_page(); render_sidebar()
render_header("IP OSINT", "Inspect public IP network metadata and approximate geolocation.")
cfg = load_config(); configure(cfg.timeout, cfg.hibp_api_key)
ip = st.text_input("Public IP address", placeholder="8.8.8.8")
if st.button("Analyze IP", type="primary"):
    if not ip.strip(): st.warning("Enter an IP."); st.stop()
    st.json(get_ip_info(ip))
    st.caption("IP geolocation is approximate and is not precise physical location data.")
