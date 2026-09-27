import streamlit as st
from agent import OSINTAgent
from report import build_markdown_report

st.set_page_config(
    page_title="OpenOSINT AI Agent",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.main { max-width: 1400px; }
.hero {
    padding: 1.4rem 1.6rem;
    border-radius: 18px;
    background: linear-gradient(135deg, #07111f, #102a43);
    color: white;
    margin-bottom: 1.2rem;
}
.hero h1 { margin: 0; font-size: 2.2rem; }
.hero p { margin: .45rem 0 0; color: #cbd5e1; }
.card {
    padding: 1rem;
    border: 1px solid #dbe4ee;
    border-radius: 14px;
    background: #ffffff;
}
.small { color: #64748b; font-size: .88rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
<h1>🕵️ OpenOSINT AI Agent</h1>
<p>AI-assisted, permission-based OSINT research with transparent tool execution and downloadable reports.</p>
</div>
""", unsafe_allow_html=True)

def get_secret(name, default=None):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default

groq_key = get_secret("GROQ_API_KEY")
default_model = get_secret("GROQ_MODEL", "openai/gpt-oss-120b")

with st.sidebar:
    st.header("⚙️ Configuration")
    if groq_key:
        st.success("Groq API key detected")
    else:
        st.error("GROQ_API_KEY is missing")

    model = st.text_input("Groq model", value=default_model)
    max_iterations = st.slider("Maximum agent steps", 1, 8, 5)
    timeout = st.slider("HTTP timeout (seconds)", 5, 30, 15)

    st.divider()
    st.subheader("Optional integrations")
    hibp_key = get_secret("HIBP_API_KEY")
    if hibp_key:
        st.success("HIBP enabled")
    else:
        st.info("HIBP disabled. Add HIBP_API_KEY to enable breach lookup.")

    st.divider()
    st.caption("Use only for authorized security research, investigations, defensive work, or assets you have permission to investigate.")

if not groq_key:
    st.warning("Add `GROQ_API_KEY` in Streamlit Cloud → App settings → Secrets, then restart the app.")
    st.stop()

agent = OSINTAgent(
    api_key=groq_key,
    model=model,
    max_iterations=max_iterations,
    timeout=timeout,
    hibp_api_key=hibp_key,
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_run" not in st.session_state:
    st.session_state.last_run = None

st.subheader("Ask the OSINT agent")
st.caption(
    "Examples: investigate the domain example.com, check the public IP 8.8.8.8, "
    "look for public profiles for username exampleuser, or create a passive OSINT summary for example.com."
)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Enter an authorized OSINT research request...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("Running the agent...", expanded=True) as status:
            try:
                result = agent.run(prompt)
                status.update(label="Investigation complete", state="complete")
            except Exception as exc:
                status.update(label="Agent error", state="error")
                st.error(f"{type(exc).__name__}: {exc}")
                st.stop()

        st.markdown(result["answer"])

        if result["tool_log"]:
            st.subheader("🔎 Tool execution")
            for item in result["tool_log"]:
                with st.expander(
                    f'{item["tool"]}  |  {item["status"]}',
                    expanded=False
                ):
                    st.json(item.get("arguments", {}))
                    st.code(item.get("result", ""), language="text")

        report = build_markdown_report(
            prompt=prompt,
            answer=result["answer"],
            tool_log=result["tool_log"],
            model=model,
        )

        st.download_button(
            "⬇️ Download Markdown report",
            data=report,
            file_name="osint_report.md",
            mime="text/markdown",
        )

    st.session_state.messages.append({"role": "assistant", "content": result["answer"]})
    st.session_state.last_run = result

st.divider()
c1, c2, c3 = st.columns(3)
c1.metric("Agent", "Groq + tools")
c2.metric("Mode", "Passive / authorized")
c3.metric("Report", "Markdown")
