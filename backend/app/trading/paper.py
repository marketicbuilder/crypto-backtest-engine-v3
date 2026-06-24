"""In-memory paper-trading broker.

Fills market orders at the current mid price (the user supplies the
price feed) with configurable fees / slippage.  Useful for forward-testing
a strategy live against streaming data before going to a real exchange.
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Callable, Dict

from .base import Broker, Fill, Order


class PaperBroker(Broker):
    def __init__(self, price_fn: Callable[[str], float],
                 starting_cash: float = 10_000.0,
                 fee_pct: float = 0.001,
                 slippage_pct: float = 0.0005) -> None:
        self._price = price_fn
        self._cash = starting_cash
        self._positions: Dict[str, float] = defaultdict(float)
        self.fee_pct = fee_pct
        self.slippage_pct = slippage_pct
        self.history: list[Fill] = []

    def submit(self, order: Order) -> Fill:
        px = self._price(order.symbol)
        fill_px = px * (1 + self.slippage_pct) if order.side == "buy" else px * (1 - self.slippage_pct)
        notional = fill_px * order.qty
        fee = notional * self.fee_pct
        if order.side == "buy":
            if notional + fee > self._cash:
                raise RuntimeError("insufficient paper cash")
            self._cash -= notional + fee
            self._positions[order.symbol] += order.qty
        else:
            if order.qty > self._positions[order.symbol] + 1e-9:
                raise RuntimeError("insufficient paper position")
            self._cash += notional - fee
            self._positions[order.symbol] -= order.qty
        fill = Fill(
            order_id=str(uuid.uuid4()), symbol=order.symbol, side=order.side,
            qty=order.qty, price=fill_px, fee=fee,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self.history.append(fill)
        return fill

    def cancel(self, order_id: str) -> bool:
        return True  # paper broker fills synchronously

    def position(self, symbol: str) -> float:
        return self._positions.get(symbol, 0.0)

    def cash(self) -> float:
        return self._cash
