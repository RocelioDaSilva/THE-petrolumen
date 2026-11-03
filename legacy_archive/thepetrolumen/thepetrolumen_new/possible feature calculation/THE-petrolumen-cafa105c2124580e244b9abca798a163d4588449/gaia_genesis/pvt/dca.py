import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

def hyperbolic_decline(t, qi, Di, b):
    """
    Função de declínio hiperbólico.
    
    Args:
        t (array): Tempo em dias
        qi (float): Taxa inicial de produção
        Di (float): Taxa inicial de declínio
        b (float): Expoente de declínio
    
    Returns:
        array: Taxa de produção prevista
    """
    return qi * (1 + b * Di * t) ** (-1/b)

def exponential_decline(t, qi, Di):
    """
    Função de declínio exponencial (caso especial do hiperbólico com b=0).
    
    Args:
        t (array): Tempo em dias
        qi (float): Taxa inicial de produção
        Di (float): Taxa de declínio
    
    Returns:
        array: Taxa de produção prevista
    """
    return qi * np.exp(-Di * t)

def harmonic_decline(t, qi, Di):
    """
    Função de declínio harmônico (caso especial do hiperbólico com b=1).
    
    Args:
        t (array): Tempo em dias
        qi (float): Taxa inicial de produção
        Di (float): Taxa inicial de declínio
    
    Returns:
        array: Taxa de produção prevista
    """
    return qi / (1 + Di * t)

def fit_decline_curve(time, rate, decline_type='hyperbolic'):
    """
    Ajusta uma curva de declínio aos dados de produção.
    
    Args:
        time (array): Tempo em dias
        rate (array): Taxa de produção
        decline_type (str): Tipo de declínio ('hyperbolic', 'exponential', 'harmonic')
    
    Returns:
        tuple: (qi, Di, b) - Parâmetros ajustados
    """
    if decline_type == 'exponential':
        popt, _ = curve_fit(exponential_decline, time, rate, p0=[rate[0], 0.1])
        return popt[0], popt[1], 0.0
    elif decline_type == 'harmonic':
        popt, _ = curve_fit(harmonic_decline, time, rate, p0=[rate[0], 0.1])
        return popt[0], popt[1], 1.0
    else:  # hyperbolic
        popt, _ = curve_fit(hyperbolic_decline, time, rate, p0=[rate[0], 0.1, 0.5])
        return popt[0], popt[1], popt[2]

def plot_decline_curve(time, rate, qi, Di, b, decline_type='hyperbolic'):
    """
    Plota a curva de declínio ajustada junto com os dados reais.
    
    Args:
        time (array): Tempo em dias
        rate (array): Taxa de produção real
        qi (float): Taxa inicial ajustada
        Di (float): Taxa de declínio ajustada
        b (float): Expoente de declínio
        decline_type (str): Tipo de declínio
    
    Returns:
        tuple: (fig, ax) - Objetos da figura matplotlib
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot dados reais
    ax.scatter(time, rate, label='Dados Reais', color='blue')
    
    # Plot curva ajustada
    t_fit = np.linspace(0, max(time) * 1.5, 100)
    if decline_type == 'exponential':
        rate_fit = exponential_decline(t_fit, qi, Di)
    elif decline_type == 'harmonic':
        rate_fit = harmonic_decline(t_fit, qi, Di)
    else:
        rate_fit = hyperbolic_decline(t_fit, qi, Di, b)
    
    ax.plot(t_fit, rate_fit, label='Curva Ajustada', color='red')
    
    ax.set_xlabel('Tempo (dias)')
    ax.set_ylabel('Taxa de Produção')
    ax.set_title('Análise de Curva de Declínio')
    ax.grid(True)
    ax.legend()
    
    return fig, ax 