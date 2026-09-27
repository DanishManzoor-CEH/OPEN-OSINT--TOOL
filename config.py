import streamlit as st
from dataclasses import dataclass

@dataclass
class AppConfig:
    groq_api_key: str
    groq_model: str
    hibp_api_key: str | None
    max_iterations: int
    timeout: int

def secret(name, default=None):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default

def load_config():
    return AppConfig(
        groq_api_key=secret("GROQ_API_KEY", ""),
        groq_model=secret("GROQ_MODEL", "openai/gpt-oss-120b"),
        hibp_api_key=secret("HIBP_API_KEY"),
        max_iterations=int(secret("MAX_AGENT_STEPS", 6)),
        timeout=int(secret("HTTP_TIMEOUT", 15)),
    )
