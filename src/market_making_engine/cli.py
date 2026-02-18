from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from .backtest import run_backtest
from .config import BacktestConfig, CalibrationConfig, StrategyConfig
from .data_provider import fetch_binance_klines
from .intensity import fit_intensity
from .reporting import write_backtest_summary, write_mle_report


def _load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def cmd_calibrate(args: argparse.Namespace) -> int:
    df = _load_csv(args.input)
    cfg = CalibrationConfig(model=args.model)
    fit = fit_intensity(
        df,
        model=cfg.model,
        k_min=args.k_min,
        k_max=args.k_max,
        grid_points=args.k_grid_points,
    )

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([asdict(fit)]).to_csv(out, index=False)

    report_path = args.report or "reports/mle_report.md"
    write_mle_report(report_path, fit, df)
    print(f"Saved fit -> {out}")
    print(f"Saved report -> {report_path}")
    return 0


def cmd_backtest(args: argparse.Namespace) -> int:
    mid_df = _load_csv(args.mid)
    fit_df = _load_csv(args.fit)

    fit_row = fit_df.iloc[0].to_dict()
    from .intensity import IntensityFit

    fit = IntensityFit(
        model=str(fit_row["model"]),
        A=float(fit_row["A"]),
        k=float(fit_row["k"]),
        log_likelihood=float(fit_row.get("log_likelihood", 0.0)),
        aic=float(fit_row.get("aic", 0.0)),
        bic=float(fit_row.get("bic", 0.0)),
    )

    strat = StrategyConfig(
        gamma=args.gamma,
        sigma=args.sigma,
        horizon_steps=args.horizon_steps,
        dt=args.dt,
        max_inventory=args.max_inventory,
        order_size=args.order_size,
    )
    cfg = BacktestConfig(markout_horizon=args.markout_horizon, seed=args.seed)

    result = run_backtest(mid_df[args.mid_col], fit, strat, cfg)

    Path(args.outdir).mkdir(parents=True, exist_ok=True)
    result.timeseries.to_csv(Path(args.outdir) / "backtest_timeseries.csv", index=False)
    result.fills.to_csv(Path(args.outdir) / "fills.csv", index=False)
    write_backtest_summary(Path(args.outdir) / "backtest_summary.md", result.summary)

    print("Backtest done.")
    for k, v in result.summary.items():
        print(f"  {k}: {v}")
    return 0


def cmd_fetch_data(args: argparse.Namespace) -> int:
    if args.provider != "binance":
        raise ValueError("Only binance provider is supported in MVP")

    df = fetch_binance_klines(
        symbol=args.symbol,
        interval=args.interval,
        start_time=args.start,
        end_time=args.end,
        limit=args.limit,
    )
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)
    print(f"Saved {len(df)} rows to {args.output}")
    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    rng = np.random.default_rng(args.seed)

    # Synthetic intensity calibration data
    deltas = np.linspace(0.01, 0.5, 40)
    true_A, true_k = 1.2, 8.0
    exposure = np.full_like(deltas, 200.0)
    lam = true_A * np.exp(-true_k * deltas)
    counts = rng.poisson(lam * exposure)
    calib = pd.DataFrame({"delta": deltas, "count": counts, "exposure": exposure})

    Path(args.outdir).mkdir(parents=True, exist_ok=True)
    calib_path = Path(args.outdir) / "sample_intensity_data.csv"
    calib.to_csv(calib_path, index=False)

    fit = fit_intensity(calib, model="exponential")
    pd.DataFrame([asdict(fit)]).to_csv(Path(args.outdir) / "fit.csv", index=False)
    write_mle_report(Path(args.outdir) / "mle_report.md", fit, calib)

    # Synthetic mid-price path
    n = args.steps
    rets = rng.normal(0.0, 0.002, size=n)
    mid = 100.0 + np.cumsum(rets)
    mid_df = pd.DataFrame({"mid": mid})
    mid_df.to_csv(Path(args.outdir) / "mid.csv", index=False)

    result = run_backtest(mid_df["mid"], fit, StrategyConfig(horizon_steps=n), BacktestConfig(seed=args.seed))
    result.timeseries.to_csv(Path(args.outdir) / "backtest_timeseries.csv", index=False)
    result.fills.to_csv(Path(args.outdir) / "fills.csv", index=False)
    write_backtest_summary(Path(args.outdir) / "backtest_summary.md", result.summary)

    print(f"Demo artifacts written to {args.outdir}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mm-engine")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("calibrate", help="Calibrate order-arrival intensity via MLE")
    c.add_argument("--input", required=True, help="CSV with delta,count,exposure")
    c.add_argument("--model", default="exponential", choices=["exponential", "power"])
    c.add_argument("--k-min", type=float, default=1e-4)
    c.add_argument("--k-max", type=float, default=50.0)
    c.add_argument("--k-grid-points", type=int, default=2000)
    c.add_argument("--output", default="reports/fit.csv")
    c.add_argument("--report", default="reports/mle_report.md")
    c.set_defaults(func=cmd_calibrate)

    b = sub.add_parser("backtest", help="Run market-making backtest")
    b.add_argument("--mid", required=True, help="CSV with mid price series")
    b.add_argument("--fit", required=True, help="CSV output from calibrate")
    b.add_argument("--mid-col", default="mid")
    b.add_argument("--gamma", type=float, default=0.1)
    b.add_argument("--sigma", type=float, default=0.02)
    b.add_argument("--horizon-steps", type=int, default=300)
    b.add_argument("--dt", type=float, default=1.0)
    b.add_argument("--max-inventory", type=int, default=20)
    b.add_argument("--order-size", type=float, default=1.0)
    b.add_argument("--markout-horizon", type=int, default=5)
    b.add_argument("--seed", type=int, default=7)
    b.add_argument("--outdir", default="reports")
    b.set_defaults(func=cmd_backtest)

    f = sub.add_parser("fetch-data", help="Fetch free market data (MVP: Binance klines)")
    f.add_argument("--provider", default="binance", choices=["binance"])
    f.add_argument("--symbol", default="BTCUSDT")
    f.add_argument("--interval", default="1m")
    f.add_argument("--start", default=None, help="ISO-8601 start time, e.g. 2026-02-01T00:00:00Z")
    f.add_argument("--end", default=None, help="ISO-8601 end time")
    f.add_argument("--limit", type=int, default=1000)
    f.add_argument("--output", default="data/processed/binance_klines.csv")
    f.set_defaults(func=cmd_fetch_data)

    d = sub.add_parser("demo", help="Generate synthetic data, calibrate, and backtest")
    d.add_argument("--outdir", default="reports")
    d.add_argument("--steps", type=int, default=300)
    d.add_argument("--seed", type=int, default=7)
    d.set_defaults(func=cmd_demo)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
