import numpy as np
from typing import Dict, Union, Callable

class Variable:
    """Classe para diferenciação automática com tracking de derivadas"""
    
    def __init__(self, value: float, derivatives: Dict[str, float] = None):
        self.value = float(value)
        self.derivatives = derivatives or {}
    
    def __add__(self, other):
        other = self._convert(other)
        derivatives = {var: self.derivatives.get(var, 0.0) + other.derivatives.get(var, 0.0)
                      for var in set(self.derivatives) | set(other.derivatives)}
        return Variable(self.value + other.value, derivatives)
    
    def __mul__(self, other):
        other = self._convert(other)
        derivatives = {}
        for var in set(self.derivatives) | set(other.derivatives):
            derivatives[var] = (self.value * other.derivatives.get(var, 0.0) +
                              other.value * self.derivatives.get(var, 0.0))
        return Variable(self.value * other.value, derivatives)
    
    def __truediv__(self, other):
        other = self._convert(other)
        derivatives = {}
        for var in set(self.derivatives) | set(other.derivatives):
            derivatives[var] = ((other.value * self.derivatives.get(var, 0.0) -
                               self.value * other.derivatives.get(var, 0.0)) /
                              (other.value * other.value))
        return Variable(self.value / other.value, derivatives)
    
    @staticmethod
    def _convert(other):
        if isinstance(other, (int, float)):
            return Variable(float(other))
        return other

class AutoDiff:
    """Gerenciador de diferenciação automática para simulação de reservatórios"""
    
    def __init__(self):
        self.variables: Dict[str, Variable] = {}
        
    def create_variable(self, name: str, value: float) -> Variable:
        """Cria uma nova variável com derivada em relação a si mesma = 1"""
        var = Variable(value, {name: 1.0})
        self.variables[name] = var
        return var
    
    def evaluate_function(self, func: Callable, variables: Dict[str, float]) -> Dict[str, float]:
        """Avalia uma função e suas derivadas para um conjunto de variáveis"""
        # Criar variáveis AD
        ad_vars = {name: self.create_variable(name, value)
                  for name, value in variables.items()}
        
        # Avaliar função
        result = func(**ad_vars)
        
        # Retornar valor e derivadas
        return {
            "value": result.value,
            "derivatives": result.derivatives
        }

# Funções auxiliares para cálculos de reservatório
def calculate_transmissibility(k: Variable, A: float, dx: float, mu: Variable) -> Variable:
    """Calcula transmissibilidade usando AD"""
    return k * A / (dx * mu)

def calculate_flow_rate(trans: Variable, dp: Variable) -> Variable:
    """Calcula taxa de fluxo usando AD"""
    return trans * dp

def calculate_accumulation(phi: Variable, rho: Variable, V: float) -> Variable:
    """Calcula termo de acumulação usando AD"""
    return phi * rho * V
