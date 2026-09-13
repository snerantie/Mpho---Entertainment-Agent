"""Generate a personalised outreach proposal for a lead.

If an LLM key is configured, we ask the model to write it. Otherwise we
fall back to a solid, editable template so the pipeline still produces
usable drafts with zero keys.
"""
from __future__ import annotations

import json

from config import settings, PITCH_JSON
from .models import Company, Lead
from . import compliance

# Built-in defaults, used if data/pitch.json is missing or invalid.
DEFAULT_OFFER = (
    "a creative partnership that connects your brand with South African "
    "entertainment audiences through culturally-relevant campaigns, "
    "activations, and content."
)
DEFAULT_CATEGORY_ANGLE = {
    "alcohol": (
        "Alcohol brands win in SA by owning moments — music, sport, and "
        "nightlife. We build responsible, standout activations that drive "
        "brand love while respecting advertising codes."
    ),
    "film_tv": (
        "In film & TV, cut-through comes from authentic storytelling and "
        "smart distribution. We help you reach and grow engaged local "
        "audiences across broadcast and streaming."
    ),
    "fashion": (
        "Fashion brands live and die by culture and community. We craft "
        "campaigns and collaborations that put your label at the centre of "
        "the conversation."
    ),
}


def load_pitch() -> tuple[str, dict]:
    """Read the editable pitch (offer + per-category angle) from pitch.json.

    Falls back to the built-in defaults if the file is missing/invalid.
    """
    try:
        data = json.loads(PITCH_JSON.read_text(encoding="utf-8"))
        offer = data.get("offer") or DEFAULT_OFFER
        angle = data.get("category_angle") or DEFAULT_CATEGORY_ANGLE
        return offer, angle
    except Exception:
        return DEFAULT_OFFER, dict(DEFAULT_CATEGORY_ANGLE)


def save_pitch(offer: str, category_angle: dict) -> None:
    PITCH_JSON.write_text(
        json.dumps({"offer": offer, "category_angle": category_angle},
                   indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _greeting(lead: Lead) -> str:
    if lead.contact_name:
        first = lead.contact_name.split()[0]
        return f"Hi {first},"
    return "Hi there,"


def template_proposal(lead: Lead) -> tuple[str, str]:
    """Return (subject, body) built from the template."""
    s = settings.sender
    offer, category_angle = load_pitch()
    angle = category_angle.get(lead.category, "")
    subject = f"Partnership idea for {lead.company}"
    body = f"""{_greeting(lead)}

I'm {s.name} from {s.company}. I've been following what {lead.company} is
doing and think there's a strong opportunity to work together.

We offer {offer}

{angle}

I'd love to share a short proposal tailored to {lead.company}. Would you be
open to a 20-minute call in the next week or two?

{compliance.signature_block()}
{compliance.compliance_footer()}
"""
    return subject, body


def _llm_prompt(lead: Lead) -> str:
    s = settings.sender
    offer, category_angle = load_pitch()
    return f"""Write a concise, warm B2B outreach email (max ~180 words).

From: {s.name}, {s.company} ({s.website})
To: {lead.contact_name or 'a marketing decision-maker'} \
({lead.role or 'unknown role'}) at {lead.company}, a South African \
{lead.category.replace('_', '/')} brand.

Our offer: {offer}
Relevant angle: {category_angle.get(lead.category, '')}

Rules:
- Personalise to the company; do NOT invent specific facts or campaigns.
- One clear call to action: a short intro call.
- Professional, friendly, not pushy. No hype words.
- Return the SUBJECT line on the first line prefixed with "Subject: ", \
then a blank line, then the body.
- Do NOT include a signature or unsubscribe footer (added separately)."""


def llm_proposal(lead: Lead) -> tuple[str, str] | None:
    provider = settings.llm_provider
    try:
        if provider == "anthropic" and settings.anthropic_api_key:
            import anthropic

            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            msg = client.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=600,
                messages=[{"role": "user", "content": _llm_prompt(lead)}],
            )
            text = msg.content[0].text
        elif provider == "openai" and settings.openai_api_key:
            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": _llm_prompt(lead)}],
            )
            text = resp.choices[0].message.content
        else:
            return None
    except Exception as e:
        print(f"  [llm] generation failed ({provider}): {e} — using template")
        return None

    subject, _, body = text.partition("\n")
    subject = subject.replace("Subject:", "").strip()
    body = body.strip()
    body = f"{body}\n{compliance.signature_block()}\n{compliance.compliance_footer()}"
    return subject or f"Partnership idea for {lead.company}", body


def generate(lead: Lead) -> tuple[str, str]:
    """Return (subject, body). Uses the LLM if configured, else the template."""
    result = llm_proposal(lead)
    if result:
        return result
    return template_proposal(lead)
