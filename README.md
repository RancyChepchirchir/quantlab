# QuantLab

**Quantitative derivatives pricing, implied-volatility calibration, market-data ingestion, and neural-pricing research platform.**

QuantLab is a full-stack quantitative finance research environment for pricing derivatives, studying numerical methods, calibrating implied volatility, comparing European and American option models, and experimenting with machine-learning approaches to option pricing.

The project combines:

- a **FastAPI quantitative backend**,
- a **Next.js research interface**,
- classical derivatives-pricing models,
- numerical solvers,
- implied-volatility inversion,
- real option-market data,
- volatility-smile and surface diagnostics,
- raw SVI fitting,
- arbitrage diagnostics,
- and research-oriented neural pricing experiments.

The goal is not simply to provide an option-price calculator. QuantLab is designed as an extensible laboratory in which multiple pricing methodologies can be compared under a common computational and visualization framework.

---

# 1. Current Status

QuantLab v1 currently includes:

- Black–Scholes European option pricing
- European option Greeks
- Cox–Ross–Rubinstein binomial pricing
- American option pricing
- American implied-volatility inversion
- finite-difference pricing infrastructure
- Monte Carlo pricing experiments
- volatility smile analysis
- ATM volatility term structures
- volatility skew diagnostics
- European put–call parity reference diagnostics
- Black–Scholes versus American-IV comparison
- real end-of-day option-chain ingestion
- Massive market-data integration
- Alpha Vantage integration
- mock market-data provider
- matched call/put contract sampling
- representative-expiry selection
- service-level market-data caching
- provider rate-limit cooldowns
- structured provider error handling
- inverse-distance volatility interpolation
- raw SVI smile calibration
- SVI parameter diagnostics
- basic butterfly-warning diagnostics
- cross-maturity calendar-arbitrage diagnostics
- Next.js volatility research interface
- automated backend testing
- frontend lint/build validation
- GitHub Actions CI
- Railway backend deployment
- Vercel frontend deployment
- production smoke tests
- release validation tooling

---

# 2. Architecture

The project is organised as a monorepo:

```text
quantlab/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── services/
│   │   │   └── market_data/
│   │   │       └── providers/
│   │   └── main.py
│   │
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── app/
│   │   └── volatility-lab/
│   ├── components/
│   ├── lib/
│   │   └── api/
│   ├── package.json
│   ├── package-lock.json
│   └── .env.example
│
├── scripts/
│   ├── release_check.sh
│   ├── smoke_test.py
│   └── version_audit.sh
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
└── README.md
```

The main application flow is:

```text
Market / manual option prices
            │
            ▼
      FastAPI backend
            │
            ├── pricing models
            ├── IV inversion
            ├── diagnostics
            ├── SVI calibration
            └── surface interpolation
            │
            ▼
       JSON API
            │
            ▼
      Next.js frontend
            │
            ├── smiles
            ├── term structure
            ├── skew
            ├── SVI diagnostics
            ├── arbitrage diagnostics
            └── surface visualisation
```

---

# 3. Quantitative Models

## 3.1 Black–Scholes

For a European call option,

\[
C
=
S_0 e^{-qT}N(d_1)
-
K e^{-rT}N(d_2),
\]

where

\[
d_1
=
\frac{
\ln(S_0/K)
+
(r-q+\frac{1}{2}\sigma^2)T
}{
\sigma\sqrt{T}
},
\]

and

\[
d_2
=
d_1-\sigma\sqrt{T}.
\]

For a European put,

\[
P
=
K e^{-rT}N(-d_2)
-
S_0 e^{-qT}N(-d_1).
\]

The principal inputs are:

- spot price \(S_0\),
- strike \(K\),
- risk-free rate \(r\),
- dividend yield \(q\),
- volatility \(\sigma\),
- maturity \(T\).

Black–Scholes is used both as a pricing model and as the European implied-volatility inversion benchmark.

---

# 4. American Option Pricing

American options may be exercised before expiry and therefore generally cannot be priced by the standard Black–Scholes closed form.

QuantLab uses the Cox–Ross–Rubinstein binomial model as the principal American pricing engine.

For time step

\[
\Delta t = \frac{T}{N},
\]

the CRR up/down factors are

\[
u=e^{\sigma\sqrt{\Delta t}},
\]

\[
d=\frac{1}{u},
\]

with risk-neutral probability

\[
p
=
\frac{
e^{(r-q)\Delta t}-d
}{
u-d
}.
\]

At every node, the American option value is

\[
V
=
\max
\left(
V_{\text{exercise}},
V_{\text{continuation}}
\right).
\]

This explicitly represents the early-exercise feature.

---

# 5. Implied Volatility

Given an observed market price \(V_{\text{market}}\), implied volatility solves

\[
V_{\text{model}}(\sigma)
-
V_{\text{market}}
=
0.
\]

QuantLab performs implied-volatility inversion for both:

- European Black–Scholes pricing,
- American CRR pricing.

The Volatility Lab therefore reports:

```text
Observed market price
        │
        ├── Black–Scholes inversion
        │       ↓
        │     BS IV
        │
        └── CRR inversion
                ↓
            American IV
```

The model discrepancy

\[
\Delta IV
=
IV_{\text{American}}
-
IV_{\text{BS}}
\]

is reported for observations where both inversions converge.

---

# 6. Volatility Smile Diagnostics

QuantLab analyses implied volatility across strike and maturity.

For each maturity it calculates quantities including:

- implied volatility by strike,
- nearest-to-money implied volatility,
- volatility skew,
- log-moneyness,
- ATM term structure.

Basic log-moneyness is

\[
k
=
\log
\left(
\frac{K}{S}
\right).
\]

The current implementation uses spot-relative log-moneyness. A future version may use forward log-moneyness when a full forward/dividend term structure is available.

---

# 7. Put–Call Reference Diagnostic

European put–call parity is

\[
C-P
=
S_0 e^{-qT}
-
K e^{-rT}.
\]

QuantLab compares matched observed call and put prices against this relationship.

Because the imported US-listed options may be American-style contracts, the resulting difference is treated as a **reference diagnostic**, not automatically as evidence of arbitrage.

The frontend therefore labels this explicitly as a European parity reference.

---

# 8. Volatility Surface

QuantLab currently provides two approaches to volatility-surface representation.

## 8.1 IDW baseline

A non-parametric inverse-distance weighting interpolation is used as a simple baseline across strike and maturity.

This is useful for:

- visualisation,
- validating surface plumbing,
- comparing parametric and non-parametric fits.

It is not intended to represent a theoretically arbitrage-free volatility model.

---

# 9. SVI

QuantLab implements the raw SVI total-variance parameterisation:

\[
w(k)
=
a
+
b
\left[
\rho(k-m)
+
\sqrt{(k-m)^2+\sigma^2}
\right].
\]

Here,

\[
w(k,T)
=
IV(k,T)^2T.
\]

The five raw-SVI parameters are:

- \(a\): vertical level,
- \(b\): slope scale,
- \(\rho\): asymmetry/skew parameter,
- \(m\): horizontal translation,
- \(\sigma\): curvature scale.

SVI is currently fitted independently for each maturity with at least three distinct strikes.

The API returns:

```text
SVI smile
├── maturity
├── a
├── b
├── rho
├── m
├── sigma
├── RMSE
├── observation count
├── fitted points
└── arbitrage diagnostics
```

The current optimiser is intentionally dependency-light and uses coordinate search.

A future version may replace this with constrained optimisation using SciPy while retaining the same service API.

---

# 10. SVI Arbitrage Diagnostics

## 10.1 Total variance

A fitted SVI smile is checked for non-positive total variance.

A surface with

\[
w(k,T) \leq 0
\]

is considered invalid.

---

## 10.2 Parameter-region checks

The implementation checks basic raw-SVI requirements including:

\[
b \geq 0,
\]

\[
|\rho| < 1,
\]

and

\[
\sigma > 0.
\]

---

## 10.3 Butterfly warning

QuantLab currently implements a conservative diagnostic warning rather than claiming a complete analytical proof of butterfly-arbitrage freedom.

The current checks are intended to surface suspicious fitted smiles for review.

A later version may implement the full Gatheral/Jacquier no-butterfly conditions or move to SSVI.

---

# 11. Calendar-Arbitrage Diagnostics

For adjacent maturities

\[
T_1 < T_2,
\]

the fitted total variance should satisfy

\[
w(k,T_2)
\geq
w(k,T_1)
\]

at common log-moneyness values.

QuantLab evaluates adjacent fitted SVI smiles over their overlapping log-moneyness domain.

For each maturity pair the API reports:

- shorter maturity,
- longer maturity,
- minimum total-variance difference,
- number of violating grid points,
- number of comparison points,
- violation fraction,
- global warning status.

This provides a numerical diagnostic for possible calendar arbitrage.

---

# 12. Market Data

QuantLab uses a provider abstraction rather than coupling the application directly to one market-data service.

Current providers include:

```text
MarketDataProvider
│
├── Mock
├── Massive
└── Alpha Vantage
```

The main API route is:

```http
GET /market-data/options/{symbol}
```

Example:

```bash
curl \
  "http://127.0.0.1:8000/market-data/options/SPY?provider=massive"
```

---

# 13. Massive Integration

Massive is currently used primarily for end-of-day option-market data.

The integration performs:

1. underlying spot retrieval,
2. option-contract discovery,
3. representative-expiry selection,
4. near-ATM strike selection,
5. matched call/put pairing,
6. end-of-day option-price retrieval,
7. normalization into QuantLab's provider-independent schema.

The current sampling strategy targets approximately:

```text
2 representative expiries
×
3 near-ATM strikes
×
2 option types
=
up to 12 option observations
```

The exact number may be lower if provider data is unavailable.

---

# 14. Representative Expiry Selection

QuantLab avoids blindly importing every listed maturity.

The market-data layer selects representative expiries so that the resulting calibration contains cross-maturity information while remaining efficient enough for interactive use.

This supports:

- volatility term structure,
- SVI fitting,
- calendar diagnostics,
- surface interpolation.

---

# 15. Matched Call/Put Selection

At each selected maturity, QuantLab identifies strikes for which both calls and puts are available.

Candidate strikes are ranked primarily by distance from the underlying spot price.

This allows downstream diagnostics such as:

- call/put comparison,
- parity reference calculations,
- American-versus-European IV analysis.

---

# 16. Market-Data Cache

QuantLab has a service-level option-chain cache.

Default TTL:

```text
300 seconds
```

A successful request returns metadata including:

```json
{
  "cache_hit": false,
  "cache_age_seconds": 0.0,
  "cache_ttl_seconds": 300
}
```

A repeated request may return:

```json
{
  "cache_hit": true,
  "cache_age_seconds": 18.4,
  "cache_ttl_seconds": 300
}
```

The endpoint can explicitly bypass the cache:

```http
?refresh=true
```

Example:

```bash
curl \
  "http://127.0.0.1:8000/market-data/options/SPY?provider=massive&refresh=true"
```

Use refresh conservatively because it deliberately contacts the upstream provider.

---

# 17. Provider Failure Cooldown

QuantLab also caches retryable provider failures for a short cooldown period.

This prevents repeated UI clicks from repeatedly contacting a provider that has already returned a rate-limit or temporary upstream failure.

Example response:

```json
{
  "detail": {
    "message": "Massive API rate limit reached.",
    "provider": "massive",
    "upstream_status": 429,
    "retryable": true,
    "cached": true,
    "retry_after_seconds": 42.1
  }
}
```

The frontend converts these into meaningful states such as:

```text
Rate limited
Retryable
Cached provider state
Retry available in ~42 seconds
```

instead of exposing raw Python stack traces.

---

# 18. Volatility Lab

The main research interface is:

```text
/volatility-lab
```

It currently supports:

- manual market inputs,
- demo quotes,
- real market-chain loading,
- market-data cache status,
- selected-expiry metadata,
- market-data error states,
- Black–Scholes IV calibration,
- American CRR IV,
- volatility smiles,
- ATM term structure,
- skew analysis,
- model discrepancy statistics,
- SVI fitting,
- observed-versus-SVI plots,
- SVI parameter diagnostics,
- calendar diagnostics,
- IDW surface visualisation,
- calibrated quote tables.

---

# 19. Local Setup

## Requirements

Recommended:

```text
Python 3.9+
Node.js 20+
npm
Git
```

The project has been developed locally with Python 3.9 and deployed successfully using Railway's supported Python environment.

---

# 20. Backend Setup

From the repository root:

```bash
cd backend

python3 -m venv .venv
```

Activate:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python3 -m pip install --upgrade pip

pip install -r requirements.txt
```

Copy the environment template if required:

```bash
cp .env.example .env
```

Configure provider keys in your shell or deployment environment.

For example:

```bash
export MASSIVE_API_KEY="..."
export ALPHA_VANTAGE_API_KEY="..."
```

Never commit real API keys.

Run FastAPI:

```bash
PYTHONPATH=. uvicorn \
  app.main:app \
  --reload
```

Local backend:

```text
http://127.0.0.1:8000
```

FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

OpenAPI specification:

```text
http://127.0.0.1:8000/openapi.json
```

---

# 21. Frontend Setup

Open another terminal:

```bash
cd frontend

npm install
```

Create:

```bash
cp .env.example .env.local
```

For local development:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

Run:

```bash
npm run dev
```

Frontend:

```text
http://localhost:3000
```

Volatility Lab:

```text
http://localhost:3000/volatility-lab
```

---

# 22. Testing

Run the backend test suite:

```bash
cd backend

PYTHONPATH=. pytest -v
```

Compile the backend:

```bash
python3 -m compileall -q app
```

Frontend lint:

```bash
cd frontend

npm run lint
```

Frontend production build:

```bash
npm run build
```

---

# 23. Release Check

QuantLab includes a complete local release gate:

```bash
cd ~/Projects/quantlab

./scripts/release_check.sh
```

The release checker performs:

```text
Backend compilation
        ↓
Backend pytest suite
        ↓
Frontend ESLint
        ↓
Next.js production build
        ↓
Environment-file safety check
        ↓
Critical Python syntax check
        ↓
Git working-tree status
```

A successful run ends with:

```text
QUANTLAB RELEASE CHECK PASSED
```

---

# 24. Dependency Audit

Run:

```bash
./scripts/version_audit.sh
```

This reports:

- Python version,
- direct backend dependencies,
- installed backend package versions,
- Node version,
- npm version,
- frontend framework versions,
- available lockfiles.

This should be run before changing dependency constraints or release environments.

---

# 25. Smoke Tests

QuantLab includes a production-compatible smoke-test harness.

Local:

```bash
python3 scripts/smoke_test.py \
  --backend http://127.0.0.1:8000 \
  --frontend http://localhost:3000
```

Production:

```bash
python3 scripts/smoke_test.py \
  --backend YOUR_RAILWAY_URL \
  --frontend YOUR_VERCEL_URL
```

The smoke test verifies:

```text
FastAPI health
Mock market data
Service-level cache
Volatility calibration
SVI fitting
Calendar diagnostics
IDW surface
Frontend reachability
```

It deliberately does **not** call Massive or Alpha Vantage.

External provider quotas should not determine whether the QuantLab application itself is considered healthy.

A healthy deployment ends with:

```text
QUANTLAB RELEASE HEALTHY
```

---

# 26. Continuous Integration

QuantLab uses GitHub Actions.

Workflow:

```text
.github/workflows/ci.yml
```

Current CI checks include:

```text
Backend
├── install dependencies
├── compile Python
└── pytest

Frontend
├── npm ci
├── lint
└── production build

Integration
├── launch FastAPI
├── run API smoke request
├── validate volatility response
└── validate SVI response
```

The integration pipeline uses deterministic mock/manual data and does not require external API credentials.

---

# 27. Deployment

## Backend

The FastAPI backend is deployed on Railway.

Production configuration should include:

```text
MASSIVE_API_KEY
ALPHA_VANTAGE_API_KEY
```

as Railway environment variables when those providers are enabled.

API keys must never be committed to the repository.

---

## Frontend

The Next.js frontend is deployed on Vercel.

Set:

```env
NEXT_PUBLIC_API_URL=https://YOUR-RAILWAY-BACKEND
```

in the Vercel project environment.

---

# 28. Security and Secrets

The repository contains example environment files only:

```text
backend/.env.example
frontend/.env.example
```

Real environment files and API credentials should remain untracked.

The release script checks for accidentally tracked `.env` files before a release.

If an API key is accidentally exposed publicly, revoke and replace it immediately.

---

# 29. Research Interpretation

QuantLab is a research and educational platform.

It should not be interpreted as:

- a live trading system,
- an execution platform,
- investment advice,
- a validated commercial derivatives-risk engine,
- or an exchange-grade arbitrage detector.

Market data may be delayed or end-of-day.

Provider entitlements and rate limits may vary.

---

# 30. Current Modeling Limitations

## Market depth

The current real-market sampling intentionally selects a relatively small representative subset of the option chain.

This keeps provider usage and interactive latency manageable, but it limits smile resolution.

---

## Interest rates

The current Volatility Lab typically uses a user-supplied scalar risk-free rate.

A future implementation should support a maturity-dependent yield curve.

---

## Dividend assumptions

A scalar dividend yield is currently supported.

For equity and ETF options, actual discrete dividends may materially affect American-option pricing.

---

## American-option parity

European put–call parity is used only as a reference diagnostic when analysing American-style options.

---

## SVI calibration

Raw SVI is currently calibrated independently by maturity using a lightweight coordinate-search optimiser.

The implementation is suitable for experimentation but is not yet a production calibration engine.

---

## Butterfly diagnostics

The current SVI butterfly check is intentionally conservative and incomplete.

It should be interpreted as a warning mechanism rather than a formal guarantee of static-arbitrage freedom.

---

## Calendar diagnostics

Cross-maturity tests are performed numerically over the overlapping fitted log-moneyness domains.

They identify potential violations but do not transform the fitted surface into a globally arbitrage-free parameterisation.

---

## IDW interpolation

The IDW surface is a visualization/reference baseline rather than a finance-specific arbitrage-free volatility model.

---

# 31. Planned Research Extensions

Potential QuantLab v2 research directions include:

- SSVI
- constrained SVI optimisation
- full Gatheral–Jacquier arbitrage conditions
- forward-moneyness calibration
- yield-curve integration
- discrete-dividend American pricing
- projected Crank–Nicolson American-option inversion
- local volatility
- Dupire surface construction
- Heston calibration
- SABR
- stochastic-local-volatility models
- risk-neutral density extraction
- delta-space volatility smiles
- risk reversals
- butterflies
- volatility cones
- intraday options data
- expanded provider support
- persistent Redis market-data cache
- historical calibration storage
- neural pricing operators
- PINNs
- DeepONets
- uncertainty-aware surrogate pricing
- classical-versus-neural solver benchmarks

---

# 32. Neural Pricing Research

QuantLab is intended to support experiments comparing numerical and machine-learning pricing methods.

A future unified benchmark layer can compare:

```text
Black–Scholes
CRR
Finite differences
Monte Carlo
PINNs
DeepONets
other neural operators
```

under common metrics such as:

- absolute pricing error,
- relative pricing error,
- RMSE,
- maximum error,
- inference latency,
- calibration time,
- training cost,
- convergence rate,
- extrapolation error.

This is deliberately separated from the stable Volatility Lab so experimental models do not compromise the core pricing platform.

---

# 33. Design Philosophy

QuantLab follows several principles.

### Provider independence

Market-data services should be replaceable without rewriting the quantitative models.

### Model independence

Pricing engines should expose consistent interfaces wherever practical.

### Diagnostics before aesthetics

A volatility curve is not considered useful merely because it looks smooth.

The system surfaces fit quality, model discrepancy, data quality, and arbitrage warnings.

### Deterministic tests

CI should not depend on third-party APIs.

### Explicit freshness

Market-data caching is controlled by QuantLab rather than hidden behind framework-level frontend caching.

### Research reproducibility

Quantitative experiments should eventually run from standardized benchmark definitions rather than isolated notebooks.

---

# 34. Example Workflow

A typical Volatility Lab workflow is:

```text
1. Start backend
        ↓
2. Start frontend
        ↓
3. Open /volatility-lab
        ↓
4. Load demo quotes
   or SPY market chain
        ↓
5. Inspect market-data status
        ↓
6. Calibrate surface
        ↓
7. Examine BS IV
        ↓
8. Examine American IV
        ↓
9. Compare ΔIV
        ↓
10. Inspect skew
        ↓
11. Inspect ATM term structure
        ↓
12. Inspect SVI fit
        ↓
13. Review smile warnings
        ↓
14. Review calendar diagnostics
        ↓
15. Compare against IDW baseline
```

---

# 35. API Examples

## Mock option chain

```bash
curl -s \
  "http://127.0.0.1:8000/market-data/options/SPY?provider=mock" \
  | python3 -m json.tool
```

## Massive option chain

```bash
curl -s \
  "http://127.0.0.1:8000/market-data/options/SPY?provider=massive" \
  | python3 -m json.tool
```

## Force provider refresh

```bash
curl -s \
  "http://127.0.0.1:8000/market-data/options/SPY?provider=massive&refresh=true" \
  | python3 -m json.tool
```

## Volatility calibration

```bash
curl -s -X POST \
  "http://127.0.0.1:8000/calibration/volatility-surface" \
  -H "Content-Type: application/json" \
  -d '{
    "spot": 100,
    "rate": 0.05,
    "dividend_yield": 0,
    "quotes": [
      {
        "strike": 90,
        "maturity": 0.5,
        "market_price": 13.50,
        "option_type": "call"
      },
      {
        "strike": 100,
        "maturity": 0.5,
        "market_price": 6.90,
        "option_type": "call"
      },
      {
        "strike": 110,
        "maturity": 0.5,
        "market_price": 2.90,
        "option_type": "call"
      },
      {
        "strike": 90,
        "maturity": 1.0,
        "market_price": 17.10,
        "option_type": "call"
      },
      {
        "strike": 100,
        "maturity": 1.0,
        "market_price": 10.80,
        "option_type": "call"
      },
      {
        "strike": 110,
        "maturity": 1.0,
        "market_price": 6.30,
        "option_type": "call"
      }
    ]
  }' \
  | python3 -m json.tool
```

---

# 36. Release Procedure

Before creating a release:

```bash
cd ~/Projects/quantlab
```

Run:

```bash
./scripts/version_audit.sh
```

Then:

```bash
./scripts/release_check.sh
```

Then test local deployment:

```bash
python3 scripts/smoke_test.py \
  --backend http://127.0.0.1:8000 \
  --frontend http://localhost:3000
```

Then test production:

```bash
python3 scripts/smoke_test.py \
  --backend YOUR_RAILWAY_URL \
  --frontend YOUR_VERCEL_URL
```

Check Git status:

```bash
git status
```

Push:

```bash
git push
```

Confirm:

```text
GitHub Actions       ✓
Railway deployment   ✓
Vercel deployment    ✓
Production smoke     ✓
```

Only then tag the release.

---

# 37. License

Add the intended open-source or proprietary license before public distribution.

Until a license is explicitly added, no additional licensing rights should be assumed.

---

# 38. Disclaimer

QuantLab is intended for research, education, software experimentation, and quantitative-method comparison.

It is not investment advice and is not intended for direct production trading or financial decision-making without independent validation.

---

## QuantLab

**Pricing models are useful. Understanding when they fail is more useful.**