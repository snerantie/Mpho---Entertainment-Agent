"""Simple CSV-backed storage. Swap for Google Sheets/Airtable later
without touching the rest of the pipeline."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from .models import Company, Lead


def read_companies(path: Path) -> list[Company]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return [
            Company(
                name=r["name"].strip(),
                domain=r["domain"].strip(),
                category=r["category"].strip(),
                country=r.get("country", "South Africa").strip(),
                contact=r.get("contact", "").strip(),
                notes=r.get("notes", "").strip(),
            )
            for r in csv.DictReader(f)
            if r.get("name")
        ]


def read_leads(path: Path) -> list[Lead]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    leads = []
    for r in rows:
        lead = Lead(company=r.get("company", ""), domain=r.get("domain", ""),
                    category=r.get("category", ""))
        for k, v in r.items():
            if hasattr(lead, k):
                setattr(lead, k, v)
        leads.append(lead)
    return leads


def write_leads(path: Path, leads: Iterable[Lead]) -> None:
    leads = list(leads)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=Lead.fieldnames())
        writer.writeheader()
        for lead in leads:
            writer.writerow(lead.to_row())


def read_suppression(path: Path) -> set[str]:
    """Return a set of lowercased emails/domains that must never be contacted."""
    if not path.exists():
        return set()
    out: set[str] = set()
    with path.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            val = (r.get("email") or r.get("domain") or "").strip().lower()
            if val:
                out.add(val)
    return out


def append_suppression(path: Path, value: str, reason: str = "opt_out") -> None:
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["email", "reason"])
        if not exists:
            writer.writeheader()
        writer.writerow({"email": value.strip().lower(), "reason": reason})
