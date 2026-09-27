# OpenOSINT AI V2

Multi-page Streamlit OSINT research dashboard using Groq tool calling.

## Features
- Dashboard
- Multi-step AI investigation
- Email OSINT + optional HIBP
- Username profile checks
- Domain DNS/RDAP/HTTP/robots
- Public IP metadata
- Investigation history
- Markdown reports
- Streamlit Cloud Secrets

## Local
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Create `.streamlit/secrets.toml`:
```toml
GROQ_API_KEY = "gsk_your_key"
GROQ_MODEL = "openai/gpt-oss-120b"
# HIBP_API_KEY = "your_key"
```

## Streamlit Cloud
Push the repository to GitHub, create a Streamlit app with `app.py`, select Python 3.12, and paste the secrets into Advanced Settings -> Secrets.

Do not commit the real `secrets.toml`.

## Storage
History and reports use local files under `data/`. Managed cloud storage may be ephemeral. Use a database/object-storage backend for persistent production history.

## Safety
Use only public information and targets you are authorized to investigate. This app does not include credential attacks, authentication bypass, exploitation, private-account access, or secret extraction.
