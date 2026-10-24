"""Sources, méthode et limites."""

from __future__ import annotations

import streamlit as st

from geocapital import ui
from geocapital.data import load_data
from geocapital.scoring import EQUITY_BOND_VOL_RATIO, MATURE_ERP, PROFILES, RISK_FREE_RATE


def _go_map() -> None:
    st.session_state["nav"] = "Carte vivante"


def render() -> None:
    meta = load_data()
    ui.page_head(
        "Sources & méthode",
        "Un score n'a de valeur que si l'on peut l'expliquer.",
        "GeoCapital relie trois couches : l'histoire, les indicateurs et la décision financière. Cette page rend les règles visibles, y compris les limites.",
    )

    cols = st.columns(3)
    steps = [
        ("01 · Passé", "Le récit", "5 à 7 dates fondatrices, les institutions, les relations et les dépendances. Le passé n'explique pas tout, mais il éclaire les rigidités."),
        ("02 · Présent", "Les chiffres", "11 indicateurs datés et sourcés, traduits en feux vert/orange/rouge. Aucun chiffre n'est généré par l'IA."),
        ("03 · Décision", "Le prix du risque", "Score pondéré selon votre profil, rendement exigé Ke, verdict et trois raisons. La décision reste la vôtre."),
    ]
    for col, (eyebrow, title, text) in zip(cols, steps):
        with col:
            st.markdown(
                f"""
                <div class="gc-card" style="min-height:190px">
                  <div class="gc-eyebrow">{ui.esc(eyebrow)}</div>
                  <h4 style="font-family:'DM Serif Display',Georgia,serif;font-size:1.3rem;font-weight:400">{ui.esc(title)}</h4>
                  <p style="font-size:.82rem;line-height:1.65">{ui.esc(text)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    ui.section_title("Le score GeoCapital", "5 composantes, 100 points")
    st.markdown(
        """
        <table class="gc-table">
          <thead><tr><th>Composante</th><th>Ce qu'elle mesure</th><th>Entrées principales</th></tr></thead>
          <tbody>
            <tr><td class="gc-table-label">Dynamisme économique</td><td>Capacité à créer de la valeur et de l'emploi</td><td>Croissance du PIB, chômage, potentiel de croissance</td></tr>
            <tr><td class="gc-table-label">Stabilité macro</td><td>Prévisibilité des prix et de la monnaie</td><td>Inflation, taux réel, stabilité de la devise</td></tr>
            <tr><td class="gc-table-label">Solvabilité</td><td>Capacité à honorer la dette</td><td>Dette/PIB, notation, CDS</td></tr>
            <tr><td class="gc-table-label">Institutions</td><td>Qualité de l'État et capacité de rebond</td><td>Gouvernance, résilience historique</td></tr>
            <tr><td class="gc-table-label">Ouverture & affaires</td><td>Facilité à investir, exporter, s'implanter</td><td>Climat des affaires, ouverture commerciale</td></tr>
          </tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Les scores qualitatifs (gouvernance, résilience, climat des affaires, ouverture, stabilité devise) sont des évaluations GeoCapital explicites, calibrées à partir de sources publiques. Ils ne sont pas des données brutes.")

    ui.section_title("Les trois profils", "le même pays, trois lectures")
    header = "".join(f"<th>{ui.esc(profile)}</th>" for profile in PROFILES)
    rows = []
    for key, label in [
        ("dynamisme", "Dynamisme"),
        ("stabilite", "Stabilité"),
        ("solvabilite", "Solvabilité"),
        ("institutions", "Institutions"),
        ("ouverture", "Ouverture"),
    ]:
        cells = "".join(f"<td>{PROFILES[profile]['weights'][key]*100:.0f} %</td>" for profile in PROFILES)
        rows.append(f"<tr><td class='gc-table-label'>{label}</td>{cells}</tr>")
    st.markdown(
        f'<table class="gc-table"><thead><tr><th>Pondération</th>{header}</tr></thead><tbody>{"".join(rows)}</tbody></table>',
        unsafe_allow_html=True,
    )

    ui.section_title("Le rendement exigé", "Ke, méthode Damodaran")
    st.markdown(
        f"""
        <div class="gc-card gc-card-gold">
          <h4 style="font-family:'DM Serif Display',Georgia,serif;font-size:1.3rem;font-weight:400">Ke = taux sans risque + bêta × prime de marché + prime de risque pays</h4>
          <p style="margin-top:8px;font-size:.85rem;line-height:1.7">
            Taux sans risque retenu : <strong>{RISK_FREE_RATE:.2f} %</strong>. Prime de marché mature : <strong>{MATURE_ERP:.2f} %</strong>.
            Bêta de marché : <strong>1,0</strong>. La prime pays est le maximum entre le spread de notation et le spread CDS,
            multiplié par <strong>{EQUITY_BOND_VOL_RATIO:.1f}</strong> (ratio volatilité actions/obligations).
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="gc-small" style="margin-top:8px">Le Ke est un seuil de rendement exigé, pas une performance attendue. Il sert à comparer le prix du risque entre pays et à éviter de payer trop cher un actif risqué.</div>',
        unsafe_allow_html=True,
    )

    ui.section_title("Données manquantes", "le vide est une information")
    st.markdown(
        """
        <div class="gc-callout red">
          <strong>Liban et Syrie.</strong> Une notation absente, un CDS non coté ou des comptes publics non certifiés ne sont pas traités comme des cases neutres.
          Le score de solvabilité est pénalisé, la prime de risque est portée à un niveau élevé et le verdict « Investir » est bloqué.
          C'est une règle de prudence : quand le marché ne peut pas prix le risque, l'investisseur doit exiger une marge d'incertitude supplémentaire.
        </div>
        """,
        unsafe_allow_html=True,
    )

    ui.section_title("Le rôle de l'IA", "expliquer, jamais inventer")
    ai_cols = st.columns(2)
    with ai_cols[0]:
        st.markdown(
            """
            <div class="gc-card">
              <div class="gc-eyebrow">Ce que fait l'IA</div>
              <ul class="gc-list">
                <li>Reformuler la synthèse d'un pays.</li>
                <li>Décrypter un événement en chaîne causale.</li>
                <li>Expliquer le verdict à un débutant.</li>
                <li>Commenter une allocation fictive.</li>
                <li>Expliquer une réponse de quiz.</li>
              </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with ai_cols[1]:
        st.markdown(
            """
            <div class="gc-card">
              <div class="gc-eyebrow">Ce qu'elle ne fait pas</div>
              <ul class="gc-list">
                <li>Elle ne crée aucun chiffre, aucune date, aucune notation.</li>
                <li>Elle ne remplace pas les sources de la base.</li>
                <li>Elle ne donne pas de conseil personnalisé.</li>
                <li>Elle ne prédit pas les marchés.</li>
                <li>Elle ne comble pas une donnée manquante.</li>
              </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    ui.section_title("Sources", "la base GeoCapital")
    for source in meta.get("sources", []):
        st.markdown(
            f'<div style="padding:9px 0;border-bottom:1px solid rgba(148,163,184,.1)"><a href="{ui.esc(source.get("url"))}" target="_blank" style="font-size:.82rem;font-weight:650">{ui.esc(source.get("name"))}</a><div class="gc-small">{ui.esc(source.get("use"))}</div></div>',
            unsafe_allow_html=True,
        )
    st.caption(f"Mise à jour : {meta.get('app', {}).get('last_update', '2024-2025')}. Les valeurs sont arrondies, les millésimes peuvent différer d'un indicateur à l'autre, et les CDS sont des ordres de grandeur.")

    ui.section_title("Limites et avertissement", "à lire avant de décider")
    st.markdown(
        """
        <div class="gc-card">
          <ul class="gc-list">
            <li><strong>Pas de temps réel :</strong> les données sont préparées pour le MVP, pas actualisées automatiquement.</li>
            <li><strong>Pas de conseil en investissement :</strong> le score et le verdict sont pédagogiques et ne tiennent pas compte de votre situation personnelle.</li>
            <li><strong>Modèle simplifié :</strong> les corrélations et volatilités du portefeuille sont des estimations, pas un modèle de risque professionnel.</li>
            <li><strong>Risque politique :</strong> un score peut être démenti par un choc brutal, une sanction ou une guerre.</li>
            <li><strong>Qualitatif assumé :</strong> les scores de gouvernance et de résilience sont des jugements explicites, pas des mesures objectives.</li>
          </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    st.button("Retour à la carte vivante", type="primary", on_click=_go_map)
    ui.footer()
