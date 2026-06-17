import pandas as pd
import numpy as np
import regime_detection as rd
import weight_allocation as wa

def calculate_drawdown(cumulative_returns):
    peak = cumulative_returns.cummax()
    drawdown = (cumulative_returns - peak) / peak
    return drawdown.min()

def run_backtest(initial_capital=100000, plot_results=True):
    print("--- AQUA Backtest Engine Initializing ---")
    
    # 1. Fetch Data & Run HMM
    print("[1] Fetching Macro & Sector Data...")
    df_macro = rd.load_macro_data()
    if df_macro is None:
        print("Backtest aborted: Macro data missing.")
        return
        
    df_sectors = rd.fetch_sector_data()
    
    print("[2] Running historical regime detection (this may take a moment)...")
    historical_data, _ = rd.detect_regimes(df_macro, df_sectors, verbose=False)
    
    # 2. Align Regimes and Forward Returns
    # We extract the 'Regime_Label' and actual 'returns' for each sector
    print("[3] Aligning historical states and computing forward returns...")
    regimes_dict = {}
    returns_dict = {}
    
    for sector, df in historical_data.items():
        regimes_dict[sector] = df['Regime_Label']
        # Convert logarithmic percentage returns back to simple decimal returns for the backtest
        returns_dict[sector] = np.exp(df['returns'] / 100.0) - 1.0 
        
    df_regimes = pd.DataFrame(regimes_dict)
    df_returns = pd.DataFrame(returns_dict)
    
    # Shift returns by -1 because weights generated at end of month T 
    # will capture the returns of month T+1.
    df_forward_returns = df_returns.shift(-1)
    
    # Drop NAs to ensure we only test periods where we have both regimes and next month's returns
    valid_dates = df_regimes.dropna().index.intersection(df_forward_returns.dropna().index)
    df_regimes = df_regimes.loc[valid_dates]
    df_forward_returns = df_forward_returns.loc[valid_dates]
    
    # 3. Simulate the Portfolio Walk-Forward
    print("[4] Executing Walk-Forward Portfolio Simulation...\n")
    
    portfolio_records = []
    
    for date in valid_dates:
        # Extract the regime for each sector on this specific date
        current_regimes = df_regimes.loc[date].to_dict()
        
        # Calculate target weights via our AQUA allocator (assuming no macro shocks for baseline)
        target_weights = wa.get_sector_weights(current_regimes)
        
        # Extract the forward returns for the next period
        next_returns = df_forward_returns.loc[date].to_dict()
        
        # Calculate Portfolio Return: Sum of (Weight * Forward Return)
        port_return = sum(target_weights.get(sec, 0) * next_returns.get(sec, 0) for sec in target_weights.keys())
        
        # Calculate Equal Weight Benchmark Return
        eq_weight = 1.0 / len(next_returns)
        benchmark_return = sum(eq_weight * next_returns.get(sec, 0) for sec in next_returns.keys())
        
        portfolio_records.append({
            'Date': date,
            'AQUA_Return': port_return,
            'Benchmark_Return': benchmark_return
        })
        
    # 4. Performance Analytics
    results = pd.DataFrame(portfolio_records).set_index('Date')
    
    # Calculate Cumulative Wealth Index (Base = 1.0)
    results['AQUA_Equity'] = (1 + results['AQUA_Return']).cumprod()
    results['Benchmark_Equity'] = (1 + results['Benchmark_Return']).cumprod()
    
    # Metrics calculation
    years = len(results) / 12.0 # Assuming monthly data
    
    aqua_total_return = results['AQUA_Equity'].iloc[-1] - 1
    aqua_cagr = (results['AQUA_Equity'].iloc[-1] ** (1 / years)) - 1
    aqua_vol = results['AQUA_Return'].std() * np.sqrt(12)
    aqua_sharpe = aqua_cagr / aqua_vol if aqua_vol > 0 else 0
    aqua_mdd = calculate_drawdown(results['AQUA_Equity'])
    
    bench_cagr = (results['Benchmark_Equity'].iloc[-1] ** (1 / years)) - 1
    bench_vol = results['Benchmark_Return'].std() * np.sqrt(12)
    bench_sharpe = bench_cagr / bench_vol if bench_vol > 0 else 0
    bench_mdd = calculate_drawdown(results['Benchmark_Equity'])
    
    # Print Results
    print("==================================================")
    print("              BACKTEST RESULTS                    ")
    print("==================================================")
    print(f"Months Tested: {len(results)} (~{years:.1f} Years)")
    print("-" * 50)
    print(f"{'Metric':<20} | {'AQUA Strategy':<12} | {'Equal Weight':<12}")
    print("-" * 50)
    print(f"{'Total Return':<20} | {aqua_total_return*100:>11.2f}% | {(results['Benchmark_Equity'].iloc[-1] - 1)*100:>11.2f}%")
    print(f"{'CAGR':<20} | {aqua_cagr*100:>11.2f}% | {bench_cagr*100:>11.2f}%")
    print(f"{'Annual Volatility':<20} | {aqua_vol*100:>11.2f}% | {bench_vol*100:>11.2f}%")
    print(f"{'Sharpe Ratio':<20} | {aqua_sharpe:>11.2f}  | {bench_sharpe:>11.2f}")
    print(f"{'Max Drawdown':<20} | {aqua_mdd*100:>11.2f}% | {bench_mdd*100:>11.2f}%")
    print("==================================================\n")

    if plot_results:
        try:
            import matplotlib.pyplot as plt
            plt.figure(figsize=(10, 6))
            plt.plot(results.index, results['AQUA_Equity'] * initial_capital, label='AQUA Strategy', color='blue', linewidth=2)
            plt.plot(results.index, results['Benchmark_Equity'] * initial_capital, label='Equal Weight Benchmark', color='gray', linestyle='--')
            plt.title('AQUA Portfolio vs Equal Weight Benchmark')
            plt.ylabel('Portfolio Value (Base = $100k)')
            plt.xlabel('Date')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.show()
        except ImportError:
            print("Note: matplotlib is not installed. Skipping equity curve plot.")

if __name__ == "__main__":
    run_backtest()