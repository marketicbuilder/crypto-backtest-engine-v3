"""Event-driven backtest engine.

Iterates bar-by-bar.  Each bar:

1. Update open position: check stop-loss, take-profit, trailing stop.
2. Ask the strategy for a decision based on the *previous* bar's close
   (so we don't peek into the bar we're about to trade).
3. Execute the order at the *next* bar's open with configurable fees
   and slippage.

Supports long-only or long+short (toggle via ``allow_short``), one
position at a time per symbol (``max_open_positions=1`` for the MVP),
and optional leverage.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pandas as pd

from ..strategies.base import Signal, Strategy
from .metrics import Trade, compute_metrics


@dataclass
class BacktestConfig:
    starting_balance: float = 10_000.0
    fee_pct: float = 0.001          # 0.10% taker
    slippage_pct: float = 0.0005    # 5 bps
    risk_per_trade: float = 0.02    # 2% of equity at risk
    max_open_positions: int = 1
    stop_loss_pct: Optional[float] = None     # overrides strategy default
    take_profit_pct: Optional[float] = None
    trailing_stop_pct: Optional[float] = None
    leverage: float = 1.0
    allow_short: bool = False


@dataclass
class _OpenPosition:
    side: str           # "long" | "short"
    entry_time: pd.Timestamp
    entry_price: float
    qty: float
    stop: Optional[float]
    take: Optional[float]
    trail: Optional[float]      # current trailing stop level
    trail_pct: Optional[float]
    score: float
    reason: str
    fees_paid: float


@dataclass
class BacktestResult:
    equity: pd.Series
    trades: List[Trade]
    metrics: Dict
    signals: pd.DataFrame
    config: BacktestConfig


class BacktestEngine:
    def __init__(self, cfg: BacktestConfig) -> None:
        self.cfg = cfg

    # ------------------------------------------------------------------
    def run(self, df: pd.DataFrame, strategy: Strategy) -> BacktestResult:
        if "time" in df.columns and not isinstance(df.index, pd.DatetimeIndex):
            df = df.copy()
            df["time"] = pd.to_datetime(df["time"])
            df = df.set_index("time")

        prepared = strategy.prepare(df)

        equity = self.cfg.starting_balance
        cash = self.cfg.starting_balance
        pos: Optional[_OpenPosition] = None
        equity_curve: list[tuple[pd.Timestamp, float]] = []
        trades: list[Trade] = []
        signal_rows: list[dict] = []

        rows = list(prepared.itertuples(index=True))
        for i in range(len(rows) - 1):
            cur = rows[i]
            nxt = rows[i + 1]
            ts_cur = cur.Index
            ts_nxt = nxt.Index
            close_cur = cur.close
            open_nxt = nxt.open
            high_nxt = nxt.high
            low_nxt = nxt.low

            # 1) manage open position on the next bar
            if pos is not None:
                exit_price: Optional[float] = None
                exit_reason: str = ""

                if pos.side == "long":
                    # trailing stop update using the high of the next bar
                    if pos.trail_pct is not None:
                        new_trail = high_nxt * (1 - pos.trail_pct)
                        if pos.trail is None or new_trail > pos.trail:
                            pos.trail = new_trail
                    # SL / TP / trailing hit?
                    if pos.stop is not None and low_nxt <= pos.stop:
                        exit_price, exit_reason = pos.stop, f"stop-loss {pos.stop:.2f}"
                    elif pos.take is not None and high_nxt >= pos.take:
                        exit_price, exit_reason = pos.take, f"take-profit {pos.take:.2f}"
                    elif pos.trail is not None and low_nxt <= pos.trail:
                        exit_price, exit_reason = pos.trail, f"trailing-stop {pos.trail:.2f}"
                else:  # short
                    if pos.trail_pct is not None:
                        new_trail = low_nxt * (1 + pos.trail_pct)
                        if pos.trail is None or new_trail < pos.trail:
                            pos.trail = new_trail
                    if pos.stop is not None and high_nxt >= pos.stop:
                        exit_price, exit_reason = pos.stop, f"stop-loss {pos.stop:.2f}"
                    elif pos.take is not None and low_nxt <= pos.take:
                        exit_price, exit_reason = pos.take, f"take-profit {pos.take:.2f}"
                    elif pos.trail is not None and high_nxt >= pos.trail:
                        exit_price, exit_reason = pos.trail, f"trailing-stop {pos.trail:.2f}"

                if exit_price is not None:
                    cash, trade = self._close(pos, ts_nxt, exit_price, exit_reason, cash)
                    trades.append(trade)
                    pos = None

            # 2) get strategy decision based on *current* close
            row = prepared.loc[ts_cur]
            position_size = pos.qty if pos else 0.0
            sig: Signal = strategy.decide(row, position_size if pos and pos.side == "long" else -position_size if pos else 0.0)

            signal_rows.append({
                "time": ts_cur, "action": sig.action, "score": sig.score,
                "reason": sig.reason, "close": close_cur,
            })

            # 3) act on the signal at the next bar's open
            if sig.action == "buy" and pos is None:
                pos, cash = self._open(
                    side="long", ts=ts_nxt, price=open_nxt, cash=cash, sig=sig,
                )
            elif sig.action == "sell":
                if pos and pos.side == "long":
                    cash, trade = self._close(pos, ts_nxt, open_nxt, "strategy sell signal", cash)
                    trades.append(trade)
                    pos = None
                elif pos is None and self.cfg.allow_short:
                    pos, cash = self._open(
                        side="short", ts=ts_nxt, price=open_nxt, cash=cash, sig=sig,
                    )

            # 4) mark-to-market equity using next bar's close
            mtm = cash
            if pos is not None:
                if pos.side == "long":
                    mtm += pos.qty * nxt.close
                else:
                    mtm += pos.qty * (2 * pos.entry_price - nxt.close)
            equity_curve.append((ts_nxt, mtm))
            equity = mtm

        # close any open position on the last bar
        if pos is not None:
            last = rows[-1]
            cash, trade = self._close(pos, last.Index, last.close, "end of backtest", cash)
            trades.append(trade)
            equity_curve.append((last.Index, cash))

        eq = pd.Series(
            [v for _, v in equity_curve],
            index=pd.DatetimeIndex([t for t, _ in equity_curve], name="time"),
            name="equity",
        )
        metrics = compute_metrics(eq, trades, self.cfg.starting_balance)
        signals = pd.DataFrame(signal_rows).set_index("time") if signal_rows else pd.DataFrame()
        return BacktestResult(equity=eq, trades=trades, metrics=metrics,
                              signals=signals, config=self.cfg)

    # ------------------------------------------------------------------ helpers
    def _open(self, *, side: str, ts, price: float, cash: float, sig: Signal) -> tuple[_OpenPosition, float]:
        cfg = self.cfg
        # apply slippage in the direction that hurts us
        fill = price * (1 + cfg.slippage_pct) if side == "long" else price * (1 - cfg.slippage_pct)
        # risk-based sizing: risk = risk_per_trade * cash / stop_distance
        sl_pct = cfg.stop_loss_pct or sig.stop_loss_pct or 0.05
        risk_cash = cash * cfg.risk_per_trade
        qty_by_risk = (risk_cash / (fill * sl_pct)) if sl_pct > 0 else 0
        # cap by available cash * leverage
        qty_by_cash = (cash * cfg.leverage) / fill
        qty = max(min(qty_by_risk, qty_by_cash), 0.0)
        notional = qty * fill
        fee = notional * cfg.fee_pct
        cash -= fee
        # NOTE: we don't subtract notional from cash (leverage / margin)
        # but we do reserve a cash buffer for the long. Simpler MVP:
        if side == "long":
            cash -= notional
        stop = fill * (1 - sl_pct) if side == "long" else fill * (1 + sl_pct)
        tp_pct = cfg.take_profit_pct or sig.take_profit_pct
        take = (fill * (1 + tp_pct) if side == "long" else fill * (1 - tp_pct)) if tp_pct else None
        trail_pct = cfg.trailing_stop_pct
        pos = _OpenPosition(
            side=side, entry_time=ts, entry_price=fill, qty=qty,
            stop=stop, take=take, trail=None, trail_pct=trail_pct,
            score=sig.score, reason=sig.reason, fees_paid=fee,
        )
        return pos, cash

    def _close(self, pos: _OpenPosition, ts, price: float, reason: str, cash: float) -> tuple[float, Trade]:
        cfg = self.cfg
        fill = price * (1 - cfg.slippage_pct) if pos.side == "long" else price * (1 + cfg.slippage_pct)
        notional = pos.qty * fill
        fee = notional * cfg.fee_pct
        if pos.side == "long":
            cash += notional - fee
            pnl = (fill - pos.entry_price) * pos.qty - (pos.fees_paid + fee)
            pnl_pct = (fill / pos.entry_price - 1)
        else:
            # short: cash already holds the proceeds conceptually; we settle pnl
            pnl = (pos.entry_price - fill) * pos.qty - (pos.fees_paid + fee)
            pnl_pct = (pos.entry_price / fill - 1)
            cash += pnl
        trade = Trade(
            entry_time=pos.entry_time, exit_time=ts, side=pos.side,
            entry_price=pos.entry_price, exit_price=fill, qty=pos.qty,
            pnl=pnl, pnl_pct=pnl_pct, fees=pos.fees_paid + fee,
            score=pos.score, reason_entry=pos.reason, reason_exit=reason,
        )
        return cash, trade
