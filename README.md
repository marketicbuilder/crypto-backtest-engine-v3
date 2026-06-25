# BitEdge — Bitget AI Builder Base Camp Hackathon S1

**Live Demo:** https://bitedge.vercel.app
**GitHub:** https://github.com/marketicbuilder/crypto-backtest-engine-v3
**API Docs:** https://crypto-backtest-engine-v3-production.up.railway.app/docs

---

## Hackathon Submission

### Why I Built It

Most retail crypto traders blow up accounts not because their ideas are wrong — but because they never test them first. Paid backtesting tools are expensive, and free ones cut corners on realism: they ignore fees, slippage, leverage mechanics, and trailing stops. The result is a false sense of confidence before deploying real capital.

BitEdge was built to close that gap. The core insight is simple: **a strategy that cannot survive a backtest will not survive real markets.** BitEdge gives any trader access to institutional-grade strategy evaluation using entirely free-tier APIs, with Bitget as the primary data source.

---

### Core Logic — How the Strategy Works

The engine's flagship strategy is a **multi-factor AI scoring system** that combines 8 signals into a single 0–100 score on every bar.

- **Above 60** → BUY
- **Below 40** → SELL
- **Between 40–60** → HOLD

Every signal contributes a weighted delta to a neutral baseline of 50. The final score is clamped to the 0–100 range.

| Signal | Weight | Logic |
|---|---|---|
| RSI (14) | ±20 | Below 35 = oversold bullish; above 70 = overbought bearish |
| MACD | ±15 | MACD line above or below signal line |
| EMA Trend (20/50) | ±10 | Fast EMA vs slow EMA — trend direction |
| Volume | +10 | Volume rising above its 20-bar SMA = conviction |
| 10-bar Momentum | ±10 | Price change above ±5% signals strength or weakness |
| Fear and Greed Index | ±10 | Contrarian — extreme fear signals buy, extreme greed signals caution |
| Bitget L/S Ratio | ±10 | Crowd positioning from Bitget Futures — contrarian signal |
| Bitget Funding Rate | ±10 | Elevated funding = overheated longs; negative funding = oversold |

The **Bitget long/short ratio and funding rate** are live signals pulled directly from the Bitget Futures v2 API with no authentication required. They add a real-time market microstructure layer that pure price indicators cannot capture.

Each signal degrades gracefully. If sentiment or funding data is unavailable for a given symbol or date range, that signal contribution defaults to zero and the engine continues running on pure technicals without crashing.

---

### Risk Management

- Configurable **fees and slippage** baked into every simulated trade
- **Leverage** up to 10x with proper position sizing
- **Stop-loss, take-profit, and trailing stop** support
- **Risk-per-trade position sizing** — size is calculated as a percentage of equity
- **Max open positions cap** to prevent over-concentration
- **Next-bar open execution** — no look-ahead bias; fills simulate what actually happens in live markets
- **17 performance metrics**: Sharpe, Sortino, Calmar, profit factor, win rate, max drawdown, streak analysis

---

### Key Development Challenges and How They Were Solved

**1. Free API rate limits and data gaps**
Bitget's public OHLCV endpoint returns a maximum of 1,000 bars per request. To support multi-year backtests, BitEdge implements an auto-paginating client that walks backward through time in 1,000-bar windows with a 50ms sleep between requests. All fetched data is cached to disk as gzip-compressed Parquet files. Five years of BTC daily data downloads once and serves every subsequent backtest in milliseconds.

**2. Graceful signal degradation**
Fear and Greed data and news sentiment are not available for every symbol or historical range. Rather than failing or requiring fallback logic in every strategy, the scoring engine treats each signal as an independent optional contributor. Absent signals return 0 delta. The engine's output is always valid regardless of which signals are live.

**3. Plug-in strategy architecture**
A decorator-based registry means any strategy file dropped into `backend/app/strategies/` is auto-registered globally without touching any other code. New strategies appear in the UI the moment the file exists.

**4. Realistic simulation**
Most free backtesting tools use close-to-close pricing. BitEdge uses next-bar open execution with configurable fees, slippage, leverage, stops, and risk-per-trade sizing. The simulation reflects what would actually happen, not what a clean chart suggests.

**5. Parameter optimisation**
A grid-search optimiser runs full parameter combinations across any strategy and ranks results by Sharpe ratio, Calmar ratio, or total return. It runs synchronously for now, with the architecture designed to move to a Celery or RQ background task queue as volume scales.

---

### What Is Complete

- 8-signal AI scoring engine with Bitget L/S ratio and funding rate as live signals
- EMA crossover and RSI mean-reversion strategies
- Event-driven backtest engine with realistic costs (fees, slippage, leverage, stops)
- 17 performance metrics: Sharpe, Sortino, Calmar, profit factor, win rate, max drawdown, streak analysis
- Equity curve, drawdown chart, monthly returns heatmap, trade distribution
- Side-by-side strategy comparison
- Parameter grid-search optimisation
- Rule-based AI insights summarising backtest results
- Bitget Live Broker adapter — same strategy interface runs across backtest, paper, and live modes with zero code changes
- Paper trading mode
- Telegram and Discord trade alerts
- CSV and JSON trade log export
- On-disk Parquet cache
- Docker and docker-compose
- GitHub Actions CI (lint, tests, Docker build)
- Vercel and Railway deployment

### What Is Still Missing / Next Steps

- Async optimisation with a background job queue (Celery or RQ)
- Supabase persistence for saving and comparing backtest history across sessions
- Futures and perpetuals support with funding rate PnL accounting
- Portfolio-level backtesting across multiple assets simultaneously
- ML-based signal weighting — replacing fixed weights with a regime-detecting model that shifts allocation between momentum and sentiment signals depending on market conditions
- Bitget WebSocket integration for real-time paper trading
- On-chain signals via DefiLlama TVL and protocol flow data

---

### Frameworks, Models, and APIs

**Backend:** FastAPI, pandas, numpy, PyArrow, uvicorn

**Frontend:** Next.js 14 (App Router), Tailwind CSS, shadcn/ui, TradingView Lightweight Charts

| API | Usage |
|---|---|
| Bitget Spot v2 REST | Primary OHLCV historical data source |
| Bitget Futures v2 REST | Live long/short ratio and funding rate signals |
| Alternative.me | Fear and Greed Index |
| CryptoPanic | News sentiment scoring |
| DefiLlama | TVL and on-chain protocol data |

**Bitget tools used:** Bitget REST API — Spot v2 and Futures v2

---

### Experience with Bitget AI Tools and the Future of Agentic Trading

The Bitget Spot v2 and Futures v2 APIs were straightforward to integrate. The authentication scheme is well-documented, response structures are consistent, and the public endpoints for market data require no credentials — which dramatically lowers the barrier for developers building research tools.

The single biggest improvement that would help builders: **a first-party paper trading sandbox** that mirrors the live API exactly, including order acknowledgement, fill simulation, and position tracking. Right now paper mode requires building a full simulation layer separately, which is significant engineering overhead. A sandbox environment with identical request and response schemas to production would reduce time-to-testing substantially.

On the future of agentic trading: the next meaningful leap is not better indicators — it is **regime awareness**. Fixed signal weights assume markets behave consistently across conditions, which they do not. A bull market rewards momentum signals. A bear market rewards sentiment and mean-reversion signals. A sideways market punishes both. The next version of BitEdge replaces fixed weights with a regime-detecting model that observes volatility, trend strength, and market structure and adjusts signal allocation dynamically. An agent that knows what kind of market it is operating in is categorically more robust than any static strategy, regardless of how many signals it combines. That is the direction this is heading, and it is where agentic trading infrastructure needs to go.

---

*Built for the Bitget AI Builder Base Camp Hackathon S1 — Trading Infra track.*
