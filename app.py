import streamlit as st
from config import load_config
from ui import configure_page, render_sidebar, render_header

configure_page()
render_sidebar()
render_header("OpenOSINT AI", "V2 • AI-assisted, evidence-first OSINT research workspace")

st.markdown("""
### Welcome

Use the pages in the sidebar to run investigations or individual OSINT modules.

- **Investigation** — multi-step Groq agent with tool calling.
- **Email OSINT** — email syntax and optional HIBP lookup.
- **Username OSINT** — public profile availability checks.
- **Domain OSINT** — DNS, RDAP, HTTP and robots.txt.
- **IP OSINT** — public IP/network metadata.
- **Reports** — generated Markdown reports.
- **History** — previous investigations.
- **Settings** — configuration status.

> Use only public information and targets you are authorized to investigate.
""")

cfg = load_config()
c1, c2, c3 = st.columns(3)
c1.metric("AI backend", "Groq")
c2.metric("Model", cfg.groq_model)
c3.metric("Mode", "Passive / authorized")

st.divider()
st.subheader("Quick start")
st.code('GROQ_API_KEY = "gsk_your_key"\nGROQ_MODEL = "openai/gpt-oss-120b"', language="toml")
st.info("This is an independent Streamlit implementation inspired by an agent/tool architecture; it is not the original OpenOSINT source code.")
