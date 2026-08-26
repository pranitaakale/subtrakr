# SubTrackr

SubTrackr turns a transaction CSV into a reviewable subscription inventory. The MVP lets a user upload transactions, identifies likely recurring charges, collects a simple confirmation, and shows subscription value, renewal risk, and actionable recommendations.

## Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, SQLite
- **Frontend:** React, TypeScript, Vite

## Quick start

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open the address printed by Vite (normally `http://localhost:5173`). The frontend expects the API at `http://localhost:8000`.

## CSV format

Upload a CSV containing a date, merchant/description, and amount column. Common column names such as `date`, `transaction_date`, `description`, `merchant`, `amount`, `debit`, and `credit` are accepted. A sample is in `backend/sample_data/transactions.csv`.

## MVP flow

1. Upload a transaction CSV.
2. Review detected recurring charges and confirm or dismiss each one.
3. Give a confirmed subscription a one-to-five value rating (optional).
4. Use the dashboard to review value, renewal risk, and recommendations.

## Delivery roadmap

1. **MVP foundation (included):** upload, parsing, normalization, detection, confirmation, scoring, dashboard.
2. Add authenticated user accounts, PostgreSQL, encrypted file storage, and migrations.
3. Replace heuristic classification/risk with evaluated models and add monitoring.
4. Add bank integrations, notifications, and cloud deployment.
