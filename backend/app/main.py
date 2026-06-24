"""FastAPI entry point.

Mounts the four routers (data, strategies, backtests, insights) and a
health probe.  CORS is enabled for the Next.js dev server.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import backtests, data, insights, strategies

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(
    title="AI Crypto Backtest Engine",
    version="0.1.0",
    description="Free-tier crypto backtesting API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(strategies.router)
app.include_router(data.router)
app.include_router(backtests.router)
app.include_router(insights.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
