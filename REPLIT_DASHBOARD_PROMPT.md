# Replit Prompt — Build MVP Dashboard for `market-making-engine`

Use this prompt in Replit AI Agent:

---

Build a **modern interactive dashboard** for a Python project called `market-making-engine`.

## Goal
Create a visually polished MVP dashboard so a user can:
1. Fetch free market data (Binance klines),
2. Run calibration,
3. Run backtest,
4. Inspect outputs (inventory, PnL, fills, adverse selection, MLE report),
5. Understand how the Avellaneda–Stoikov model behaves via controls.

## Tech requirements
- Use **Streamlit** for speed.
- Python 3.10+.
- Keep code organized:
  - `dashboard/app.py`
  - `dashboard/components/*.py`
  - `dashboard/services/engine.py` (wrapper around CLI or direct imports)
  - `dashboard/styles.css` (custom styling)
- Add `requirements-dashboard.txt`.

## Integration requirements
The existing engine exposes CLI commands:
- `mm-engine fetch-data`
- `mm-engine calibrate`
- `mm-engine backtest`
- `mm-engine demo`

Support both:
1. **Direct Python call path** (preferred when importable),
2. **CLI subprocess fallback** (robust in Replit environments).

## UX requirements
Create a cyberpunk-style dark dashboard with clear sections:

### 1) Sidebar controls
- Symbol (default BTCUSDT)
- Interval (1m, 5m, 15m)
- Limit (100–1000)
- Strategy params: gamma, sigma, horizon_steps, max_inventory, order_size
- Calibration model selector: exponential/power
- Markout horizon
- Seed

### 2) Action buttons
- `Fetch Data`
- `Calibrate`
- `Run Backtest`
- `Run Demo`
- `Refresh Artifacts`

### 3) Main panels
- KPI cards:
  - Final PnL
  - Realized spread capture
  - Inventory PnL
  - Adverse selection cost
  - Number of fills
- Charts:
  - Mid-price series
  - Inventory over time
  - MtM PnL over time
  - Drawdown curve
  - Fill scatter on price chart
- Calibration diagnostics:
  - Table with A, k, log-likelihood, AIC, BIC
  - Empirical vs fitted intensity plot (if possible)
- Report viewer:
  - Render `reports/mle_report.md`
  - Render `reports/backtest_summary.md`

## File I/O expectations
- Read/write artifacts under:
  - `data/processed/`
  - `reports/`
- Handle missing files gracefully with friendly messages.
- Add a “last run status” panel (success/fail + timestamp + stderr if failed).

## Engineering requirements
- Use typed helper functions where possible.
- Add defensive error handling around subprocess calls.
- Keep all paths project-relative.
- Include a small utility that detects whether `mm-engine` is installed; if not, show setup instructions.

## Nice-to-have (if quick)
- Parameter sensitivity mini-sweep (gamma range) and show PnL vs gamma line chart.
- Export button for a zip of report artifacts.

## Deliverables
1. Working Streamlit app with instructions in `dashboard/README.md`.
2. Command to run locally:
   - `streamlit run dashboard/app.py`
3. Dashboard should run even if only `mm-engine demo` data exists.

## Acceptance criteria
- User can click through from data fetch → calibrate → backtest in one session.
- KPI cards and at least 3 plots update from generated artifacts.
- Markdown reports are visible in app.
- Errors are surfaced clearly without crashing app.

Also provide a short "How it works" section in the dashboard explaining:
- reservation price,
- spread logic,
- why inventory and adverse selection matter.

---

