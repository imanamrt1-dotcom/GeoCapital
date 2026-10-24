"""Module 2 à 4 — Fiche pays, tableau de bord, score et verdict."""

from __future__ import annotations

from typing import Any

import streamlit as st

from geocapital import ai, ui
from geocapital.data import (
    INDICATOR_LABELS,
    INDICATOR_ORDER,
    countries,
    country_by_id,
    indicator_display,
    indicator_meta,
    load_data,
)
from geocapital.scoring import (
    COMPONENT_LABELS,
    PROFILES,
    VERDICT_STYLES,
    component_scores,
    indicator_status,
    overall_score,
    required_return,
    risk_label,
    score_breakdown,
    top_reasons,
)


def _go_compare(country_id: str) -> None:
    current = st.session_state.get("compare_ids", [])
    others = [item for item in current if item != country_id]
    fallback = "china" if country_id != "china" else "usa"
    peers = ([others[0]] if others else [fallback])
    st.session_state["compare_ids"] = [country_id, peers[0]][:2]
    st.session_state["nav"] = "Comparateur"


def _go_decoder(country_id: str) -> None:
    st.session_state["decoder_country"] = country_id
    st.session_state["nav"] = "Décodeur"


def _institution_card(institutions: dict[str, Any]) -> None:
    labels = {
        "regime": "Régime",
        "executive": "Exécutif",
        "legislature": "Législatif",
        "central_bank": "Banque centrale",
        "currency": "Devise",
        "law": "Cadre juridique",
        "fact": "À retenir",
    }
    blocks = []
    for key, label in labels.items():
        value = institutions.get(key)
        if not value:
            continue
        blocks.append(
            f"""
            <div style="padding:9px 0;border-top:1px solid rgba(148,163,184,.11)">
              <div style="color:#73849b;font-size:.62rem;letter-spacing:.1em;text-transform:uppercase;font-weight:800;margin-bottom:2px">{ui.esc(label)}</div>
              <div style="color:#c4d0df;font-size:.79rem;line-height:1.45">{ui.esc(value)}</div>
            </div>
            """
        )
    st.markdown(
        '<div class="gc-card" style="padding:17px"><h4 style="margin-bottom:4px">Institutions & pouvoir</h4>'
        + "".join(blocks)
        + "</div>",
        unsafe_allow_html=True,
    )


def _profile_scores(country: dict[str, Any]) -> dict[str, float]:
    return {profile: overall_score(country, profile)["score"] for profile in PROFILES}


def _render_reasons(country: dict[str, Any], profile: str) -> None:
    blocks = []
    for reason in top_reasons(country, profile):
        icon = "↗" if reason["kind"] == "positive" else "↘"
        color = "#4ade80" if reason["kind"] == "positive" else "#fb7185"
        blocks.append(
            f"""
            <div style="display:flex;gap:11px;padding:10px 0;border-top:1px solid rgba(148,163,184,.11)">
              <div style="color:{color};font-weight:800;font-size:1rem;margin-top:1px">{icon}</div>
              <div>
                <div style="color:#e4ecf6;font-size:.82rem;font-weight:750;margin-bottom:2px">{ui.esc(reason['title'])}</div>
                <div style="color:#98a8bd;font-size:.76rem;line-height:1.5">{ui.esc(reason['text'])}</div>
              </div>
            </div>
            """
        )
    st.markdown("".join(blocks), unsafe_allow_html=True)


def _ai_country_block(country: dict[str, Any], result: dict[str, Any], suffix: str = "story") -> None:
    with st.expander("Approfondir avec Claude Haiku", expanded=False):
        if not ai.is_available():
            st.caption(
                "Mode éditorial : la synthèse GeoCapital ci-dessus fonctionne sans IA. "
                "Pour activer l'analyse générative, ajoutez `ANTHROPIC_API_KEY` dans les secrets Streamlit. "
                "L'IA ne reçoit que les données validées de cette fiche."
            )
            return
        st.caption("L'IA reformule les faits de la fiche. Elle ne crée aucun chiffre et ne remplace pas les sources.")
        if st.button("Générer la synthèse", key=f"ai_brief_{country['id']}_{suffix}", type="primary"):
            with st.spinner("Lecture de la fiche et rédaction..."):
                text = ai.country_brief(country, result)
            if text:
                st.markdown(text)
            else:
                st.warning("L'appel IA n'a pas abouti. Le contenu éditorial reste disponible.")


def _render_quiz(country: dict[str, Any]) -> None:
    question = country.get("quiz", {})
    if not question:
        return
    cid = country["id"]
    st.markdown(
        f"""
        <div class="gc-card gc-card-gold" style="margin-bottom:14px">
          <div class="gc-eyebrow">Quiz éclair · 1 question</div>
          <h4 style="font-size:1.14rem;line-height:1.4">{ui.esc(question.get('question'))}</h4>
        </div>
        """,
        unsafe_allow_html=True,
    )
    choice = st.radio(
        "Votre réponse",
        question.get("options", []),
        index=None,
        key=f"quiz_choice_{cid}",
        label_visibility="collapsed",
    )
    validate = st.button("Valider ma réponse", key=f"quiz_btn_{cid}", type="primary")
    if validate:
        if choice is None:
            st.warning("Choisissez une réponse avant de valider.")
        else:
            correct = question["options"].index(choice) == question["answer"]
            st.session_state["quiz_correct"][cid] = correct
            st.session_state[f"quiz_result_{cid}"] = {"correct": correct, "choice": choice}

    saved = st.session_state.get(f"quiz_result_{cid}")
    if saved and saved.get("choice") == choice:
        correct = bool(saved["correct"])
        if correct:
            st.success("Bonne réponse. Vous pouvez cocher ce pays comme compris.")
        else:
            st.error("Pas tout à fait. Lisez l'explication, puis réessayez.")
        st.markdown(
            f'<div class="gc-callout {"green" if correct else "red"}"><strong>Pourquoi ?</strong> {ui.esc(question.get("explanation"))}</div>',
            unsafe_allow_html=True,
        )
        if ai.is_available():
            if st.button("Expliquer avec l'IA", key=f"ai_quiz_{cid}"):
                with st.spinner("Explication..."):
                    text = ai.explain_quiz(country, question, correct)
                if text:
                    st.markdown(text)
        else:
            st.caption("Astuce : l'explication ci-dessus est éditoriale et vérifiée. L'IA peut la reformuler si une clé API est configurée.")

    if st.session_state["quiz_correct"].get(cid):
        st.markdown('<span class="gc-chip green">Quiz réussi</span>', unsafe_allow_html=True)


def render() -> None:
    all_countries = countries()
    ids = [c["id"] for c in all_countries]
    if st.session_state.get("country_id") not in ids:
        st.session_state["country_id"] = ids[0]

    select_col, profile_col = st.columns([1.5, 1.7])
    with select_col:
        selected_id = st.selectbox(
            "Choisir un pays",
            ids,
            format_func=lambda cid: f"{country_by_id(cid)['flag']} {country_by_id(cid)['name']}",
            key="country_id",
        )
    with profile_col:
        profile = st.radio(
            "Profil d'investisseur",
            list(PROFILES.keys()),
            horizontal=True,
            key="profile",
        )

    country = country_by_id(selected_id)
    if country is None:
        st.error("Pays introuvable.")
        return

    if selected_id not in st.session_state["explored"]:
        st.session_state["explored"] = sorted([*st.session_state["explored"], selected_id])

    result = overall_score(country, profile)
    result["verdict_tone"] = VERDICT_STYLES[result["verdict"]]["tone"]
    ke = required_return(country)
    scores = _profile_scores(country)
    rank = sorted(
        [overall_score(c, profile)["score"] for c in all_countries],
        reverse=True,
    ).index(result["score"]) + 1

    ui.country_hero(country, result)
    action_a, action_b, action_c, action_d = st.columns([1, 1, 1, 2.2])
    with action_a:
        st.button("Comparer", key=f"country_compare_{selected_id}", width="stretch", on_click=_go_compare, args=(selected_id,))
    with action_b:
        st.button("Décodeur", key=f"country_decoder_{selected_id}", width="stretch", on_click=_go_decoder, args=(selected_id,))
    with action_c:
        st.markdown(
            f'<div class="gc-chip" style="margin-top:4px">Rang {rank}/10 · profil {ui.esc(profile)}</div>',
            unsafe_allow_html=True,
        )
    with action_d:
        st.markdown(
            f'<div style="text-align:right;color:#7f8fa5;font-size:.72rem;margin-top:8px">Dernière mise à jour des données : {ui.esc(load_data().get("app", {}).get("last_update", "2024-2025"))}</div>',
            unsafe_allow_html=True,
        )

    tab_story, tab_dashboard, tab_score, tab_quiz = st.tabs(
        ["Récit & institutions", "Tableau de bord", "Score & verdict", "Quiz"]
    )

    with tab_story:
        ui.callout(country.get("summary", ""), "gold")
        left, right = st.columns([1.65, 1], gap="large")
        with left:
            ui.section_title("Frise historique", "les dates qui expliquent le risque actuel")
            ui.timeline(country.get("history", []))
        with right:
            _institution_card(country.get("institutions", {}))
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            current = result["components"]
            st.markdown(
                f"""
                <div class="gc-card" style="padding:17px">
                  <div class="gc-eyebrow">Du passé au risque</div>
                  <h4 style="font-size:.94rem">Ce récit se lit dans les chiffres</h4>
                  <p style="font-size:.78rem;line-height:1.6">
                    Le passé pèse sur la solvabilité ({current['solvabilite']:.0f}/100), la stabilité ({current['stabilite']:.0f}/100)
                    et la qualité des institutions ({current['institutions']:.0f}/100). C'est cette chaîne que le score transforme en décision.
                  </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        ui.section_title("Relations & dépendances", "alliés, rivaux, points de fragilité")
        rel = country.get("relations", {})
        rel_cols = st.columns(3)
        with rel_cols[0]:
            ui.relation_column("Alliés", "🤝", rel.get("allies", []))
        with rel_cols[1]:
            ui.relation_column("Rivaux", "⚔️", rel.get("rivals", []))
        with rel_cols[2]:
            ui.relation_column("Dépendances", "🔗", rel.get("dependencies", []))

        ui.section_title("Ce qui pèse sur la décision", "forces, risques et portes d'entrée")
        strength_col, risk_col, opp_col = st.columns(3)
        with strength_col:
            st.markdown(
                '<div class="gc-card"><div class="gc-eyebrow">Forces</div><ul class="gc-list">'
                + "".join(f"<li>{ui.esc(item)}</li>" for item in country.get("strengths", []))
                + "</ul></div>",
                unsafe_allow_html=True,
            )
        with risk_col:
            st.markdown(
                '<div class="gc-card"><div class="gc-eyebrow">Risques</div><ul class="gc-list">'
                + "".join(f"<li>{ui.esc(item)}</li>" for item in country.get("risks", []))
                + "</ul></div>",
                unsafe_allow_html=True,
            )
        with opp_col:
            st.markdown(
                '<div class="gc-card"><div class="gc-eyebrow">Opportunités</div><ul class="gc-list">'
                + "".join(f"<li>{ui.esc(item)}</li>" for item in country.get("opportunities", []))
                + "</ul></div>",
                unsafe_allow_html=True,
            )

        _ai_country_block(country, result)

    with tab_dashboard:
        ui.section_title("Les 11 indicateurs", "feu vert, orange ou rouge")
        st.markdown(
            '<div class="gc-small" style="margin-bottom:12px">Chaque indicateur est daté et sourcé. La couleur est une grille de lecture GeoCapital, pas une opinion de marché en temps réel.</div>',
            unsafe_allow_html=True,
        )
        cols = st.columns(4)
        for index, key in enumerate(INDICATOR_ORDER):
            meta = indicator_meta(country, key)
            value, unit, date = indicator_display(country, key)
            status = indicator_status(country, key)
            note = meta.get("note", "")
            source = meta.get("source", "Source non renseignée")
            with cols[index % 4]:
                ui.indicator_card(
                    INDICATOR_LABELS[key],
                    value,
                    unit,
                    status,
                    note,
                    source,
                    date,
                )
                st.markdown("<div style='height:9px'></div>", unsafe_allow_html=True)

        if country["id"] in {"lebanon", "syria"}:
            ui.callout(
                "Ici, une donnée manquante n'est pas une case vide : c'est un signal de risque. "
                "Sans notation active ni CDS coté, le marché ne peut pas donner de prix fiable à la dette. GeoCapital bloque donc le verdict « Investir ».",
                "red",
            )

        ui.section_title("Le prix du risque", "formule de Damodaran")
        ke_cols = st.columns(4)
        with ke_cols[0]:
            ui.kpi("4,20 %", "Taux sans risque", "Référence : Trésor américain 10 ans")
        with ke_cols[1]:
            ui.kpi("4,50 %", "Prime de marché mature", "Actions vs obligations, Damodaran")
        with ke_cols[2]:
            ui.kpi(f"{ke['crp']:.1f} %", "Prime de risque pays", f"Calculée via {ke['crp_source']}")
        with ke_cols[3]:
            ui.kpi(f"{ke['ke']:.1f} %", "Rendement exigé Ke", "Taux minimal pour accepter ce risque")
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="gc-card">
              <div class="gc-eyebrow">Comment lire</div>
              <h4 style="font-size:.98rem">Ke = taux sans risque + bêta × prime de marché + prime pays</h4>
              <p style="font-size:.82rem;line-height:1.65;margin-top:6px">
                Pour {ui.esc(country['name'])}, le calcul donne {ke['risk_free']:.1f} % + 1,0 × {ke['erp']:.1f} % + {ke['crp']:.1f} % = <strong style="color:#e6b86b">{ke['ke']:.1f} %</strong>.
                Plus le risque perçu est élevé, plus l'investisseur doit exiger de rendement. Ce n'est pas un rendement promis : c'est un seuil de rentabilité exigé.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("Sources : FMI, banques centrales, agences de notation, marché CDS, Damodaran. Données arrondies et indicatives.")

    with tab_score:
        score_left, score_right = st.columns([1, 1.15], gap="large")
        with score_left:
            st.markdown(
                f"""
                <div class="gc-card">
                  <div class="gc-score-row">
                    {ui.ring(result['score'], 'score / 100')}
                    <div>
                      {ui.verdict_badge(result['verdict'], result['verdict_tone'])}
                      <div class="gc-verdict-sub">{ui.esc(result['verdict_reason'])}</div>
                      <div class="gc-small" style="margin-top:10px">Rang {rank}/10 · profil {ui.esc(profile)} · risque {result['risk']:.0f}/100 ({risk_label(result['risk']).lower()})</div>
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="gc-card">
                  <div class="gc-eyebrow">Les 3 raisons du verdict</div>
                  {''.join([f'<div style="padding:9px 0;border-top:1px solid rgba(148,163,184,.11)"><strong style="color:#e4ecf6;font-size:.82rem">{ui.esc(r["title"])}</strong><div style="color:#98a8bd;font-size:.76rem;line-height:1.5;margin-top:2px">{ui.esc(r["text"])}</div></div>' for r in top_reasons(country, profile)])}
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="gc-card gc-card-gold">
                  <div class="gc-eyebrow">Rendement exigé</div>
                  <div class="gc-ke"><strong>{ke['ke']:.1f} %</strong><span>Ke annuel</span></div>
                  <div class="gc-small" style="margin-top:7px">Taux sans risque {ke['risk_free']:.1f} % + prime mature {ke['erp']:.1f} % + prime pays {ke['crp']:.1f} % ({ui.esc(ke['crp_source'])}).</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with score_right:
            st.markdown(
                f"""
                <div class="gc-card">
                  <div class="gc-eyebrow">Décomposition transparente</div>
                  <h4 style="margin-bottom:14px">Cinq briques, une décision</h4>
                </div>
                """,
                unsafe_allow_html=True,
            )
            ui.component_bars(score_breakdown(country, profile))

            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="gc-card">
                  <div class="gc-eyebrow">Selon votre profil</div>
                  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:8px">
                    {''.join([f'<div style="text-align:center;padding:11px 5px;border-radius:12px;background:{"rgba(230,184,107,.12)" if p == profile else "rgba(255,255,255,.035)"};border:1px solid {"rgba(230,184,107,.3)" if p == profile else "rgba(148,163,184,.14)"}"><div style="color:#e6b86b;font-weight:800;font-size:1.25rem">{scores[p]:.0f}</div><div style="color:#8fa0b6;font-size:.65rem;text-transform:uppercase;letter-spacing:.08em">{ui.esc(p)}</div></div>' for p in PROFILES])}
                  </div>
                  <p style="font-size:.76rem;margin-top:10px;color:#8292a8;line-height:1.5">Le même pays ne convient pas à tout le monde. Le profil pondère différemment la croissance, la stabilité et la solvabilité.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            _ai_country_block(country, result, suffix="score")

            components = component_scores(country)
            weakest = min(components.items(), key=lambda item: item[1])
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            ui.callout(
                f"Point de vigilance principal : {COMPONENT_LABELS.get(weakest[0], weakest[0])} ({weakest[1]:.0f}/100). "
                "Le score est un outil de comparaison, pas une prévision. Une note élevée peut cacher un risque politique brutal.",
                "orange",
            )

    with tab_quiz:
        _render_quiz(country)

    ui.footer()
