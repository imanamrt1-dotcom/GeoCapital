"""Module 6 — Progression et carte mentale."""

from __future__ import annotations

import streamlit as st

from geocapital import ui
from geocapital.data import countries
from geocapital.scoring import VERDICT_STYLES, overall_score


def _go_country(country_id: str) -> None:
    st.session_state["country_id"] = country_id
    st.session_state["nav"] = "Fiche pays"


def _reset_progress() -> None:
    st.session_state["explored"] = []
    st.session_state["quiz_correct"] = {}
    for key in list(st.session_state.keys()):
        if key.startswith("quiz_choice_") or key.startswith("quiz_result_"):
            del st.session_state[key]


def render() -> None:
    all_countries = countries()
    explored = set(st.session_state.get("explored", []))
    quiz_correct = st.session_state.get("quiz_correct", {})
    correct_count = sum(1 for value in quiz_correct.values() if value)
    profile = st.session_state.get("profile", "Équilibré")

    ui.page_head(
        "Ma progression",
        "Une carte mentale se remplit pays après pays.",
        "GeoCapital ne récompense pas le temps passé : il récompense la compréhension. Chaque fiche lue et chaque quiz réussi ajoute un pays à votre carte mentale.",
    )

    completion = len(explored) / len(all_countries) * 100 if all_countries else 0
    explored_scores = [
        overall_score(country, profile)["score"] for country in all_countries if country["id"] in explored
    ]
    average = sum(explored_scores) / len(explored_scores) if explored_scores else 0

    top_cols = st.columns([1.1, 1, 1, 1])
    with top_cols[0]:
        ui.kpi(f"{len(explored)}<small>/10</small>", "pays explorés", f"{completion:.0f} % de la carte")
    with top_cols[1]:
        ui.kpi(f"{correct_count}<small>/10</small>", "quiz réussis", "Une notion par pays")
    with top_cols[2]:
        ui.kpi(f"{average:.0f}<small>/100</small>", "score moyen exploré", f"Profil {profile}")
    with top_cols[3]:
        ui.kpi(f"{len(all_countries) - len(explored)}", "pays restants", "À vous de choisir le prochain")

    st.markdown(
        f"""
        <div class="gc-card" style="margin-top:14px">
          <div style="display:flex;justify-content:space-between;align-items:baseline;gap:10px">
            <div><div class="gc-eyebrow">Votre carte mentale</div><h4 style="font-size:1rem">Progression globale</h4></div>
            <div style="color:#e6b86b;font-weight:800">{completion:.0f} %</div>
          </div>
          <div class="gc-progress"><div style="width:{completion:.1f}%"></div></div>
          <div class="gc-small">Comprendre un pays ne veut pas dire l'aimer. L'objectif est de savoir pourquoi vous l'incluez ou l'excluez.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    ui.section_title("Badges", "la progression, pas la performance")
    badges = [
        ("Premier pas", len(explored) >= 1, "1 pays exploré"),
        ("Curieux", len(explored) >= 3, "3 pays explorés"),
        ("Cartographe", len(explored) >= 5, "5 pays explorés"),
        ("Tour du monde", len(explored) >= 10, "10 pays explorés"),
        ("Quiz solide", correct_count >= 5, "5 quiz réussis"),
    ]
    badge_cols = st.columns(5)
    for col, (label, active, note) in zip(badge_cols, badges):
        with col:
            st.markdown(
                f'<div class="gc-badge {"on" if active else ""}" style="width:100%;justify-content:center;padding:12px 8px;text-align:center;display:flex;flex-direction:column;gap:3px"><span>{"★" if active else "☆"} {ui.esc(label)}</span><span style="font-weight:500;font-size:.62rem;opacity:.7">{ui.esc(note)}</span></div>',
                unsafe_allow_html=True,
            )

    ui.section_title("Les 10 pays", "votre état d'avancement")
    groups = ["Développé", "Émergent", "Golfe", "Frontière"]
    group_cols = st.columns(4)
    for col, group in zip(group_cols, groups):
        with col:
            st.markdown(f'<div class="gc-eyebrow" style="margin-bottom:8px">{ui.esc(group)}</div>', unsafe_allow_html=True)
            for country in [c for c in all_countries if c["group"] == group]:
                done = country["id"] in explored
                quiz = quiz_correct.get(country["id"])
                result = overall_score(country, profile)
                status = "Exploré" if done else "À découvrir"
                quiz_text = "Quiz réussi" if quiz else "Quiz à faire" if done else "Fiche à ouvrir"
                st.markdown(
                    f"""
                    <div class="gc-tile {'done' if done else ''}" style="min-height:132px;padding:13px">
                      <div class="gc-tile-top">
                        <span class="gc-tile-flag">{country['flag']}</span>
                        <span class="gc-chip {'green' if done else ''}" style="font-size:.6rem">{'✓' if done else '○'} {ui.esc(status)}</span>
                      </div>
                      <h4 style="font-size:.86rem">{ui.esc(country['name'])}</h4>
                      <p>{ui.esc(quiz_text)} · score {result['score']:.0f}/100</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.button(
                    "Revoir" if done else "Ouvrir",
                    key=f"progress_open_{country['id']}",
                    width="stretch",
                    on_click=_go_country,
                    args=(country["id"],),
                )

    unvisited = [c for c in all_countries if c["id"] not in explored]
    ui.section_title("Prochaine étape", "une suggestion, pas une obligation")
    if unvisited:
        ranked = sorted(unvisited, key=lambda c: overall_score(c, profile)["score"], reverse=True)
        next_country = ranked[0]
        next_col, button_col = st.columns([3, 1])
        with next_col:
            st.markdown(
                f"""
                <div class="gc-card gc-card-gold">
                  <div class="gc-eyebrow">À explorer ensuite</div>
                  <h4 style="font-size:1.05rem">{next_country['flag']} {ui.esc(next_country['name'])} · {overall_score(next_country, profile)['score']:.0f}/100</h4>
                  <p>{ui.esc(next_country.get('headline', ''))}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with button_col:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            st.button(
                "Ouvrir la fiche",
                key="progress_next",
                type="primary",
                width="stretch",
                on_click=_go_country,
                args=(next_country["id"],),
            )
    else:
        ui.callout("Vous avez parcouru les dix pays. Revenez sur les fiches pour comparer les trajectoires et tester les trois profils.", "green")

    with st.expander("Réinitialiser ma progression", expanded=False):
        st.caption("Cette action efface uniquement les pays explorés et les quiz de cette session. Le portefeuille n'est pas modifié.")
        confirm = st.checkbox("Je confirme la réinitialisation.", key="confirm_reset_progress")
        st.button(
            "Réinitialiser",
            key="reset_progress",
            disabled=not confirm,
            on_click=_reset_progress,
        )

    ui.callout(
        "La note d'un pays dépend de votre profil. Un pays peut être « Investir » pour un profil audacieux et « Attendre » pour un profil prudent. "
        "La progression ne mesure donc pas une vérité absolue, mais votre capacité à lire le compromis risque/rendement.",
        "blue",
    )
    ui.footer()
