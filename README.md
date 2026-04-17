# AQUA — Macro-Factor Driven Sector Allocation

This repository contains a lightweight macro-factor-driven allocation engine for Indian equity sectors. The core idea: detect market regimes with an HMM-based pipeline and produce sector-level portfolio weights using previously estimated macro sensitivities (FEVD / VECM results).

Key modules:
- `regime_detection.py`: HMM-based regime detection (per-sector) using sector returns, volatility and macro features.
- `weight_allocation.py`: Deterministic allocator that uses a hardcoded FEVD/Granger-signal matrix to produce normalized sector weights.
- `main.py`: Example orchestration that ties regime detection -> allocation -> trade-signal generation.

## What this does
- Uses historical VECM / FEVD estimates (embedded as numeric constants) to quantify how much each macro factor (Oil, USD/INR exchange rate `ER`, and Foreign Institutional Investor flows `FII`) explains sector variance.
- Uses a simple rule set:
  - In `Bull` regime: overweight sectors with high macro sensitivity (i.e., low `Self` variance). If a sector shows Granger significance, apply a 1.2x boost.
  - In `Bear` regime: overweight sectors with high `Self` variance (defensive characteristics).
  - Apply multiplicative penalties when specific macro shocks are present (e.g., `{'Oil': 'high'}` reduces weights for sectors sensitive to oil).

## FEVD / Macro Sensitivity Matrix (source: VECM period=10, embedded)
SECTOR | Self (%) | Oil (%) | ER (%) | FII (%) | Granger_Sig
---|---:|---:|---:|---:|:---
Auto    | 91.40 | 1.43  | 4.39  | 2.78  | False
Bank    | 54.36 | 19.79 | 8.81  | 17.04 | True
IT      | 72.09 | 0.97  | 5.40  | 21.54 | False
FMCG    | 71.52 | 6.35  | 11.58 | 10.55 | False
Media   | 77.74 | 10.64 | 9.86  | 1.77  | False
Metal   | 69.60 | 6.47  | 2.70  | 21.23 | False
Realty  | 48.81 | 4.88  | 22.73 | 23.58 | True
Pharma  | 80.55 | 14.40 | 3.79  | 1.26  | True
FinServ | 25.74 | 6.58  | 6.64  | 61.04 | True

These numbers are embedded in `weight_allocation.py` as the `SECTOR_DATA` constant.

## API — `get_sector_weights(regimes, macro_shocks=None)`
- `regimes`: either a single string (`'Bull'`, `'Bear'`, `'Sideways'`) or a dict mapping sectors to HMM labels (e.g., `{'Auto':'Bullish', ...}`)
- `macro_shocks`: optional dict to apply real-time penalties. Supported keys: `'Oil'`, `'FII'`, `'ER'` with values `'high'`, `'outflow'`, `'weak'` respectively.
- Returns: dict of normalized weights (sum to 1.0) with 4-decimal rounding.

Example usage (from `main.py`):

```python
from weight_allocation import get_sector_weights

# Global regime example
weights = get_sector_weights('Bull')
print(weights)

# Per-sector regimes example with a macro shock
per_sector = {'Auto': 'Bullish', 'Bank': 'Bearish', 'IT': 'Sideways'}
weights = get_sector_weights(per_sector, macro_shocks={'FII': 'outflow'})
print(weights)
```

## Exact example outputs (computed from the current `SECTOR_DATA` rules)
These outputs were generated using the current `weight_allocation.py` logic in this repository.

BULL regime sample output:

```
{
  "Auto": 0.0248,
  "Bank": 0.1582,
  "IT": 0.0806,
  "FMCG": 0.0822,
  "Media": 0.0643,
  "Metal": 0.0878,
  "Realty": 0.1774,
  "Pharma": 0.0674,
  "FinServ": 0.2573
}
```

BEAR regime sample output:

```
{
  "Auto": 0.1544,
  "Bank": 0.0919,
  "IT": 0.1218,
  "FMCG": 0.1208,
  "Media": 0.1314,
  "Metal": 0.1176,
  "Realty": 0.0825,
  "Pharma": 0.1361,
  "FinServ": 0.0435
}
```

Notes: the allocator returns weights rounded to 4 decimal places and ensures they sum to 1.0.

## Running the project

1. Create and activate a Python virtual environment (recommended).

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Quick local test — run the weight allocator directly:

```bash
python weight_allocation.py
```

3. Example end-to-end (HMM regime -> allocation -> signals):

```bash
python main.py
```

`main.py` demonstrates calling `regime_detection.get_current_market_regimes()` to obtain per-sector HMM labels and then passing them to `get_sector_weights()`; it also contains a `generate_signals()` function that converts target weights into simple BUY/SELL/HOLD signals based on a 1% execution threshold.

## Data files
- `india_market_macro.csv` — macro time series used by `regime_detection.py` (CPI, GS10, TBILL3M, etc.).
- `macro_eco_data.csv` and files under `Miscellaneous/` — additional datasets and notebooks used during research.

## Design notes & assumptions
- The FEVD numbers are taken from a prior VECM estimation and are intentionally embedded as constants (design choice to keep allocator deterministic and easy to test).
- `regime_detection.py` implements an HMM per-sector using `hmmlearn.GaussianHMM` with 3 hidden states and a heuristic mapping of state means into `Bullish` / `Bearish` / `Sideways` labels.
- Risk adjustments for macro shocks are multiplicative and bounded (minimum weight multiplier = 0.1) to avoid zeroing allocations completely.

## Findings from `AQUA.ipynb`

`AQUA.ipynb` performs the data-prep and VECM/FEVD analysis that produced the macro sensitivity numbers used in `weight_allocation.py`:
- Data: monthly macro series including Crude Oil (`Oil`), USD/INR (`ER`) and FII flows (`FII`) are log-transformed and aligned with sector log-prices where available.
- Stationarity: Unit-root tests (ADF & Phillips-Perron) are run on level and differenced series to guide model specification.
- VAR/VECM workflow:
  - Optimal lag selection via information criteria on a VAR.
  - Johansen cointegration test to select cointegration rank (often forced to r >= 1 for uniform extraction).
  - VECM estimation and diagnostic checks (normality, Durbin–Watson residuals).
- Causality & dynamics:
  - Granger-causality (Wald) tests for each target variable to check whether macro variables significantly lead sector/macro targets.
  - Impulse Response Functions (IRFs) and orthogonalized IRFs are computed.
  - Forecast Error Variance Decomposition (FEVD) over 10 periods is computed and the period-10 decomposition is reported.

Key empirical takeaways (as encoded in `SECTOR_DATA`):
- `FinServ` shows the largest contribution from `FII` (≈ 61.04%), indicating sector variance is heavily explained by FII flows.
- `Realty` has material exposure to both `ER` (≈ 22.73%) and `FII` (≈ 23.58%).
- `Bank` shows notable sensitivity to `Oil` (≈ 19.79%).
- `Pharma` is relatively more sensitive to `Oil` (≈ 14.40%) than many other sectors.

These FEVD-derived sensitivity scores (period=10) are what feed the allocator’s deterministic rules.

## Methods & Implementation Details

**`regime_detection.py` — what it does and method used**
- Purpose: infer historical and current market regimes per sector to inform allocation decisions.
- Inputs: cleaned macro features (from `india_market_macro.csv`) and monthly resampled sector close prices pulled via `yfinance`.
- Features computed per sector: log-returns (`returns`) and 6-month rolling `volatility` plus macro features (`inflation`, `yield_spread`).
- Model: a per-sector Gaussian Hidden Markov Model (`hmmlearn.GaussianHMM`) with `n_components=3` and `covariance_type='full'`.
- Preprocessing: features are standardized with `sklearn.preprocessing.StandardScaler` before HMM fitting.
- State interpretation: after predicting the hidden states, the code computes the mean of each state and maps a state to `Bullish` / `Bearish` / `Sideways` using a simple heuristic:
  - `Bullish` if mean `returns` > 0.5 and mean `volatility` < 2
  - `Bearish` if mean `returns` < 0 and mean `volatility` > 2
  - otherwise `Sideways`
- Output: a historical DataFrame per sector (with inferred state labels) and a `latest_regimes` mapping giving the most recent label per sector.

Notes on production-readiness: the HMM mapping is intentionally simple and should be validated (or replaced with a supervised regime labeler) if used for live trading.

**`weight_allocation.py` — what it does and method used**
- Purpose: deterministic sector-level position sizing using pre-computed macro sensitivities.
- Core data: `SECTOR_DATA` — a hardcoded dictionary of FEVD shares (`Self`, `Oil`, `ER`, `FII`) and a boolean `Granger_Sig` flag derived from the notebook's Granger tests.
- Allocation logic:
  - If a sector is in a `bear` regime: `base_weight = Self` (favor high self-explained variance — defensive sectors).
  - If a sector is in a `bull` regime: `base_weight = 100 - Self` (favor macro-sensitive, cyclical sectors).
    - If `Granger_Sig` is True, the bull base weight is multiplied by `1.2` to reward sectors where macro factors statistically lead.
  - If `sideways`: a small equal baseline weight (`1.0`) is used.
- Macro-shock penalties: multiplicative penalties are applied when `macro_shocks` indicates adverse conditions:
  - `Oil == 'high'` multiplies weight by `max(0.1, 1 - data['Oil']/100)`
  - `FII == 'outflow'` multiplies by `max(0.1, 1 - data['FII']/100)`
  - `ER == 'weak'` multiplies by `max(0.1, 1 - data['ER']/100)`
  - The `0.1` floor avoids zeroing a sector completely.
- Normalization: raw adjusted weights are normalized so the final weights sum to exactly `1.0`, and values are rounded to 4 decimals.

Design rationale:
- Embedding FEVD results keeps the allocator deterministic and testable.
- The combination of `Self` vs `100 - Self` provides a simple, interpretable separation between defensive and cyclical allocation drivers.
- Granger-based boosts and multiplicative penalties allow compact encoding of directional macro risk signals while keeping the allocator simple.

## License & contact
This code is provided as-is for research and experimentation for a quant firm named AQUA. For questions, contact the repository owner.
