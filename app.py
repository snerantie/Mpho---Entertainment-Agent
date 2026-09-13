"""Mpho — Entertainment Agent: no-code web app.

Run it with:  streamlit run app.py

Everything you need is here as clickable buttons and editable tables —
no code or terminal commands required after launch.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

import config
from src import proposal, service

st.set_page_config(page_title="Mpho — Entertainment Agent", page_icon="🎬", layout="wide")

st.title("🎬 Mpho — Entertainment Agent")
st.caption(
    "Research SA entertainment brands, find decision-makers, write proposals, "
    "and prepare outreach — all from this page."
)

tab_setup, tab_companies, tab_pitch, tab_run, tab_drafts, tab_dnc = st.tabs(
    ["⚙️ Setup", "🏢 Companies", "✍️ Pitch", "▶️ Run", "📧 Drafts", "🚫 Do-not-contact"]
)


# ---------------------------------------------------------------- Setup
with tab_setup:
    st.subheader("Your details & optional integrations")
    st.write(
        "Fill in your details below. API keys are **optional** — the app works "
        "without them using built-in fallbacks. Everything is saved locally."
    )
    env = config.current_env()

    with st.form("setup_form"):
        st.markdown("**Your identity** (used in every proposal + signature)")
        c1, c2 = st.columns(2)
        env["SENDER_NAME"] = c1.text_input("Your name", env["SENDER_NAME"])
        env["SENDER_COMPANY"] = c2.text_input("Your company / agency", env["SENDER_COMPANY"])
        env["SENDER_EMAIL"] = c1.text_input("Your email (the 'From' address)", env["SENDER_EMAIL"])
        env["SENDER_PHONE"] = c2.text_input("Phone", env["SENDER_PHONE"])
        env["SENDER_WEBSITE"] = c1.text_input("Website", env["SENDER_WEBSITE"])
        env["SENDER_ADDRESS"] = c2.text_input(
            "Physical address (required for anti-spam / POPIA)", env["SENDER_ADDRESS"]
        )

        st.markdown("---")
        st.markdown("**Email finding** — add a [Hunter.io](https://hunter.io) key for real emails (free tier available)")
        env["HUNTER_API_KEY"] = st.text_input("Hunter.io API key", env["HUNTER_API_KEY"], type="password")

        st.markdown("**Proposal writing** — optionally use an AI model for richer, personalised proposals")
        provider = st.selectbox(
            "AI provider", ["", "anthropic", "openai"],
            index=["", "anthropic", "openai"].index(env["LLM_PROVIDER"]) if env["LLM_PROVIDER"] in ("", "anthropic", "openai") else 0,
            format_func=lambda x: {"": "None (use template)", "anthropic": "Anthropic (Claude)", "openai": "OpenAI (GPT)"}[x],
        )
        env["LLM_PROVIDER"] = provider
        cc1, cc2 = st.columns(2)
        env["ANTHROPIC_API_KEY"] = cc1.text_input("Anthropic API key", env["ANTHROPIC_API_KEY"], type="password")
        env["OPENAI_API_KEY"] = cc2.text_input("OpenAI API key", env["OPENAI_API_KEY"], type="password")

        st.markdown("---")
        st.markdown("**Sending** — default is safe **Draft** mode (nothing is sent)")
        mode = st.radio(
            "What should the app do with proposals?",
            ["draft", "smtp"],
            index=0 if env["SEND_MODE"] != "smtp" else 1,
            format_func=lambda x: "Draft only (review before sending)" if x == "draft" else "Actually send via email server (SMTP)",
            horizontal=True,
        )
        env["SEND_MODE"] = mode
        s1, s2 = st.columns(2)
        env["SMTP_HOST"] = s1.text_input("SMTP host (e.g. smtp.gmail.com)", env["SMTP_HOST"])
        env["SMTP_PORT"] = s2.text_input("SMTP port", env["SMTP_PORT"])
        env["SMTP_USERNAME"] = s1.text_input("SMTP username", env["SMTP_USERNAME"])
        env["SMTP_PASSWORD"] = s2.text_input("SMTP password", env["SMTP_PASSWORD"], type="password")
        env["DAILY_SEND_LIMIT"] = st.text_input(
            "Max emails to process per run", env["DAILY_SEND_LIMIT"]
        )

        submitted = st.form_submit_button("💾 Save settings", type="primary")
        if submitted:
            config.save_env(env)
            st.success("Settings saved!")

    if config.settings.send_mode == "smtp":
        st.warning(
            "⚠️ **Send mode is ON.** Real emails will be sent when you run "
            "'Generate proposals'. Switch back to Draft mode to only preview."
        )


# ------------------------------------------------------------ Companies
with tab_companies:
    st.subheader("Target companies")
    st.write(
        "Add or edit the brands you want to reach. **category** should be one of "
        "`alcohol`, `film_tv`, or `fashion`. The **contact** column is optional — "
        "a decision-maker's name (e.g. from LinkedIn) helps find their email."
    )
    rows = service.load_companies_rows()
    df = pd.DataFrame(rows, columns=service.COMPANY_COLUMNS) if rows else pd.DataFrame(columns=service.COMPANY_COLUMNS)
    edited = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "category": st.column_config.SelectboxColumn(
                "category", options=["alcohol", "film_tv", "fashion"], required=True
            ),
        },
        key="companies_editor",
    )
    if st.button("💾 Save companies", type="primary"):
        count = service.save_companies_rows(edited.to_dict("records"))
        st.success(f"Saved {count} companies.")


# ---------------------------------------------------------------- Pitch
with tab_pitch:
    st.subheader("What you're offering")
    st.write("This text is woven into every proposal. Make it sound like you.")
    offer, angles = proposal.load_pitch()
    with st.form("pitch_form"):
        offer_in = st.text_area(
            "Your core offer (completes the sentence \"We offer …\")",
            offer, height=100,
        )
        st.markdown("**Category-specific angles** — a tailored hook per brand type")
        alcohol_in = st.text_area("Alcohol brands", angles.get("alcohol", ""), height=90)
        film_in = st.text_area("Film & TV brands", angles.get("film_tv", ""), height=90)
        fashion_in = st.text_area("Fashion brands", angles.get("fashion", ""), height=90)
        if st.form_submit_button("💾 Save pitch", type="primary"):
            proposal.save_pitch(
                offer_in,
                {"alcohol": alcohol_in, "film_tv": film_in, "fashion": fashion_in},
            )
            st.success("Pitch saved!")


# ------------------------------------------------------------------ Run
with tab_run:
    st.subheader("Run the pipeline")
    st.write(
        "**Step 1:** find decision-maker emails for your companies.  \n"
        "**Step 2:** generate a proposal for each and prepare the email."
    )
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔎 Step 1 — Find contacts", use_container_width=True):
            log = st.empty()
            messages: list[str] = []

            def _p(m: str) -> None:
                messages.append(m)
                log.code("\n".join(messages))

            with st.spinner("Searching…"):
                service.find_contacts(progress=_p)
            st.success("Done finding contacts. See the results table below.")

    with col2:
        verb = "Send" if config.settings.send_mode == "smtp" else "Draft"
        if st.button(f"✍️ Step 2 — Generate proposals ({verb})", use_container_width=True):
            log2 = st.empty()
            messages2: list[str] = []

            def _p2(m: str) -> None:
                messages2.append(m)
                log2.code("\n".join(messages2))

            with st.spinner("Writing proposals…"):
                service.generate_drafts(progress=_p2)
            st.success("Done. Check the Drafts tab to review.")

    st.markdown("### Current leads")
    leads = service.load_leads()
    if leads:
        show_cols = ["company", "category", "contact_name", "email",
                     "email_confidence", "status"]
        ldf = pd.DataFrame(leads)
        ldf = ldf[[c for c in show_cols if c in ldf.columns]]
        st.dataframe(ldf, use_container_width=True, hide_index=True)
    else:
        st.info("No leads yet — run Step 1.")


# --------------------------------------------------------------- Drafts
with tab_drafts:
    st.subheader("Review proposal drafts")
    drafts = service.list_drafts()
    if not drafts:
        st.info("No drafts yet. Run Step 2 on the Run tab.")
    else:
        names = [d["name"] for d in drafts]
        choice = st.selectbox("Pick a draft to preview", names)
        chosen = next((d for d in drafts if d["name"] == choice), None)
        if chosen:
            st.code(service.read_draft(chosen["path"]), language="text")
            st.caption(
                "In Draft mode these are saved as .eml files you can open in "
                "your email client. Turn on Send mode in Setup to send automatically."
            )


# ------------------------------------------------------- Do-not-contact
with tab_dnc:
    st.subheader("Do-not-contact list (POPIA / opt-outs)")
    st.write(
        "Anyone here is **never** contacted. Add addresses that opt out, "
        "bounce, or that you simply want to exclude."
    )
    new_email = st.text_input("Add an email or domain to suppress")
    if st.button("Add to do-not-contact"):
        if new_email.strip():
            service.add_suppression(new_email.strip())
            st.success(f"Added {new_email.strip()}.")
        else:
            st.warning("Enter an email or domain first.")

    current = service.load_suppression()
    if current:
        st.dataframe(pd.DataFrame({"suppressed": current}),
                     use_container_width=True, hide_index=True)
    else:
        st.info("The list is empty.")
