import numpy as np
import pandas as pd
from scipy.interpolate import griddata
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns

class PetrophysicalMapping:
    def __init__(self):
        """
        Inicializa o objeto de mapeamento petrofísico.
        """
        self.well_data = {}
        self.property_maps = {}
        self.correlation_matrix = None
        
    def load_well_data(self, well_name, depth, properties):
        """
        Carrega dados de poço para mapeamento.
        
        Args:
            well_name (str): Nome do poço
            depth (array): Profundidade
            properties (dict): Dicionário com propriedades petrofísicas
        """
        self.well_data[well_name] = {
            'depth': depth,
            'properties': properties
        }
        
    def calculate_correlations(self):
        """
        Calcula matriz de correlação entre propriedades.
        """
        all_data = []
        for well in self.well_data.values():
            df = pd.DataFrame(well['properties'])
            all_data.append(df)
        
        if all_data:
            combined_data = pd.concat(all_data, ignore_index=True)
            self.correlation_matrix = combined_data.corr()
            
    def plot_correlation_matrix(self):
        """
        Plota matriz de correlação entre propriedades.
        """
        if self.correlation_matrix is None:
            self.calculate_correlations()
            
        plt.figure(figsize=(10, 8))
        sns.heatmap(self.correlation_matrix, annot=True, cmap='coolwarm', center=0)
        plt.title('Matriz de Correlação entre Propriedades Petrofísicas')
        return plt.gcf()
        
    def create_property_map(self, property_name, method='kriging', resolution=100):
        """
        Cria mapa de propriedade usando diferentes métodos.
        
        Args:
            property_name (str): Nome da propriedade
            method (str): Método de interpolação ('kriging', 'linear', 'cubic', 'nearest')
            resolution (int): Resolução do mapa
        """
        # Coletar dados de todos os poços
        x = []
        y = []
        z = []
        values = []
        
        for well_name, data in self.well_data.items():
            x.extend([data['x']] * len(data['depth']))
            y.extend([data['y']] * len(data['depth']))
            z.extend(data['depth'])
            values.extend(data['properties'][property_name])
            
        x = np.array(x)
        y = np.array(y)
        z = np.array(z)
        values = np.array(values)
        
        # Criar grade
        grid_x = np.linspace(min(x), max(x), resolution)
        grid_y = np.linspace(min(y), max(y), resolution)
        grid_z = np.linspace(min(z), max(z), resolution)
        
        if method == 'kriging':
            # Usar Random Forest para krigagem
            X = np.column_stack((x, y, z))
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X, values)
            
            # Prever valores na grade
            grid_points = np.array(np.meshgrid(grid_x, grid_y, grid_z)).T.reshape(-1, 3)
            predicted = model.predict(grid_points).reshape(resolution, resolution, resolution)
            
        else:
            # Interpolação tradicional
            points = np.column_stack((x, y, z))
            grid_points = np.array(np.meshgrid(grid_x, grid_y, grid_z)).T.reshape(-1, 3)
            predicted = griddata(points, values, grid_points, method=method)
            predicted = predicted.reshape(resolution, resolution, resolution)
            
        self.property_maps[property_name] = {
            'x': grid_x,
            'y': grid_y,
            'z': grid_z,
            'values': predicted
        }
        
    def plot_property_map(self, property_name, depth_index=None):
        """
        Plota mapa de propriedade em uma profundidade específica.
        
        Args:
            property_name (str): Nome da propriedade
            depth_index (int): Índice da profundidade (None para média)
        """
        if property_name not in self.property_maps:
            raise ValueError(f"Mapa de {property_name} não encontrado")
            
        map_data = self.property_maps[property_name]
        
        if depth_index is None:
            # Plotar média em profundidade
            values = np.mean(map_data['values'], axis=2)
        else:
            values = map_data['values'][:, :, depth_index]
            
        plt.figure(figsize=(10, 8))
        plt.imshow(values, extent=[map_data['x'].min(), map_data['x'].max(),
                                 map_data['y'].min(), map_data['y'].max()],
                  origin='lower', cmap='viridis')
        plt.colorbar(label=property_name)
        plt.title(f'Mapa de {property_name}')
        plt.xlabel('X')
        plt.ylabel('Y')
        
        return plt.gcf()
        
    def calculate_statistics(self, property_name):
        """
        Calcula estatísticas para uma propriedade.
        
        Args:
            property_name (str): Nome da propriedade
        """
        if property_name not in self.property_maps:
            raise ValueError(f"Mapa de {property_name} não encontrado")
            
        values = self.property_maps[property_name]['values'].flatten()
        values = values[~np.isnan(values)]
        
        return {
            'mean': np.mean(values),
            'std': np.std(values),
            'min': np.min(values),
            'max': np.max(values),
            'median': np.median(values),
            'p10': np.percentile(values, 10),
            'p90': np.percentile(values, 90)
        }
        
    def export_maps(self, filename_prefix):
        """
        Exporta mapas para arquivos CSV.
        
        Args:
            filename_prefix (str): Prefixo para nomes dos arquivos
        """
        for property_name, map_data in self.property_maps.items():
            filename = f"{filename_prefix}_{property_name}.csv"
            
            # Criar grade de coordenadas
            x, y, z = np.meshgrid(map_data['x'], map_data['y'], map_data['z'])
            
            # Criar DataFrame
            df = pd.DataFrame({
                'X': x.flatten(),
                'Y': y.flatten(),
                'Z': z.flatten(),
                property_name: map_data['values'].flatten()
            })
            
            # Salvar arquivo
            df.to_csv(filename, index=False) 