"""Core pipeline actions, framework-agnostic.

Both the CLI (run.py) and the web app (app.py) call these functions so the
business logic lives in exactly one place. Functions accept an optional
`progress` callback (called with a status string) so callers can display
progress however they like.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Callable, Optional

from config import COMPANIES_CSV, LEADS_CSV, SUPPRESSION_CSV, settings
from . import compliance, email_finder, proposal, sender, storage
from .models import Lead

Progress = Optional[Callable[[str], None]]

# Company CSV column order (kept stable for the editor).
COMPANY_COLUMNS = ["name", "domain", "category", "country", "contact", "notes"]


def _emit(progress: Progress, msg: str) -> None:
    if progress:
        progress(msg)


# --------------------------------------------------------------------------
# Stage 1: find decision-maker emails
# --------------------------------------------------------------------------
def find_contacts(progress: Progress = None) -> list[dict]:
    companies = storage.read_companies(COMPANIES_CSV)
    if not companies:
        _emit(progress, "No companies found. Add some in the Companies tab.")
        return []

    leads = storage.read_leads(LEADS_CSV)
    results: list[dict] = []

    _emit(progress, f"Searching contacts for {len(companies)} companies…")
    for c in companies:
        if any(l.company == c.name and l.email for l in leads):
            results.append({"company": c.name, "email": "", "outcome": "already have a contact"})
            _emit(progress, f"• {c.name}: already have a contact, skipping")
            continue

        res = email_finder.find_email(c.domain, known_contact=c.contact)
        lead = Lead(company=c.name, domain=c.domain, category=c.category)
        if res and res.email:
            lead.contact_name = res.contact_name
            lead.role = res.role
            lead.email = res.email
            lead.email_source = res.source
            lead.email_confidence = res.confidence
            lead.status = "researched"
            results.append({"company": c.name, "email": res.email,
                            "outcome": f"{res.source}/{res.confidence}"})
            _emit(progress, f"• {c.name}: {res.email} ({res.source}/{res.confidence})")
        else:
            lead.notes = "No email found — add a contact name or set a Hunter.io key"
            results.append({"company": c.name, "email": "", "outcome": "no email found"})
            _emit(progress, f"• {c.name}: no email (need a Hunter.io key or a known contact)")
        leads.append(lead)

    storage.write_leads(LEADS_CSV, leads)
    _emit(progress, f"Saved {len(leads)} leads.")
    return results


# --------------------------------------------------------------------------
# Stage 2: generate proposals + draft/send
# --------------------------------------------------------------------------
def generate_drafts(progress: Progress = None) -> list[dict]:
    leads = storage.read_leads(LEADS_CSV)
    if not leads:
        _emit(progress, "No leads yet. Run 'Find contacts' first.")
        return []

    results: list[dict] = []
    processed = 0
    limit = settings.daily_send_limit
    mode = settings.send_mode
    _emit(progress, f"Generating proposals (mode={mode}, limit={limit})…")

    for lead in leads:
        if processed >= limit:
            _emit(progress, f"Hit the limit ({limit}). Stopping.")
            break
        if not lead.email or lead.status in ("sent", "suppressed", "replied"):
            continue
        if compliance.is_suppressed(lead.email, lead.domain):
            lead.status = "suppressed"
            results.append({"company": lead.company, "status": "suppressed", "path": ""})
            _emit(progress, f"• {lead.company}: suppressed (on do-not-contact list)")
            continue

        subj, body = proposal.generate(lead)
        status, path = sender.deliver(lead, subj, body)
        lead.status = status
        lead.draft_path = path
        processed += 1
        results.append({"company": lead.company, "status": status, "path": path})
        _emit(progress, f"• {lead.company}: {status} -> {path}")

    storage.write_leads(LEADS_CSV, leads)
    _emit(progress, f"Done. Processed {processed} leads.")
    return results


# --------------------------------------------------------------------------
# Read helpers for the UI
# --------------------------------------------------------------------------
def load_leads() -> list[dict]:
    return [l.to_row() for l in storage.read_leads(LEADS_CSV)]


def load_companies_rows() -> list[dict]:
    rows = [c.to_row() for c in storage.read_companies(COMPANIES_CSV)]
    return rows


def save_companies_rows(rows: list[dict]) -> int:
    """Write the companies CSV from a list of dict rows. Returns count saved."""
    clean = []
    for r in rows:
        name = str(r.get("name", "")).strip()
        if not name:
            continue
        clean.append({col: str(r.get(col, "") or "").strip() for col in COMPANY_COLUMNS})
    COMPANIES_CSV.parent.mkdir(parents=True, exist_ok=True)
    with COMPANIES_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COMPANY_COLUMNS)
        writer.writeheader()
        writer.writerows(clean)
    return len(clean)


def list_drafts() -> list[dict]:
    from config import DRAFTS_DIR
    out = []
    for p in sorted(DRAFTS_DIR.glob("*.eml")):
        out.append({"name": p.name, "path": str(p)})
    return out


def read_draft(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return f"(could not read draft: {e})"


def load_suppression() -> list[str]:
    return sorted(storage.read_suppression(SUPPRESSION_CSV))


def add_suppression(email: str) -> None:
    compliance.opt_out(email, reason="manual")
