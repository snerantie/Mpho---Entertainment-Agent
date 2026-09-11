"""Find decision-maker emails for a company.

Strategy:
  1. If a HUNTER_API_KEY is set, query Hunter.io Domain Search and pick the
     most relevant marketing/brand decision-maker.
  2. Otherwise, fall back to pattern-guessing from the person's name +
     domain. Guessed emails are flagged low-confidence and should be
     verified before use.

Target roles we care about (marketing / brand decision-makers):
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

import requests

from config import settings

TARGET_ROLE_KEYWORDS = [
    "marketing", "brand", "chief marketing", "cmo", "communications",
    "partnerships", "sponsorship", "media", "growth", "commercial",
]

# Common corporate email patterns, ordered by prevalence.
EMAIL_PATTERNS = [
    "{first}.{last}",
    "{first}{last}",
    "{f}{last}",
    "{first}",
    "{first}_{last}",
    "{f}.{last}",
]


@dataclass
class EmailResult:
    contact_name: str = ""
    role: str = ""
    email: str = ""
    source: str = ""       # hunter | pattern_guess
    confidence: str = ""   # high | medium | low


def _role_score(position: str) -> int:
    p = (position or "").lower()
    return sum(1 for kw in TARGET_ROLE_KEYWORDS if kw in p)


def find_via_hunter(domain: str) -> Optional[EmailResult]:
    if not settings.hunter_api_key:
        return None
    try:
        resp = requests.get(
            "https://api.hunter.io/v2/domain-search",
            params={"domain": domain, "api_key": settings.hunter_api_key,
                    "limit": 25},
            timeout=20,
        )
        resp.raise_for_status()
        emails = resp.json().get("data", {}).get("emails", [])
    except Exception as e:  # network / quota / auth issues -> fall back
        print(f"  [hunter] lookup failed for {domain}: {e}")
        return None

    if not emails:
        return None

    # Prefer the highest role-relevance, then Hunter's own confidence score.
    best = max(
        emails,
        key=lambda e: (_role_score(e.get("position", "")),
                       e.get("confidence", 0) or 0),
    )
    name = " ".join(
        x for x in [best.get("first_name", ""), best.get("last_name", "")] if x
    ).strip()
    conf_num = best.get("confidence", 0) or 0
    confidence = "high" if conf_num >= 80 else "medium" if conf_num >= 50 else "low"
    return EmailResult(
        contact_name=name,
        role=best.get("position", "") or "",
        email=best.get("value", ""),
        source="hunter",
        confidence=confidence,
    )


def _slug(s: str) -> str:
    return re.sub(r"[^a-z]", "", (s or "").lower())


def guess_from_name(full_name: str, domain: str,
                    pattern: str = "{first}.{last}") -> Optional[EmailResult]:
    """Pattern-guess an email. Low confidence — must be verified before send."""
    parts = [p for p in re.split(r"\s+", full_name.strip()) if p]
    if not parts or not domain:
        return None
    first = _slug(parts[0])
    last = _slug(parts[-1]) if len(parts) > 1 else ""
    if not first:
        return None
    local = pattern.format(first=first, last=last, f=first[:1],
                           l=(last[:1] if last else ""))
    local = local.strip(".").replace("..", ".")
    return EmailResult(
        contact_name=full_name.strip(),
        role="",
        email=f"{local}@{domain}",
        source="pattern_guess",
        confidence="low",
    )


def find_email(domain: str, known_contact: str = "") -> Optional[EmailResult]:
    """Main entrypoint. Tries Hunter first, then a name-pattern guess."""
    result = find_via_hunter(domain)
    if result and result.email:
        return result
    if known_contact:
        return guess_from_name(known_contact, domain)
    return None
