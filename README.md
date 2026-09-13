# Mpho — Entertainment Agent

Automates the lead-gen → outreach pipeline for **South African entertainment
brands** (alcohol, film/TV, fashion):

1. **Discover** target companies (seeded list, easy to extend)
2. **Find** decision-maker emails (Hunter.io, with a name-pattern fallback)
3. **Write** a personalised proposal per lead (LLM, with a template fallback)
4. **Draft or send** the email (safe *draft* mode by default)
5. **Track** every lead's status in a dashboard

> It runs **end-to-end with zero API keys** using built-in fallbacks. Add keys
> to upgrade quality — right from the web app, no files to edit.

## 🖱️ No-code: the web app (recommended)

Everything is clickable — no terminal commands after launch.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Then use the tabs in your browser:

| Tab | What you do |
|-----|-------------|
| ⚙️ **Setup** | Enter your name/company + optional API keys; choose Draft or Send mode |
| 🏢 **Companies** | Add/edit target brands in a spreadsheet-style table |
| ✍️ **Pitch** | Write what you're offering (used in every proposal) |
| ▶️ **Run** | Click **Find contacts**, then **Generate proposals** |
| 📧 **Drafts** | Preview each proposal before it goes out |
| 🚫 **Do-not-contact** | Manage opt-outs / excluded addresses |

## ⌨️ Power users: the command line

```bash
python run.py all         # find contacts, then draft proposals
python run.py status      # see the dashboard
```

Generated emails land in `drafts/*.eml` for you to review. **Nothing is sent
until you switch to Send mode** (Setup tab) and provide email-server details.

### CLI commands

| Command | What it does |
|---------|--------------|
| `python run.py find` | Build/refresh leads from `data/companies.csv` |
| `python run.py draft` | Generate proposals + draft (or send) emails |
| `python run.py all` | `find` then `draft` |
| `python run.py status` | Print a table of all leads |
| `python run.py suppress <email>` | Add to the do-not-contact list |

## Where things live

Prefer the **web app** for all of this — but under the hood:

- **Target companies** → `data/companies.csv` (Companies tab)
- **Your offer / pitch angle** → `data/pitch.json` (Pitch tab)
- **Your identity + keys + limits** → `.env` (Setup tab)
- **Do-not-contact list** → `data/suppression.csv` (Do-not-contact tab, auto-managed)

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
