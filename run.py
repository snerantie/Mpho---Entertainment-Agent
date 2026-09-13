#!/usr/bin/env python3
"""Mpho — Entertainment Agent: CLI orchestrator.

Commands:
  python run.py find       Build/refresh leads from data/companies.csv
  python run.py draft      Generate proposals + draft (or send) emails
  python run.py all        find -> draft in one go
  python run.py status     Show a summary table of all leads
  python run.py suppress <email>   Add an email/domain to the do-not-contact list

Prefer the web app? Run:  streamlit run app.py

Runs end-to-end with NO API keys (uses fallbacks). Add keys via the web app
or .env to upgrade email-finding (Hunter) and proposal writing (LLM).
"""
from __future__ import annotations

import sys

from rich.console import Console
from rich.table import Table

from config import LEADS_CSV
from src import service, storage

console = Console()


def cmd_find() -> None:
    service.find_contacts(progress=lambda m: console.print(f"  {m}"))


def cmd_draft() -> None:
    service.generate_drafts(progress=lambda m: console.print(f"  {m}"))
    console.print("Review the .eml files in [bold]drafts/[/bold] before sending.")


def cmd_status() -> None:
    leads = storage.read_leads(LEADS_CSV)
    if not leads:
        console.print("[yellow]No leads yet. Run `python run.py find`.[/yellow]")
        return
    table = Table(title="Mpho — Leads")
    for col in ("Company", "Category", "Contact", "Email", "Conf", "Status"):
        table.add_column(col, overflow="fold")
    for l in leads:
        table.add_row(l.company, l.category, l.contact_name or "-",
                      l.email or "-", l.email_confidence or "-", l.status)
    console.print(table)


def cmd_suppress(value: str) -> None:
    service.add_suppression(value)
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
