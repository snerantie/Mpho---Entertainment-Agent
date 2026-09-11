"""Central configuration. Reads from environment / .env file.

Nothing here is required — sensible defaults keep the pipeline runnable
with zero API keys.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
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


@dataclass(frozen=True)
class Sender:
    name: str = os.getenv("SENDER_NAME", "Your Name")
    company: str = os.getenv("SENDER_COMPANY", "Your Agency")
    email: str = os.getenv("SENDER_EMAIL", "you@youragency.co.za")
    phone: str = os.getenv("SENDER_PHONE", "")
    website: str = os.getenv("SENDER_WEBSITE", "")
    address: str = os.getenv("SENDER_ADDRESS", "")


@dataclass(frozen=True)
class Settings:
    hunter_api_key: str = os.getenv("HUNTER_API_KEY", "")
    llm_provider: str = os.getenv("LLM_PROVIDER", "").lower().strip()
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    send_mode: str = os.getenv("SEND_MODE", "draft").lower().strip()
    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587") or 587)
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")

    daily_send_limit: int = int(os.getenv("DAILY_SEND_LIMIT", "25") or 25)

    sender: Sender = Sender()


settings = Settings()
