"""Bitget live trading adapter — stub for future use.

Implements the ``Broker`` interface against the Bitget spot v2 REST API.
Requires ``BITGET_API_KEY``, ``BITGET_API_SECRET``, ``BITGET_API_PASSPHRASE``.
Left intentionally minimal until users opt in to real trading.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
import uuid

import requests

from .base import Broker, Fill, Order

BASE = os.environ.get("BITGET_BASE", "https://api.bitget.com")


class BitgetLiveBroker(Broker):
    def __init__(self) -> None:
        self.key = os.environ["BITGET_API_KEY"]
        self.secret = os.environ["BITGET_API_SECRET"]
        self.passphrase = os.environ["BITGET_API_PASSPHRASE"]

    # ---- signing -----------------------------------------------------
    def _sign(self, ts: str, method: str, path: str, body: str = "") -> str:
        msg = f"{ts}{method}{path}{body}"
        mac = hmac.new(self.secret.encode(), msg.encode(), hashlib.sha256).digest()
        return base64.b64encode(mac).decode()

    def _headers(self, method: str, path: str, body: str = "") -> dict:
        ts = str(int(time.time() * 1000))
        return {
            "ACCESS-KEY": self.key,
            "ACCESS-SIGN": self._sign(ts, method, path, body),
            "ACCESS-TIMESTAMP": ts,
            "ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json",
            "locale": "en-US",
        }

    # ---- broker interface --------------------------------------------
    def submit(self, order: Order) -> Fill:
        path = "/api/v2/spot/trade/place-order"
        body = json.dumps({
            "symbol": order.symbol,
            "side": order.side,
            "orderType": order.type,
            "size": str(order.qty),
            "clientOid": order.client_id or str(uuid.uuid4()),
            **({"price": str(order.price)} if order.type == "limit" and order.price else {}),
        })
        r = requests.post(BASE + path, data=body, headers=self._headers("POST", path, body), timeout=15)
        r.raise_for_status()
        d = r.json().get("data", {})
        return Fill(order_id=d.get("orderId", ""), symbol=order.symbol, side=order.side,
                    qty=order.qty, price=order.price or 0.0, fee=0.0,
                    timestamp=str(int(time.time() * 1000)))

    def cancel(self, order_id: str) -> bool:
        path = "/api/v2/spot/trade/cancel-order"
        body = json.dumps({"orderId": order_id})
        r = requests.post(BASE + path, data=body, headers=self._headers("POST", path, body), timeout=15)
        return r.ok

    def position(self, symbol: str) -> float:
        path = "/api/v2/spot/account/assets"
        r = requests.get(BASE + path, headers=self._headers("GET", path), timeout=15)
        r.raise_for_status()
        coin = symbol.replace("USDT", "")
        for a in r.json().get("data", []):
            if a.get("coin") == coin:
                return float(a.get("available", 0))
        return 0.0

    def cash(self) -> float:
        path = "/api/v2/spot/account/assets"
        r = requests.get(BASE + path, headers=self._headers("GET", path), timeout=15)
        r.raise_for_status()
        for a in r.json().get("data", []):
            if a.get("coin") == "USDT":
                return float(a.get("available", 0))
        return 0.0
