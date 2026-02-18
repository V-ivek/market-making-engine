from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(slots=True)
class IntensityFit:
    model: str
    A: float
    k: float
    log_likelihood: float
    aic: float
    bic: float


def lambda_exponential(delta: np.ndarray | float, A: float, k: float) -> np.ndarray:
    d = np.asarray(delta, dtype=float)
    return A * np.exp(-k * np.maximum(d, 0.0))


def lambda_power(delta: np.ndarray | float, A: float, k: float, delta0: float = 1e-4) -> np.ndarray:
    d = np.asarray(delta, dtype=float)
    return A * np.power(np.maximum(d, 0.0) + delta0, -k)


def _poisson_log_likelihood(counts: np.ndarray, exposure: np.ndarray, lam: np.ndarray) -> float:
    lam_e = np.maximum(lam * exposure, 1e-12)
    counts = counts.astype(float)
    log_fact = np.array([math.lgamma(c + 1.0) for c in counts])
    return float(np.sum(counts * np.log(lam_e) - lam_e - log_fact))


def fit_exponential_mle(df: pd.DataFrame, k_min: float = 1e-4, k_max: float = 50.0, grid_points: int = 2000) -> IntensityFit:
    """Fit lambda(delta)=A*exp(-k delta) via profile likelihood grid search in k."""
    delta = df["delta"].to_numpy(dtype=float)
    counts = df["count"].to_numpy(dtype=float)
    exposure = df["exposure"].to_numpy(dtype=float)

    k_grid = np.linspace(k_min, k_max, grid_points)
    best = None

    for k in k_grid:
        z = np.exp(-k * np.maximum(delta, 0.0)) * exposure
        denom = float(np.sum(z))
        A = float(np.sum(counts) / max(denom, 1e-12))
        lam = lambda_exponential(delta, A, k)
        ll = _poisson_log_likelihood(counts, exposure, lam)
        if best is None or ll > best[0]:
            best = (ll, A, k)

    ll, A, k = best
    n = len(df)
    p = 2
    return IntensityFit(model="exponential", A=A, k=k, log_likelihood=ll, aic=2 * p - 2 * ll, bic=np.log(max(n, 1)) * p - 2 * ll)


def fit_power_mle(df: pd.DataFrame, delta0: float = 1e-4, k_min: float = 1e-3, k_max: float = 10.0, grid_points: int = 2000) -> IntensityFit:
    """Fit lambda(delta)=A*(delta+delta0)^(-k) via profile likelihood grid search in k."""
    delta = df["delta"].to_numpy(dtype=float)
    counts = df["count"].to_numpy(dtype=float)
    exposure = df["exposure"].to_numpy(dtype=float)

    k_grid = np.linspace(k_min, k_max, grid_points)
    best = None

    for k in k_grid:
        z = np.power(np.maximum(delta, 0.0) + delta0, -k) * exposure
        denom = float(np.sum(z))
        A = float(np.sum(counts) / max(denom, 1e-12))
        lam = lambda_power(delta, A, k, delta0=delta0)
        ll = _poisson_log_likelihood(counts, exposure, lam)
        if best is None or ll > best[0]:
            best = (ll, A, k)

    ll, A, k = best
    n = len(df)
    p = 2
    return IntensityFit(model="power", A=A, k=k, log_likelihood=ll, aic=2 * p - 2 * ll, bic=np.log(max(n, 1)) * p - 2 * ll)


def fit_intensity(df: pd.DataFrame, model: str = "exponential", **kwargs) -> IntensityFit:
    if model == "exponential":
        return fit_exponential_mle(df, **kwargs)
    if model == "power":
        return fit_power_mle(df, **kwargs)
    raise ValueError(f"Unsupported model: {model}")
