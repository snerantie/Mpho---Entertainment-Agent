#!/usr/bin/env python3
"""SA Brand Leads — CLI orchestrator.

Commands:
  python run.py find       Build/refresh leads from data/companies.csv
  python run.py draft      Generate proposals + draft (or send) emails
  python run.py all        find -> draft in one go
  python run.py status     Show a summary table of all leads
  python run.py suppress <email>   Add an email/domain to the do-not-contact list

Runs end-to-end with NO API keys (uses fallbacks). Add keys in .env to
upgrade email-finding (Hunter) and proposal writing (LLM).
"""
from __future__ import annotations

import sys

from rich.console import Console
from rich.table import Table

from config import COMPANIES_CSV, LEADS_CSV, settings
from src import compliance, email_finder, proposal, sender, storage
from src.models import Lead

console = Console()


def cmd_find() -> None:
    companies = storage.read_companies(COMPANIES_CSV)
    if not companies:
        console.print(f"[red]No companies found in {COMPANIES_CSV}[/red]")
        return

    existing = {(l.company, l.contact_name): l for l in storage.read_leads(LEADS_CSV)}
    leads: list[Lead] = list(existing.values())

    console.print(f"[bold]Finding contacts for {len(companies)} companies…[/bold]")
    for c in companies:
        # Skip if we already have a lead with an email for this company.
        if any(l.company == c.name and l.email for l in leads):
            console.print(f"  • {c.name}: already have a contact, skipping")
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
            console.print(
                f"  • {c.name}: [green]{res.email}[/green] "
                f"({res.source}/{res.confidence})"
            )
        else:
            lead.notes = "No email found — add a contact name to data/companies notes or set HUNTER_API_KEY"
            console.print(
                f"  • {c.name}: [yellow]no email (need HUNTER_API_KEY or a known contact)[/yellow]"
            )
        leads.append(lead)

    storage.write_leads(LEADS_CSV, leads)
    console.print(f"\n[bold green]Saved {len(leads)} leads to {LEADS_CSV}[/bold green]")


def cmd_draft() -> None:
    leads = storage.read_leads(LEADS_CSV)
    if not leads:
        console.print("[yellow]No leads yet. Run `python run.py find` first.[/yellow]")
        return

    sent_count = 0
    limit = settings.daily_send_limit
    mode = settings.send_mode

    console.print(
        f"[bold]Generating proposals (mode={mode}, limit={limit})…[/bold]"
    )
    for lead in leads:
        if sent_count >= limit:
            console.print(f"[yellow]Hit daily limit ({limit}). Stopping.[/yellow]")
            break
        if not lead.email:
            continue
        if lead.status in ("sent", "suppressed", "replied"):
            continue
        if compliance.is_suppressed(lead.email, lead.domain):
            lead.status = "suppressed"
            console.print(f"  • {lead.company}: [red]suppressed[/red]")
            continue

        subject, body = proposal.generate(lead)
        status, path = sender.deliver(lead, subject, body)
        lead.status = status
        lead.draft_path = path
        sent_count += 1
        verb = "sent" if status == "sent" else "drafted"
        console.print(f"  • {lead.company}{'/' + lead.contact_name if lead.contact_name else ''}: [green]{verb}[/green] -> {path}")

    storage.write_leads(LEADS_CSV, leads)
    console.print(f"\n[bold green]Done. Processed {sent_count} leads.[/bold green]")
    if mode == "draft":
        console.print("Review the .eml files in [bold]drafts/[/bold] before sending.")


def cmd_status() -> None:
    leads = storage.read_leads(LEADS_CSV)
    if not leads:
        console.print("[yellow]No leads yet. Run `python run.py find`.[/yellow]")
        return
    table = Table(title="SA Brand Leads")
    for col in ("Company", "Category", "Contact", "Email", "Conf", "Status"):
        table.add_column(col, overflow="fold")
    for l in leads:
        table.add_row(l.company, l.category, l.contact_name or "-",
                      l.email or "-", l.email_confidence or "-", l.status)
    console.print(table)


def cmd_suppress(value: str) -> None:
    compliance.opt_out(value, reason="manual")
    console.print(f"[green]Added {value} to the do-not-contact list.[/green]")


def main() -> None:
    args = sys.argv[1:]
    cmd = args[0] if args else "help"
    if cmd == "find":
        cmd_find()
    elif cmd == "draft":
        cmd_draft()
    elif cmd == "all":
        cmd_find()
        cmd_draft()
    elif cmd == "status":
        cmd_status()
    elif cmd == "suppress" and len(args) > 1:
        cmd_suppress(args[1])
    else:
        console.print(__doc__)


if __name__ == "__main__":
    main()
