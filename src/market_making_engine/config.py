from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class StrategyConfig:
    gamma: float = 0.1
    sigma: float = 0.02
    horizon_steps: int = 300
    dt: float = 1.0
    max_inventory: int = 20
    order_size: float = 1.0


@dataclass(slots=True)
class BacktestConfig:
    markout_horizon: int = 5
    seed: int = 7


@dataclass(slots=True)
class CalibrationConfig:
    model: str = "exponential"
    k_min: float = 1e-4
    k_max: float = 50.0
    k_grid_points: int = 2000
    delta0: float = 1e-4  # for power-law model
