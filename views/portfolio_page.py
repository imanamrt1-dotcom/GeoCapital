"""Module 6 — Le portefeuille mondial."""

from __future__ import annotations

from typing import Any

import plotly.graph_objects as go
import streamlit as st

from geocapital import ai, ui
from geocapital.data import countries
from geocapital.scoring import overall_score, portfolio_metrics, required_return

PALETTE = [
    "#e6b86b", "#7dd3fc", "#a3e635", "#fbbf24", "#c084fc",
    "#34d399", "#fb7185", "#93c5fd", "#f97316", "#94a3b8",
]

PRESETS = {
    "Défensif": {
        "usa": 30000, "france": 20000, "japan": 15000, "uae": 20000, "morocco": 15000,
    },
    "Équilibré": {c["id"]: 10000 for c in countries()},
    "Offensif": {
        "china": 30000, "saudi": 20000, "uae": 20000, "morocco": 15000, "south_africa": 15000,
    },
}


def _set_amounts(amounts: dict[str, int]) -> None:
    for country in countries():
        st.session_state[f"amount_{country['id']}"] = int(amounts.get(country["id"], 0))


def _apply_preset(name: str) -> None:
    _set_amounts(PRESETS[name])


def _reset() -> None:
    _set_amounts({c["id"]: 10000 for c in countries()})


def _donut(holdings: list[dict[str, Any]], portfolio: dict[str, Any]) -> go.Figure:
    active = [h for h in holdings if h["weight"] > 0]
    labels = [f"{h['country']['flag']} {h['country']['name']}" for h in active]
    values = [h["weight"] * 100000 for h in active]
    colors = PALETTE[: len(active)]
    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.64,
            marker=dict(colors=colors, line=dict(color="#0b1423", width=2)),
            textinfo="percent",
            textfont=dict(size=10, color="#0b1423"),
            hovertemplate="<b>%{label}</b><br>%{value:,.0f} €<br>%{percent}<extra></extra>",
            sort=False,
        )
    )
    fig.update_layout(
        height=360,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Manrope, sans-serif", color="#94a3b8"),
        showlegend=False,
        annotations=[
            dict(
                text=f"<b>{portfolio['expected_return']:.1f} %</b><br><span style='font-size:10px;color:#8fa0b6'>Ke moyen</span>",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=19, color="#f1f5fb"),
            )
        ],
    )
    return fig


def _risk_contribution_chart(holdings: list[dict[str, Any]]) -> go.Figure:
    active = sorted(
        [h for h in holdings if h["weight"] > 0],
        key=lambda h: h["weight"] * overall_score(h["country"])["volatility"],
    )
    labels = [f"{h['country']['flag']} {h['country']['name']}" for h in active]
    values = [h["weight"] * overall_score(h["country"])["volatility"] for h in active]
    fig = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker=dict(color=["#fb7185" if value > 8 else "#e6b86b" if value > 4 else "#4ade80" for value in values]),
            hovertemplate="<b>%{y}</b><br>Contribution approx. : %{x:.1f}<extra></extra>",
        )
    )
    fig.update_layout(
        height=330,
        margin=dict(l=10, r=15, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Manrope, sans-serif", color="#94a3b8"),
        xaxis=dict(title="Poids × volatilité", gridcolor="rgba(148,163,184,.09)"),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        showlegend=False,
    )
    return fig


def _table(holdings: list[dict[str, Any]], total: float) -> None:
    active = sorted([h for h in holdings if h["weight"] > 0], key=lambda h: h["weight"], reverse=True)
    rows = []
    for holding in active:
        country = holding["country"]
        ke = required_return(country)["ke"]
        vol = overall_score(country)["volatility"]
        weight = holding["weight"] if total > 0 else 0
        amount = weight * 100000
        rows.append(
            f"""
            <tr>
              <td>{country['flag']} {ui.esc(country['name'])}</td>
              <td>{weight*100:.1f} %</td>
              <td>{ui.eur(amount)}</td>
              <td>{ke:.1f} %</td>
              <td>{vol:.1f} %</td>
              <td>{weight*vol:.1f}</td>
            </tr>
            """
        )
    st.markdown(
        f"""
        <div style="overflow-x:auto"><table class="gc-table">
          <thead><tr><th>Pays</th><th>Poids normalisé</th><th>Montant</th><th>Ke</th><th>Volatilité</th><th>Contribution risque</th></tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table></div>
        """,
        unsafe_allow_html=True,
    )


def _commentary(holdings: list[dict[str, Any]], metrics: dict[str, Any]) -> str:
    active = [h for h in holdings if h["weight"] > 0]
    if not active:
        return "Aucune allocation : le portefeuille ne peut pas être analysé."
    top = max(active, key=lambda h: h["weight"])
    riskiest = max(active, key=lambda h: overall_score(h["country"])["volatility"])
    concentration = (
        "très concentré" if metrics["hhi"] > 0.30 else "modérément concentré" if metrics["hhi"] > 0.20 else "relativement diversifié"
    )
    diversification_text = (
        "La diversification réduit la volatilité estimée par rapport à la moyenne pondérée des pays."
        if metrics["diversification"] > 0.5
        else "La diversification apporte peu : les pays choisis évoluent de façon trop proche."
    )
    return (
        f"Votre allocation est {concentration} : {top['country']['name']} pèse {metrics['top_weight']:.0f} % du portefeuille. "
        f"Le rendement exigé pondéré s'élève à {metrics['expected_return']:.1f} % par an, pour une volatilité estimée de {metrics['volatility']:.1f} %. "
        f"{diversification_text} Le pays qui contribue le plus au risque est {riskiest['country']['name']}. "
        f"Le portefeuille n'est pas une recommandation : c'est une manière de voir que le rendement et le risque se paient ensemble."
    )


def render() -> None:
    for country in countries():
        st.session_state.setdefault(f"amount_{country['id']}", 10000)

    profile = st.session_state.get("profile", "Équilibré")
    ui.page_head(
        "Portefeuille mondial",
        "100 000 €, dix pays, une leçon de risque.",
        "Répartissez un capital fictif entre les pays. Le simulateur calcule le rendement exigé pondéré, la volatilité et l'effet réel de la diversification. Aucun ordre n'est passé, aucun rendement n'est garanti.",
    )

    preset_cols = st.columns([1, 1, 1, 2.2])
    with preset_cols[0]:
        st.button("Défensif", key="preset_defensive", width="stretch", on_click=_apply_preset, args=("Défensif",))
    with preset_cols[1]:
        st.button("Équilibré", key="preset_balanced", width="stretch", on_click=_apply_preset, args=("Équilibré",))
    with preset_cols[2]:
        st.button("Offensif", key="preset_offensive", width="stretch", on_click=_apply_preset, args=("Offensif",))
    with preset_cols[3]:
        st.markdown(
            '<div class="gc-small" style="text-align:right;margin-top:9px">Les presets sont pédagogiques. Modifiez ensuite librement chaque poche.</div>',
            unsafe_allow_html=True,
        )

    ui.section_title("Votre allocation", "montants en euros")
    allocations = {}
    cols = st.columns(5)
    for index, country in enumerate(countries()):
        result = overall_score(country, profile)
        with cols[index % 5]:
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin:7px 0 3px"><span style="font-size:.79rem;color:#dce6f3;font-weight:700">{country["flag"]} {ui.esc(country["name"])}</span><span style="font-size:.67rem;color:#7f8fa5">{result["score"]:.0f}</span></div>',
                unsafe_allow_html=True,
            )
            allocations[country["id"]] = st.number_input(
                f"Montant {country['name']}",
                min_value=0,
                max_value=100000,
                step=1000,
                key=f"amount_{country['id']}",
                label_visibility="collapsed",
            )

    total = sum(allocations.values())
    total_col, action_col = st.columns([2, 1])
    with total_col:
        if total == 100000:
            st.markdown('<span class="gc-chip green">Total saisi : 100 000 € · allocation exacte</span>', unsafe_allow_html=True)
        elif total > 0:
            st.markdown(
                f'<span class="gc-chip orange">Total saisi : {ui.eur(total)} · normalisé à 100 000 € pour la simulation</span>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown('<span class="gc-chip red">Total saisi : 0 €</span>', unsafe_allow_html=True)
    with action_col:
        st.button("Tout réinitialiser", key="reset_portfolio", width="stretch", on_click=_reset)

    if total <= 0:
        ui.callout("Ajoutez au moins un montant pour lancer la simulation.", "red")
        ui.footer()
        return

    holdings = [
        {
            "country": country,
            "weight": allocations[country["id"]] / total,
            "amount": allocations[country["id"]],
        }
        for country in countries()
    ]
    metrics = portfolio_metrics(holdings)

    st.markdown("<div style='height:1.1rem'></div>", unsafe_allow_html=True)
    kpi_cols = st.columns(4)
    with kpi_cols[0]:
        ui.kpi(
            f"{metrics['expected_return']:.1f}<small> %</small>",
            "Rendement espéré",
            "Proxy : Ke moyen pondéré",
        )
    with kpi_cols[1]:
        ui.kpi(
            f"{metrics['volatility']:.1f}<small> %</small>",
            "Volatilité estimée",
            "Risque annualisé du portefeuille",
        )
    with kpi_cols[2]:
        ui.kpi(
            f"{metrics['diversification']:.1f}<small> pts</small>",
            "Gain de diversification",
            "Moins de volatilité grâce aux corrélations",
        )
    with kpi_cols[3]:
        ui.kpi(
            f"{metrics['effective_countries']:.1f}",
            "Pays effectifs",
            f"Concentration HHI {metrics['hhi']:.2f}",
        )

    chart_col, diagnosis_col = st.columns([1.15, 1], gap="large")
    with chart_col:
        ui.section_title("Répartition normalisée", "100 000 €")
        st.plotly_chart(_donut(holdings, metrics), width="stretch", config={"displayModeBar": False})
        legend = "".join(
            f'<div style="display:flex;justify-content:space-between;padding:5px 0;border-top:1px solid rgba(148,163,184,.10);font-size:.72rem"><span style="color:#aab7c9">{ui.esc(h["country"]["flag"])} {ui.esc(h["country"]["name"])}</span><span style="color:#7f8fa5">{h["weight"]*100:.1f} %</span></div>'
            for h in sorted(holdings, key=lambda item: item["weight"], reverse=True)
            if h["weight"] > 0
        )
        st.markdown(legend, unsafe_allow_html=True)

    with diagnosis_col:
        ui.section_title("Diagnostic", "ce que votre allocation raconte")
        st.markdown(
            f"""
            <div class="gc-card gc-card-gold">
              <p style="font-size:.86rem;line-height:1.72;color:#c3cedd">{ui.esc(_commentary(holdings, metrics))}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:9px'></div>", unsafe_allow_html=True)
        ui.section_title("Contribution au risque", "poids × volatilité")
        st.plotly_chart(_risk_contribution_chart(holdings), width="stretch", config={"displayModeBar": False})

    ui.section_title("Détail du portefeuille", "montants normalisés à 100 000 €")
    _table(holdings, total)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    ai_col, dl_col = st.columns([1, 1])
    with ai_col:
        with st.expander("Commenter avec Claude Haiku", expanded=False):
            if not ai.is_available():
                st.caption(
                    "Le diagnostic ci-dessus est déterministe et fonctionne sans API. "
                    "Ajoutez `ANTHROPIC_API_KEY` pour obtenir une reformulation pédagogique de cette même allocation."
                )
            else:
                st.caption("L'IA reçoit uniquement l'allocation et les métriques calculées.")
                if st.button("Générer le commentaire", key="ai_portfolio", type="primary"):
                    facts = [
                        {
                            "pays": h["country"]["name"],
                            "poids": round(h["weight"] * 100, 1),
                            "ke": required_return(h["country"])["ke"],
                            "volatilite": overall_score(h["country"])["volatility"],
                        }
                        for h in holdings
                        if h["weight"] > 0
                    ]
                    with st.spinner("Analyse de l'allocation..."):
                        text = ai.portfolio_commentary(facts, metrics)
                    if text:
                        st.markdown(text)
                    else:
                        st.warning("L'appel IA n'a pas abouti. Le diagnostic déterministe reste disponible.")
    with dl_col:
        import pandas as pd

        export_rows = []
        for h in holdings:
            if h["weight"] <= 0:
                continue
            export_rows.append(
                {
                    "Pays": h["country"]["name"],
                    "Poids (%)": round(h["weight"] * 100, 2),
                    "Montant (€)": round(h["weight"] * 100000, 0),
                    "Ke (%)": required_return(h["country"])["ke"],
                    "Volatilité (%)": overall_score(h["country"])["volatility"],
                }
            )
        csv = pd.DataFrame(export_rows).to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "Télécharger l'allocation",
            data=csv,
            file_name="geocapital_portefeuille.csv",
            mime="text/csv",
            width="stretch",
        )

    ui.callout(
        "Limites du modèle : la volatilité est une estimation pédagogique, les corrélations sont simplifiées par groupe de pays, "
        "et le portefeuille est investi en actions pays sans couverture de change. Une vraie allocation doit tenir compte de votre horizon, "
        "de votre situation fiscale et de votre capacité à supporter une perte.",
        "blue",
    )
    ui.footer()
