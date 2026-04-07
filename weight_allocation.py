import numpy as np

# ==========================================
# MACRO SENSITIVITY MATRIX (FEVD)
# ==========================================
# Data extracted from VECM analysis (Period 10)
# 'Granger_Sig' is True if P-value < 0.05 (Macro factors significantly lead the sector)
SECTOR_DATA = {
    'Auto':    {'Self': 91.40, 'Oil': 1.43,  'ER': 4.39,  'FII': 2.78,  'Granger_Sig': False},
    'Bank':    {'Self': 54.36, 'Oil': 19.79, 'ER': 8.81,  'FII': 17.04, 'Granger_Sig': True},
    'IT':      {'Self': 72.09, 'Oil': 0.97,  'ER': 5.40,  'FII': 21.54, 'Granger_Sig': False},
    'FMCG':    {'Self': 71.52, 'Oil': 6.35,  'ER': 11.58, 'FII': 10.55, 'Granger_Sig': False},
    'Media':   {'Self': 77.74, 'Oil': 10.64, 'ER': 9.86,  'FII': 1.77,  'Granger_Sig': False},
    'Metal':   {'Self': 69.60, 'Oil': 6.47,  'ER': 2.70,  'FII': 21.23, 'Granger_Sig': False},
    'Realty':  {'Self': 48.81, 'Oil': 4.88,  'ER': 22.73, 'FII': 23.58, 'Granger_Sig': True},
    'Pharma':  {'Self': 80.55, 'Oil': 14.40, 'ER': 3.79,  'FII': 1.26,  'Granger_Sig': True},
    'FinServ': {'Self': 25.74, 'Oil': 6.58,  'ER': 6.64,  'FII': 61.04, 'Granger_Sig': True}
}

def get_sector_weights(regime: str, macro_shocks: dict = None) -> dict:
    """
    Calculates target portfolio weights for sectoral indices based on market regime 
    and quantitative macro sensitivities.
    
    Args:
        regime (str): Current market regime ('Bull', 'Bear', 'Sideways').
        macro_shocks (dict): Optional. Dictionary of current macro conditions.
                             e.g., {'Oil': 'high', 'FII': 'outflow', 'ER': 'weak'}
                             
    Returns:
        dict: Normalized weights for each sector summing to 1.0.
    """
    if macro_shocks is None:
        macro_shocks = {}
        
    raw_weights = {}
    
    for sector, data in SECTOR_DATA.items():
        base_weight = 0
        
        # ----------------------------------------------------
        # 1. BASE REGIME ALLOCATION LOGIC
        # ----------------------------------------------------
        if regime.lower() == 'bear':
            # In Bear markets, overweight Defensives (High Self-Variance)
            # These sectors ignore macro chaos.
            base_weight = data['Self']
            
        elif regime.lower() == 'bull':
            # In Bull markets, overweight Cyclicals (High Macro Sensitivity)
            # Total Macro Sensitivity = 100 - Self Variance
            base_weight = 100 - data['Self']
            
            # Boost weight slightly if the sector is statistically proven to be 
            # lead by macro factors (Granger Causality = True)
            if data['Granger_Sig']:
                base_weight *= 1.2 
                
        elif regime.lower() == 'sideways':
            # In Sideways markets, apply Equal Weighting as a baseline
            base_weight = 1.0 
            
        else:
            raise ValueError(f"Unknown regime: {regime}. Use 'Bull', 'Bear', or 'Sideways'.")
            
        # ----------------------------------------------------
        # 2. DYNAMIC MACRO SHOCK PENALTIES
        # ----------------------------------------------------
        # If specific bad macro events are happening, penalize sectors 
        # that are highly sensitive to them.
        
        penalty_multiplier = 1.0
        
        if macro_shocks.get('Oil') == 'high':
            # Penalize sectors highly sensitive to Oil (e.g., Bank, Pharma)
            # The higher the sensitivity, the larger the penalty.
            penalty_multiplier *= max(0.1, 1 - (data['Oil'] / 100))
            
        if macro_shocks.get('FII') == 'outflow':
            # Penalize sectors highly sensitive to FII (e.g., FinServ, Realty, Metal)
            penalty_multiplier *= max(0.1, 1 - (data['FII'] / 100))
            
        if macro_shocks.get('ER') == 'weak':
            # Penalize sectors highly sensitive to Exchange Rate (e.g., Realty)
            penalty_multiplier *= max(0.1, 1 - (data['ER'] / 100))
            
        # Apply the penalty
        raw_weights[sector] = base_weight * penalty_multiplier

    # ----------------------------------------------------
    # 3. NORMALIZATION
    # ----------------------------------------------------
    # Ensure all weights sum exactly to 1.0
    total_weight = sum(raw_weights.values())
    
    final_weights = {sector: round((weight / total_weight), 4) for sector, weight in raw_weights.items()}
    
    return final_weights

# ==========================================
# QUICK TEST / USAGE EXAMPLE (Remove or comment out in production)
# ==========================================
if __name__ == "__main__":
    print("--- Testing Weight Allocator ---")
    
    print("\n1. Standard Bear Market (Flight to Defensives):")
    print(get_sector_weights('Bear'))
    
    print("\n2. Standard Bull Market (Risk-On):")
    print(get_sector_weights('Bull'))
    
    print("\n3. Bull Market, but FIIs are suddenly pulling out ('outflow'):")
    print(get_sector_weights('Bull', macro_shocks={'FII': 'outflow'}))