"""Data models for companies and leads."""
from __future__ import annotations

from dataclasses import dataclass, asdict, fields


@dataclass
class Company:
    name: str
    domain: str
    category: str          # alcohol | film_tv | fashion
    country: str = "South Africa"
    contact: str = ""      # optional known decision-maker name (e.g. from LinkedIn)
    notes: str = ""

    def to_row(self) -> dict:
        return asdict(self)


@dataclass
class Lead:
    company: str
    domain: str
    category: str
    contact_name: str = ""
    role: str = ""
    email: str = ""
    email_source: str = ""       # hunter | pattern_guess | manual
    email_confidence: str = ""   # high | medium | low
    status: str = "new"          # new | researched | drafted | sent | replied | suppressed
    proposal_path: str = ""
    draft_path: str = ""
    notes: str = ""

    def to_row(self) -> dict:
        return asdict(self)

    @staticmethod
    def fieldnames() -> list[str]:
        return [f.name for f in fields(Lead)]
