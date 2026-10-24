"""GeoCapital — application Streamlit.

Lancement local :
    py -m streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from geocapital import ui

PAGES = [
    "Carte vivante",
    "Fiche pays",
    "Comparateur",
    "Décodeur",
    "Portefeuille",
    "Progression",
    "Sources & méthode",
]

ICONS = {
    "Carte vivante": "◉",
    "Fiche pays": "▤",
    "Comparateur": "⇄",
    "Décodeur": "⌁",
    "Portefeuille": "◫",
    "Progression": "✦",
    "Sources & méthode": "◎",
}


def _init_state() -> None:
    from geocapital.data import countries

    st.session_state.setdefault("nav", "Carte vivante")
    st.session_state.setdefault("country_id", "usa")
    st.session_state.setdefault("profile", "Équilibré")
    st.session_state.setdefault("map_metric", "Attractivité")
    st.session_state.setdefault("compare_ids", ["usa", "china"])
    st.session_state.setdefault("decoder_country", "usa")
    st.session_state.setdefault("explored", [])
    st.session_state.setdefault("quiz_correct", {})
    for country in countries():
        st.session_state.setdefault(f"amount_{country['id']}", 10000)
    if st.session_state.get("nav") not in PAGES:
        st.session_state["nav"] = "Carte vivante"


def _sidebar() -> None:
    from geocapital import ai
    from geocapital.data import country_by_id, load_data

    explored = st.session_state.get("explored", [])
    profile = st.session_state.get("profile", "Équilibré")
    completion = len(explored) / 10 * 100
    quiz_passed = sum(1 for value in st.session_state.get("quiz_correct", {}).values() if value)
    current = country_by_id(st.session_state.get("country_id", "usa"))

    with st.sidebar:
        st.markdown(
            """
            <div class="gc-brand">
              <div class="gc-brand-row">
                <div class="gc-brand-mark">◍</div>
                <div>
                  <div class="gc-brand-title">GeoCapital</div>
                  <div class="gc-brand-sub">Passé · Risque · Décision</div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="gc-side-label">Navigation</div>', unsafe_allow_html=True)
        st.radio(
            "Navigation",
            PAGES,
            format_func=lambda page: f"{ICONS.get(page, '·')}  {page}",
            key="nav",
            label_visibility="collapsed",
        )

        st.markdown('<div class="gc-side-label">Votre parcours</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="gc-side-progress">
              <div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px">
                <span class="gc-side-muted">Carte mentale</span>
                <strong>{len(explored)}/10</strong>
              </div>
              <div class="gc-progress"><div style="width:{completion:.1f}%"></div></div>
              <div class="gc-side-muted">Profil {profile} · {quiz_passed} quiz réussis</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if current:
            st.markdown(
                f'<div style="margin-top:10px;color:#7f8ea4;font-size:.72rem;line-height:1.5">Dernière fiche : {current["flag"]} <strong style="color:#c8d4e3">{current["name"]}</strong></div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div class="gc-side-label">Moteur</div>', unsafe_allow_html=True)
        if ai.is_available():
            st.markdown('<span class="gc-chip green">● IA connectée · Claude Haiku</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="gc-chip">○ Mode éditorial · IA optionnelle</span>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="gc-side-muted" style="margin-top:10px">{load_data().get("app", {}).get("last_update", "Données 2024-2025")}<br>Prototype pédagogique · v1.0</div>',
            unsafe_allow_html=True,
        )


def main() -> None:
    st.set_page_config(
        page_title="GeoCapital — Passé, risque, décision",
        page_icon="🌍",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    ui.inject_css()
    _init_state()
    _sidebar()

    # Imports après set_page_config : les modules de vues utilisent Streamlit.
    from views import (
        comparator_page,
        country_page,
        decoder_page,
        map_page,
        methodology_page,
        portfolio_page,
        progress_page,
    )

    page = st.session_state.get("nav", "Carte vivante")
    routes = {
        "Carte vivante": map_page.render,
        "Fiche pays": country_page.render,
        "Comparateur": comparator_page.render,
        "Décodeur": decoder_page.render,
        "Portefeuille": portfolio_page.render,
        "Progression": progress_page.render,
        "Sources & méthode": methodology_page.render,
    }
    routes.get(page, map_page.render)()


if __name__ == "__main__":
    main()
