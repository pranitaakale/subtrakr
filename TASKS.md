# Incremental implementation plan

Use these as small, reviewable commits once the project is initialized with Git.

| Commit | Scope | Completion check |
| --- | --- | --- |
| `chore: scaffold SubTrackr full-stack MVP` | Repository layout, FastAPI, React/Vite, setup documentation | Both services start locally |
| `feat: import and normalize transaction CSVs` | Flexible CSV parser, transaction persistence, sample data | Valid common bank export imports; malformed files show a useful error |
| `feat: detect recurring subscription candidates` | Merchant normalization, cadence and amount-consistency heuristics | Sample dataset detects Netflix, Spotify, and Cloud Storage |
| `feat: add subscription review workflow` | Confirm/dismiss API and one-to-five value feedback | Review updates a candidate without a page reload |
| `feat: add risk-aware subscription dashboard` | Dashboard summary, value score, renewal risk, explainable recommendations | Confirmed subscriptions change monthly spend and risk summary |
| `test: cover ingestion and scoring rules` | API and service tests using pytest | Core rules have regression coverage |
| `chore: productionize persistence and delivery` | Alembic, PostgreSQL, auth, Docker, CI | Deployable environment with migration path |

## Next engineering tasks

- Add unit tests for date/amount formats, repeated uploads, and score boundaries.
- Add an upload identifier and user scope before enabling multi-user use.
- Add a predicted next renewal date from the most recent transaction.
- Replace the prototype risk rule with a model only after collecting labels and establishing baseline metrics.
- Add data retention, encryption, authentication, and consent screens before handling real financial data in production.
