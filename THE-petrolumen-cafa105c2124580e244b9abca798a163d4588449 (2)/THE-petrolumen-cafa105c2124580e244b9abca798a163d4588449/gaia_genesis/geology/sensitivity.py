import numpy as np
import pandas as pd
from scipy.stats import norm, uniform, lognorm
import matplotlib.pyplot as plt
import seaborn as sns
from SALib.sample import saltelli
from SALib.analyze import sobol
from sklearn.ensemble import RandomForestRegressor

class SensitivityAnalysis:
    def __init__(self):
        """
        Inicializa o objeto de análise de sensitividade.
        """
        self.parameters = {}
        self.samples = None
        self.results = None
        self.sensitivity_indices = None
        
    def add_parameter(self, name, distribution, params):
        """
        Adiciona um parâmetro para análise.
        
        Args:
            name (str): Nome do parâmetro
            distribution (str): Distribuição ('normal', 'uniform', 'lognormal')
            params (dict): Parâmetros da distribuição
        """
        self.parameters[name] = {
            'distribution': distribution,
            'params': params
        }
        
    def generate_samples(self, n_samples=1000):
        """
        Gera amostras usando o método de Saltelli.
        
        Args:
            n_samples (int): Número de amostras
        """
        # Definir problema para SALib
        problem = {
            'num_vars': len(self.parameters),
            'names': list(self.parameters.keys()),
            'bounds': []
        }
        
        for param in self.parameters.values():
            if param['distribution'] == 'normal':
                mean, std = param['params']['mean'], param['params']['std']
                problem['bounds'].append([mean - 3*std, mean + 3*std])
            elif param['distribution'] == 'uniform':
                min_val, max_val = param['params']['min'], param['params']['max']
                problem['bounds'].append([min_val, max_val])
            elif param['distribution'] == 'lognormal':
                mean, std = param['params']['mean'], param['params']['std']
                problem['bounds'].append([mean/10, mean*10])
                
        # Gerar amostras
        self.samples = saltelli.sample(problem, n_samples)
        
    def run_analysis(self, model_function):
        """
        Executa a análise de sensitividade.
        
        Args:
            model_function (callable): Função que calcula o resultado do modelo
        """
        if self.samples is None:
            raise ValueError("Amostras não geradas")
            
        # Executar modelo para cada amostra
        self.results = np.array([model_function(sample) for sample in self.samples])
        
        # Calcular índices de sensitividade
        problem = {
            'num_vars': len(self.parameters),
            'names': list(self.parameters.keys()),
            'bounds': [[0, 1]] * len(self.parameters)
        }
        
        self.sensitivity_indices = sobol.analyze(problem, self.results)
        
    def plot_sensitivity_indices(self):
        """
        Plota os índices de sensitividade.
        """
        if self.sensitivity_indices is None:
            raise ValueError("Análise não executada")
            
        # Preparar dados
        indices = pd.DataFrame({
            'Parameter': list(self.parameters.keys()),
            'S1': self.sensitivity_indices['S1'],
            'ST': self.sensitivity_indices['ST']
        })
        
        # Plotar
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Índices de primeira ordem
        sns.barplot(data=indices, x='Parameter', y='S1', ax=ax1)
        ax1.set_title('Índices de Primeira Ordem (S1)')
        ax1.set_xticklabels(ax1.get_xticklabels(), rotation=45)
        
        # Índices totais
        sns.barplot(data=indices, x='Parameter', y='ST', ax=ax2)
        ax2.set_title('Índices Totais (ST)')
        ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45)
        
        plt.tight_layout()
        return fig
        
    def plot_uncertainty(self, n_samples=1000):
        """
        Plota análise de incerteza.
        
        Args:
            n_samples (int): Número de amostras para Monte Carlo
        """
        if not self.parameters:
            raise ValueError("Nenhum parâmetro definido")
            
        # Gerar amostras Monte Carlo
        samples = {}
        for name, param in self.parameters.items():
            if param['distribution'] == 'normal':
                samples[name] = norm.rvs(
                    loc=param['params']['mean'],
                    scale=param['params']['std'],
                    size=n_samples
                )
            elif param['distribution'] == 'uniform':
                samples[name] = uniform.rvs(
                    loc=param['params']['min'],
                    scale=param['params']['max'] - param['params']['min'],
                    size=n_samples
                )
            elif param['distribution'] == 'lognormal':
                samples[name] = lognorm.rvs(
                    s=param['params']['std'],
                    scale=np.exp(param['params']['mean']),
                    size=n_samples
                )
                
        # Plotar distribuições
        n_params = len(self.parameters)
        fig, axes = plt.subplots(n_params, 1, figsize=(10, 4*n_params))
        
        for i, (name, values) in enumerate(samples.items()):
            sns.histplot(values, ax=axes[i], kde=True)
            axes[i].set_title(f'Distribuição de {name}')
            
        plt.tight_layout()
        return fig
        
    def calculate_uncertainty_metrics(self, results):
        """
        Calcula métricas de incerteza.
        
        Args:
            results (array): Resultados do modelo
        """
        return {
            'mean': np.mean(results),
            'std': np.std(results),
            'p10': np.percentile(results, 10),
            'p50': np.percentile(results, 50),
            'p90': np.percentile(results, 90),
            'min': np.min(results),
            'max': np.max(results)
        }
        
    def plot_tornado(self, base_case, results):
        """
        Plota gráfico tornado.
        
        Args:
            base_case (float): Caso base
            results (dict): Resultados para cada parâmetro
        """
        # Calcular variações
        variations = []
        for param, value in results.items():
            variations.append({
                'Parameter': param,
                'Variation': abs(value - base_case) / base_case * 100
            })
            
        # Ordenar por variação
        variations = sorted(variations, key=lambda x: x['Variation'], reverse=True)
        
        # Plotar
        plt.figure(figsize=(10, 6))
        sns.barplot(data=pd.DataFrame(variations), x='Variation', y='Parameter')
        plt.title('Análise Tornado')
        plt.xlabel('Variação (%)')
        plt.ylabel('Parâmetro')
        
        return plt.gcf()
        
    def export_results(self, filename):
        """
        Exporta resultados da análise.
        
        Args:
            filename (str): Nome do arquivo
        """
        if self.sensitivity_indices is None:
            raise ValueError("Análise não executada")
            
        # Criar DataFrame com resultados
        results = pd.DataFrame({
            'Parameter': list(self.parameters.keys()),
            'S1': self.sensitivity_indices['S1'],
            'ST': self.sensitivity_indices['ST'],
            'S1_conf': self.sensitivity_indices['S1_conf'],
            'ST_conf': self.sensitivity_indices['ST_conf']
        })
        
        # Salvar arquivo
        results.to_csv(filename, index=False) 