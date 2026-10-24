"""Module 5 — Le décodeur d'actualité."""

from __future__ import annotations

import streamlit as st

from geocapital import ai, ui
from geocapital.data import countries, country_by_id, load_events
from geocapital.scoring import VERDICT_STYLES, overall_score, required_return


def _go_country(country_id: str) -> None:
    st.session_state["country_id"] = country_id
    st.session_state["nav"] = "Fiche pays"


def render() -> None:
    ui.page_head(
        "Décodeur d'actualité",
        "Un fait divers n'est pas une causalité.",
        "Choisissez un événement. GeoCapital déroule la chaîne : fait → économie → finance → gagnants et perdants. Chaque étape renvoie à une notion et à un précédent historique du pays.",
    )

    events = load_events()
    valid_ids = [c["id"] for c in countries()]
    if st.session_state.get("decoder_country") not in valid_ids:
        st.session_state["decoder_country"] = valid_ids[0]

    control_a, control_b = st.columns([1, 2.2])
    with control_a:
        selected_country = st.selectbox(
            "Pays",
            valid_ids,
            format_func=lambda cid: f"{country_by_id(cid)['flag']} {country_by_id(cid)['name']}",
            key="decoder_country",
        )
    available = [event for event in events if event.get("country") == selected_country]
    with control_b:
        if not available:
            st.warning("Aucun événement préparé pour ce pays.")
            return
        event_id = st.selectbox(
            "Événement récent",
            [event["id"] for event in available],
            format_func=lambda eid: next(
                f"{event['date']} · {event['title']}" for event in available if event["id"] == eid
            ),
            key=f"decoder_event_{selected_country}",
        )
    event = next(event for event in available if event["id"] == event_id)
    country = country_by_id(selected_country)
    result = overall_score(country, st.session_state.get("profile", "Équilibré"))
    ke = required_return(country)

    st.markdown(
        f"""
        <div class="gc-card gc-card-gold" style="margin:10px 0 16px">
          <div style="display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap;align-items:flex-start">
            <div>
              <div class="gc-eyebrow">{ui.esc(event.get('category'))} · {ui.esc(country['flag'])} {ui.esc(country['name'])}</div>
              <h2 style="font-family:'DM Serif Display',Georgia,serif;font-weight:400;color:#f8f4e9;font-size:clamp(1.5rem,2.6vw,2.25rem);margin:.25rem 0 .55rem;line-height:1.1">{ui.esc(event.get('title'))}</h2>
              <p style="color:#aab7c9;font-size:.88rem;max-width:780px;margin:0">{ui.esc(event.get('summary'))}</p>
            </div>
            <div style="text-align:right">
              <span class="gc-chip gold">{ui.esc(event.get('date'))}</span>
              <div class="gc-small" style="margin-top:7px">Source : {ui.esc(event.get('source'))}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    main_col, side_col = st.columns([1.55, 1], gap="large")
    with main_col:
        ui.section_title("La chaîne causale", "4 étapes, aucune saute")
        ui.chain_steps(event.get("chain", []))
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        ui.callout(
            "La finance ne réagit pas à l'événement lui-même, mais à ce qu'il change dans les flux, les taux, les profits et le risque perçu. "
            "C'est pour cela qu'un même fait peut faire monter un actif et en faire baisser un autre.",
            "blue",
        )

        with st.expander("Les concepts nécessaires", expanded=False):
            for concept in event.get("concepts", []):
                st.markdown(
                    f"**{ui.esc(concept['term'])}** — {ui.esc(concept['definition'])}"
                )

        with st.expander("Décoder avec Claude Haiku", expanded=False):
            if not ai.is_available():
                st.caption(
                    "Le décodage éditorial ci-dessus est complet et ne dépend pas d'une API. "
                    "Ajoutez `ANTHROPIC_API_KEY` pour faire reformuler la chaîne causale par l'IA, à partir des mêmes faits."
                )
            else:
                st.caption("L'IA reçoit uniquement l'événement, la chaîne et l'écho historique préparés.")
                if st.button("Générer une explication", key=f"ai_event_{event['id']}", type="primary"):
                    with st.spinner("Relecture de la chaîne causale..."):
                        text = ai.decode_event(event, country)
                    if text:
                        st.markdown(text)
                    else:
                        st.warning("L'appel IA n'a pas abouti. Le contenu éditorial reste disponible.")

    with side_col:
        ui.section_title("Qui gagne, qui perd", "entreprises, actifs, pays exposés")
        ui.winners_losers(event.get("winners", []), event.get("losers", []))

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        echo = event.get("history", {})
        st.markdown(
            f"""
            <div class="gc-card">
              <div class="gc-eyebrow">Écho historique · {ui.esc(echo.get('year'))}</div>
              <h4 style="font-size:1rem">{ui.esc(echo.get('title'))}</h4>
              <p style="font-size:.8rem;line-height:1.65">{ui.esc(echo.get('text'))}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        tone = VERDICT_STYLES[result["verdict"]]["tone"]
        st.markdown(
            f"""
            <div class="gc-card">
              <div class="gc-eyebrow">Lien avec la fiche pays</div>
              <h4 style="font-size:1rem">{ui.esc(country['name'])}</h4>
              <div style="display:flex;gap:8px;flex-wrap:wrap;margin:9px 0">
                {ui.verdict_badge(result['verdict'], tone)}
                <span class="gc-chip">Score {result['score']:.0f}/100</span>
                <span class="gc-chip">Ke {ke['ke']:.1f} %</span>
              </div>
              <p style="font-size:.78rem">Le même choc n'a pas le même effet selon la dette, les réserves et la crédibilité de la banque centrale.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.button(
            "Ouvrir la fiche complète",
            key=f"decoder_open_{country['id']}",
            width="stretch",
            on_click=_go_country,
            args=(country["id"],),
        )

    ui.callout(
        "Règle de fiabilité : chaque chiffre affiché vient de la base GeoCapital. L'IA peut expliquer, reformuler ou relier, mais elle n'a pas le droit d'inventer une donnée. "
        "Quand une donnée manque, le décodeur le signale et le traite comme un risque.",
        "green",
    )
    ui.footer()
