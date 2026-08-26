# SubTrackr — AI-Powered Subscription Intelligence

> Turn transaction history into actionable subscription insights.

SubTrackr is a full-stack financial intelligence application that analyzes transaction data to identify recurring payments and potential subscriptions. It helps users understand their subscription spending through **automated recurring transaction detection, subscription value scoring, renewal-risk analysis, and actionable recommendations**.

The application follows a simple principle:

> **Automatically infer everything possible from transaction data, then ask the user only for the minimum information required to personalize recommendations.**

---

## The Problem

Subscription spending is often fragmented across multiple services. Small recurring charges can easily go unnoticed, making it difficult for users to understand:

- Which subscriptions are currently active?
- How much are they spending every month?
- Which recurring payments are actually subscriptions?
- Which services may no longer provide enough value?
- Which subscriptions should be reviewed before renewal?

Transaction histories contain useful information, but users typically do not have an intelligent system that converts those records into clear, actionable subscription insights.

---

## 💡 The Solution

SubTrackr analyzes transaction patterns to identify likely recurring payments and potential subscriptions. Users only need to confirm uncertain results and provide minimal feedback where transaction data alone cannot determine personal value.

The system then combines financial patterns and user feedback to generate:

- Subscription insights
- Subscription Value Scores
- Renewal-risk indicators
- Explainable recommendations

---

## ✨ Key Features

### Transaction CSV Upload

Upload transaction history using a CSV file.

### Recurring Payment Detection

Analyze payment intervals, frequency, and amount consistency to identify likely recurring charges.

### Subscription Review

Review, confirm, or dismiss detected recurring payments to distinguish subscriptions from other recurring expenses.

### Subscription Value Score

Evaluate subscriptions using available financial information and minimal user feedback.

### Renewal Risk Analysis

Identify subscriptions that may require attention before their next expected renewal.

### Explainable Recommendations

Present actionable insights and the factors contributing to each recommendation instead of displaying unexplained scores.

---

## Application Flow

```text
Transaction CSV
      ↓
Data Parsing & Normalization
      ↓
Merchant & Transaction Analysis
      ↓
Recurring Payment Detection
      ↓
Subscription Confirmation
      ↓
Minimal User Feedback
      ↓
Value Scoring + Renewal Risk Analysis
      ↓
Explainable Recommendations
      ↓
Subscription Dashboard
```

---

## Architecture

```text
                    ┌──────────────────────┐
                    │   React Frontend     │
                    │  Upload + Dashboard  │
                    └───────────┬──────────┘
                                │
                                ▼
                    ┌──────────────────────┐
                    │    FastAPI Backend   │
                    │    REST API Layer    │
                    └───────────┬──────────┘
                                │
             ┌──────────────────┼──────────────────┐
             ▼                  ▼                  ▼
      Data Processing     Intelligence Engine    Database
          Pipeline        Scoring & Risk Logic    Storage
             │                  │
             └──────────────────┼──────────────────┘
                                ▼
                    Personalized Recommendations
```

---

## Tech Stack

### Backend

- Python
- FastAPI
- SQLAlchemy
- SQLite

### Frontend

- React
- TypeScript
- Vite

### Data & Intelligence

- Transaction pattern analysis
- Recurring payment detection
- Rule-based / weighted value scoring
- Renewal-risk heuristics

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js
- npm

### 1. Clone the Repository

```bash
git clone https://github.com/pranitaakale/subtrakr.git
cd subtrakr
```

### 2. Start the Backend

```bash
cd backend
python -m venv .venv
```

#### Windows PowerShell

```bash
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI server:

```bash
uvicorn app.main:app --reload --port 8000
```

The backend API will be available at:

```text
http://localhost:8000
```

### 3. Start the Frontend

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the URL displayed by Vite, typically:

```text
http://localhost:5173
```

---

## 📁 Input Data Format

SubTrackr accepts transaction CSV files containing transaction dates, descriptions or merchants, and amounts.

Example:

```csv
date,description,amount
2026-01-05,NETFLIX.COM,649
2026-02-05,NETFLIX.COM,649
2026-03-05,NETFLIX.COM,649
2026-01-10,SPOTIFY,119
```

Common column names may include:

- `date`
- `transaction_date`
- `description`
- `merchant`
- `amount`
- `debit`
- `credit`

---

## 📊 How the Intelligence Layer Works

### Subscription Detection

The system groups transactions by merchant and analyzes:

- Payment frequency
- Time between transactions
- Amount consistency
- Historical payment patterns

A recurring pattern is then classified as a potential subscription or recurring expense.

### Subscription Value Score

The Value Score combines available information such as:

- Subscription cost
- Payment history
- Subscription duration
- User-reported usage frequency
- User-reported importance
- Potential overlap with similar services

The score helps categorize subscriptions as:

- **High Value**
- **Moderate Value**
- **Low Value**

### Renewal Risk

The system identifies subscriptions that may need review before their next expected renewal by considering signals such as:

- Low Value Score
- Low recent usage
- Declining interest
- High cost
- Potential subscription overlap

> **Note:** The current version uses transparent scoring and heuristic-based intelligence. Future versions will incorporate trained and evaluated machine-learning models for subscription classification and renewal-risk prediction.

---

## 🗺️ Project Roadmap

### Current MVP

- [x] Transaction CSV upload
- [x] Data parsing and normalization
- [x] Recurring payment detection
- [x] Subscription identification
- [x] Subscription confirmation workflow
- [x] Minimal personalization
- [x] Subscription Value Score
- [x] Renewal-risk insights
- [x] Dashboard

### Future Improvements

- [ ] User authentication
- [ ] PostgreSQL database
- [ ] Improved ML-based subscription classification
- [ ] Trained renewal-risk prediction model
- [ ] Model explainability
- [ ] Renewal notifications
- [ ] Docker containerization
- [ ] Cloud deployment
- [ ] Secure bank or payment integrations

---

## 📸 Screenshots

_Add screenshots or GIFs of the application here._

Suggested screenshots:

1. Transaction upload page
2. Detected subscriptions and confirmation workflow
3. Subscription intelligence dashboard
4. Value Score and Renewal Risk recommendation

---

## 📌 Portfolio Summary

**SubTrackr is an AI-powered subscription intelligence platform that analyzes transaction data to detect recurring payments, identify potential subscriptions, evaluate subscription value, and generate personalized renewal recommendations.**

The project demonstrates an end-to-end data product pipeline:

> **Raw Transaction Data → Data Processing → Pattern Detection → Subscription Intelligence → Personalized Recommendations → User Dashboard**

---

## 🤝 Contributing

Contributions, suggestions, and improvements are welcome. Feel free to fork the repository and submit a pull request.

---

## 📄 License

This project is intended for educational and portfolio purposes. Add an appropriate open-source license if you plan to distribute or reuse the project.
