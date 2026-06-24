"""Lightweight on-disk cache used by data providers.

Stores raw responses as gzip-compressed Parquet (DataFrame) or JSON.
Keyed by SHA-1 of the request URL + params.  Default TTL is 30 days
for historical data (which never changes) and 1 hour for live data.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import pandas as pd

CACHE_DIR = Path(os.environ.get("CACHE_DIR", ".cache"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _key(name: str, params: dict) -> str:
    s = name + "|" + json.dumps(params, sort_keys=True, default=str)
    return hashlib.sha1(s.encode()).hexdigest()


@dataclass
class CacheEntry:
    path: Path
    created: float


def _stored(name: str, params: dict, suffix: str) -> CacheEntry:
    k = _key(name, params)
    return CacheEntry(path=CACHE_DIR / f"{k}{suffix}", created=time.time())


def get_df(name: str, params: dict, ttl: int = 30 * 86400) -> Optional[pd.DataFrame]:
    entry = _stored(name, params, ".parquet.gz")
    if not entry.path.exists():
        return None
    if time.time() - entry.path.stat().st_mtime > ttl:
        return None
    with gzip.open(entry.path, "rb") as fh:
        return pd.read_parquet(fh)


def set_df(name: str, params: dict, df: pd.DataFrame) -> None:
    entry = _stored(name, params, ".parquet.gz")
    with gzip.open(entry.path, "wb") as fh:
        df.to_parquet(fh)


def get_json(name: str, params: dict, ttl: int = 3600) -> Optional[Any]:
    entry = _stored(name, params, ".json.gz")
    if not entry.path.exists():
        return None
    if time.time() - entry.path.stat().st_mtime > ttl:
        return None
    with gzip.open(entry.path, "rb") as fh:
        return json.loads(fh.read().decode())


def set_json(name: str, params: dict, obj: Any) -> None:
    entry = _stored(name, params, ".json.gz")
    with gzip.open(entry.path, "wb") as fh:
        fh.write(json.dumps(obj, default=str).encode())
