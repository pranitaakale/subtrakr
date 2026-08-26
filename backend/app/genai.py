"""Grounded GenAI layer: only subscription aggregates are sent to the model."""
from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI


SYSTEM_PROMPT = """You are SubTrackr Analyst. Answer only from the supplied structured subscription data.
Do not invent merchants, charges, dates, savings, or account information. State uncertainty when data is missing.
Give concise, actionable personal-finance observations, not financial advice. Mention that suggestions need user review."""


def local_answer(question: str, context: dict[str, Any]) -> str:
    """Deterministic grounded summary when OpenAI is unavailable."""
    dashboard = context.get("dashboard", {})
    subscriptions = context.get("subscriptions", [])
    pending = [item for item in subscriptions if item.get("status") == "pending"]
    confirmed = [item for item in subscriptions if item.get("status") == "confirmed"]
    high_risk = [item for item in confirmed if item.get("renewal_risk", 0) >= 70]
    top_ml = sorted(
        (item for item in subscriptions if item.get("ml_probability") is not None),
        key=lambda item: item.get("ml_probability", 0),
        reverse=True,
    )[:3]
    question_lower = question.lower()

    if not subscriptions:
        return "No subscription data is loaded yet. Upload a transaction CSV first, then ask about review priorities or monthly spend."

    if any(word in question_lower for word in ("review", "priorit", "first", "start")):
        names = [item["merchant"] for item in (pending or sorted(subscriptions, key=lambda item: item.get("renewal_risk", 0), reverse=True))]
        return (
            f"Start with {', '.join(names[:3])}. "
            f"{dashboard.get('pending_review', len(pending))} candidates still need review. "
            "Confirm real subscriptions and dismiss one-off merchants so the classifier can learn from your feedback."
        )

    if any(word in question_lower for word in ("risk", "cancel", "renew")):
        if not high_risk:
            return "No confirmed subscriptions are currently flagged as high renewal risk. Review pending candidates before the next billing cycle."
        return (
            f"Highest renewal risk among confirmed subscriptions: {', '.join(item['merchant'] for item in high_risk)}. "
            "These have elevated cost or low value ratings in the current dashboard."
        )

    if any(word in question_lower for word in ("spend", "cost", "monthly", "budget")):
        spend = dashboard.get("estimated_monthly_spend")
        return (
            f"Confirmed subscriptions are estimated at ${spend:.2f}/month across {dashboard.get('active_subscriptions', len(confirmed))} active items. "
            "Use the value ratings after confirming each subscription to refine this view."
        )

    if any(word in question_lower for word in ("ml", "model", "probability", "classifier")):
        if not top_ml:
            return "The recurring-payment classifier has not trained yet. Upload more transaction history or confirm/dismiss candidates to generate merchant-level labels."
        summary = "; ".join(
            f"{item['merchant']} ({int(item['ml_probability'] * 100)}%: {item.get('ml_explanation', [''])[0]})"
            for item in top_ml
        )
        return f"Strongest ML recurring-payment signals: {summary}."

    return (
        f"You have {dashboard.get('total_candidates', len(subscriptions))} detected candidates, "
        f"{dashboard.get('pending_review', len(pending))} pending review, and about ${dashboard.get('estimated_monthly_spend', 0):.2f}/month in confirmed spend. "
        "Ask about review priorities, renewal risk, monthly spend, or ML probabilities."
    )


def answer(question: str, context: dict[str, Any]) -> dict[str, str]:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return {"answer": local_answer(question, context), "mode": "local_grounded"}
    try:
        client = OpenAI(api_key=key)
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            input=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": f"Question: {question}\n\nGrounded data:\n{json.dumps(context, default=str)}"}],
        )
        return {"answer": response.output_text, "mode": "openai_grounded"}
    except Exception as exc:
        return {"answer": local_answer(question, context), "mode": f"local_fallback:{exc.__class__.__name__}"}
