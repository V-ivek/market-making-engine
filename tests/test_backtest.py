import numpy as np
import pandas as pd

from market_making_engine.backtest import run_backtest
from market_making_engine.config import BacktestConfig, StrategyConfig
from market_making_engine.intensity import IntensityFit


def test_backtest_runs_and_has_summary():
    mid = pd.Series(100 + np.cumsum(np.zeros(50)))
    fit = IntensityFit(model="exponential", A=1.0, k=5.0, log_likelihood=0.0, aic=0.0, bic=0.0)
    result = run_backtest(mid, fit, StrategyConfig(horizon_steps=50), BacktestConfig(seed=1))
    assert "final_pnl" in result.summary
    assert len(result.timeseries) == 50
