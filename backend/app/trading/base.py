"""Execution-broker interface.

The backtest engine, paper-trading driver and live-trading driver all
consume the same ``Broker`` interface so a strategy written today works
unchanged once you flip the broker.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class Order:
    symbol: str
    side: Literal["buy", "sell"]
    qty: float
    type: Literal["market", "limit"] = "market"
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    client_id: Optional[str] = None


@dataclass
class Fill:
    order_id: str
    symbol: str
    side: str
    qty: float
    price: float
    fee: float
    timestamp: str


class Broker(ABC):
    @abstractmethod
    def submit(self, order: Order) -> Fill: ...

    @abstractmethod
    def cancel(self, order_id: str) -> bool: ...

    @abstractmethod
    def position(self, symbol: str) -> float: ...

    @abstractmethod
    def cash(self) -> float: ...
