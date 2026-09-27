# OpenOSINT AI Agent for Streamlit

An AI-assisted OSINT research application built with Streamlit and Groq.

The project uses a Groq model as the reasoning layer and executes explicit Python tools for public, passive OSINT collection. Tool results are returned to the model so it can continue the investigation without inventing tool output.

## Features

- Streamlit web dashboard
- Groq-powered agent
- Local function/tool calling
- Multi-step agent loop
- Public domain DNS resolution
- Public RDAP domain metadata
- Public IP metadata
- Public username profile checks
- Email syntax validation
- Optional Have I Been Pwned lookup
- Passive search-query generation
- HTTP header inspection
- Public robots.txt retrieval
- Transparent tool execution log
- Markdown report download
- GitHub + Streamlit Community Cloud deployment
- Secrets kept outside GitHub

## Project structure

```text
openosint-streamlit/
├── app.py
├── agent.py
├── tools.py
├── report.py
├── requirements.txt
├── README.md
├── .gitignore
└── .streamlit/
    ├── config.toml
    └── secrets.toml.example
```

## 1. Run locally

Python 3.11 or 3.12 is recommended.

```bash
git clone https://github.com/YOUR_USERNAME/openosint-streamlit.git
cd openosint-streamlit

python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Create local secrets:

```text
.streamlit/secrets.toml
```

Example:

```toml
GROQ_API_KEY = "gsk_your_actual_key"
GROQ_MODEL = "openai/gpt-oss-120b"

# Optional:
# HIBP_API_KEY = "your_key"
```

Start the app:

```bash
streamlit run app.py
```

## 2. Deploy to Streamlit Community Cloud

Push the project to GitHub.

Do NOT push:

```text
.streamlit/secrets.toml
.env
```

In Streamlit Community Cloud:

1. Create a new app.
2. Select your GitHub repository.
3. Select the `main` branch.
4. Select `app.py`.
5. Open Advanced settings.
6. Choose Python 3.12.
7. Paste the contents of your secrets into the Secrets field.
8. Deploy.

Example Cloud secrets:

```toml
GROQ_API_KEY = "gsk_your_actual_key"
GROQ_MODEL = "openai/gpt-oss-120b"
```

Optional:

```toml
HIBP_API_KEY = "your_key"
```

## 3. Recommended first tests

After deployment, test:

```text
Investigate the public domain example.com. Check DNS, RDAP metadata, HTTP headers and robots.txt, then summarize the findings.
```

Then:

```text
Check public profile availability for the username exampleuser. Do not assume that any profile belongs to the same person.
```

And:

```text
Generate passive search queries for the domain example.com.
```

## Security model

This version intentionally focuses on passive and public information.

It does not:
- bypass authentication
- brute force accounts
- exploit targets
- access private accounts
- attempt credential attacks
- claim identity from a username match
- infer precise physical location from IP data

Use the application only for assets and information you are authorized to investigate.

## Architecture

```text
                    ┌──────────────────────┐
                    │ Streamlit Web App    │
                    │ app.py               │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ OSINT Agent          │
                    │ agent.py             │
                    └──────────┬───────────┘
                               │
                     Groq Tool Calling
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
       ┌─────────────────┐          ┌──────────────────┐
       │ Groq LLM        │          │ Python OSINT     │
       │ GPT-OSS 120B    │          │ tools.py        │
       └─────────────────┘          └────────┬─────────┘
                                             │
              ┌──────────────┬───────────────┼───────────────┐
              ▼              ▼               ▼               ▼
            DNS             RDAP            IP              HTTP
          Public           Public          Public          Public
```

## Important

This project is an implementation inspired by the agent/tool architecture of OpenOSINT. It is not the OpenOSINT source code itself and does not bundle every OpenOSINT module.

The tool layer is intentionally adapted for a managed Streamlit environment where Kali-specific binaries and long-running local services should not be assumed to exist.
