"""Send or draft outreach emails.

Default mode is "draft": we write a ready-to-review .eml file to drafts/
and never send anything. Set SEND_MODE=smtp (and SMTP_* creds) to actually
send. Suppression + daily limits are enforced regardless of mode.
"""
from __future__ import annotations

import re
import smtplib
from email.message import EmailMessage
from pathlib import Path

from config import settings, DRAFTS_DIR
from .models import Lead
from . import compliance


def _safe_name(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", s).strip("_").lower()


def write_draft(lead: Lead, subject: str, body: str) -> Path:
    msg = EmailMessage()
    msg["From"] = f"{settings.sender.name} <{settings.sender.email}>"
    msg["To"] = lead.email
    msg["Subject"] = subject
    msg.set_content(body)

    fname = f"{_safe_name(lead.company)}__{_safe_name(lead.contact_name or 'contact')}.eml"
    path = DRAFTS_DIR / fname
    path.write_bytes(bytes(msg))
    return path


def send_smtp(lead: Lead, subject: str, body: str) -> bool:
    if not (settings.smtp_host and settings.smtp_username):
        print("  [smtp] not configured — skipping actual send")
        return False
    msg = EmailMessage()
    msg["From"] = f"{settings.sender.name} <{settings.sender.email}>"
    msg["To"] = lead.email
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as srv:
            srv.starttls()
            srv.login(settings.smtp_username, settings.smtp_password)
            srv.send_message(msg)
        return True
    except Exception as e:
        print(f"  [smtp] send failed: {e}")
        return False


def deliver(lead: Lead, subject: str, body: str) -> tuple[str, str]:
    """Draft or send based on SEND_MODE. Enforces suppression first.

    Returns (new_status, artifact_path).
    """
    if compliance.is_suppressed(lead.email, lead.domain):
        return "suppressed", ""

    if settings.send_mode == "smtp":
        ok = send_smtp(lead, subject, body)
        # Always keep a copy on disk for records.
        path = write_draft(lead, subject, body)
        return ("sent" if ok else "drafted"), str(path)

    path = write_draft(lead, subject, body)
    return "drafted", str(path)
