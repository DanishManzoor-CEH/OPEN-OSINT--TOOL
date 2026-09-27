import streamlit as st
from ui import configure_page, render_sidebar, render_header
from storage import list_investigations, load_investigation

configure_page(); render_sidebar()
render_header("Investigation History", "Browse investigations saved by this app instance.")
items = list_investigations()
if not items: st.info("No investigations yet.")
for path in items:
    data = load_investigation(path)
    with st.expander(data.get("prompt", path.name)[:120]):
        st.caption(data.get("created_at", ""))
        st.markdown(data.get("result", {}).get("answer", ""))
