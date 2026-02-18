from __future__ import annotations

from pathlib import Path

import pandas as pd

from .intensity import IntensityFit


def write_mle_report(path: str | Path, fit: IntensityFit, data: pd.DataFrame) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    text = f"""# MLE Estimation Report

## Model
- Family: `{fit.model}`
- Parameters:
  - A = {fit.A:.8f}
  - k = {fit.k:.8f}

## Likelihood diagnostics
- Log-likelihood: {fit.log_likelihood:.4f}
- AIC: {fit.aic:.4f}
- BIC: {fit.bic:.4f}
- Sample bins: {len(data)}
- Total observed arrivals: {float(data['count'].sum()):.2f}
- Total exposure: {float(data['exposure'].sum()):.2f}

## Data schema used
Input table columns:
- `delta` (float): quote distance from mid in price units
- `count` (int/float): observed arrivals in the bin
- `exposure` (float): total exposure time for that delta bin

## Notes
- Estimation uses Poisson likelihood per bin.
- Parameters are fitted by profile-likelihood grid search for robustness without external optimizers.
"""
    p.write_text(text)
    return p


def write_backtest_summary(path: str | Path, summary: dict) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Backtest Summary", ""] + [f"- {k}: {v}" for k, v in summary.items()]
    p.write_text("\n".join(lines) + "\n")
    return p
