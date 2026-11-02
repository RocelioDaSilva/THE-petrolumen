import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform, cdist
from scipy.stats import norm
import matplotlib.pyplot as plt
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, Matern, RationalQuadratic
from sklearn.preprocessing import StandardScaler

class Geostatistics:
    """Advanced geostatistical modeling and property upscaling"""
    
    def __init__(self):
        """
        Inicializa o objeto de geoestatística.
        """
        self.variogram_models = {
            "spherical": self._spherical_variogram,
            "exponential": self._exponential_variogram,
            "gaussian": self._gaussian_variogram
        }
        self.data = None
        self.variogram = None
        self.kriging_model = None
        self.grid = None
        
    def load_data(self, data, x_col, y_col, z_col, value_col):
        """
        Carrega dados para análise geoestatística.
        
        Args:
            data (pd.DataFrame): DataFrame com os dados
            x_col (str): Nome da coluna com coordenada X
            y_col (str): Nome da coluna com coordenada Y
            z_col (str): Nome da coluna com coordenada Z
            value_col (str): Nome da coluna com o valor a ser analisado
        """
        self.data = {
            'x': data[x_col].values,
            'y': data[y_col].values,
            'z': data[z_col].values,
            'value': data[value_col].values
        }
        
    def set_data(self, coordinates: np.ndarray, values: np.ndarray):
        """Set sample data points"""
        self.data = {
            "coordinates": coordinates,
            "values": values,
            "n_samples": len(values)
        }
        
    def calculate_variogram(self, n_lags=10, max_lag=None):
        """
        Calcula o variograma experimental.
        
        Args:
            n_lags (int): Número de lags
            max_lag (float): Distância máxima para cálculo do variograma
        """
        if self.data is None:
            raise ValueError("Dados não carregados")
            
        # Calcular matriz de distâncias
        coords = np.column_stack((self.data['x'], self.data['y'], self.data['z']))
        distances = squareform(pdist(coords))
        
        # Calcular diferenças ao quadrado
        values = self.data['value']
        n = len(values)
        diff_sq = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                diff_sq[i,j] = (values[i] - values[j])**2
                
        # Definir lags
        if max_lag is None:
            max_lag = np.max(distances)
        lags = np.linspace(0, max_lag, n_lags+1)
        
        # Calcular variograma
        gamma = []
        for i in range(n_lags):
            lag_min = lags[i]
            lag_max = lags[i+1]
            mask = (distances > lag_min) & (distances <= lag_max)
            if np.any(mask):
                gamma.append(np.mean(diff_sq[mask]) / 2)
            else:
                gamma.append(np.nan)
                
        self.variogram = {
            'lags': lags[:-1],
            'gamma': gamma
        }
        
    def fit_variogram_model(self, model_type='spherical', nugget=0, sill=None, range_param=None):
        """
        Ajusta um modelo teórico ao variograma experimental.
        
        Args:
            model_type (str): Tipo de modelo ('spherical', 'exponential', 'gaussian')
            nugget (float): Efeito pepita
            sill (float): Patamar
            range_param (float): Alcance
        """
        if self.variogram is None:
            raise ValueError("Variograma não calculado")
            
        # Definir modelo teórico
        def spherical(h, c0, c, a):
            if h == 0:
                return 0
            elif h >= a:
                return c0 + c
            else:
                return c0 + c * (1.5 * h/a - 0.5 * (h/a)**3)
                
        def exponential(h, c0, c, a):
            if h == 0:
                return 0
            else:
                return c0 + c * (1 - np.exp(-3 * h/a))
                
        def gaussian(h, c0, c, a):
            if h == 0:
                return 0
            else:
                return c0 + c * (1 - np.exp(-3 * (h/a)**2))
                
        models = {
            'spherical': spherical,
            'exponential': exponential,
            'gaussian': gaussian
        }
        
        if model_type not in models:
            raise ValueError(f"Modelo {model_type} não suportado")
            
        # Ajustar parâmetros
        if sill is None:
            sill = np.nanmax(self.variogram['gamma'])
        if range_param is None:
            range_param = np.nanmax(self.variogram['lags'])
            
        # Calcular modelo
        h = self.variogram['lags']
        gamma_model = models[model_type](h, nugget, sill - nugget, range_param)
        
        self.variogram['model'] = {
            'type': model_type,
            'nugget': nugget,
            'sill': sill,
            'range': range_param,
            'gamma': gamma_model
        }
        
    def plot_variogram(self):
        """
        Plota o variograma experimental e o modelo ajustado.
        """
        if self.variogram is None:
            raise ValueError("Variograma não calculado")
            
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plotar variograma experimental
        ax.scatter(self.variogram['lags'], self.variogram['gamma'],
                  label='Experimental', color='blue')
        
        # Plotar modelo se disponível
        if 'model' in self.variogram:
            ax.plot(self.variogram['lags'], self.variogram['model']['gamma'],
                   label=f"Modelo {self.variogram['model']['type']}",
                   color='red')
            
            # Adicionar parâmetros do modelo
            model = self.variogram['model']
            text = f"Nugget: {model['nugget']:.2f}\n"
            text += f"Sill: {model['sill']:.2f}\n"
            text += f"Range: {model['range']:.2f}"
            ax.text(0.05, 0.95, text, transform=ax.transAxes,
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
        ax.set_xlabel('Distância')
        ax.set_ylabel('Semivariância')
        ax.set_title('Variograma')
        ax.grid(True)
        ax.legend()
        
        return fig
        
    def perform_kriging(self, grid_x, grid_y, grid_z, method='ordinary'):
        """
        Realiza krigagem para estimar valores em uma grade.
        
        Args:
            grid_x, grid_y, grid_z (array): Coordenadas da grade
            method (str): Método de krigagem ('simple' ou 'ordinary')
        """
        if self.variogram is None or 'model' not in self.variogram:
            raise ValueError("Modelo de variograma não ajustado")
            
        # Definir kernel baseado no modelo de variograma
        model = self.variogram['model']
        if model['type'] == 'spherical':
            kernel = RBF(length_scale=model['range'])
        elif model['type'] == 'exponential':
            kernel = Matern(length_scale=model['range'], nu=0.5)
        else:  # gaussian
            kernel = RBF(length_scale=model['range'])
            
        # Preparar dados
        X = np.column_stack((self.data['x'], self.data['y'], self.data['z']))
        y = self.data['value']
        
        # Criar e treinar modelo
        self.kriging_model = GaussianProcessRegressor(
            kernel=kernel,
            normalize_y=True,
            random_state=42
        )
        self.kriging_model.fit(X, y)
        
        # Preparar pontos da grade
        grid_points = np.column_stack((grid_x.flatten(), grid_y.flatten(), grid_z.flatten()))
        
        # Realizar predição
        predicted, std = self.kriging_model.predict(grid_points, return_std=True)
        
        return {
            'predicted': predicted.reshape(grid_x.shape),
            'std': std.reshape(grid_x.shape)
        }
        
    def kriging(self, grid_coords: np.ndarray,
                variogram_params: Dict) -> Tuple[np.ndarray, np.ndarray]:
        """Perform ordinary kriging"""
        n_points = len(grid_coords)
        estimates = np.zeros(n_points)
        variances = np.zeros(n_points)
        
        for i in range(n_points):
            point = grid_coords[i]
            # Get kriging weights
            weights = self._calc_kriging_weights(
                point, variogram_params)
            # Calculate estimate and variance
            estimates[i] = np.sum(weights * self.data["values"])
            variances[i] = self._calc_kriging_variance(
                weights, variogram_params)
            
        return estimates, variances
        
    def calculate_uncertainty(self, n_realizations=100):
        """
        Calcula incerteza usando simulação sequencial gaussiana.
        
        Args:
            n_realizations (int): Número de realizações
        """
        if self.kriging_model is None:
            raise ValueError("Modelo de krigagem não criado")
            
        # Gerar realizações
        realizations = []
        for _ in range(n_realizations):
            # Adicionar ruído gaussiano
            noise = np.random.normal(0, 1, size=self.data['value'].shape)
            realization = self.data['value'] + noise * np.std(self.data['value'])
            realizations.append(realization)
            
        # Calcular estatísticas
        realizations = np.array(realizations)
        mean = np.mean(realizations, axis=0)
        std = np.std(realizations, axis=0)
        p10 = np.percentile(realizations, 10, axis=0)
        p90 = np.percentile(realizations, 90, axis=0)
        
        return {
            'mean': mean,
            'std': std,
            'p10': p10,
            'p90': p90,
            'realizations': realizations
        }
        
    def export_to_sgems(self, filename):
        """
        Exporta dados para formato compatível com S-GeMS.
        
        Args:
            filename (str): Nome do arquivo de saída
        """
        if self.data is None:
            raise ValueError("Dados não carregados")
            
        # Criar arquivo no formato S-GeMS
        with open(filename, 'w') as f:
            # Escrever cabeçalho
            f.write("X Y Z Value\n")
            
            # Escrever dados
            for i in range(len(self.data['x'])):
                f.write(f"{self.data['x'][i]} {self.data['y'][i]} {self.data['z'][i]} {self.data['value'][i]}\n")
                
    def sequential_gaussian_simulation(self, grid_coords: np.ndarray,
                                    variogram_params: Dict,
                                    n_realizations: int = 1) -> np.ndarray:
        """Generate multiple realizations using SGS"""
        realizations = np.zeros((n_realizations, len(grid_coords)))
        
        for i in range(n_realizations):
            # Random path
            path = np.random.permutation(len(grid_coords))
            # Initialize realization
            realization = np.zeros(len(grid_coords))
            
            # Sequential simulation
            for j in path:
                # Kriging at current point
                mean, variance = self.kriging(
                    grid_coords[j].reshape(1,-1),
                    variogram_params
                )
                # Draw random value from distribution
                realization[j] = norm.rvs(
                    loc=mean, scale=np.sqrt(variance))
                
            realizations[i] = realization
            
        return realizations
        
    def upscale_property(self, fine_grid: np.ndarray,
                        coarse_grid: np.ndarray,
                        property_values: np.ndarray,
                        method: str = "arithmetic") -> np.ndarray:
        """Upscale property from fine to coarse grid"""
        if method == "arithmetic":
            return self._arithmetic_average(
                fine_grid, coarse_grid, property_values)
        elif method == "harmonic":
            return self._harmonic_average(
                fine_grid, coarse_grid, property_values)
        elif method == "geometric":
            return self._geometric_average(
                fine_grid, coarse_grid, property_values)
        else:
            raise ValueError(f"Unknown upscaling method: {method}")
            
    def _calc_experimental_variogram(self, lags: np.ndarray) -> Dict:
        """Calculate experimental variogram"""
        # Calculate distances between all pairs
        distances = cdist(self.data["coordinates"], 
                        self.data["coordinates"])
        # Calculate squared differences
        squared_diffs = (self.data["values"][:, None] - 
                        self.data["values"][None, :])**2
                        
        variogram = []
        for lag in lags[:-1]:
            # Find pairs within lag distance
            mask = (distances >= lag) & (distances < lag + lags[1])
            if mask.any():
                variogram.append(np.mean(squared_diffs[mask]) / 2)
            else:
                variogram.append(np.nan)
                
        return {
            "lags": lags[:-1],
            "values": np.array(variogram)
        }
        
    def _fit_variogram_model(self, exp_variogram: Dict,
                            model: str) -> Tuple[float, float, float]:
        """Fit theoretical variogram model"""
        from scipy.optimize import minimize
        
        def objective(params):
            sill, range_param, nugget = params
            theoretical = self.variogram_models[model](
                exp_variogram["lags"], sill, range_param, nugget)
            return np.sum((theoretical - exp_variogram["values"])**2)
            
        # Initial guess
        x0 = [np.nanmax(exp_variogram["values"]),  # sill
              np.mean(exp_variogram["lags"]),      # range
              0.0]                                 # nugget
              
        result = minimize(objective, x0, 
                         bounds=[(0,None), (0,None), (0,None)])
                         
        return result.x
        
    def _spherical_variogram(self, h: np.ndarray,
                            sill: float, range_param: float,
                            nugget: float) -> np.ndarray:
        """Spherical variogram model"""
        gamma = np.zeros_like(h)
        mask = h <= range_param
        
        gamma[mask] = nugget + sill * (
            1.5 * h[mask]/range_param - 
            0.5 * (h[mask]/range_param)**3
        )
        gamma[~mask] = nugget + sill
        return gamma
        
    def _exponential_variogram(self, h: np.ndarray,
                              sill: float, range_param: float,
                              nugget: float) -> np.ndarray:
        """Exponential variogram model"""
        return nugget + sill * (1 - np.exp(-3 * h/range_param))
        
    def _gaussian_variogram(self, h: np.ndarray,
                           sill: float, range_param: float,
                           nugget: float) -> np.ndarray:
        """Gaussian variogram model"""
        return nugget + sill * (1 - np.exp(-3 * h**2/range_param**2))
        
    def _calc_kriging_weights(self, point: np.ndarray,
                             variogram_params: Dict) -> np.ndarray:
        """Calculate kriging weights"""
        n = self.data["n_samples"]
        
        # Build kriging matrix
        K = np.zeros((n+1, n+1))
        k = np.zeros(n+1)
        
        # Fill covariance matrix
        for i in range(n):
            for j in range(n):
                d = np.linalg.norm(
                    self.data["coordinates"][i] - 
                    self.data["coordinates"][j]
                )
                K[i,j] = self.variogram_models[variogram_params["model"]](
                    np.array([d]),
                    variogram_params["sill"],
                    variogram_params["range"],
                    variogram_params["nugget"]
                )[0]
                
        # Add constraint row/column
        K[:-1,-1] = 1
        K[-1,:-1] = 1
        K[-1,-1] = 0
        
        # Fill right hand side
        for i in range(n):
            d = np.linalg.norm(
                self.data["coordinates"][i] - point
            )
            k[i] = self.variogram_models[variogram_params["model"]](
                np.array([d]),
                variogram_params["sill"],
                variogram_params["range"],
                variogram_params["nugget"]
            )[0]
        k[-1] = 1
        
        # Solve system
        weights = np.linalg.solve(K, k)[:-1]
        return weights
        
    def _calc_kriging_variance(self, weights: np.ndarray,
                              variogram_params: Dict) -> float:
        """Calculate kriging variance"""
        # Implementation depends on variogram model
        return variogram_params["sill"] - np.sum(weights)
        
    def _arithmetic_average(self, fine_grid: np.ndarray,
                          coarse_grid: np.ndarray,
                          values: np.ndarray) -> np.ndarray:
        """Arithmetic averaging for upscaling"""
        # Implement arithmetic averaging
        return np.mean(values)
        
    def _harmonic_average(self, fine_grid: np.ndarray,
                         coarse_grid: np.ndarray,
                         values: np.ndarray) -> np.ndarray:
        """Harmonic averaging for upscaling"""
        # Implement harmonic averaging
        return 1 / np.mean(1/values)
        
    def _geometric_average(self, fine_grid: np.ndarray,
                         coarse_grid: np.ndarray,
                         values: np.ndarray) -> np.ndarray:
        """Geometric averaging for upscaling"""
        # Implement geometric averaging
        return np.exp(np.mean(np.log(values)))
        
    def _get_max_dist(self) -> float:
        """Get maximum distance in dataset"""
        return np.max(cdist(self.data["coordinates"],
                          self.data["coordinates"]))