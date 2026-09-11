"""POPIA / anti-spam guardrails.

South Africa's POPIA and general direct-marketing norms require:
  - a genuine business reason for contact,
  - accurate sender identity + physical address,
  - an easy, honoured opt-out,
  - a suppression list so opt-outs are never re-contacted.

This module centralises those checks so the rest of the pipeline
can't accidentally email someone it shouldn't.
"""
from __future__ import annotations

from config import settings, SUPPRESSION_CSV
from . import storage


def is_suppressed(email: str, domain: str = "") -> bool:
    suppressed = storage.read_suppression(SUPPRESSION_CSV)
    if not suppressed:
        return False
    email = (email or "").lower().strip()
    domain = (domain or "").lower().strip()
    return email in suppressed or (bool(domain) and domain in suppressed)


def opt_out(email: str, reason: str = "opt_out") -> None:
    storage.append_suppression(SUPPRESSION_CSV, email, reason)


def signature_block() -> str:
    s = settings.sender
    lines = [
        "",
        "—",
        f"{s.name}",
        f"{s.company}",
    ]
    if s.email:
        lines.append(s.email)
    if s.phone:
        lines.append(s.phone)
    if s.website:
        lines.append(s.website)
    return "\n".join(lines)


def compliance_footer() -> str:
    """Required footer: identity, address, and a clear opt-out."""
    s = settings.sender
    parts = [
        "",
        "---",
        f"This is a business proposal from {s.company}.",
    ]
    if s.address:
        parts.append(s.address)
    parts.append(
        f"If you'd prefer not to receive further messages, reply with "
        f'"UNSUBSCRIBE" and we will remove you immediately.'
    )
    return "\n".join(parts)
