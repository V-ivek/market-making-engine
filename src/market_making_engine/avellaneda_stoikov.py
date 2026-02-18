from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(slots=True)
class Quote:
    reservation_price: float
    bid: float
    ask: float
    half_spread: float


def optimal_quote(
    mid_price: float,
    inventory: float,
    gamma: float,
    sigma: float,
    time_to_horizon: float,
    k: float,
) -> Quote:
    """Compute Avellaneda-Stoikov reservation price and optimal spread.

    r_t = s_t - q_t * gamma * sigma^2 * (T-t)
    delta* = (1/gamma) ln(1 + gamma/k) + 0.5 * gamma * sigma^2 * (T-t)
    bid = r_t - delta*, ask = r_t + delta*
    """
    reservation = mid_price - inventory * gamma * sigma * sigma * time_to_horizon
    half_spread = (1.0 / gamma) * math.log(1.0 + gamma / max(k, 1e-12)) + 0.5 * gamma * sigma * sigma * time_to_horizon
    return Quote(
        reservation_price=reservation,
        bid=reservation - half_spread,
        ask=reservation + half_spread,
        half_spread=half_spread,
    )
