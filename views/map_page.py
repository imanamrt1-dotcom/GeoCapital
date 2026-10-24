"""Module 1 — La carte vivante."""

from __future__ import annotations

from typing import Any

import plotly.graph_objects as go
import streamlit as st

from geocapital import ai, ui
from geocapital.data import countries
from geocapital.scoring import (
    PROFILES,
    VERDICT_STYLES,
    overall_score,
    required_return,
)

METRICS = {
    "Attractivité": "Score GeoCapital",
    "Risque maîtrisé": "Plus haut = risque plus faible",
    "Croissance": "Dynamisme économique",
    "Stabilité devise": "Score de stabilité de la devise",
}


def go_to_country(country_id: str) -> None:
    st.session_state["country_id"] = country_id
    st.session_state["nav"] = "Fiche pays"


def _metric_value(country: dict[str, Any], metric: str, profile: str) -> float:
    result = overall_score(country, profile)
    if metric == "Risque maîtrisé":
        return 100 - result["risk"]
    if metric == "Croissance":
        return result["components"]["dynamisme"]
    if metric == "Stabilité devise":
        return float(country.get("qualitative", {}).get("currency_stability", 50))
    return result["score"]


def _rows(profile: str) -> list[dict[str, Any]]:
    rows = []
    for country in countries():
        result = overall_score(country, profile)
        ke = required_return(country)
        rows.append(
            {
                "country": country,
                "score": result["score"],
                "risk": result["risk"],
                "verdict": result["verdict"],
                "tone": VERDICT_STYLES[result["verdict"]]["tone"],
                "ke": ke["ke"],
                "crp": ke["crp"],
            }
        )
    return rows


def _map_figure(rows: list[dict[str, Any]], metric: str, profile: str) -> go.Figure:
    values = [_metric_value(row["country"], metric, profile) for row in rows]
    custom = [
        [
            row["country"]["name"],
            f"{row['score']:.0f}",
            f"{row['ke']:.1f} %",
            f"{row['risk']:.0f}",
            row["verdict"],
        ]
        for row in rows
    ]
    fig = go.Figure(
        go.Choropleth(
            locations=[row["country"]["iso3"] for row in rows],
            z=values,
            customdata=custom,
            locationmode="ISO-3",
            colorscale=[
                [0.0, "#6b1f2a"],
                [0.28, "#9a3412"],
                [0.47, "#b45309"],
                [0.62, "#a3a30d"],
                [0.78, "#4d9b3a"],
                [1.0, "#22c55e"],
            ],
            zmin=0,
            zmax=100,
            marker_line_color="#0b1220",
            marker_line_width=0.9,
            colorbar=dict(
                title=dict(text=metric, font=dict(color="#9aa8bd", size=11)),
                thickness=9,
                len=0.62,
                x=1.01,
                tickfont=dict(color="#7f8fa5", size=9),
                outlinewidth=0,
                bgcolor="rgba(0,0,0,0)",
            ),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                + f"{metric} : %{{z:.0f}}/100<br>"
                + "Score GeoCapital : %{customdata[1]}/100<br>"
                + "Rendement exigé : %{customdata[2]}<br>"
                + "Risque : %{customdata[3]}/100<br>"
                + "Verdict : %{customdata[4]}<extra></extra>"
            ),
        )
    )
    fig.update_geos(
        projection_type="natural earth",
        showframe=False,
        showcoastlines=False,
        showland=True,
        landcolor="#151d2d",
        showocean=True,
        oceancolor="#080e19",
        showcountries=True,
        countrycolor="#2b3548",
        bgcolor="rgba(0,0,0,0)",
        lataxis_range=[-58, 85],
        domain=dict(x=[0.0, 0.94], y=[0.0, 1.0]),
    )
    fig.update_layout(
        height=540,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Manrope, sans-serif", color="#cbd5e1"),
        hoverlabel=dict(
            bgcolor="#0e1626",
            bordercolor="#334155",
            font=dict(color="#e9eef7", family="Manrope, sans-serif"),
        ),
        dragmode=False,
    )
    return fig


def _risk_return_figure(rows: list[dict[str, Any]]) -> go.Figure:
    group_colors = {
        "Développé": "#7dd3fc",
        "Émergent": "#e6b86b",
        "Golfe": "#a3e635",
        "Frontière": "#fb7185",
    }
    fig = go.Figure()
    for group, color in group_colors.items():
        subset = [r for r in rows if r["country"]["group"] == group]
        if not subset:
            continue
        fig.add_trace(
            go.Scatter(
                x=[r["risk"] for r in subset],
                y=[r["ke"] for r in subset],
                mode="markers+text",
                name=group,
                text=[r["country"]["name"] for r in subset],
                textposition="top center",
                textfont=dict(size=9, color="#aebaca"),
                marker=dict(
                    size=[max(10, r["score"] * 0.38) for r in subset],
                    color=color,
                    opacity=0.82,
                    line=dict(width=1, color="#0b1220"),
                ),
                customdata=[
                    [r["country"]["flag"], r["score"], r["verdict"]] for r in subset
                ],
                hovertemplate=(
                    "%{customdata[0]} <b>%{text}</b><br>"
                    "Risque : %{x:.0f}/100<br>"
                    "Rendement exigé : %{y:.1f} %<br>"
                    "Score : %{customdata[1]:.0f}/100<br>"
                    "%{customdata[2]}<extra></extra>"
                ),
            )
        )
    fig.add_vline(x=50, line_dash="dot", line_color="rgba(148,163,184,.25)")
    fig.add_hline(y=12, line_dash="dot", line_color="rgba(148,163,184,.25)")
    fig.update_layout(
        height=420,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Manrope, sans-serif", color="#94a3b8"),
        xaxis=dict(
            title="Risque pays (0 = faible, 100 = très élevé)",
            range=[0, 100],
            gridcolor="rgba(148,163,184,.09)",
            zeroline=False,
        ),
        yaxis=dict(
            title="Rendement exigé Ke (%)",
            gridcolor="rgba(148,163,184,.09)",
            zeroline=False,
        ),
        legend=dict(
            orientation="h",
            y=-0.18,
            x=0,
            font=dict(size=10),
            bgcolor="rgba(0,0,0,0)",
        ),
        hoverlabel=dict(bgcolor="#0e1626", bordercolor="#334155"),
    )
    return fig


def render() -> None:
    profile = st.session_state.get("profile", "Équilibré")
    rows = _rows(profile)
    ranked = sorted(rows, key=lambda r: r["score"], reverse=True)
    positive = sum(1 for row in rows if row["verdict"] in {"Investir", "Investir avec prudence"})

    ui.hero(
        "Carte vivante · 10 pays · 3 profils",
        "Comprendre le passé. Mesurer le risque. Décider.",
        "Cliquez sur un pays, lisez son histoire en trois minutes, puis regardez ses indicateurs devenir une décision financière. Le score change avec votre tolérance au risque.",
        ["Passé → présent → décision", "Données sourcées", "IA explicative"],
    )

    top_cols = st.columns(4)
    with top_cols[0]:
        ui.kpi("10", "pays couverts", "Du plus sûr au plus fragile")
    with top_cols[1]:
        ui.kpi(f"{ranked[0]['score']:.0f}<small>/100</small>", "meilleur score", f"{ranked[0]['country']['flag']} {ranked[0]['country']['name']}")
    with top_cols[2]:
        median_ke = sorted(row["ke"] for row in rows)[len(rows) // 2]
        ui.kpi(f"{median_ke:.1f}<small> %</small>", "rendement médian exigé", "Prime de risque pays incluse")
    with top_cols[3]:
        ui.kpi(f"{positive}<small>/10</small>", "verdicts positifs", "Investir ou investir avec prudence")

    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)

    control_a, control_b, control_c = st.columns([1.5, 1.25, 1.25])
    with control_a:
        profile = st.radio(
            "Votre profil d'investisseur",
            list(PROFILES.keys()),
            horizontal=True,
            key="profile",
            help="Le score n'est pas absolu : il dépend de ce que vous cherchez.",
        )
    with control_b:
        metric = st.selectbox("Indicateur affiché", list(METRICS.keys()), key="map_metric")
    with control_c:
        st.markdown(
            f'<div class="gc-chip gold" style="margin-top:1.85rem">Profil {ui.esc(profile)} · {PROFILES[profile]["weights"]["dynamisme"]*100:.0f}% croissance</div>',
            unsafe_allow_html=True,
        )

    map_col, side_col = st.columns([2.25, 1], gap="large")
    with map_col:
        st.markdown(
            f'<div class="gc-section-title"><h3>Le monde vu par le risque</h3><span>{ui.esc(METRICS[metric])}</span></div>',
            unsafe_allow_html=True,
        )
        fig = _map_figure(rows, metric, profile)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        st.caption("Seuls les 10 pays du MVP sont colorés. Les pays gris ne sont pas notés dans cette version.")

    with side_col:
        st.markdown(
            f"""
            <div class="gc-card gc-card-gold">
              <div class="gc-eyebrow">Grille de lecture</div>
              <h4>{ui.esc(PROFILES[profile]['label'])}</h4>
              <p>{ui.esc(PROFILES[profile]['description'])}</p>
              <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:12px">
                <span class="gc-chip">Croissance {PROFILES[profile]['weights']['dynamisme']*100:.0f}%</span>
                <span class="gc-chip">Stabilité {PROFILES[profile]['weights']['stabilite']*100:.0f}%</span>
                <span class="gc-chip">Solvabilité {PROFILES[profile]['weights']['solvabilite']*100:.0f}%</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        ui.section_title("Les mieux notés", "pour ce profil")
        for row in ranked[:3]:
            c = row["country"]
            st.markdown(
                f"""
                <div class="gc-card" style="padding:14px;margin-bottom:8px">
                  <div style="display:flex;justify-content:space-between;align-items:center;gap:8px">
                    <div><span style="font-size:1.4rem">{c['flag']}</span>
                    <strong style="color:#f1f5fb;font-size:.88rem;margin-left:6px">{ui.esc(c['name'])}</strong></div>
                    <strong style="color:var(--gold);font-size:1.2rem">{row['score']:.0f}</strong>
                  </div>
                  <div class="gc-small" style="margin-top:5px">{ui.esc(row['verdict'])} · Ke {row['ke']:.1f} %</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown(
            '<div class="gc-small" style="margin-top:10px">Le score mesure l’attractivité relative. Il ne remplace ni une due diligence, ni un conseil personnalisé.</div>',
            unsafe_allow_html=True,
        )

    ui.section_title("Explorer un pays", "cliquez pour ouvrir la fiche")
    quick = st.columns(5)
    for index, row in enumerate(rows):
        with quick[index % 5]:
            st.button(
                f"{row['country']['flag']} {row['country']['name']} · {row['score']:.0f}",
                key=f"map_open_{row['country']['id']}",
                width="stretch",
                on_click=go_to_country,
                args=(row["country"]["id"],),
            )

    st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)
    with st.expander("Voir la carte risque / rendement", expanded=False):
        st.markdown(
            '<div class="gc-small" style="margin-bottom:8px">Plus un pays est à droite, plus son risque est élevé. Plus il est haut, plus l’investisseur exige de rendement. La taille de la bulle représente le score GeoCapital.</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(_risk_return_figure(rows), width="stretch", config={"displayModeBar": False})

    ui.callout(
        "Le rendement exigé n'est pas une prédiction de performance. C'est le rendement minimum qu'un investisseur rationnel devrait demander pour accepter ce niveau de risque. "
        "Un pays peut offrir un fort potentiel et rester risqué : c'est tout l'intérêt de lire le score et le verdict ensemble.",
        "blue",
    )

    if ai.is_available():
        st.caption("Mode IA activé : les analyses optionnelles utilisent uniquement les données de la base GeoCapital.")
    ui.footer()
