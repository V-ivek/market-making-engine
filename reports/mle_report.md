# MLE Estimation Report

## Model
- Family: `exponential`
- Parameters:
  - A = 1.19283981
  - k = 7.92904862

## Likelihood diagnostics
- Log-likelihood: -124.4669
- AIC: 252.9337
- BIC: 256.3115
- Sample bins: 40
- Total observed arrivals: 2281.00
- Total exposure: 8000.00

## Data schema used
Input table columns:
- `delta` (float): quote distance from mid in price units
- `count` (int/float): observed arrivals in the bin
- `exposure` (float): total exposure time for that delta bin

## Notes
- Estimation uses Poisson likelihood per bin.
- Parameters are fitted by profile-likelihood grid search for robustness without external optimizers.
