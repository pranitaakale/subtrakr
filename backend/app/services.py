import csv
import io
import re
from collections import defaultdict
from datetime import datetime

from fastapi import HTTPException

DATE_COLUMNS = ("date", "transaction_date", "transaction date", "posted date")
MERCHANT_COLUMNS = ("merchant", "description", "name", "payee", "transaction description")
AMOUNT_COLUMNS = ("amount", "debit", "value", "transaction amount")


def _matching_column(fields: list[str], choices: tuple[str, ...]) -> str | None:
    normalized = {field.strip().lower(): field for field in fields}
    return next((normalized[name] for name in choices if name in normalized), None)


def normalize_merchant(value: str) -> str:
    value = re.sub(r"\b(card|purchase|pos|debit|credit|payment|online)\b", "", value.lower())
    value = re.sub(r"[^a-z0-9 ]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:255]


def parse_date(value: str):
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%b %d, %Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unsupported date: {value}")


def parse_amount(value: str) -> float:
    cleaned = value.replace(",", "").replace("$", "").replace("₹", "").strip()
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = f"-{cleaned[1:-1]}"
    return abs(float(cleaned))


def parse_csv(contents: bytes) -> list[dict]:
    try:
        reader = csv.DictReader(io.StringIO(contents.decode("utf-8-sig")))
        if not reader.fieldnames:
            raise ValueError("Missing CSV header")
        date_col = _matching_column(reader.fieldnames, DATE_COLUMNS)
        merchant_col = _matching_column(reader.fieldnames, MERCHANT_COLUMNS)
        amount_col = _matching_column(reader.fieldnames, AMOUNT_COLUMNS)
        if not all((date_col, merchant_col, amount_col)):
            raise ValueError("CSV needs a date, merchant/description, and amount column")
        rows = []
        for row in reader:
            if not row.get(merchant_col) or not row.get(amount_col):
                continue
            amount = parse_amount(row[amount_col])
            if amount == 0:
                continue
            merchant = row[merchant_col].strip()
            rows.append({"date": parse_date(row[date_col]), "merchant": merchant, "normalized": normalize_merchant(merchant), "amount": amount})
        if not rows:
            raise ValueError("No usable transaction rows found")
        return rows
    except (UnicodeDecodeError, ValueError, csv.Error) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def detect_recurring(transactions: list[dict]) -> list[dict]:
    groups = defaultdict(list)
    for tx in transactions:
        groups[tx["normalized"]].append(tx)
    detected = []
    for merchant, entries in groups.items():
        entries.sort(key=lambda item: item["date"])
        if len(entries) < 2:
            continue
        intervals = [(entries[index]["date"] - entries[index - 1]["date"]).days for index in range(1, len(entries))]
        avg_interval = sum(intervals) / len(intervals)
        avg_amount = sum(item["amount"] for item in entries) / len(entries)
        amount_variance = max(abs(item["amount"] - avg_amount) / avg_amount for item in entries) if avg_amount else 1
        cadence_match = min((abs(avg_interval - cadence), cadence) for cadence in (7, 14, 30, 90, 365))[1]
        interval_consistency = sum(abs(interval - avg_interval) <= max(3, avg_interval * 0.2) for interval in intervals) / len(intervals)
        confidence = min(0.98, 0.35 + 0.2 * len(entries) + 0.25 * interval_consistency + 0.2 * (1 - min(amount_variance, 1)))
        if confidence >= 0.65 and cadence_match in (7, 14, 30, 90, 365):
            detected.append({"merchant": entries[-1]["merchant"], "normalized": merchant, "average_amount": round(avg_amount, 2), "cadence_days": cadence_match, "transaction_count": len(entries), "confidence": round(confidence, 2)})
    return detected


def scores(subscription) -> tuple[float, float, str]:
    monthly_cost = subscription.average_amount * (30 / subscription.cadence_days)
    value = 50 if subscription.value_rating is None else subscription.value_rating * 20
    value_score = max(0, min(100, value - min(30, monthly_cost / 10)))
    risk = 40 + min(35, monthly_cost / 8) + (20 if subscription.value_rating and subscription.value_rating <= 2 else 0)
    risk = max(0, min(100, risk))
    if subscription.status == "dismissed":
        recommendation = "Dismissed during review; no action needed."
    elif risk >= 70:
        recommendation = "High renewal risk: consider cancelling or downgrading before the next billing date."
    elif value_score < 45:
        recommendation = "Low value for its cost: review usage and consider a lower-cost plan."
    else:
        recommendation = "Looks reasonable based on the available transaction and feedback data."
    return round(value_score, 1), round(risk, 1), recommendation
