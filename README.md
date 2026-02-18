# market-making-engine

Avellaneda-Stoikov market-making engine with:
- order-arrival intensity calibration (MLE),
- MLE report generation,
- inventory/P&L/adverse-selection backtesting.

## Quickstart

```bash
cd /home/dev/market-making-engine
python -m venv .venv
source .venv/bin/activate
pip install -e .

# End-to-end synthetic demo
mm-engine demo --outdir reports
```

## Calibrate from real data

Input CSV columns: `delta,count,exposure`

```bash
mm-engine calibrate \
  --input data/intensity_bins.csv \
  --model exponential \
  --output reports/fit.csv \
  --report reports/mle_report.md
```

## Backtest from mid-price + fitted intensity

```bash
mm-engine backtest \
  --mid data/mid.csv \
  --fit reports/fit.csv \
  --mid-col mid \
  --gamma 0.1 --sigma 0.02 \
  --horizon-steps 300 \
  --outdir reports
```

Outputs:
- `reports/backtest_timeseries.csv`
- `reports/fills.csv`
- `reports/backtest_summary.md`
- `reports/mle_report.md`

## Specs in this repo

- `IMPLEMENTATION_SPEC.md` — current executable v1 spec
- `RESEARCH_SPEC.md` — quant methodology spec (A–S + MLE + diagnostics + acceptance gates)
- `DEV_SPEC.md` — engineering architecture spec (modules, CLI, testing, CI, milestones)

## Git + GitHub

Initial local commit exists:
- `66a444c feat: scaffold Avellaneda-Stoikov engine with MLE calibration and backtest`

To connect and push to GitHub:

```bash
git remote add origin <your-github-repo-url>
git branch -M main
git push -u origin main
```
