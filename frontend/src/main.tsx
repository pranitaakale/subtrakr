import {FormEvent, useEffect, useState} from "react";
import {createRoot} from "react-dom/client";
import {Bot, CheckCircle2, CircleAlert, Sparkles, Upload} from "lucide-react";
import "./styles.css";

// const API = '/api'
const API = import.meta.env.VITE_API_URL;
type Subscription = {
  id: number;
  merchant: string;
  average_amount: number;
  cadence_days: number;
  transaction_count: number;
  confidence: number;
  status: string;
  value_rating: number | null;
  value_score: number;
  renewal_risk: number;
  recommendation: string;
  ml_probability?: number;
  ml_explanation?: string[];
};
type Dashboard = {
  total_candidates: number;
  active_subscriptions: number;
  pending_review: number;
  estimated_monthly_spend: number;
  high_risk_count: number;
};
type ModelStatus = {
  available: boolean;
  message?: string;
  feature_names?: string[];
  trained_on?: string;
  sample_count?: number;
  human_label_count?: number;
  metrics?: {
    precision: number;
    recall: number;
    f1: number;
    roc_auc: number | null;
  };
};

function App() {
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [model, setModel] = useState<ModelStatus | null>(null);
  const [message, setMessage] = useState(
    "Upload a CSV to find recurring charges.",
  );
  const [loading, setLoading] = useState(false);
  const [question, setQuestion] = useState(
    "Which subscriptions should I review first?",
  );
  const [analystAnswer, setAnalystAnswer] = useState(
    "Ask the grounded AI analyst about your detected subscriptions.",
  );
  const [asking, setAsking] = useState(false);
  const refresh = async () => {
    const [subs, dash, status] = await Promise.all([
      fetch(`${API}/subscriptions`).then((r) => r.json()),
      fetch(`${API}/dashboard`).then((r) => r.json()),
      fetch(`${API}/ml/status`).then((r) => r.json()),
    ]);
    setSubscriptions(subs);
    setDashboard(dash);
    setModel(status);
  };
  useEffect(() => {
    refresh().catch(() => setMessage("Start the API server to use SubTrackr."));
  }, []);
  const upload = async (file: File) => {
    setLoading(true);
    const form = new FormData();
    form.append("file", file);
    try {
      const r = await fetch(`${API}/uploads`, {method: "POST", body: form});
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail);
      setMessage(
        `Imported ${data.transactions_imported} transactions and found ${data.recurring_candidates} recurring candidates.`,
      );
      await refresh();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Upload failed.");
    } finally {
      setLoading(false);
    }
  };
  const review = async (id: number, status: string, value_rating?: number) => {
    await fetch(`${API}/subscriptions/${id}/review`, {
      method: "PATCH",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({status, value_rating}),
    });
    await refresh();
  };
  const askAnalyst = async (event: FormEvent) => {
    event.preventDefault();
    setAsking(true);
    try {
      const r = await fetch(`${API}/analyst`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({question}),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail);
      setAnalystAnswer(data.answer);
    } catch (e) {
      setAnalystAnswer(
        e instanceof Error
          ? e.message
          : "The analyst could not answer right now.",
      );
    } finally {
      setAsking(false);
    }
  };
  return (
    <main>
      <header>
        <div>
          <p className="eyebrow">PERSONAL FINANCE, CLARIFIED</p>
          <h1>SubTrackr</h1>
        </div>
        <p>ML-powered subscription intelligence.</p>
      </header>
      <section className="upload">
        <Upload size={25} />
        <div>
          <strong>
            {loading
              ? "Engineering features and training…"
              : "Import transaction history"}
          </strong>
          <span>{message}</span>
        </div>
        <label className="button">
          Choose CSV
          <input
            type="file"
            accept=".csv"
            onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])}
          />
        </label>
      </section>
      <section className="metrics">
        <Metric
          label="Detected candidates"
          value={dashboard?.total_candidates ?? "—"}
        />
        <Metric
          label="Needs your review"
          value={dashboard?.pending_review ?? "—"}
        />
        <Metric
          label="Active subscriptions"
          value={dashboard?.active_subscriptions ?? "—"}
        />
        <Metric
          label="Monthly spend"
          value={
            dashboard ? `$${dashboard.estimated_monthly_spend.toFixed(2)}` : "—"
          }
        />
      </section>
      <section className="model-panel">
        <div className="panel-heading">
          <Sparkles size={20} />
          <div>
            <p className="eyebrow">TRAINABLE CLASSIFIER</p>
            <h2>Model health</h2>
          </div>
        </div>
        {model?.available ? (
          <>
            <p>
              Logistic regression is trained on merchant-level behavioral
              features. Human confirmations and dismissals override bootstrap
              labels.
            </p>
            <div className="model-stats">
              <Metric
                label="Holdout precision"
                value={model.metrics?.precision ?? "—"}
              />
              <Metric label="Recall" value={model.metrics?.recall ?? "—"} />
              <Metric label="F1 score" value={model.metrics?.f1 ?? "—"} />
              <Metric
                label="Human labels"
                value={model.human_label_count ?? 0}
              />
            </div>
            <small>Features: {model.feature_names?.join(" · ")}</small>
          </>
        ) : (
          <p>{model?.message ?? "Checking model status…"}</p>
        )}
      </section>
      <section className="analyst">
        <div className="panel-heading">
          <Bot size={20} />
          <div>
            <p className="eyebrow">GROUNDED GENAI</p>
            <h2>Subscription analyst</h2>
          </div>
        </div>
        <p>
          Answers are constrained to the subscriptions, dashboard totals, model
          probabilities, and explanations in this app.
        </p>
        <form onSubmit={askAnalyst}>
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            aria-label="Question for analyst"
          />
          <button className="primary" disabled={asking}>
            {asking ? "Thinking…" : "Ask analyst"}
          </button>
        </form>
        <div className="analyst-answer">{analystAnswer}</div>
      </section>
      <section>
        <div className="section-title">
          <div>
            <p className="eyebrow">REVIEW QUEUE</p>
            <h2>Subscription signals</h2>
          </div>
          <span>{subscriptions.length} found</span>
        </div>
        {subscriptions.length === 0 ? (
          <div className="empty">
            No candidates yet. Try the sample CSV from the project folder.
          </div>
        ) : (
          <div className="cards">
            {subscriptions.map((s) => (
              <article className="card" key={s.id}>
                <div className="card-top">
                  <div>
                    <h3>{s.merchant}</h3>
                    <p>
                      ${s.average_amount.toFixed(2)} · every {s.cadence_days}{" "}
                      days · {Math.round(s.confidence * 100)}% rule confidence
                    </p>
                  </div>
                  <Risk risk={s.renewal_risk} />
                </div>
                {s.ml_probability !== undefined && (
                  <div className="ml-evidence">
                    <strong>
                      ML probability: {Math.round(s.ml_probability * 100)}%
                    </strong>
                    <span>{s.ml_explanation?.join(" · ")}</span>
                  </div>
                )}
                <p className="recommendation">{s.recommendation}</p>
                {s.status === "pending" ? (
                  <div className="actions">
                    <button onClick={() => review(s.id, "dismissed")}>
                      Not a subscription
                    </button>
                    <button
                      className="primary"
                      onClick={() => review(s.id, "confirmed", 3)}
                    >
                      Confirm subscription
                    </button>
                  </div>
                ) : (
                  <div className="feedback">
                    <span>
                      {s.status === "confirmed" ? (
                        <CheckCircle2 size={17} />
                      ) : (
                        <CircleAlert size={17} />
                      )}{" "}
                      {s.status === "confirmed"
                        ? `Confirmed · Value score ${s.value_score}/100`
                        : "Dismissed"}
                    </span>
                    {s.status === "confirmed" && (
                      <div className="ratings">
                        How valuable?{" "}
                        {[1, 2, 3, 4, 5].map((n) => (
                          <button
                            className={s.value_rating === n ? "selected" : ""}
                            key={n}
                            onClick={() => review(s.id, "confirmed", n)}
                          >
                            {n}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
function Metric({label, value}: {label: string; value: string | number}) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
function Risk({risk}: {risk: number}) {
  return (
    <div
      className={`risk ${risk >= 70 ? "high" : risk >= 50 ? "medium" : "low"}`}
    >
      <span>Renewal risk</span>
      <strong>{risk}/100</strong>
    </div>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
