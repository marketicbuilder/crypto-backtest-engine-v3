# AI Crypto Backtest Engine

> **Bitget Hackathon Submission** — Multi-factor AI scoring engine for crypto trading strategy research, backtesting, and live execution via Bitget.

---

## Why I Built It

Most retail crypto traders blow up accounts not because their ideas are wrong — but because they never test them. Paid backtesting tools are expensive, and free ones lack realistic simulation (fees, slippage, leverage, trailing stops). I built this engine to give anyone access to institutional-grade backtesting using **entirely free-tier APIs** — no Bloomberg terminal required.

The core insight: a strategy that cannot survive a backtest will not survive real markets. This engine lets you kill bad ideas cheaply before putting real money on them.

---

## How the Strategy Works

### The AI Scoring Engine

The flagship strategy is a **multi-factor scoring system** that combines 7 signals into a single 0–100 score every bar. Above 60 = BUY, below 40 = SELL, between = HOLD.

| Signal | Weight | Logic |
|---|---|---|
| RSI (14) | ±20 | < 35 = oversold bullish; > 70 = overbought bearish |
| MACD | ±15 | MACD line above/below signal line |
| EMA Trend (20/50) | ±10 | Fast EMA vs slow EMA — trend direction |
| Volume | +10 | Volume rising above its 20-bar SMA = conviction |
| 10-bar Momentum | ±10 | Price change > ±5% signals strength or weakness |
| Fear & Greed Index | ±10 | Contrarian — extreme fear = buy, extreme greed = caution |
| News Sentiment | ±15 | CryptoPanic score > 0.3 or < -0.3 |

**Score formula:** `score = clamp(50 + sum(weighted_signals), 0, 100)`

Each signal degrades gracefully — if Fear & Greed or news data is unavailable, those contributions neutralise to 0 and the engine runs on pure technicals.

### Why This Works

- **Mean-reversion + trend confirmation** — RSI catches oversold dips; EMA/MACD confirm the trend hasn't reversed. Together they avoid buying falling knives.
- **Sentiment as a contrarian edge** — When Fear & Greed hits extreme fear (< 25), markets are historically oversold. The engine buys the opposite of the crowd.
- **Volume as a conviction filter** — Price moves without volume are noise. Rising volume increases signal confidence.
- **News sentiment** provides a forward-looking signal that pure price indicators miss entirely.

### Additional Strategies

- **EMA Cross** — Golden/death cross on configurable fast/slow EMAs
- **RSI Mean Reversion** — Pure oversold/overbought bounce strategy

Any strategy file dropped into `backend/app/strategies/` auto-registers via the `@register` decorator — no other code changes needed.

---

## Risk Management

Every strategy supports: stop-loss (default 5%), take-profit (default 12%), trailing stop, leverage up to 10x, risk-per-trade position sizing, max open positions cap, and realistic fees + slippage deducted on every trade.

---

## Architecture

```
┌────────────────────────────────────┐
│         Next.js Frontend           │
│  Backtest · Compare · Optimise     │
└────────────┬───────────────────────┘
             │ REST
┌────────────▼───────────────────────┐
│         FastAPI Backend            │
│  Data Loader → Engine → Broker     │
│  Strategy Registry (plug-in)       │
└────────────────────────────────────┘
```

Data flow: frontend sends config → backend fetches OHLCV from Binance (auto-cached as Parquet) → optionally enriches with Fear & Greed + news sentiment → strategy scores every bar → engine simulates trades → returns 17 metrics, equity curve, drawdown, trade log, and AI insights.

---

## Key Development Challenges

**1. Free APIs with 1,000-bar limits** — Built an auto-paginating Binance client with 50ms rate-limit sleep and on-disk gzip-Parquet cache. 5 years of BTC daily data downloads once, serves forever.

**2. Graceful signal degradation** — Fear & Greed and news aren't available for all symbols or date ranges. All optional signals default to neutral (0 contribution) when absent so the engine never crashes.

**3. Plug-in strategy system** — The `@register` decorator at the bottom of any strategy file auto-registers it globally. Drop a file, it appears in the UI instantly.

**4. Grid-search optimisation** — Runs full parameter grids synchronously with results returned as a ranked table. Designed to move to a background task queue (Celery/RQ) as a next step.

---

## What's Complete

- Multi-factor AI scoring engine (7 signals)
- EMA crossover and RSI mean-reversion strategies
- Event-driven backtest engine with realistic costs
- 17 performance metrics (Sharpe, Sortino, Calmar, profit factor, win rate, max drawdown, streaks)
- Equity curve, drawdown, monthly returns, and trade distribution charts
- Side-by-side strategy comparison
- Parameter grid-search optimisation (Sharpe / Calmar / Return objectives)
- Rule-based AI insights
- Bitget live trading adapter (Spot v2 REST API, HMAC-SHA256 signing)
- Paper trading mode
- Telegram and Discord trade alerts
- CSV / JSON trade log export
- On-disk Parquet cache
- Docker + docker-compose
- GitHub Actions CI (lint, tests, Docker build)
- Vercel + Railway deployment configs

## What's Next

- Async optimisation with job queue
- Supabase persistence for backtest history
- Futures / perpetuals support with funding rates
- Portfolio-level backtesting across multiple assets
- ML-based signal weighting (replace fixed weights with a trained model)
- Bitget WebSocket for real-time paper trading
- On-chain signals via DefiLlama TVL and protocol flows

---

## Frameworks, Models & APIs

**Backend:** FastAPI, pandas, numpy, PyArrow, uvicorn

**Frontend:** Next.js 14 (App Router), Tailwind CSS, shadcn/ui, TradingView Lightweight Charts

**APIs (all free tier):**

| API | Usage |
|---|---|
| Binance Public REST | OHLCV historical data — no key needed |
| CoinGecko | Token metadata and prices |
| Alternative.me | Fear & Greed Index |
| CryptoPanic | News sentiment scoring |
| DefiLlama | TVL and on-chain protocol data |
| GeckoTerminal | DEX pool data |

**Bitget Integration:** Bitget Spot v2 REST API — live order placement, position queries, and balance checks via the `BitgetLiveBroker` adapter. HMAC-SHA256 signing implemented from scratch. The same strategy interface runs unchanged across backtest → paper → live modes with zero code changes.

> Bitget tools used: **Bitget REST API (Spot v2)**

---

## Experience with Bitget AI Tools

The Spot v2 API was clean to integrate — the authentication scheme is well-documented and responses are consistent. The biggest improvement I'd suggest is a **paper trading sandbox endpoint** that mirrors the live API exactly. Right now paper mode requires a separate simulation layer (which I built), but a first-party sandbox would dramatically reduce the barrier to testing live strategies safely.

On the future of Agentic Trading: the next evolution of this engine is replacing fixed scoring weights with a regime-detecting model — heavier momentum weighting in bull markets, heavier sentiment/fear weighting in bear markets. An agent that knows what kind of market it's in and adjusts accordingly is far more robust than any fixed strategy. That's where this is going.

---

## Deployment

- **Frontend:** Vercel — auto-deploys from `main`
- **Backend:** Railway (Docker) — auto-deploys from `main`
- **CI/CD:** GitHub Actions on every push

**Backend env vars (Railway):**
```
CRYPTOPANIC_TOKEN=        # free signup at cryptopanic.com
BITGET_API_KEY=           # live trading only
BITGET_API_SECRET=        # live trading only
BITGET_API_PASSPHRASE=    # live trading only
TELEGRAM_BOT_TOKEN=       # optional
DISCORD_WEBHOOK_URL=      # optional
```

**Frontend env var (Vercel):**
```
NEXT_PUBLIC_API_BASE=https://your-backend.up.railway.app
```

---

## Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/crypto-backtest-engine.git
cd crypto-backtest-engine/backend
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload

# New terminal
cd frontend
npm install && npm run dev
```

Or: `docker-compose up --build`

---

## Sample Backtest Output

Full logs in `/output/demo/`:
- `equity.csv` — portfolio value at every bar
- `trades.csv` — entry/exit timestamps, prices, PnL, fees, score, reason
- `signals.csv` — raw signal scores at every bar
- `metrics.json` — all 17 performance metrics

---

## Links

- **GitHub:** https://github.com/YOUR_USERNAME/crypto-backtest-engine
- **Live Demo:** https://your-frontend.vercel.app
- **API Docs:** https://your-backend.up.railway.app/docs
- **Demo Video:** *(YouTube / X link)*
- **Project Post:** *(X post with #BitgetHackathon and @BitgetAI)*
- **Bitget Campaign Repost:** *(X repost link)*

---

*Built for the Bitget AI Hackathon. All data from free public APIs. Not financial advice.*
