"""Couche IA optionnelle.

L'IA ne reçoit que des faits déjà validés dans la base GeoCapital.
Sans clé API, l'application reste entièrement fonctionnelle grâce aux
contenus éditoriaux et aux explications déterministes.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = os.getenv("GEOCAPITAL_MODEL", "claude-haiku-4-5-20251001")
MAX_TOKENS = 700

SYSTEM_RULES = """Tu es l'analyste pédagogique de GeoCapital.
Règles absolues :
- Explique uniquement à partir des faits fournis dans le message.
- N'invente aucun chiffre, aucune date, aucune notation et aucun événement.
- Si une donnée manque, dis-le et traite le vide comme un signal de prudence.
- Écris en français clair, pour un étudiant ou un jeune investisseur.
- Pas de conseil financier personnalisé. Termine par une nuance pédagogique si utile.
- Format : 120 à 180 mots, paragraphes courts, ton précis et vivant.
"""


def api_key() -> str | None:
    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if key:
        return key
    try:
        import streamlit as st

        secret = st.secrets.get("ANTHROPIC_API_KEY", "")
        return str(secret).strip() or None
    except Exception:
        return None


def is_available() -> bool:
    return bool(api_key())


def _call(prompt: str, max_tokens: int = MAX_TOKENS) -> str | None:
    key = api_key()
    if not key:
        return None
    payload = {
        "model": DEFAULT_MODEL,
        "max_tokens": max_tokens,
        "temperature": 0.2,
        "system": SYSTEM_RULES,
        "messages": [{"role": "user", "content": prompt}],
    }
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
        blocks = data.get("content", [])
        text = " ".join(block.get("text", "") for block in blocks if block.get("type") == "text")
        return text.strip() or None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, KeyError):
        return None


def country_brief(country: dict[str, Any], score_payload: dict[str, Any]) -> str | None:
    facts = {
        "pays": country["name"],
        "résumé_éditorial": country.get("summary"),
        "profil": score_payload.get("profile"),
        "score": score_payload.get("score"),
        "verdict": score_payload.get("verdict"),
        "rendement_exigé": score_payload.get("ke"),
        "forces": country.get("strengths", []),
        "risques": country.get("risks", []),
        "indicateurs": {
            k: v.get("value") for k, v in country.get("indicators", {}).items()
        },
    }
    prompt = (
        "Rédige la synthèse GeoCapital de ce pays en 3 minutes de lecture. "
        "Relie une cause historique à un risque financier actuel, puis explique le verdict. "
        "N'ajoute aucun chiffre absent des faits.\n\nFAITS:\n"
        + json.dumps(facts, ensure_ascii=False, indent=2)
    )
    return _call(prompt)


def explain_verdict(country: dict[str, Any], score_payload: dict[str, Any]) -> str | None:
    facts = {
        "pays": country["name"],
        "score": score_payload.get("score"),
        "verdict": score_payload.get("verdict"),
        "composantes": score_payload.get("components"),
        "rendement_exigé": score_payload.get("ke"),
        "risque": score_payload.get("risk"),
    }
    prompt = (
        "Explique ce verdict d'investissement à un débutant. "
        "Décompose en : ce que le score mesure, pourquoi ce pays obtient ce résultat, "
        "et ce que le rendement exigé signifie concrètement. "
        "N'ajoute aucun chiffre absent des faits.\n\nFAITS:\n"
        + json.dumps(facts, ensure_ascii=False, indent=2)
    )
    return _call(prompt, max_tokens=500)


def decode_event(event: dict[str, Any], country: dict[str, Any]) -> str | None:
    facts = {
        "pays": country["name"],
        "événement": event.get("title"),
        "date": event.get("date"),
        "chaîne_causale": [step.get("text") for step in event.get("chain", [])],
        "gagnants": event.get("winners"),
        "perdants": event.get("losers"),
        "écho_historique": event.get("history"),
        "concepts": event.get("concepts"),
    }
    prompt = (
        "Explique cet événement en chaîne causale : fait → économie → finance → gagnants/perdants. "
        "Termine par l'écho historique fourni. N'invente aucun chiffre ni événement.\n\nFAITS:\n"
        + json.dumps(facts, ensure_ascii=False, indent=2)
    )
    return _call(prompt, max_tokens=550)


def portfolio_commentary(
    country_facts: list[dict[str, Any]],
    metrics: dict[str, Any],
) -> str | None:
    facts = {
        "allocation": country_facts,
        "rendement_exigé_pondéré": metrics.get("expected_return"),
        "volatilité_estimée": metrics.get("volatility"),
        "diversification": metrics.get("diversification"),
        "concentration_hhi": metrics.get("hhi"),
        "pays_effectifs": metrics.get("effective_countries"),
    }
    prompt = (
        "Commente ce portefeuille pédagogique de 100 000 €. "
        "Explique le rendement exigé, le risque, la diversification et le principal point de concentration. "
        "Ne recommande pas un achat ou une vente et n'ajoute aucun chiffre absent des faits.\n\nFAITS:\n"
        + json.dumps(facts, ensure_ascii=False, indent=2)
    )
    return _call(prompt, max_tokens=500)


def explain_quiz(country: dict[str, Any], question: dict[str, Any], correct: bool) -> str | None:
    facts = {
        "pays": country["name"],
        "question": question.get("question"),
        "bonne_réponse": question.get("options", [None])[question.get("answer", 0)],
        "explication": question.get("explanation"),
        "réponse_de_l_utilisateur_correcte": correct,
    }
    prompt = (
        "Explique la réponse à ce quiz en une notion claire et une phrase de contexte. "
        "Ne donne pas de nouveaux faits.\n\nFAITS:\n"
        + json.dumps(facts, ensure_ascii=False, indent=2)
    )
    return _call(prompt, max_tokens=350)
