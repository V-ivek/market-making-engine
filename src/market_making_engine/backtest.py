from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .avellaneda_stoikov import optimal_quote
from .config import BacktestConfig, StrategyConfig
from .intensity import IntensityFit, lambda_exponential, lambda_power


@dataclass(slots=True)
class BacktestResult:
    timeseries: pd.DataFrame
    fills: pd.DataFrame
    summary: dict


def _arrival_rate(delta: float, fit: IntensityFit) -> float:
    if fit.model == "exponential":
        return float(lambda_exponential(delta, fit.A, fit.k))
    if fit.model == "power":
        return float(lambda_power(delta, fit.A, fit.k))
    raise ValueError(f"Unknown intensity model: {fit.model}")


def run_backtest(mid: pd.Series, fit: IntensityFit, strat: StrategyConfig, cfg: BacktestConfig) -> BacktestResult:
    rng = np.random.default_rng(cfg.seed)
    m = mid.to_numpy(dtype=float)
    n = len(m)

    inventory = np.zeros(n)
    cash = np.zeros(n)
    realized_spread = np.zeros(n)
    inventory_pnl = np.zeros(n)

    fills = []

    q = 0.0
    c = 0.0

    for t in range(n):
        tau_steps = max(strat.horizon_steps - t, 0)
        tau = tau_steps * strat.dt

        quote = optimal_quote(
            mid_price=m[t],
            inventory=q,
            gamma=strat.gamma,
            sigma=strat.sigma,
            time_to_horizon=tau,
            k=max(fit.k, 1e-8),
        )

        delta_bid = max(m[t] - quote.bid, 0.0)
        delta_ask = max(quote.ask - m[t], 0.0)

        lam_bid = _arrival_rate(delta_bid, fit)
        lam_ask = _arrival_rate(delta_ask, fit)

        p_bid = 1.0 - np.exp(-lam_bid * strat.dt)
        p_ask = 1.0 - np.exp(-lam_ask * strat.dt)

        bid_fill = (rng.uniform() < p_bid) and (q + strat.order_size <= strat.max_inventory)
        ask_fill = (rng.uniform() < p_ask) and (q - strat.order_size >= -strat.max_inventory)

        if bid_fill:
            q += strat.order_size
            c -= quote.bid * strat.order_size
            edge = (m[t] - quote.bid) * strat.order_size
            realized_spread[t] += edge
            fills.append({"t": t, "side": "buy", "price": quote.bid, "mid": m[t], "delta": delta_bid})

        if ask_fill:
            q -= strat.order_size
            c += quote.ask * strat.order_size
            edge = (quote.ask - m[t]) * strat.order_size
            realized_spread[t] += edge
            fills.append({"t": t, "side": "sell", "price": quote.ask, "mid": m[t], "delta": delta_ask})

        if t > 0:
            inventory_pnl[t] = (inventory[t - 1]) * (m[t] - m[t - 1])

        inventory[t] = q
        cash[t] = c

    mtm = cash + inventory * m

    ts = pd.DataFrame(
        {
            "t": np.arange(n),
            "mid": m,
            "inventory": inventory,
            "cash": cash,
            "mtm_pnl": mtm,
            "realized_spread": np.cumsum(realized_spread),
            "inventory_pnl": np.cumsum(inventory_pnl),
        }
    )

    fills_df = pd.DataFrame(fills)
    adverse = 0.0
    if not fills_df.empty:
        mark = []
        for row in fills_df.itertuples(index=False):
            t0 = int(row.t)
            t1 = min(t0 + cfg.markout_horizon, n - 1)
            future_mid = m[t1]
            side = 1.0 if row.side == "buy" else -1.0
            # positive means adverse move against fill
            adverse_cost = side * (row.mid - future_mid)
            mark.append(adverse_cost)
        fills_df["adverse_selection_cost"] = mark
        adverse = float(np.sum(mark))

    summary = {
        "final_pnl": float(mtm[-1]),
        "max_abs_inventory": float(np.max(np.abs(inventory))),
        "inventory_mean": float(np.mean(inventory)),
        "inventory_std": float(np.std(inventory)),
        "realized_spread_capture": float(np.sum(realized_spread)),
        "inventory_pnl": float(np.sum(inventory_pnl)),
        "adverse_selection_cost": adverse,
        "num_fills": int(len(fills_df)),
    }

    return BacktestResult(timeseries=ts, fills=fills_df, summary=summary)
