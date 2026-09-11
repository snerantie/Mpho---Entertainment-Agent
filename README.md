# SA Brand Leads — outreach automation

Automates the lead-gen → outreach pipeline for **South African entertainment
brands** (alcohol, film/TV, fashion):

1. **Discover** target companies (seeded list, easy to extend)
2. **Find** decision-maker emails (Hunter.io, with a name-pattern fallback)
3. **Write** a personalised proposal per lead (LLM, with a template fallback)
4. **Draft or send** the email (safe *draft* mode by default)
5. **Track** every lead's status in a CSV dashboard

> It runs **end-to-end with zero API keys** using built-in fallbacks. Add keys
> in `.env` to upgrade quality.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env      # optional — fill in what you have
python run.py all         # find contacts, then draft proposals
python run.py status      # see the dashboard
```

Generated emails land in `drafts/*.eml` for you to review. **Nothing is sent
until you set `SEND_MODE=smtp`** and provide SMTP credentials.

## Commands

| Command | What it does |
|---------|--------------|
| `python run.py find` | Build/refresh leads from `data/companies.csv` |
| `python run.py draft` | Generate proposals + draft (or send) emails |
| `python run.py all` | `find` then `draft` |
| `python run.py status` | Print a table of all leads |
| `python run.py suppress <email>` | Add to the do-not-contact list |

## Where to edit things

- **Target companies** → `data/companies.csv` (add rows; `contact` column is an
  optional known decision-maker name from LinkedIn)
- **Your offer / pitch angle** → `OFFER` and `CATEGORY_ANGLE` in `src/proposal.py`
- **Your identity + limits** → `.env` (`SENDER_*`, `DAILY_SEND_LIMIT`)
- **Do-not-contact list** → `data/suppression.csv` (auto-managed)

## How the fallbacks work

| Stage | With keys | Without keys |
|-------|-----------|--------------|
| Email finding | Hunter.io domain search, picks best marketing/brand role | Guesses `first.last@domain` from a known contact name (**low confidence — verify before sending**) |
| Proposal | LLM (Anthropic or OpenAI) | Editable template |
| Sending | SMTP | Writes `.eml` drafts only |

## ⚠️ Compliance (POPIA + anti-spam)

Built in, but **your responsibility to honour**:
- Accurate sender identity + physical address in every email (set `SENDER_ADDRESS`)
- A clear opt-out in every message (added automatically)
- Opt-outs are recorded in `data/suppression.csv` and **never re-contacted**
- `DAILY_SEND_LIMIT` throttles volume

Only contact businesses where you have a genuine, relevant reason. Guessed
emails should be verified (e.g. ZeroBounce/NeverBounce) before real sends.

## Roadmap ideas

- Google Sheets / Airtable dashboard instead of CSV (swap `src/storage.py`)
- Auto-discovery of new companies via web search
- Reply detection + automated follow-up sequences
- Email verification step before sending guessed addresses
