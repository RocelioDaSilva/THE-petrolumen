import numpy as np
from typing import Dict, List, Optional
import logging
from datetime import datetime

class EconomicAnalysis:
    """Classe para análise econômica de projetos de reservatórios."""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.cash_flow = None
        self.economic_parameters = None
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('EconomicAnalysis')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
        
    def set_economic_parameters(self,
                              oil_price: float,
                              gas_price: float,
                              discount_rate: float,
                              project_life: int,
                              capex: Dict[str, float],
                              opex: Dict[str, float],
                              tax_rate: float = 0.34):
        """
        Define parâmetros econômicos.
        
        Args:
            oil_price: Preço do óleo ($/bbl)
            gas_price: Preço do gás ($/Mscf)
            discount_rate: Taxa de desconto (%)
            project_life: Vida do projeto (anos)
            capex: Dicionário com investimentos
            opex: Dicionário com custos operacionais
            tax_rate: Alíquota de impostos
        """
        self.economic_parameters = {
            'oil_price': oil_price,
            'gas_price': gas_price,
            'discount_rate': discount_rate,
            'project_life': project_life,
            'capex': capex,
            'opex': opex,
            'tax_rate': tax_rate
        }
        
    def calculate_cash_flow(self,
                          oil_production: np.ndarray,
                          gas_production: np.ndarray,
                          water_production: np.ndarray) -> Dict:
        """
        Calcula fluxo de caixa.
        
        Args:
            oil_production: Produção de óleo (bbl/dia)
            gas_production: Produção de gás (Mscf/dia)
            water_production: Produção de água (bbl/dia)
            
        Returns:
            Dicionário com resultados do fluxo de caixa
        """
        if self.economic_parameters is None:
            raise ValueError("Parâmetros econômicos não definidos")
            
        # Receitas
        oil_revenue = oil_production * self.economic_parameters['oil_price']
        gas_revenue = gas_production * self.economic_parameters['gas_price']
        total_revenue = oil_revenue + gas_revenue
        
        # Custos
        opex_total = np.sum(list(self.economic_parameters['opex'].values()))
        total_costs = opex_total
        
        # EBITDA
        ebitda = total_revenue - total_costs
        
        # Depreciação
        depreciation = np.sum(list(self.economic_parameters['capex'].values())) / self.economic_parameters['project_life']
        
        # Lucro antes dos impostos
        ebit = ebitda - depreciation
        
        # Impostos
        taxes = ebit * self.economic_parameters['tax_rate']
        
        # Lucro líquido
        net_income = ebit - taxes
        
        # Fluxo de caixa
        cash_flow = net_income + depreciation
        
        self.cash_flow = {
            'revenue': {
                'oil': oil_revenue,
                'gas': gas_revenue,
                'total': total_revenue
            },
            'costs': {
                'opex': opex_total,
                'total': total_costs
            },
            'ebitda': ebitda,
            'depreciation': depreciation,
            'ebit': ebit,
            'taxes': taxes,
            'net_income': net_income,
            'cash_flow': cash_flow
        }
        
        return self.cash_flow
        
    def calculate_npv(self) -> float:
        """
        Calcula Valor Presente Líquido (NPV).
        
        Returns:
            NPV
        """
        if self.cash_flow is None:
            raise ValueError("Fluxo de caixa não calculado")
            
        discount_factor = 1 / (1 + self.economic_parameters['discount_rate']/100)
        npv = 0
        
        for t in range(self.economic_parameters['project_life']):
            npv += self.cash_flow['cash_flow'][t] * (discount_factor ** t)
            
        return npv
        
    def calculate_irr(self) -> float:
        """
        Calcula Taxa Interna de Retorno (IRR).
        
        Returns:
            IRR (%)
        """
        if self.cash_flow is None:
            raise ValueError("Fluxo de caixa não calculado")
            
        # Implementar cálculo de IRR
        pass
        
    def calculate_payback(self) -> float:
        """
        Calcula Payback.
        
        Returns:
            Payback (anos)
        """
        if self.cash_flow is None:
            raise ValueError("Fluxo de caixa não calculado")
            
        cumulative_cash_flow = np.cumsum(self.cash_flow['cash_flow'])
        payback = np.where(cumulative_cash_flow >= 0)[0][0]
        
        return payback
        
    def calculate_roi(self) -> float:
        """
        Calcula Retorno sobre Investimento (ROI).
        
        Returns:
            ROI (%)
        """
        if self.cash_flow is None:
            raise ValueError("Fluxo de caixa não calculado")
            
        total_investment = np.sum(list(self.economic_parameters['capex'].values()))
        total_profit = np.sum(self.cash_flow['net_income'])
        
        roi = (total_profit / total_investment) * 100
        return roi
        
    def sensitivity_analysis(self,
                           parameter: str,
                           range_values: List[float]) -> Dict:
        """
        Análise de sensibilidade.
        
        Args:
            parameter: Parâmetro a ser analisado
            range_values: Lista de valores para análise
            
        Returns:
            Dicionário com resultados da análise
        """
        if self.economic_parameters is None:
            raise ValueError("Parâmetros econômicos não definidos")
            
        results = {}
        original_value = self.economic_parameters[parameter]
        
        for value in range_values:
            self.economic_parameters[parameter] = value
            npv = self.calculate_npv()
            results[value] = npv
            
        # Restaura valor original
        self.economic_parameters[parameter] = original_value
        
        return results
        
    def monte_carlo_simulation(self,
                             n_simulations: int,
                             parameters: Dict[str, tuple]) -> Dict:
        """
        Simulação de Monte Carlo.
        
        Args:
            n_simulations: Número de simulações
            parameters: Dicionário com parâmetros e suas distribuições
            
        Returns:
            Dicionário com resultados da simulação
        """
        if self.economic_parameters is None:
            raise ValueError("Parâmetros econômicos não definidos")
            
        npvs = []
        
        for _ in range(n_simulations):
            # Amostra parâmetros
            for param, (dist, *args) in parameters.items():
                self.economic_parameters[param] = dist(*args)
                
            # Calcula NPV
            npv = self.calculate_npv()
            npvs.append(npv)
            
        return {
            'mean': np.mean(npvs),
            'std': np.std(npvs),
            'p10': np.percentile(npvs, 10),
            'p50': np.percentile(npvs, 50),
            'p90': np.percentile(npvs, 90)
        } 