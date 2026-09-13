"""Central configuration.

Settings are read *live* from the environment on every access (via property
getters), so the web UI can update os.environ / the .env file and have changes
take effect immediately — no restart or module reload needed.

Nothing here is required — sensible defaults keep the pipeline runnable with
zero API keys.
"""
from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # dotenv is optional
    pass

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DRAFTS_DIR = ROOT / "drafts"
DATA_DIR.mkdir(exist_ok=True)
DRAFTS_DIR.mkdir(exist_ok=True)

COMPANIES_CSV = DATA_DIR / "companies.csv"
LEADS_CSV = DATA_DIR / "leads.csv"
SUPPRESSION_CSV = DATA_DIR / "suppression.csv"
PITCH_JSON = DATA_DIR / "pitch.json"
ENV_FILE = ROOT / ".env"

# The full set of settings the UI can edit, with defaults.
ENV_DEFAULTS = {
    "SENDER_NAME": "Your Name",
    "SENDER_COMPANY": "Your Agency",
    "SENDER_EMAIL": "you@youragency.co.za",
    "SENDER_PHONE": "",
    "SENDER_WEBSITE": "",
    "SENDER_ADDRESS": "",
    "HUNTER_API_KEY": "",
    "LLM_PROVIDER": "",
    "ANTHROPIC_API_KEY": "",
    "OPENAI_API_KEY": "",
    "SEND_MODE": "draft",
    "SMTP_HOST": "",
    "SMTP_PORT": "587",
    "SMTP_USERNAME": "",
    "SMTP_PASSWORD": "",
    "DAILY_SEND_LIMIT": "25",
}


def _get(key: str) -> str:
    return os.getenv(key, ENV_DEFAULTS.get(key, ""))


class _Sender:
    @property
    def name(self) -> str: return _get("SENDER_NAME")
    @property
    def company(self) -> str: return _get("SENDER_COMPANY")
    @property
    def email(self) -> str: return _get("SENDER_EMAIL")
    @property
    def phone(self) -> str: return _get("SENDER_PHONE")
    @property
    def website(self) -> str: return _get("SENDER_WEBSITE")
    @property
    def address(self) -> str: return _get("SENDER_ADDRESS")


class _Settings:
    """Live view over environment variables."""

    sender = _Sender()

    @property
    def hunter_api_key(self) -> str: return _get("HUNTER_API_KEY")
    @property
    def llm_provider(self) -> str: return _get("LLM_PROVIDER").lower().strip()
    @property
    def anthropic_api_key(self) -> str: return _get("ANTHROPIC_API_KEY")
    @property
    def openai_api_key(self) -> str: return _get("OPENAI_API_KEY")
    @property
    def send_mode(self) -> str: return _get("SEND_MODE").lower().strip()
    @property
    def smtp_host(self) -> str: return _get("SMTP_HOST")
    @property
    def smtp_port(self) -> int:
        try:
            return int(_get("SMTP_PORT") or 587)
        except ValueError:
            return 587
    @property
    def smtp_username(self) -> str: return _get("SMTP_USERNAME")
    @property
    def smtp_password(self) -> str: return _get("SMTP_PASSWORD")
    @property
    def daily_send_limit(self) -> int:
        try:
            return int(_get("DAILY_SEND_LIMIT") or 25)
        except ValueError:
            return 25


settings = _Settings()


def current_env() -> dict[str, str]:
    """Return the current value of every editable setting."""
    return {k: _get(k) for k in ENV_DEFAULTS}


def save_env(values: dict[str, str]) -> None:
    """Persist settings to both os.environ (live) and the .env file (durable).

    Only keys in ENV_DEFAULTS are written. Existing values are preserved for
    any key not supplied.
    """
    merged = current_env()
    for k, v in values.items():
        if k in ENV_DEFAULTS:
            merged[k] = "" if v is None else str(v)
    # Update the live process environment.
    for k, v in merged.items():
        os.environ[k] = v
    # Write .env for durability across restarts.
    lines = [f"{k}={merged[k]}" for k in ENV_DEFAULTS]
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
