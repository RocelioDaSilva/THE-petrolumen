import numpy as np
from scipy.interpolate import interp2d

def calculate_pseudo_critical(composition):
    """
    Calcula as propriedades pseudo-críticas da mistura gasosa.
    
    Args:
        composition (dict): Composição gasosa (C1-C5) em fração molar
    
    Returns:
        tuple: (Tpc, Ppc) - Temperatura e pressão pseudo-críticas
    """
    # Propriedades críticas dos componentes (T em °R, P em psia)
    critical_props = {
        'C1': {'T': 343.0, 'P': 667.8},
        'C2': {'T': 549.8, 'P': 707.8},
        'C3': {'T': 665.7, 'P': 616.3},
        'C4': {'T': 765.3, 'P': 550.7},
        'C5': {'T': 845.4, 'P': 488.6}
    }
    
    # Cálculo das propriedades pseudo-críticas
    Tpc = sum(composition[comp] * critical_props[comp]['T'] for comp in composition)
    Ppc = sum(composition[comp] * critical_props[comp]['P'] for comp in composition)
    
    return Tpc, Ppc

def calculate_z_factor(pressure, temperature, composition):
    """
    Calcula o Z-Factor via correlação de Standing & Katz.
    
    Args:
        pressure (float): Pressão em psia
        temperature (float): Temperatura em °R
        composition (dict): Composição gasosa (C1-C5) em fração molar
    
    Returns:
        float: Z-Factor
    """
    # Calcular propriedades pseudo-críticas
    Tpc, Ppc = calculate_pseudo_critical(composition)
    
    # Calcular propriedades pseudo-reduzidas
    Ppr = pressure / Ppc
    Tpr = temperature / Tpc
    
    # Coeficientes da correlação de Standing & Katz
    A1 = 0.3265
    A2 = -1.0700
    A3 = -0.5339
    A4 = 0.01569
    A5 = -0.05165
    A6 = 0.5475
    A7 = -0.7361
    A8 = 0.1844
    A9 = 0.1056
    A10 = 0.6134
    A11 = 0.7210
    
    # Cálculo do Z-Factor usando a correlação
    rho_r = 0.27 * Ppr / (Tpr * 1.0)  # Densidade reduzida inicial
    
    # Método iterativo para encontrar Z
    for _ in range(10):  # Número máximo de iterações
        Z = 1.0 + (A1 + A2/Tpr + A3/Tpr**3 + A4/Tpr**4 + A5/Tpr**5) * rho_r + \
            (A6 + A7/Tpr + A8/Tpr**2) * rho_r**2 - \
            A9 * (A7/Tpr + A8/Tpr**2) * rho_r**5 + \
            A10 * (1 + A11 * rho_r**2) * (rho_r**2 / Tpr**3) * np.exp(-A11 * rho_r**2)
        
        # Atualizar densidade reduzida
        rho_r_new = 0.27 * Ppr / (Tpr * Z)
        if abs(rho_r_new - rho_r) < 1e-6:
            break
        rho_r = rho_r_new
    
    return Z 