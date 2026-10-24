"""Module comparateur — lire deux ou trois pays côte à côte."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from geocapital import ui
from geocapital.data import (
    INDICATOR_LABELS,
    comparison_frame,
    countries,
    country_by_id,
    indicator_summary,
)
from geocapital.scoring import (
    COMPONENT_LABELS,
    PROFILES,
    VERDICT_STYLES,
    component_scores,
    indicator_status,
    overall_score,
    required_return,
)

COLORS = ["#e6b86b", "#7dd3fc", "#a3e635"]


def _go_country(country_id: str) -> None:
    st.session_state["country_id"] = country_id
    st.session_state["nav"] = "Fiche pays"


def _set_comparison(pair: tuple[str, str]) -> None:
    st.session_state["compare_ids"] = [pair[0], pair[1]]


def _radar(selected: list[dict], profile: str) -> go.Figure:
    fig = go.Figure()
    categories = [COMPONENT_LABELS[key] for key in COMPONENT_LABELS]
    for index, country in enumerate(selected):
        scores = component_scores(country)
        values = [scores[key] for key in COMPONENT_LABELS]
        fig.add_trace(
            go.Scatterpolar(
                r=values + [values[0]],
                theta=categories + [categories[0]],
                fill="toself",
                fillcolor=f"rgba({_hex_to_rgb(COLORS[index])},0.10)",
                line=dict(color=COLORS[index], width=2),
                name=f"{country['flag']} {country['name']}",
                hovertemplate="%{theta}<br>%{r:.0f}/100<extra></extra>",
            )
        )
    fig.update_layout(
        height=420,
        margin=dict(l=45, r=45, t=35, b=35),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Manrope, sans-serif", color="#94a3b8"),
        polar=dict(
            bgcolor="rgba(255,255,255,0.018)",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                showline=False,
                gridcolor="rgba(148,163,184,.14)",
                tickfont=dict(size=8, color="#64748b"),
                angle=90,
                tickangle=90,
            ),
            angularaxis=dict(
                gridcolor="rgba(148,163,184,.14)",
                linecolor="rgba(148,163,184,.18)",
                tickfont=dict(size=10, color="#aab7c9"),
            ),
        ),
        legend=dict(orientation="h", y=-0.08, x=0, font=dict(size=10)),
        showlegend=True,
    )
    return fig


def _hex_to_rgb(color: str) -> str:
    color = color.lstrip("#")
    return f"{int(color[0:2], 16)},{int(color[2:4], 16)},{int(color[4:6], 16)}"


def _ke_chart(selected: list[dict], profile: str) -> go.Figure:
    rows = []
    for country in selected:
        result = overall_score(country, profile)
        ke = required_return(country)
        rows.append((f"{country['flag']} {country['name']}", ke["ke"], result["score"]))
    rows.sort(key=lambda item: item[1])
    colors = ["#4ade80" if score >= 76 else "#a3e635" if score >= 62 else "#fbbf24" if score >= 45 else "#fb7185" for _, _, score in rows]
    fig = go.Figure(
        go.Bar(
            x=[row[1] for row in rows],
            y=[row[0] for row in rows],
            orientation="h",
            marker=dict(color=colors, line=dict(width=0)),
            text=[f"{row[1]:.1f} %" for row in rows],
            textposition="outside",
            textfont=dict(color="#cbd5e1", size=11),
            hovertemplate="<b>%{y}</b><br>Rendement exigé : %{x:.1f} %<extra></extra>",
        )
    )
    fig.update_layout(
        height=310,
        margin=dict(l=10, r=35, t=15, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Manrope, sans-serif", color="#94a3b8"),
        xaxis=dict(title="Ke (%)", gridcolor="rgba(148,163,184,.09)", range=[0, max(row[1] for row in rows) * 1.25]),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        showlegend=False,
    )
    return fig


def _table(selected: list[dict]) -> None:
    header = "".join(f"<th>{country['flag']} {ui.esc(country['name'])}</th>" for country in selected)
    rows_html = []
    for key in [
        "gdp_growth", "inflation", "debt_gdp", "policy_rate", "unemployment", "reserves",
        "rating", "cds", "crp", "equity_index", "currency",
    ]:
        cells = []
        for country in selected:
            status = indicator_status(country, key)
            cells.append(
                f'<td><span class="gc-dot {status}"></span>{ui.esc(indicator_summary(country, key))}</td>'
            )
        rows_html.append(f"<tr><td class='gc-table-label'>{ui.esc(INDICATOR_LABELS[key])}</td>{''.join(cells)}</tr>")
    st.markdown(
        f'<div style="overflow-x:auto"><table class="gc-table"><thead><tr><th>Indicateur</th>{header}</tr></thead><tbody>{"".join(rows_html)}</tbody></table></div>',
        unsafe_allow_html=True,
    )


def render() -> None:
    profile = st.session_state.get("profile", "Équilibré")
    ui.page_head(
        "Comparateur · 2 à 3 pays",
        "Deux histoires, deux risques, deux prix.",
        "Comparez la trajectoire, les institutions et le rendement exigé. Un score plus élevé ne signifie pas automatiquement un meilleur investissement : regardez aussi ce que le marché vous fait payer.",
    )

    preset_cols = st.columns(5)
    presets = [
        ("USA vs Chine", ("usa", "china")),
        ("Arabie vs Émirats", ("saudi", "uae")),
        ("Liban vs Syrie", ("lebanon", "syria")),
        ("France vs Japon", ("france", "japan")),
        ("Maroc vs Afrique du Sud", ("morocco", "south_africa")),
    ]
    for col, (label, pair) in zip(preset_cols, presets):
        with col:
            st.button(label, key=f"preset_{pair[0]}_{pair[1]}", width="stretch", on_click=_set_comparison, args=(pair,))

    control_a, control_b = st.columns([2.2, 1])
    with control_a:
        selected_ids = st.multiselect(
            "Pays à comparer",
            [c["id"] for c in countries()],
            format_func=lambda cid: f"{country_by_id(cid)['flag']} {country_by_id(cid)['name']}",
            max_selections=3,
            key="compare_ids",
            help="Sélectionnez 2 ou 3 pays.",
        )
    with control_b:
        profile = st.radio("Profil", list(PROFILES.keys()), horizontal=True, key="profile")

    selected = [country_by_id(cid) for cid in selected_ids if country_by_id(cid)]
    if len(selected) < 2:
        ui.callout("Sélectionnez au moins deux pays pour lancer la comparaison.", "blue")
        return

    cards = st.columns(len(selected))
    for index, country in enumerate(selected):
        result = overall_score(country, profile)
        ke = required_return(country)
        tone = VERDICT_STYLES[result["verdict"]]["tone"]
        with cards[index]:
            st.markdown(
                f"""
                <div class="gc-card" style="min-height:280px">
                  <div style="display:flex;align-items:center;gap:10px">
                    <span style="font-size:1.8rem">{country['flag']}</span>
                    <div><div style="color:#f1f5fb;font-weight:750;font-size:.94rem">{ui.esc(country['name'])}</div>
                    <div style="color:#7f8fa5;font-size:.68rem">{ui.esc(country['group'])}</div></div>
                  </div>
                  <div style="display:flex;align-items:center;gap:14px;margin-top:16px">
                    {ui.ring(result['score'], 'score')}
                    <div>
                      {ui.verdict_badge(result['verdict'], tone)}
                      <div style="color:#e6b86b;font-size:1.45rem;font-weight:800;margin-top:10px;letter-spacing:-.04em">{ke['ke']:.1f} %</div>
                      <div class="gc-small">Ke · risque {result['risk']:.0f}/100</div>
                    </div>
                  </div>
                  <div class="gc-small" style="margin-top:12px">{ui.esc(result['verdict_reason'])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    chart_left, chart_right = st.columns([1.2, 1], gap="large")
    with chart_left:
        ui.section_title("Profil de risque", "les cinq briques du score")
        st.plotly_chart(_radar(selected, profile), width="stretch", config={"displayModeBar": False})
    with chart_right:
        ui.section_title("Rendement exigé", "plus le risque est perçu, plus Ke monte")
        st.plotly_chart(_ke_chart(selected, profile), width="stretch", config={"displayModeBar": False})
        st.markdown(
            '<div class="gc-small">Le rendement exigé intègre le risque de crédit, pas seulement la croissance. Un pays peut croître vite et rester cher à financer.</div>',
            unsafe_allow_html=True,
        )

    ui.section_title("Tableau de bord comparé", "vert / orange / rouge")
    _table(selected)

    ui.section_title("Lecture GeoCapital", "ce que le comparatif raconte")
    best = max(selected, key=lambda c: overall_score(c, profile)["score"])
    safest = min(selected, key=lambda c: overall_score(c, profile)["risk"])
    cheapest = min(selected, key=lambda c: required_return(c)["ke"])
    most_expensive = max(selected, key=lambda c: required_return(c)["ke"])
    st.markdown(
        f"""
        <div class="gc-card gc-card-gold">
          <p style="font-size:.87rem;line-height:1.75">
            Avec le profil <strong>{ui.esc(profile)}</strong>, <strong>{ui.esc(best['name'])}</strong> obtient le meilleur score
            ({overall_score(best, profile)['score']:.0f}/100). Le pays au risque le plus faible est <strong>{ui.esc(safest['name'])}</strong>
            (risque {overall_score(safest, profile)['risk']:.0f}/100). Le rendement exigé va de
            <strong>{required_return(cheapest)['ke']:.1f} %</strong> pour {ui.esc(cheapest['name'])} à
            <strong>{required_return(most_expensive)['ke']:.1f} %</strong> pour {ui.esc(most_expensive['name'])}.
            L'écart mesure le prix que le marché demande pour accepter l'incertitude.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    download_cols = st.columns([1, 1, 3])
    with download_cols[0]:
        frame = comparison_frame(selected)
        csv = frame.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "Exporter en CSV",
            data=csv,
            file_name="geocapital_comparaison.csv",
            mime="text/csv",
            width="stretch",
        )
    for index, country in enumerate(selected):
        with download_cols[index + 1]:
            st.button(
                f"Fiche {country['flag']}",
                key=f"compare_open_{country['id']}",
                width="stretch",
                on_click=_go_country,
                args=(country["id"],),
            )

    ui.callout(
        "Un rendement exigé élevé n'est pas une promesse de gain. Il signifie que l'investisseur doit être compensé pour un risque plus grand. "
        "Si le rendement attendu d'un actif est inférieur à Ke, la décision rationnelle est de ne pas l'acheter.",
        "blue",
    )
    ui.footer()
