from weight_allocation import get_sector_weights

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