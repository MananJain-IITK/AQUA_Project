Macro-Factor Driven Quant Investment Strategy FOr AQUA Project
Overview

This repository contains the dynamic portfolio allocation module for a systematic macro-quant trading strategy. The core of this allocation framework is built on Vector Error Correction Model (VECM) statistical testing, which isolates the exact sensitivities of Indian equity sectors to macroeconomic factors (Crude Oil, USD/INR Exchange Rate, and FII flows).

The primary allocation logic is handled by weight_allocation.py, which dynamically tilts portfolio weights across sectors to maximize returns during bull markets and minimize drawdowns during bear markets.
How weight_allocation.py Works

The weight_allocation.py script acts as the position-sizing engine for the strategy. It does not generate buy/sell signals; instead, it answers the question: "Given the current market environment, how much capital should be allocated to each sector?"

It uses a hardcoded matrix of Forecast Error Variance Decomposition (FEVD) scores and Granger Causality p-values to make data-driven decisions:

    Bull Regime (Risk-On):

        The script overweights Cyclical sectors (e.g., Financial Services, Realty, Banks).

        It calculates weights based on Macro Sensitivity (100 - Self-Variance). Sectors that are highly influenced by macroeconomic tailwinds receive the most capital.

        A 1.2x multiplier is applied to sectors where macro factors have a statistically proven leading relationship (Granger Causality P-value < 0.05).

    Bear Regime (Risk-Off):

        The script overweights Defensive sectors (e.g., Auto, Pharma, FMCG).

        It calculates weights based on Self-Explained Variance. Sectors that ignore macroeconomic chaos and march to their own drum receive the most capital, acting as a safe haven.

    Dynamic Macro Shocks:

        Regardless of the broader regime, if a specific negative macro event occurs (e.g., Crude Oil spikes), the script automatically penalizes and underweights sectors that are highly sensitive to that specific factor.

How to Use It in Your Trading Strategy

To use this module, you need a main execution script (e.g., main.py or backtester.py) that feeds current market conditions into the allocator.
Step 1: Import the Function

Place weight_allocation.py in the same directory as your main script and import the function:
Python

from weight_allocation import get_sector_weights

Step 2: Define Your Inputs

The function requires you to pass the current market conditions, which your strategy should be calculating dynamically at each rebalance period (e.g., monthly).

    regime (string): Must be 'Bull', 'Bear', or 'Sideways'. This should be determined by your Component 2 logic (e.g., Nifty 50 moving averages, India VIX).

    macro_shocks (dictionary): Optional. Pass specific triggers if an indicator breaches a threshold.

        'Oil': 'high'

        'ER': 'weak'

        'FII': 'outflow'

Step 3: Call the Allocator in Your Backtest Loop

Inside your historical backtest loop or live-trading execution script, call the function to get your target weights for the next period.
Python

# --- Inside your monthly rebalancing loop ---

# 1. Your existing logic determines the current environment
current_regime = "Bear" 
current_shocks = {"FII": "outflow"} # Example: FIIs are net sellers this month

# 2. Get the dynamically calculated weights
target_weights = get_sector_weights(regime=current_regime, macro_shocks=current_shocks)

# 3. Print or log the target allocation
print("Target Portfolio for Next Month:")
for sector, weight in target_weights.items():
    print(f"{sector}: {weight * 100:.2f}%")

# 4. Pass 'target_weights' to your broker API or backtesting portfolio rebalancer
# execute_portfolio_rebalance(target_weights)

Expected Output Example

If you call the function during a Bull market where everything is normal:
Python

{'Auto': 0.0211, 'Bank': 0.1342, 'IT': 0.0684, 'FMCG': 0.0698, 'Media': 0.0545, 'Metal': 0.0745, 'Realty': 0.1504, 'Pharma': 0.0572, 'FinServ': 0.2185}
# Notice how FinServ (Cyclical) gets ~21.8% of the capital, while Auto gets ~2%.

If you call it during a Bear market:
Python

{'Auto': 0.1544, 'Bank': 0.0918, 'IT': 0.1218, 'FMCG': 0.1208, 'Media': 0.1313, 'Metal': 0.1176, 'Realty': 0.0824, 'Pharma': 0.1361, 'FinServ': 0.0435}
# Notice the rotation: FinServ drops to 4.3% to stop the bleeding, while Auto (Defensive) jumps to 15.4%.