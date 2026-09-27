import streamlit as st
from config import load_config
from ui import configure_page, render_sidebar, render_header
from agent import OSINTAgent
from report import build_report
from storage import save_investigation, save_report

configure_page(); render_sidebar()
render_header("Investigation Workspace", "Run a bounded, evidence-first AI investigation.")
cfg = load_config()

if not cfg.groq_api_key:
    st.error("GROQ_API_KEY is missing. Add it in Streamlit Secrets."); st.stop()

with st.form("investigation"):
    prompt = st.text_area("Investigation request", height=160, placeholder="Investigate example.com using public DNS, RDAP, HTTP and robots.txt data.")
    authorized = st.checkbox("I confirm I am authorized to investigate this target and will use public/authorized information.")
    run = st.form_submit_button("🚀 Start investigation", type="primary")

if run:
    if not prompt.strip(): st.warning("Enter a request."); st.stop()
    if not authorized: st.warning("Confirm authorization first."); st.stop()
    agent = OSINTAgent(cfg.groq_api_key, cfg.groq_model, cfg.max_iterations, cfg.timeout, cfg.hibp_api_key)
    with st.status("Agent is working...", expanded=True) as status:
        try:
            result = agent.run(prompt); status.update(label="Investigation complete", state="complete")
        except Exception as e:
            status.update(label="Investigation failed", state="error"); st.exception(e); st.stop()
    st.subheader("Analysis"); st.markdown(result["answer"])
    st.subheader("Evidence collected")
    for item in result["tool_log"]:
        with st.expander(f'{item["tool"]} • {item["status"]}'):
            st.json(item["arguments"]); st.code(item["result"], language="text")
    report = build_report(prompt, result["answer"], result["tool_log"], cfg.groq_model)
    save_investigation(prompt, result); save_report("investigation", report)
    st.download_button("⬇️ Download report", report, "openosint-investigation.md", "text/markdown")
