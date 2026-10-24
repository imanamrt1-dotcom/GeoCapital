"""Composants visuels et helpers d'affichage GeoCapital."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

import streamlit as st

from geocapital.scoring import status_label

ASSETS = Path(__file__).resolve().parent.parent / "assets" / "styles.css"
TONE_COLORS = {
    "green": "#4ade80",
    "lime": "#a3e635",
    "orange": "#fbbf24",
    "red": "#fb7185",
    "gold": "#e6b86b",
}


@st.cache_data(show_spinner=False)
def _css() -> str:
    return ASSETS.read_text(encoding="utf-8")


def inject_css() -> None:
    st.markdown(f"<style>{_css()}</style>", unsafe_allow_html=True)


def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def hero(eyebrow: str, title: str, subtitle: str, chips: list[str] | None = None) -> None:
    chip_html = "".join(f'<span class="gc-chip gold">{esc(chip)}</span>' for chip in (chips or []))
    st.markdown(
        f"""
        <div class="gc-hero">
          <div class="gc-hero-content">
            <div class="gc-eyebrow">{esc(eyebrow)}</div>
            <h1>{esc(title)}</h1>
            <p>{esc(subtitle)}</p>
            <div class="gc-hero-actions">{chip_html}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_head(eyebrow: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="gc-page-head">
          <div class="gc-eyebrow">{esc(eyebrow)}</div>
          <h1>{esc(title)}</h1>
          <p>{esc(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(title: str, note: str = "") -> None:
    st.markdown(
        f'<div class="gc-section-title"><h3>{esc(title)}</h3><span>{esc(note)}</span></div>',
        unsafe_allow_html=True,
    )


def kpi(value: str, label: str, note: str = "") -> None:
    st.markdown(
        f"""
        <div class="gc-kpi">
          <div class="gc-kpi-label">{esc(label)}</div>
          <div class="gc-kpi-value">{value}</div>
          <div class="gc-kpi-note">{esc(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card(title: str, body: str, extra_class: str = "") -> None:
    st.markdown(
        f'<div class="gc-card {extra_class}"><h4>{esc(title)}</h4><p>{esc(body)}</p></div>',
        unsafe_allow_html=True,
    )


def callout(text: str, tone: str = "gold") -> None:
    tone_class = "" if tone == "gold" else tone
    st.markdown(f'<div class="gc-callout {tone_class}">{esc(text)}</div>', unsafe_allow_html=True)


def ring(score: float, label: str = "score", color: str | None = None) -> str:
    pct = max(0, min(100, score))
    if color is None:
        if pct >= 76:
            color = TONE_COLORS["green"]
        elif pct >= 62:
            color = TONE_COLORS["lime"]
        elif pct >= 45:
            color = TONE_COLORS["orange"]
        else:
            color = TONE_COLORS["red"]
    return f"""
    <div class="gc-ring" style="--pct:{pct:.1f};--ring:{color}">
      <div class="gc-ring-inner">
        <span class="gc-ring-value">{pct:.0f}</span>
        <span class="gc-ring-label">{esc(label)}</span>
      </div>
    </div>
    """


def verdict_badge(verdict: str, tone: str) -> str:
    return f'<span class="gc-verdict {esc(tone)}">{esc(verdict)}</span>'


def country_hero(country: dict[str, Any], score_payload: dict[str, Any]) -> None:
    verdict = score_payload["verdict"]
    tone = score_payload.get("verdict_tone", "gold")
    st.markdown(
        f"""
        <div class="gc-country-hero">
          <div class="gc-country-hero-main">
            <div class="gc-flag">{country.get('flag', '🌍')}</div>
            <div>
              <div class="gc-eyebrow">{esc(country.get('region'))} · {esc(country.get('group'))}</div>
              <h1>{esc(country['name'])}</h1>
              <p>{esc(country.get('headline', ''))}</p>
              <div class="gc-country-meta">
                <span class="gc-chip">{esc(country.get('official_name', ''))}</span>
                <span class="gc-chip">ISO {esc(country.get('iso3', ''))}</span>
                <span class="gc-verdict {esc(tone)}">{esc(verdict)}</span>
              </div>
            </div>
          </div>
          <div class="gc-score-row">
            {ring(score_payload['score'], 'score / 100')}
            <div>
              <div class="gc-kpi-label">Rendement exigé</div>
              <div class="gc-ke"><strong>{score_payload['ke']['ke']:.1f} %</strong><span>Ke annuel</span></div>
              <div class="gc-small">Risque : {score_payload['risk']:.0f}/100 · {risk_word(score_payload['risk'])}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def indicator_card(
    label: str,
    value: str,
    unit: str,
    status: str,
    note: str,
    source: str,
    date: str,
) -> None:
    st.markdown(
        f"""
        <div class="gc-ind {esc(status)}">
          <div class="gc-ind-top">
            <div class="gc-ind-label">{esc(label)}</div>
            <div class="gc-status {esc(status)}">{esc(status_label(status))}</div>
          </div>
          <div class="gc-ind-value">{esc(value)}<small>{esc(unit)}</small></div>
          <div class="gc-ind-note">{esc(note)}</div>
          <div class="gc-ind-source">{esc(source)}{' · ' + esc(date) if date else ''}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def timeline(history: list[dict[str, Any]]) -> None:
    items = []
    for item in history:
        items.append(
            f"""
            <div class="gc-timeline-item">
              <div class="gc-timeline-year">{esc(item.get('year'))}</div>
              <div class="gc-timeline-dot"></div>
              <div class="gc-timeline-content">
                <h4>{esc(item.get('title'))}</h4>
                <p>{esc(item.get('text'))}</p>
              </div>
            </div>
            """
        )
    st.markdown(f'<div class="gc-timeline">{"".join(items)}</div>', unsafe_allow_html=True)


def relation_column(title: str, icon: str, items: list[dict[str, Any]]) -> None:
    body = "".join(
        f'<div class="gc-relation-item"><strong>{esc(i.get("name"))}</strong><span>{esc(i.get("note"))}</span></div>'
        for i in items
    )
    st.markdown(
        f'<div class="gc-relation-col"><div class="gc-relation-head"><span>{icon}</span>{esc(title)}</div>{body}</div>',
        unsafe_allow_html=True,
    )


def component_bars(rows: list[dict[str, Any]]) -> None:
    blocks = []
    for row in rows:
        score = row["score"]
        tone = "green" if score >= 70 else "orange" if score >= 50 else "red"
        blocks.append(
            f"""
            <div class="gc-bar-row">
              <div class="gc-bar-head">
                <strong>{esc(row['label'])}</strong>
                <span>{score:.0f}/100 · poids {row['weight']*100:.0f}%</span>
              </div>
              <div class="gc-bar-track"><div class="gc-bar-fill {tone}" style="width:{max(2, min(100, score)):.1f}%"></div></div>
              <div class="gc-weight">Contribution au score : {row['contribution']:.1f} pts sur {row['max']:.0f}</div>
            </div>
            """
        )
    st.markdown("".join(blocks), unsafe_allow_html=True)


def chain_steps(chain: list[dict[str, Any]]) -> None:
    blocks = []
    for index, step in enumerate(chain, start=1):
        blocks.append(
            f"""
            <div class="gc-chain-step">
              <div class="gc-chain-num">{index:02d}</div>
              <div>
                <div class="gc-chain-label">{esc(step.get('label'))}</div>
                <div class="gc-chain-text">{esc(step.get('text'))}</div>
              </div>
            </div>
            """
        )
    st.markdown("".join(blocks), unsafe_allow_html=True)


def winners_losers(winners: list[str], losers: list[str]) -> None:
    win_html = "".join(f'<div class="gc-win">↗ {esc(item)}</div>' for item in winners)
    loss_html = "".join(f'<div class="gc-loss">↘ {esc(item)}</div>' for item in losers)
    st.markdown(
        f"""
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
          <div class="gc-two-list">{win_html}</div>
          <div class="gc-two-list">{loss_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def footer() -> None:
    st.markdown(
        """
        <div class="gc-footer">
          <div><strong>GeoCapital</strong> · Connaître le passé pour anticiper le futur.<br>
          Prototype pédagogique. Données indicatives, non actualisées en temps réel.</div>
          <div>Pas un conseil en investissement · Les chiffres sont sourcés dans la base GeoCapital.<br>
          L'IA explique les données, elle ne les invente pas.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def risk_word(risk: float) -> str:
    if risk < 30:
        return "faible"
    if risk < 50:
        return "modéré"
    if risk < 70:
        return "élevé"
    return "très élevé"


def eur(value: float, decimals: int = 0) -> str:
    return f"{value:,.{decimals}f} €".replace(",", " ").replace(".", ",")


def pct(value: float, decimals: int = 1) -> str:
    return f"{value:,.{decimals}f} %".replace(",", " ").replace(".", ",")


def signed_pct(value: float, decimals: int = 1) -> str:
    if value > 0:
        return f"+{value:.{decimals}f} %".replace(".", ",")
    return f"{value:.{decimals}f} %".replace(".", ",")
