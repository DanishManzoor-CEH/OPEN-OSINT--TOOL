import streamlit as st
from config import load_config
from ui import configure_page, render_sidebar, render_header
from tools import configure, get_domain_dns, get_rdap_domain, get_http_headers, get_public_robots

configure_page(); render_sidebar()
render_header("Domain OSINT", "Collect passive public domain metadata.")
cfg = load_config(); configure(cfg.timeout, cfg.hibp_api_key)
domain = st.text_input("Domain", placeholder="example.com")
if st.button("Analyze domain", type="primary"):
    if not domain.strip(): st.warning("Enter a domain."); st.stop()
    tabs = st.tabs(["DNS", "RDAP", "HTTP", "robots.txt"])
    with tabs[0]: st.json(get_domain_dns(domain))
    with tabs[1]: st.json(get_rdap_domain(domain))
    with tabs[2]: st.json(get_http_headers(domain))
    with tabs[3]: st.json(get_public_robots(domain))
