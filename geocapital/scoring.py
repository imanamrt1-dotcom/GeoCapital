"""Moteur de score, de risque et de rendement exigé de GeoCapital.

Toutes les données chiffrées proviennent du fichier data/countries.json.
Les formules sont volontairement explicites et reproductibles.
"""

from __future__ import annotations

import math
from typing import Any


# ---------------------------------------------------------------------------
# Paramètres financiers (Damodaran, début 2025)
# ---------------------------------------------------------------------------
RISK_FREE_RATE = 4.20          # Taux du Trésor américain à 10 ans, approx.
MATURE_ERP = 4.50              # Prime de risque actions marché mature
BETA = 1.00                    # Bêta de marché retenu (indice large)
EQUITY_BOND_VOL_RATIO = 1.50   # Ratio volatilité actions / obligations (Damodaran)

RATING_SCORES = {
    "AAA": 100,
    "AA+": 95,
    "AA": 92,
    "AA-": 88,
    "A+": 84,
    "A": 80,
    "A-": 76,
    "BBB+": 70,
    "BBB": 65,
    "BBB-": 60,
    "BB+": 52,
    "BB": 46,
    "BB-": 40,
    "B+": 30,
    "B": 22,
    "B-": 14,
    "CCC": 6,
    "D": 2,
    "RD": 1,
    "NR": 20,
}

DEFAULT_SPREADS = {
    "AAA": 0.40,
    "AA+": 0.55,
    "AA": 0.70,
    "AA-": 0.80,
    "A+": 0.95,
    "A": 1.05,
    "A-": 1.15,
    "BBB+": 1.45,
    "BBB": 1.60,
    "BBB-": 1.90,
    "BB+": 2.60,
    "BB": 3.00,
    "BB-": 3.50,
    "B+": 4.50,
    "B": 5.50,
    "B-": 6.50,
    "CCC": 9.00,
    "D": 15.00,
    "RD": 15.00,
    "NR": 15.50,
}

PROFILES = {
    "Prudent": {
        "label": "Prudent",
        "description": "Priorité à la stabilité et à la capacité de rembourser.",
        "weights": {
            "dynamisme": 0.15,
            "stabilite": 0.30,
            "solvabilite": 0.30,
            "institutions": 0.15,
            "ouverture": 0.10,
        },
    },
    "Équilibré": {
        "label": "Équilibré",
        "description": "Le bon compromis entre croissance, risque et gouvernance.",
        "weights": {
            "dynamisme": 0.25,
            "stabilite": 0.20,
            "solvabilite": 0.25,
            "institutions": 0.15,
            "ouverture": 0.15,
        },
    },
    "Audacieux": {
        "label": "Audacieux",
        "description": "Recherche de croissance, tolérance au risque plus élevée.",
        "weights": {
            "dynamisme": 0.35,
            "stabilite": 0.10,
            "solvabilite": 0.20,
            "institutions": 0.10,
            "ouverture": 0.25,
        },
    },
}

COMPONENT_LABELS = {
    "dynamisme": "Dynamisme économique",
    "stabilite": "Stabilité macro",
    "solvabilite": "Solvabilité",
    "institutions": "Institutions",
    "ouverture": "Ouverture & affaires",
}

VERDICT_STYLES = {
    "Investir": {"tone": "green", "icon": "↗", "copy": "Les fondamentaux compensent le risque."},
    "Investir avec prudence": {"tone": "lime", "icon": "→", "copy": "Le potentiel existe, mais la taille de position compte."},
    "Attendre": {"tone": "orange", "icon": "Ⅱ", "copy": "Le couple risque/rendement reste insuffisant."},
    "Éviter": {"tone": "red", "icon": "↘", "copy": "Le risque n'est pas correctement rémunéré."},
}


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def linear(value: float, low: float, high: float, reverse: bool = False) -> float:
    """Transforme une valeur en score 0-100 sur un intervalle."""
    if high == low:
        return 50.0
    score = (value - low) / (high - low) * 100
    score = clamp(score)
    return 100 - score if reverse else score


def _get_indicator(country: dict[str, Any], key: str) -> dict[str, Any]:
    return country.get("indicators", {}).get(key, {}) or {}


def _numeric(country: dict[str, Any], key: str, default: float | None = None) -> float | None:
    raw = _get_indicator(country, key).get("value")
    if raw is None or isinstance(raw, str):
        return default
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


def rating_of(country: dict[str, Any]) -> str:
    return str(_get_indicator(country, "rating").get("value") or "NR")


def rating_score(country: dict[str, Any]) -> float:
    return float(RATING_SCORES.get(rating_of(country), 20))


def cds_score(cds: float | None) -> float:
    """Score CDS : 100 à 20 pb, proche de 0 au-delà de 1 000 pb."""
    if cds is None:
        return 5.0
    if cds <= 20:
        return 100.0
    log_position = math.log10(max(cds, 20) / 20) / math.log10(50)
    return clamp(100 - log_position * 95)


def default_spread(country: dict[str, Any]) -> float:
    return float(DEFAULT_SPREADS.get(rating_of(country), 15.5))


def country_risk_premium(country: dict[str, Any]) -> tuple[float, str]:
    """Prime de risque pays en %, méthode Damodaran.

    On retient le maximum entre le spread de notation et le spread CDS,
    puis on applique le ratio de volatilité actions/obligations de 1,5.
    """
    cds = _numeric(country, "cds")
    cds_crp = max(0.0, ((cds or 0.0) - 25.0) / 100.0) * EQUITY_BOND_VOL_RATIO
    rating_crp = default_spread(country) * EQUITY_BOND_VOL_RATIO
    if cds is None:
        return round(rating_crp, 2), "Notation (CDS non coté)"
    if cds_crp >= rating_crp:
        return round(cds_crp, 2), "CDS"
    return round(rating_crp, 2), "Notation"


def required_return(country: dict[str, Any]) -> dict[str, float | str]:
    crp, source = country_risk_premium(country)
    ke = RISK_FREE_RATE + BETA * MATURE_ERP + crp
    return {
        "risk_free": RISK_FREE_RATE,
        "erp": MATURE_ERP,
        "beta": BETA,
        "crp": crp,
        "crp_source": source,
        "ke": round(ke, 2),
    }


def indicator_status(country: dict[str, Any], key: str) -> str:
    """Retourne green / orange / red pour le tableau de bord."""
    c = country
    if key == "gdp_growth":
        value = _numeric(c, key, 0) or 0
        return "green" if value >= 3 else "orange" if value >= 1 else "red"
    if key == "inflation":
        value = _numeric(c, key, 0) or 0
        return "green" if 0.5 <= value <= 3.5 else "orange" if 0 <= value <= 7 else "red"
    if key == "debt_gdp":
        value = _numeric(c, key, 0) or 0
        return "green" if value <= 60 else "orange" if value <= 100 else "red"
    if key == "policy_rate":
        nominal = _numeric(c, key, 0) or 0
        inflation = _numeric(c, "inflation", 0) or 0
        real = nominal - inflation
        if nominal > 20 or real < -8:
            return "red"
        if nominal > 10 or real < -3 or real > 4:
            return "orange"
        return "green"
    if key == "unemployment":
        value = _numeric(c, key, 0) or 0
        return "green" if value <= 6 else "orange" if value <= 10 else "red"
    if key == "reserves":
        value = _numeric(c, key, 0) or 0
        stability = c.get("qualitative", {}).get("currency_stability", 50)
        if value >= 100 or stability >= 80:
            return "green"
        if value >= 20:
            return "orange"
        return "red"
    if key == "rating":
        score = rating_score(c)
        return "green" if score >= 80 else "orange" if score >= 50 else "red"
    if key == "cds":
        value = _numeric(c, key)
        if value is None:
            return "red"
        return "green" if value <= 100 else "orange" if value <= 300 else "red"
    if key == "crp":
        value = country_risk_premium(c)[0]
        return "green" if value <= 2 else "orange" if value <= 6 else "red"
    if key == "equity_index":
        value = _get_indicator(c, key).get("perf_1y", 0) or 0
        return "green" if value >= 0 else "orange" if value >= -10 else "red"
    if key == "currency":
        stability = c.get("qualitative", {}).get("currency_stability", 50)
        return "green" if stability >= 70 else "orange" if stability >= 45 else "red"
    return "orange"


def component_scores(country: dict[str, Any]) -> dict[str, float]:
    growth = _numeric(country, "gdp_growth", 0) or 0
    unemployment = _numeric(country, "unemployment", 0) or 0
    inflation = _numeric(country, "inflation", 0) or 0
    policy = _numeric(country, "policy_rate", 0) or 0
    debt = _numeric(country, "debt_gdp", 0) or 0
    cds = _numeric(country, "cds")
    q = country.get("qualitative", {})

    growth_s = linear(growth, -2.0, 5.0)
    unemployment_s = linear(unemployment, 2.0, 20.0, reverse=True)
    outlook_s = float(q.get("outlook", 50))
    inflation_s = clamp(100 - abs(inflation - 2.0) * 4.0)
    real_rate = policy - inflation
    if -1.0 <= real_rate <= 2.0:
        rate_s = 95.0
    elif -3.0 <= real_rate <= 4.0:
        rate_s = 72.0
    elif -8.0 <= real_rate <= 6.0:
        rate_s = 40.0
    else:
        rate_s = 8.0
    currency_s = float(q.get("currency_stability", 50))
    debt_s = linear(debt, 20.0, 180.0, reverse=True)
    rating_s = rating_score(country)
    cds_s = cds_score(cds)
    governance_s = float(q.get("governance", 50))
    resilience_s = float(q.get("resilience", 50))
    business_s = float(q.get("business", 50))
    openness_s = float(q.get("openness", 50))

    return {
        "dynamisme": round(0.55 * growth_s + 0.20 * unemployment_s + 0.25 * outlook_s, 1),
        "stabilite": round(0.45 * inflation_s + 0.15 * rate_s + 0.40 * currency_s, 1),
        "solvabilite": round(0.30 * debt_s + 0.40 * rating_s + 0.30 * cds_s, 1),
        "institutions": round(0.60 * governance_s + 0.40 * resilience_s, 1),
        "ouverture": round(0.60 * business_s + 0.40 * openness_s, 1),
    }


def overall_score(country: dict[str, Any], profile: str = "Équilibré") -> dict[str, Any]:
    profile = profile if profile in PROFILES else "Équilibré"
    weights = PROFILES[profile]["weights"]
    components = component_scores(country)
    score = sum(components[key] * weights[key] for key in weights)
    risk = clamp(
        100
        - (0.40 * components["stabilite"] + 0.35 * components["solvabilite"] + 0.25 * components["institutions"])
    )
    volatility = round(10 + risk * 0.48, 1)
    ke = required_return(country)
    verdict, verdict_reason = decide_verdict(score, components, country)
    return {
        "score": round(score, 1),
        "profile": profile,
        "weights": weights,
        "components": components,
        "risk": round(risk, 1),
        "volatility": volatility,
        "ke": ke,
        "verdict": verdict,
        "verdict_reason": verdict_reason,
    }


def decide_verdict(score: float, components: dict[str, float], country: dict[str, Any]) -> tuple[str, str]:
    # Un pays sans notation active ni CDS ne peut pas être "Investir".
    missing_market_signal = (
        rating_of(country) in {"NR", "D", "RD"} and _numeric(country, "cds") is None
    )
    if score >= 76 and not missing_market_signal:
        return "Investir", VERDICT_STYLES["Investir"]["copy"]
    if score >= 62 and not missing_market_signal:
        return "Investir avec prudence", VERDICT_STYLES["Investir avec prudence"]["copy"]
    if score >= 45 or (score >= 38 and components["dynamisme"] >= 55):
        return "Attendre", VERDICT_STYLES["Attendre"]["copy"]
    return "Éviter", VERDICT_STYLES["Éviter"]["copy"]


def score_breakdown(country: dict[str, Any], profile: str = "Équilibré") -> list[dict[str, Any]]:
    result = overall_score(country, profile)
    rows = []
    for key, label in COMPONENT_LABELS.items():
        weight = result["weights"][key]
        raw = result["components"][key]
        rows.append(
            {
                "key": key,
                "label": label,
                "score": raw,
                "weight": weight,
                "contribution": round(raw * weight, 1),
                "max": round(weight * 100, 1),
            }
        )
    return rows


def top_reasons(country: dict[str, Any], profile: str = "Équilibré", limit: int = 3) -> list[dict[str, str]]:
    """Deux forces structurantes + le principal point de vigilance."""
    result = overall_score(country, profile)
    components = result["components"]
    strengths = sorted(
        ((key, value) for key, value in components.items()),
        key=lambda item: item[1],
        reverse=True,
    )
    weakness = min(components.items(), key=lambda item: item[1])
    reasons: list[dict[str, str]] = []
    for key, value in strengths[:2]:
        reasons.append(
            {
                "kind": "positive",
                "title": COMPONENT_LABELS[key],
                "text": f"Score de {value:.0f}/100. {_component_comment(key, value, positive=True)}",
            }
        )
    reasons.append(
        {
            "kind": "negative",
            "title": f"Point de vigilance : {COMPONENT_LABELS[weakness[0]]}",
            "text": f"Score de {weakness[1]:.0f}/100. {_component_comment(weakness[0], weakness[1], positive=False)}",
        }
    )
    return reasons[:limit]


def _component_comment(key: str, value: float, positive: bool) -> str:
    if key == "dynamisme":
        return "La croissance, l'emploi et l'élan économique soutiennent la demande." if positive else "Le moteur de croissance est fragile, ce qui réduit la visibilité."
    if key == "stabilite":
        return "L'inflation, le taux directeur et la devise forment un cadre prévisible." if positive else "L'inflation ou la devise rendent le cadre macroéconomique moins lisible."
    if key == "solvabilite":
        return "La dette, la notation et les CDS signalent une capacité de remboursement crédible." if positive else "La dette ou l'absence de prix de marché pèsent sur la signature souveraine."
    if key == "institutions":
        return "La gouvernance et la capacité de rebond historique rassurent l'investisseur." if positive else "La gouvernance et la continuité institutionnelle restent des angles morts."
    return "L'ouverture et le climat des affaires facilitent l'implantation." if positive else "Les frictions administratives ou commerciales renchérissent l'entrée."


def status_label(status: str) -> str:
    return {"green": "Solide", "orange": "Vigilance", "red": "Risque"}.get(status, "Vigilance")


def risk_label(risk: float) -> str:
    if risk < 30:
        return "Faible"
    if risk < 50:
        return "Modéré"
    if risk < 70:
        return "Élevé"
    return "Très élevé"


def correlation(group_a: str, group_b: str) -> float:
    if group_a == group_b:
        return 0.80 if group_a != "frontier" else 0.60
    pair = {group_a, group_b}
    if pair == {"developed", "emerging"}:
        return 0.55
    if pair == {"developed", "gulf"}:
        return 0.50
    if pair == {"developed", "frontier"}:
        return 0.30
    if pair == {"emerging", "gulf"}:
        return 0.60
    if pair == {"emerging", "frontier"}:
        return 0.40
    if pair == {"gulf", "frontier"}:
        return 0.35
    return 0.45


def portfolio_metrics(holdings: list[dict[str, Any]]) -> dict[str, Any]:
    """Calcule rendement exigé, volatilité et diversification d'un portefeuille.

    holdings: [{"country": country_dict, "weight": 0.25, "amount": 25000}, ...]
    """
    active = [h for h in holdings if h.get("weight", 0) > 0]
    total_weight = sum(h["weight"] for h in active)
    if total_weight <= 0:
        return {
            "expected_return": 0,
            "volatility": 0,
            "diversification": 0,
            "hhi": 0,
            "effective_countries": 0,
            "top_weight": 0,
            "top_country": "—",
            "weighted_vol": 0,
        }
    normalized = [{**h, "weight": h["weight"] / total_weight} for h in active]
    expected = sum(h["weight"] * required_return(h["country"])["ke"] for h in normalized)
    weighted_vol = sum(h["weight"] * overall_score(h["country"])["volatility"] for h in normalized)
    variance = 0.0
    for i, hi in enumerate(normalized):
        for j, hj in enumerate(normalized):
            sigma_i = overall_score(hi["country"])["volatility"]
            sigma_j = overall_score(hj["country"])["volatility"]
            rho = 1.0 if i == j else correlation(hi["country"]["group_key"], hj["country"]["group_key"])
            variance += hi["weight"] * hj["weight"] * sigma_i * sigma_j * rho
    volatility = math.sqrt(max(variance, 0))
    hhi = sum(h["weight"] ** 2 for h in normalized)
    top = max(normalized, key=lambda h: h["weight"])
    return {
        "expected_return": round(expected, 2),
        "volatility": round(volatility, 1),
        "diversification": round(weighted_vol - volatility, 1),
        "hhi": round(hhi, 3),
        "effective_countries": round(1 / hhi, 1) if hhi else 0,
        "top_weight": round(top["weight"] * 100, 1),
        "top_country": top["country"]["name"],
        "weighted_vol": round(weighted_vol, 1),
    }
