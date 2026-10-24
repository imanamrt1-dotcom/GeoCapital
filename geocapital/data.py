"""Chargement et helpers de données GeoCapital."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
COUNTRY_DIR = ROOT / "data" / "countries"
META_FILE = ROOT / "data" / "meta.json"
EVENTS_FILE = ROOT / "data" / "events.json"

PROFILE_ORDER = ["Prudent", "Équilibré", "Audacieux"]
INDICATOR_ORDER = [
    "gdp_growth",
    "inflation",
    "debt_gdp",
    "policy_rate",
    "unemployment",
    "reserves",
    "rating",
    "cds",
    "crp",
    "equity_index",
    "currency",
]

INDICATOR_LABELS = {
    "gdp_growth": "Croissance du PIB",
    "inflation": "Inflation",
    "debt_gdp": "Dette publique / PIB",
    "policy_rate": "Taux directeur",
    "unemployment": "Chômage",
    "reserves": "Réserves de change",
    "rating": "Notation souveraine",
    "cds": "CDS 5 ans",
    "crp": "Prime de risque pays",
    "equity_index": "Indice boursier",
    "currency": "Devise",
}

INDICATOR_UNITS = {
    "gdp_growth": "%",
    "inflation": "%",
    "debt_gdp": "% du PIB",
    "policy_rate": "%",
    "unemployment": "%",
    "reserves": "Mds $",
    "rating": "",
    "cds": "pb",
    "crp": "%",
    "equity_index": "",
    "currency": "",
}


@st.cache_data(show_spinner=False)
def load_data() -> dict[str, Any]:
    meta: dict[str, Any] = {}
    if META_FILE.exists():
        with META_FILE.open("r", encoding="utf-8") as handle:
            meta = json.load(handle)
    items = []
    for path in sorted(COUNTRY_DIR.glob("*.json")):
        with path.open("r", encoding="utf-8") as handle:
            items.append(json.load(handle))
    items.sort(key=lambda item: item.get("order", 999))
    return {**meta, "countries": items}


@st.cache_data(show_spinner=False)
def load_events() -> list[dict[str, Any]]:
    with EVENTS_FILE.open("r", encoding="utf-8") as handle:
        return json.load(handle).get("events", [])


def countries() -> list[dict[str, Any]]:
    return load_data().get("countries", [])


def country_by_id(country_id: str) -> dict[str, Any] | None:
    return next((c for c in countries() if c["id"] == country_id), None)


def country_map() -> dict[str, dict[str, Any]]:
    return {c["id"]: c for c in countries()}


def indicator_value(country: dict[str, Any], key: str) -> Any:
    if key == "crp":
        from geocapital.scoring import country_risk_premium

        return country_risk_premium(country)[0]
    return country.get("indicators", {}).get(key, {}).get("value")


def indicator_meta(country: dict[str, Any], key: str) -> dict[str, Any]:
    if key == "crp":
        from geocapital.scoring import country_risk_premium

        value, source = country_risk_premium(country)
        return {
            "value": value,
            "unit": "%",
            "date": "calcul",
            "source": f"Damodaran · {source}",
            "note": "Prime exigée pour détenir le risque souverain, au-delà du risque de marché mature.",
        }
    return country.get("indicators", {}).get(key, {})


def format_number(value: Any, decimals: int = 1, suffix: str = "") -> str:
    if value is None or value == "":
        return "n.d."
    if isinstance(value, (int, float)):
        text = f"{value:,.{decimals}f}".replace(",", " ").replace(".", ",")
        return f"{text}{suffix}"
    return str(value)


def indicator_display(country: dict[str, Any], key: str) -> tuple[str, str, str]:
    """Retourne (valeur formatée, unité, période) prêt à afficher."""
    meta = indicator_meta(country, key)
    value = meta.get("value")
    unit = meta.get("unit", INDICATOR_UNITS.get(key, ""))
    date = meta.get("date", "")
    if key == "rating":
        return str(value or "NR"), meta.get("agency", "agence"), date
    if key == "reserves":
        return format_number(value, 0), "Mds $", date
    if key == "cds":
        if value is None:
            return "—", "non coté", date
        return format_number(value, 0), "pb", date
    if key == "equity_index":
        level = meta.get("level")
        text = f"{level:,.0f}".replace(",", " ") if isinstance(level, (int, float)) else "—"
        return text, meta.get("name", "indice"), date
    if key == "currency":
        return str(meta.get("code", "—")), meta.get("name", "devise"), date
    if key == "debt_gdp":
        return format_number(value, 0), "% du PIB", date
    return format_number(value, 1), unit, date


def indicator_summary(country: dict[str, Any], key: str) -> str:
    """Valeur compacte et lisible, pensée pour les tableaux comparatifs."""
    meta = indicator_meta(country, key)
    value = meta.get("value")
    if key == "rating":
        agency = meta.get("agency")
        return f"{value or 'NR'} · {agency}" if agency else str(value or "NR")
    if key == "cds":
        return f"{format_number(value, 0)} pb" if value is not None else "Non coté"
    if key == "reserves":
        return f"{format_number(value, 0)} Mds $"
    if key == "crp":
        return f"{format_number(value, 2)} %"
    if key == "equity_index":
        name = meta.get("name", "—")
        perf = meta.get("perf_1y")
        return f"{name} · {format_number(perf, 1, ' %')}" if perf is not None else name
    if key == "currency":
        code = meta.get("code", "—")
        perf = meta.get("perf_1y")
        name = meta.get("name", "")
        if perf is not None:
            return f"{code} · {format_number(perf, 1, ' %')}"
        return f"{code} · {name}" if name else code
    unit = meta.get("unit", INDICATOR_UNITS.get(key, ""))
    return f"{format_number(value, 1)} {unit}".strip()


def comparison_frame(selected: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for key in INDICATOR_ORDER:
        row: dict[str, Any] = {"Indicateur": INDICATOR_LABELS[key]}
        for c in selected:
            row[c["name"]] = indicator_summary(c, key)
        rows.append(row)
    return pd.DataFrame(rows)
