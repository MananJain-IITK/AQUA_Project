# main.py
import regime_detection as rd
import weight_allocation as wa

def generate_signals(target_weights, current_weights=None):
    """
    Compares target weights to current portfolio weights to generate trade signals.
    Returns a dictionary of trade tickets.
    """
    if current_weights is None:
        current_weights = {sector: 0.0 for sector in target_weights.keys()}
        
    signals = {}
    for sector, target in target_weights.items():
        current = current_weights.get(sector, 0.0)
        delta = target - current
        
        # Define an execution threshold (e.g., don't trade if weight change is < 1%)
        threshold = 0.01 
        
        if delta > threshold:
            action = "BUY"
        elif delta < -threshold:
            action = "SELL"
        else:
            action = "HOLD"
            
        signals[sector] = {
            "Action": action,
            "Target_Weight": round(target, 4),
            "Current_Weight": round(current, 4),
            "Delta": round(delta, 4)
        }
    return signals

def generate_live_orders(current_portfolio=None):
    """
    Primary entry point for live trading execution.
    """
    print("System Boot: Initializing Live Macro-Factor Pipeline...\n")
    
    # 1. Detect Current Market Regimes
    print("[1] Fetching Latest Market Data & Running HMM...")
    _, current_regimes = rd.get_current_market_regimes()
    
    # 2. Fetch Macro Shocks (VECM logic would go here. Defaulting to empty)
    current_shocks = {} 
    
    # 3. Calculate Target Weights
    print("[2] Executing Dynamic Weight Allocation...")
    target_weights = wa.get_sector_weights(regimes=current_regimes, macro_shocks=current_shocks)
    
    # 4. Generate Trading Signals
    print("[3] Generating Trade Execution Signals...\n")
    live_signals = generate_signals(target_weights, current_portfolio)
    
    return live_signals

if __name__ == "__main__":
    # Mock Current Portfolio (e.g., what the company currently holds)
    mock_current_holdings = {
        'Auto': 0.10, 'Bank': 0.20, 'IT': 0.15, 'FMCG': 0.15, 
        'Media': 0.05, 'Metal': 0.10, 'Realty': 0.05, 'Pharma': 0.10, 'FinServ': 0.10
    }
    
    # Generate live orders
    orders = generate_live_orders(current_portfolio=mock_current_holdings)
    
    print("--- FINAL TRADE TICKETS ---")
    for sector, data in orders.items():
        print(f"{sector: <10} | {data['Action']: <4} | Target: {data['Target_Weight']*100:>5.2f}% | "
              f"Current: {data['Current_Weight']*100:>5.2f}% | Rebalance Delta: {data['Delta']*100:>5.2f}%")