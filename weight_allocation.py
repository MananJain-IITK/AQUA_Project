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

def get_sector_weights(regimes, macro_shocks: dict = None) -> dict:
    """
    Calculates target portfolio weights for sectoral indices based on market regime 
    and quantitative macro sensitivities.
    
    Args:
        regimes (str or dict): Current market regime as a string ('Bull'), or a dictionary 
                               mapping sectors to their specific HMM regimes 
                               (e.g., {'Auto': 'Bullish', 'Bank': 'Bearish'}).
        macro_shocks (dict): Optional. Dictionary of current macro conditions.
                             e.g., {'Oil': 'high', 'FII': 'outflow', 'ER': 'weak'}
                             
    Returns:
        dict: Normalized weights for each sector summing to 1.0.
    """
    if macro_shocks is None:
        macro_shocks = {}
        
    raw_weights = {}
    
    # Helper function to map HMM outputs ('Bullish') to standard logic ('bull')
    def clean_regime(r):
        r = str(r).lower()
        if 'bull' in r: return 'bull'
        if 'bear' in r: return 'bear'
        return 'sideways'

    # Determine if we were passed a single global regime or a dictionary of sector regimes
    is_global = isinstance(regimes, str)
    if is_global:
        global_regime = clean_regime(regimes)
    
    for sector, data in SECTOR_DATA.items():
        base_weight = 0
        
        # Fetch the appropriate regime for this specific loop iteration
        if is_global:
            current_regime = global_regime
        else:
            # Default to sideways if the sector is missing from the dictionary
            raw_regime = regimes.get(sector, 'Sideways')
            current_regime = clean_regime(raw_regime)
            
        # ----------------------------------------------------
        # 1. BASE REGIME ALLOCATION LOGIC (Sector-Specific)
        # ----------------------------------------------------
        if current_regime == 'bear':
            # In Bear markets, overweight Defensives (High Self-Variance)
            base_weight = data['Self']
            
        elif current_regime == 'bull':
            # In Bull markets, overweight Cyclicals (High Macro Sensitivity)
            base_weight = 100 - data['Self']
            
            # Boost weight slightly if statistically proven to be lead by macro factors
            if data['Granger_Sig']:
                base_weight *= 1.2 
                
        else:
            # In Sideways markets, apply Equal Weighting as a baseline
            base_weight = 1.0 
            
        # ----------------------------------------------------
        # 2. DYNAMIC MACRO SHOCK PENALTIES
        # ----------------------------------------------------
        penalty_multiplier = 1.0
        
        if macro_shocks.get('Oil') == 'high':
            penalty_multiplier *= max(0.1, 1 - (data['Oil'] / 100))
            
        if macro_shocks.get('FII') == 'outflow':
            penalty_multiplier *= max(0.1, 1 - (data['FII'] / 100))
            
        if macro_shocks.get('ER') == 'weak':
            penalty_multiplier *= max(0.1, 1 - (data['ER'] / 100))
            
        raw_weights[sector] = base_weight * penalty_multiplier

    # ----------------------------------------------------
    # 3. NORMALIZATION
    # ----------------------------------------------------
    # Ensure all weights sum exactly to 1.0
    total_weight = sum(raw_weights.values())
    
    final_weights = {sector: round((weight / total_weight), 4) for sector, weight in raw_weights.items()}
    
    return final_weights

# ==========================================
# QUICK TEST / USAGE EXAMPLE
# ==========================================
if __name__ == "__main__":
    print("--- Testing Weight Allocator ---")
    
    print("\n1. Testing with a Single Global String (e.g., 'Bearish'):")
    print(get_sector_weights('Bearish'))
    
    print("\n2. Testing with Dictionary Output from HMM:")
    test_dict = {'Auto': 'Bullish', 'Bank': 'Bearish', 'IT': 'Sideways'}
    print(get_sector_weights(test_dict, macro_shocks={'FII': 'outflow'}))