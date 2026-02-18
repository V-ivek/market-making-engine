import pandas as pd

from market_making_engine.intensity import fit_exponential_mle


def test_exponential_fit_returns_positive_params():
    df = pd.DataFrame(
        {
            "delta": [0.01, 0.02, 0.03, 0.05],
            "count": [100, 80, 62, 40],
            "exposure": [100.0, 100.0, 100.0, 100.0],
        }
    )
    fit = fit_exponential_mle(df, k_min=0.01, k_max=20.0, grid_points=200)
    assert fit.A > 0
    assert fit.k > 0
