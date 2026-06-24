"""Pydantic request / response models for the API surface."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DataRequest(BaseModel):
    symbol: str = "BTCUSDT"
    interval: str = "1d"
    start: Optional[str] = None
    end: Optional[str] = None
    source: str = "binance"
    with_fear_greed: bool = True
    with_news: bool = False


class StrategySpec(BaseModel):
    name: str
    params: Dict[str, float] = Field(default_factory=dict)


class BacktestRequest(BaseModel):
    data: DataRequest
    strategy: StrategySpec
    starting_balance: float = 10_000
    fee_pct: float = 0.001
    slippage_pct: float = 0.0005
    risk_per_trade: float = 0.02
    max_open_positions: int = 1
    stop_loss_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None
    trailing_stop_pct: Optional[float] = None
    leverage: float = 1.0
    allow_short: bool = False


class TradeOut(BaseModel):
    entry_time: str
    exit_time: str
    side: str
    entry_price: float
    exit_price: float
    qty: float
    pnl: float
    pnl_pct: float
    fees: float
    score: float
    reason_entry: str
    reason_exit: str


class BacktestResponse(BaseModel):
    metrics: Dict[str, Any]
    trades: List[TradeOut]
    equity: List[Dict[str, Any]]
    drawdown: List[Dict[str, Any]]
    insights: List[str]
    strategy: StrategySpec


class CompareRequest(BaseModel):
    data: DataRequest
    strategies: List[StrategySpec]
    starting_balance: float = 10_000


class OptimiseRequest(BaseModel):
    data: DataRequest
    strategy_name: str
    param_grid: Dict[str, List[float]]
    starting_balance: float = 10_000
    fee_pct: float = 0.001
    slippage_pct: float = 0.0005
    objective: str = "sharpe"   # sharpe | calmar | return
