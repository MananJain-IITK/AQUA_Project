import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import StandardScaler
from hmmlearn.hmm import GaussianHMM
import warnings

# Suppress hmmlearn warnings for cleaner terminal output during main.py execution
warnings.filterwarnings("ignore", category=FutureWarning)

def load_macro_data(filepath="india_market_macro.csv"):
    """Loads and preprocesses macroeconomic features."""
    try:
        df_macro = pd.read_csv(filepath, parse_dates=["Date"])
        df_macro.set_index("Date", inplace=True)
        
        # Calculate macro features
        df_macro["inflation"] = np.log(df_macro["CPI"]).diff() * 100
        df_macro["yield_spread"] = df_macro["GS10"] - df_macro["TBILL3M"]
        
        return df_macro[["inflation", "yield_spread"]].dropna()
    except FileNotFoundError:
        print(f"Error: {filepath} not found. Please ensure the macro dataset is available.")
        return None

def fetch_sector_data(start_date="2011-01-01"):
    """Fetches and aligns NIFTY sectoral data."""
    nifty_sectoral_indices = {
        "Auto": "^CNXAUTO",
        "Bank": "^NSEBANK",
        "IT": "^CNXIT",
        "FMCG": "^CNXFMCG",
        "Media": "^CNXMEDIA",
        "Metal": "^CNXMETAL",
        "Realty": "^CNXREALTY",
        "Pharma": "^CNXPHARMA",
        "Fin": "^CNXFIN"
    }
    
    tickers = list(nifty_sectoral_indices.values())
    nifty = yf.download(tickers, start=start_date, interval="1d", progress=False)["Close"]
    
    # Map complex tickers back to clean sector names
    inv_map = {v: k for k, v in nifty_sectoral_indices.items()}
    nifty.rename(columns=inv_map, inplace=True)
    
    nifty.index = pd.to_datetime(nifty.index)
    nifty = nifty.resample("MS").first()
    
    return nifty

def _classify_regime_state(row):
    """Internal helper to classify HMM hidden states based on their statistical means."""
    if row["returns"] > 0.5 and row["volatility"] < 2:
        return "Bullish"
    elif row["returns"] < 0 and row["volatility"] > 2:
        return "Bearish"
    else:
        return "Sideways"

def detect_regimes(df_macro, df_sectors, verbose=False):
    """
    Fits Gaussian HMM for each sector and detects historical and current market regimes.
    
    Returns:
        historical_data (dict): Dictionary mapping sectors to their full historical DataFrames.
        latest_regimes (dict): Dictionary mapping sectors to their current regime label.
    """
    historical_data = {}
    latest_regimes = {}
    
    for sector in df_sectors.columns:
        if verbose:
            print(f"Processing Regime Detection for: {sector}")
            
        sector_price = df_sectors[[sector]].rename(columns={sector: "Price"})
        df = sector_price.join(df_macro, how="inner")
        
        df["returns"] = np.log(df["Price"]).diff() * 100
        df["volatility"] = df["returns"].rolling(6).std()
        
        data = df[["returns", "volatility", "inflation", "yield_spread"]].dropna()
        
        if len(data) < 10:
            if verbose:
                print(f"  -> Insufficient data for {sector}. Skipping.")
            continue
            
        # Standardize features for HMM
        scaler = StandardScaler()
        X = scaler.fit_transform(data)
        
        # Fit HMM
        model = GaussianHMM(n_components=3, covariance_type="full", n_iter=1000, random_state=42)
        try:
            model.fit(X)
        except Exception as e:
            if verbose:
                print(f"  -> HMM fitting failed for {sector}: {e}")
            continue
        
        data["Regime"] = model.predict(X)
        
        # Interpret Regimes
        summary = data.groupby("Regime").mean()
        regime_labels = summary.apply(_classify_regime_state, axis=1).to_dict()
        data["Regime_Label"] = data["Regime"].map(regime_labels)
        
        historical_data[sector] = data
        latest_regimes[sector] = data["Regime_Label"].iloc[-1]
        
    return historical_data, latest_regimes

def get_current_market_regimes():
    """Wrapper function to be called by main.py to execute the full pipeline."""
    df_macro = load_macro_data()
    if df_macro is None:
        return {}, {}
        
    df_sectors = fetch_sector_data()
    historical_data, latest_regimes = detect_regimes(df_macro, df_sectors, verbose=False)
    
    return historical_data, latest_regimes