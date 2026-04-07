# In your main.py file
from weight_allocation import get_sector_weights

# ... your data fetching code ...
# ... your regime detection model code ...

current_regime = "Bull" # Detected by your Markov or Nifty 50 trend model
current_macro_signals = {'Oil': 'high', 'FII': 'normal', 'ER': 'normal'}

# Get the target weights for this month
target_portfolio = get_sector_weights(
    regime=current_regime, 
    macro_shocks=current_macro_signals
)

# Example output:
# {'Auto': 0.05, 'Bank': 0.18, 'IT': 0.12, 'FMCG': 0.11 ... }

# Then, pass these weights to your portfolio execution logic/backtester
# execute_trades(target_portfolio)