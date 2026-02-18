from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd

BINANCE_REST = "https://api.binance.com/api/v3/klines"


def _to_ms(ts: Optional[str]) -> Optional[int]:
    if ts is None:
        return None
    # Accept ISO-8601, e.g. 2026-02-01T00:00:00Z
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)
    return int(dt.timestamp() * 1000)


def fetch_binance_klines(
    symbol: str,
    interval: str = "1m",
    start_time: str | None = None,
    end_time: str | None = None,
    limit: int = 1000,
) -> pd.DataFrame:
    """Fetch free public OHLCV from Binance and return normalized DataFrame.

    Columns:
      ts, open, high, low, close, volume, mid
    """
    params = {
        "symbol": symbol.upper(),
        "interval": interval,
        "limit": min(max(limit, 1), 1000),
    }
    s = _to_ms(start_time)
    e = _to_ms(end_time)
    if s is not None:
        params["startTime"] = s
    if e is not None:
        params["endTime"] = e

    url = f"{BINANCE_REST}?{urlencode(params)}"
    with urlopen(url, timeout=20) as r:
        data = json.loads(r.read().decode("utf-8"))

    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected Binance response: {data}")

    rows = []
    for k in data:
        rows.append(
            {
                "ts": pd.to_datetime(int(k[0]), unit="ms", utc=True),
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5]),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["mid"] = (df["high"] + df["low"]) / 2.0
    return df
