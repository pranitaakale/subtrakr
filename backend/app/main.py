from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Subscription, Transaction
from .genai import answer
from .ml import model_status, predict, train, transaction_groups
from .services import detect_recurring, parse_csv, scores


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="SubTrackr API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174", "https://subtrakr-two.vercel.app/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ReviewPayload(BaseModel):
    status: str = Field(pattern="^(confirmed|dismissed)$")
    value_rating: int | None = Field(default=None, ge=1, le=5)


class AnalystQuestion(BaseModel):
    question: str = Field(min_length=3, max_length=500)


def stored_rows(db: Session):
    return [{"date": row.transaction_date, "merchant": row.merchant, "normalized": row.normalized_merchant, "amount": row.amount} for row in db.query(Transaction).all()]


def labels(db: Session) -> dict[str, int]:
    return {row.normalized_merchant: int(row.status == "confirmed") for row in db.query(Subscription).filter(Subscription.status.in_(["confirmed", "dismissed"]))}


def subscription_view(row: Subscription, groups: dict[str, list[dict]]):
    result = {"id": row.id, "merchant": row.merchant, "average_amount": row.average_amount, "cadence_days": row.cadence_days, "transaction_count": row.transaction_count, "confidence": row.confidence, "classification": row.classification, "status": row.status, "value_rating": row.value_rating, "value_score": row.value_score, "renewal_risk": row.renewal_risk, "recommendation": row.recommendation}
    prediction = predict(groups.get(row.normalized_merchant, []))
    if prediction:
        result.update({"ml_probability": prediction["probability"], "ml_explanation": prediction["explanation"]})
    return result


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/uploads")
async def upload_transactions(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")
    rows = parse_csv(await file.read())
    db.add_all([Transaction(transaction_date=row["date"], merchant=row["merchant"], normalized_merchant=row["normalized"], amount=row["amount"], source_file=file.filename) for row in rows])
    detected = detect_recurring(rows)
    created = 0
    for item in detected:
        existing = db.query(Subscription).filter_by(normalized_merchant=item["normalized"]).first()
        if existing:
            for key, value in item.items():
                if key != "normalized":
                    setattr(existing, key, value)
            existing.value_score, existing.renewal_risk, existing.recommendation = scores(existing)
        else:
            subscription = Subscription(
                merchant=item["merchant"],
                normalized_merchant=item["normalized"],
                average_amount=item["average_amount"],
                cadence_days=item["cadence_days"],
                transaction_count=item["transaction_count"],
                confidence=item["confidence"],
            )
            subscription.value_score, subscription.renewal_risk, subscription.recommendation = scores(subscription)
            db.add(subscription)
            created += 1
    db.commit()
    training = train(stored_rows(db), labels(db))
    return {"transactions_imported": len(rows), "recurring_candidates": len(detected), "new_subscriptions": created, "training": training}


@app.get("/subscriptions")
def subscriptions(db: Session = Depends(get_db)):
    rows = db.query(Subscription).order_by(Subscription.renewal_risk.desc()).all()
    return [subscription_view(row, transaction_groups(stored_rows(db))) for row in rows]


@app.patch("/subscriptions/{subscription_id}/review")
def review_subscription(subscription_id: int, payload: ReviewPayload, db: Session = Depends(get_db)):
    subscription = db.get(Subscription, subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    subscription.status = payload.status
    subscription.value_rating = payload.value_rating if payload.status == "confirmed" else None
    subscription.value_score, subscription.renewal_risk, subscription.recommendation = scores(subscription)
    db.commit()
    training = train(stored_rows(db), labels(db))
    return {"id": subscription.id, "status": subscription.status, "value_score": subscription.value_score, "renewal_risk": subscription.renewal_risk, "recommendation": subscription.recommendation, "training": training}


@app.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    subscriptions = db.query(Subscription).all()
    active = [item for item in subscriptions if item.status == "confirmed"]
    estimated_monthly = sum(item.average_amount * 30 / item.cadence_days for item in active)
    high_risk = [item for item in active if item.renewal_risk >= 70]
    return {"total_candidates": len(subscriptions), "active_subscriptions": len(active), "pending_review": len([item for item in subscriptions if item.status == "pending"]), "estimated_monthly_spend": round(estimated_monthly, 2), "high_risk_count": len(high_risk), "high_risk_names": [item.merchant for item in high_risk]}


@app.get("/ml/status")
def ml_status():
    return model_status()


@app.post("/ml/retrain")
def retrain(db: Session = Depends(get_db)):
    return train(stored_rows(db), labels(db))


@app.post("/analyst")
def analyst(payload: AnalystQuestion, db: Session = Depends(get_db)):
    subscriptions = db.query(Subscription).all()
    context = {
        "dashboard": dashboard(db),
        "subscriptions": [subscription_view(item, transaction_groups(stored_rows(db))) for item in subscriptions],
        "ml_model": model_status(),
    }
    return answer(payload.question, context)
