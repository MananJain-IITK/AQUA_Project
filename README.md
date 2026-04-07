***

# Macro-Factor Driven Quant Investment Strategy

## Overview
This documentation outlines the dynamic portfolio allocation module for a systematic macro-quant trading strategy. The allocation framework is built upon Vector Error Correction Model (VECM) statistical testing, which isolates the historical sensitivities of Indian equity sectors to macroeconomic factors (Crude Oil, USD/INR Exchange Rate, and FII flows). 

The primary allocation logic is handled by the `weight_allocation.py` script, which dynamically adjusts portfolio weights across sectors to maximize exposure during bull markets and minimize drawdowns during bear markets.

---

## Module Mechanics: `weight_allocation.py`
The `weight_allocation.py` script functions as the position-sizing engine for the overarching strategy. It does not generate directional buy/sell signals; rather, it determines the optimal capital allocation for each sector given the prevailing macroeconomic environment.

The decision engine utilizes a hardcoded matrix of Forecast Error Variance Decomposition (FEVD) scores and Granger Causality p-values to execute data-driven allocation shifts:

1. **Bull Regime (Risk-On Allocation):**
   * Cyclical sectors (e.g., Financial Services, Realty, Banks) receive higher weightings.
   * Weights are calculated based on **Macro Sensitivity** (100 - Self-Variance), allocating more capital to sectors highly influenced by macroeconomic tailwinds.
   * A 1.2x multiplier is applied to sectors where macro factors exhibit a statistically significant leading relationship (Granger Causality P-value < 0.05).

2. **Bear Regime (Risk-Off Allocation):**
   * Defensive sectors (e.g., Auto, Pharma, FMCG) receive higher weightings.
   * Weights are calculated based on **Self-Explained Variance**. Sectors that exhibit low correlation to macroeconomic volatility receive higher allocations to act as safe havens.

3. **Dynamic Macro Shocks:**
   * Independent of the broader market regime, the occurrence of specific negative macro events (e.g., a spike in Crude Oil prices) triggers automatic penalties. Sectors previously identified as highly sensitive to that specific factor are systematically underweighted.

---

## Integration and Usage Guide

To implement this module, it must be integrated into a main execution script (e.g., `main.py` or `backtester.py`) that supplies the current market conditions to the allocator at each rebalancing interval.

### 1. Module Importation
The `weight_allocation.py` file must be located in the same directory as the main execution script. The allocation function is imported as follows:

```python
from weight_allocation import get_sector_weights
```

### 2. Parameter Definitions
The function evaluates market conditions calculated dynamically at each rebalance period (e.g., monthly). The required parameters are:

* **`regime`** *(string)*: Accepts `'Bull'`, `'Bear'`, or `'Sideways'`. This classification is typically provided by a separate market regime detection model.
* **`macro_shocks`** *(dictionary)*: An optional parameter used to pass specific triggers if a macroeconomic indicator breaches a predefined risk threshold (e.g., `{'Oil': 'high'}`, `{'ER': 'weak'}`, `{'FII': 'outflow'}`).

### 3. Execution Integration
Inside the historical backtest loop or live-trading environment, the function is called to generate target weights for the subsequent period. The following code block demonstrates a standard implementation:

```python
# --- Monthly Rebalancing Logic ---

# 1. The external regime detection model determines the current environment
current_regime = "Bear" 
current_shocks = {"FII": "outflow"} # Example scenario: FIIs are net sellers

# 2. The allocator generates dynamically adjusted weights
target_weights = get_sector_weights(regime=current_regime, macro_shocks=current_shocks)

# 3. Target allocation is logged or passed to the execution engine
print("Target Portfolio Allocation:")
for sector, weight in target_weights.items():
    print(f"{sector}: {weight * 100:.2f}%")

# 4. Target weights are passed to the broker API or backtesting rebalancer
# execute_portfolio_rebalance(target_weights)
```

### 4. Expected Output Profiles
The output will dynamically shift based on the inputs provided. 

During a standard **Bull** market, the allocator prioritizes cyclicals:
```python
{'Auto': 0.0211, 'Bank': 0.1342, 'IT': 0.0684, 'FMCG': 0.0698, 'Media': 0.0545, 'Metal': 0.0745, 'Realty': 0.1504, 'Pharma': 0.0572, 'FinServ': 0.2185}
# Note: Financial Services receives ~21.8% of the capital, while Auto receives ~2%.
```

During a **Bear** market, capital systematically rotates to defensive assets:
```python
{'Auto': 0.1544, 'Bank': 0.0918, 'IT': 0.1218, 'FMCG': 0.1208, 'Media': 0.1313, 'Metal': 0.1176, 'Realty': 0.0824, 'Pharma': 0.1361, 'FinServ': 0.0435}
# Note: Financial Services exposure drops to 4.3%, while Auto jumps to 15.4%.
```