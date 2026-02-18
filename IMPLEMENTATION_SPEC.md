# Implementation Spec — Avellaneda-Stoikov Market-Making Engine

## 1) Objective
Build a Python project in `/home/dev/market-making-engine` implementing:
1. Avellaneda-Stoikov (A-S) quoting logic,
2. Calibrated order-arrival intensity models using MLE,
3. Backtesting with inventory, P&L, and adverse-selection breakdown,
4. Reproducible reports and CLI workflow.

## 2) Agent-team plan (lanes)
- **Quant researcher lane**
  - Define equations and statistical assumptions.
  - Specify MLE objective(s), diagnostics, and model selection criteria.
  - Define adverse selection decomposition and interpretation.
- **Quant developer lane**
  - Define project architecture, modules, I/O schemas, CLI.
  - Implement calibration + strategy + event-loop backtest.
  - Add tests and report artifacts.

## 3) Mathematical model
Let:
- \(S_t\): mid-price,
- \(q_t\): inventory,
- \(\gamma>0\): risk aversion,
- \(\sigma\): volatility estimate,
- \(T\): strategy horizon,
- \(\tau=T-t\),
- \(k\): intensity-decay parameter.

A-S quotes:
- Reservation price: \(r_t = S_t - q_t\gamma\sigma^2\tau\)
- Optimal half-spread:
\[
\delta_t^* = \frac{1}{\gamma}\ln\left(1+\frac{\gamma}{k}\right) + \frac{1}{2}\gamma\sigma^2\tau
\]
- Quotes: \(b_t = r_t - \delta_t^*\), \(a_t = r_t + \delta_t^*\)

Inventory dynamics (unit size \(v\)):
- Bid fill: \(q_{t+1}=q_t+v\)
- Ask fill: \(q_{t+1}=q_t-v\)

## 4) Order-arrival intensity models + MLE
### Primary model
\[
\lambda(\delta) = A e^{-k\delta}, \quad A>0, k>0
\]

### Alternative model
\[
\lambda(\delta) = A(\delta+\delta_0)^{-k}, \quad \delta_0>0
\]

Using binned data \((\delta_i, n_i, E_i)\):
- \(n_i\): arrival count,
- \(E_i\): exposure time.
- Poisson assumption: \(n_i\sim\text{Poisson}(\lambda_iE_i)\)

Log-likelihood:
\[
\ell(\theta)=\sum_i n_i\log(\lambda_iE_i)-\lambda_iE_i-\log(n_i!)
\]

Fitting method:
- Profile-likelihood grid search in \(k\), closed-form \(A\) conditional on \(k\):
  - Exponential: \(\hat A(k)=\frac{\sum_i n_i}{\sum_i E_i e^{-k\delta_i}}\)
  - Power-law: \(\hat A(k)=\frac{\sum_i n_i}{\sum_i E_i(\delta_i+\delta_0)^{-k}}\)

Diagnostics:
- Log-likelihood, AIC, BIC,
- Fitted-vs-observed intensity by \(\delta\)-bin,
- Parameter sanity checks \((A>0, k>0)\).

## 5) Data schema
### Calibration input CSV
- `delta` (float): quote distance from mid,
- `count` (int/float): observed arrivals,
- `exposure` (float): exposure time at that distance.

### Backtest input CSV
- `mid` (float): mid-price series.

### Outputs
- `reports/fit.csv` (model + estimated parameters + info criteria),
- `reports/mle_report.md`,
- `reports/backtest_timeseries.csv`,
- `reports/fills.csv`,
- `reports/backtest_summary.md`.

## 6) Backtest/event-loop architecture
At each step:
1. Compute A-S quote from current \(S_t, q_t, \tau\),
2. Convert quote distances to intensities \(\lambda_{bid},\lambda_{ask}\),
3. Fill probs: \(p=1-e^{-\lambda\Delta t}\),
4. Simulate fills, update inventory/cash,
5. Compute P&L components.

Inventory caps enforced: \(q\in[-q_{max},q_{max}]\).

## 7) Metrics and decomposition
- **Inventory metrics:** mean, std, max |inventory|,
- **P&L:** final MtM P&L = cash + inventory × mid,
- **Spread capture:** immediate edge at fill vs mid,
- **Inventory P&L:** mark-to-market from carrying position,
- **Adverse selection:** post-fill markout cost over horizon \(h\), aggregated across fills.

## 8) Project structure
```text
src/market_making_engine/
  avellaneda_stoikov.py
  intensity.py
  backtest.py
  reporting.py
  config.py
  cli.py
tests/
reports/
IMPLEMENTATION_SPEC.md
```

## 9) CLI entrypoints
- `mm-engine calibrate --input ... --model exponential|power`
- `mm-engine backtest --mid ... --fit ...`
- `mm-engine demo` (synthetic end-to-end smoke run)

## 10) Test strategy
- Unit tests:
  - intensity fit returns valid params,
  - backtest loop runs and produces summary.
- Extend later with:
  - property checks (monotonic intensity vs delta for exponential),
  - regression fixtures for deterministic seeds.

## 11) Milestones + acceptance criteria
1. **Spec + scaffold** ✅
   - Clear equations, data schema, architecture.
2. **Calibration engine** ✅
   - MLE fit + AIC/BIC + report generation.
3. **Backtester** ✅
   - Inventory/P&L/adverse-selection metrics.
4. **CLI + artifacts** ✅
   - Reproducible command flow from input to reports.
5. **Tests** ✅
   - Basic unit coverage in place.

## 12) Risks / caveats
- Poisson independence and stationarity assumptions may break intraday.
- Fill simulation is reduced-form (distance-based intensity), not full LOB microstructure.
- Power-law model may require stronger regularization and robust optimization for noisy data.
