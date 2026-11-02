import numpy as np
import pandas as pd
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter
import segyio
import lasio
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

class ReservoirCharacterization:
    def __init__(self):
        """
        Inicializa o objeto de caracterização de reservatório.
        """
        self.well_data = {}
        self.seismic_data = None
        self.facies_data = None
        self.property_maps = {}
        self.grid = None
        
    def load_seismic_data(self, segy_file):
        """
        Carrega dados sísmicos de um arquivo SEG-Y.
        
        Args:
            segy_file (str): Caminho do arquivo SEG-Y
        """
        with segyio.open(segy_file, 'r') as f:
            # Carregar dados sísmicos
            self.seismic_data = {
                'data': f.trace.raw[:],
                'header': f.header,
                'bin_headers': f.bin,
                'trace_headers': f.trace.header
            }
            
    def load_well_data(self, well_name, las_file, tops_file=None):
        """
        Carrega dados de poço e topos de formação.
        
        Args:
            well_name (str): Nome do poço
            las_file (str): Caminho do arquivo LAS
            tops_file (str, optional): Caminho do arquivo com topos de formação
        """
        # Carregar dados de log
        las = lasio.read(las_file)
        df = las.df()
        
        # Carregar topos se disponível
        tops = None
        if tops_file:
            tops = pd.read_csv(tops_file)
            
        self.well_data[well_name] = {
            'logs': df,
            'tops': tops
        }
        
    def create_property_map(self, property_name, method='kriging', resolution=100):
        """
        Cria mapa de propriedade a partir de dados de poço.
        
        Args:
            property_name (str): Nome da propriedade
            method (str): Método de interpolação
            resolution (int): Resolução do mapa
        """
        # Coletar dados dos poços
        points = []
        values = []
        
        for well_name, data in self.well_data.items():
            if property_name in data['logs'].columns:
                # Usar média da propriedade para cada poço
                value = data['logs'][property_name].mean()
                # Obter coordenadas do poço (assumindo que estão nos headers)
                x = data['logs'].iloc[0]['X']
                y = data['logs'].iloc[0]['Y']
                points.append([x, y])
                values.append(value)
                
        if not points:
            raise ValueError(f"Propriedade {property_name} não encontrada em nenhum poço")
            
        # Criar grade regular
        x_min, x_max = min(p[0] for p in points), max(p[0] for p in points)
        y_min, y_max = min(p[1] for p in points), max(p[1] for p in points)
        
        xi = np.linspace(x_min, x_max, resolution)
        yi = np.linspace(y_min, y_max, resolution)
        xi, yi = np.meshgrid(xi, yi)
        
        # Interpolar
        zi = griddata(points, values, (xi, yi), method=method)
        
        # Suavizar se necessário
        if method == 'kriging':
            zi = gaussian_filter(zi, sigma=1)
            
        self.property_maps[property_name] = {
            'x': xi,
            'y': yi,
            'z': zi
        }
        
    def perform_facies_classification(self, properties, n_facies=3):
        """
        Realiza classificação de fácies usando dados de poço.
        
        Args:
            properties (list): Lista de propriedades para usar na classificação
            n_facies (int): Número de fácies
        """
        # Coletar dados para classificação
        X = []
        well_names = []
        
        for well_name, data in self.well_data.items():
            if all(prop in data['logs'].columns for prop in properties):
                # Usar média das propriedades para cada poço
                values = [data['logs'][prop].mean() for prop in properties]
                X.append(values)
                well_names.append(well_name)
                
        if not X:
            raise ValueError("Dados insuficientes para classificação de fácies")
            
        # Normalizar dados
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Realizar classificação
        kmeans = KMeans(n_clusters=n_facies, random_state=42)
        facies = kmeans.fit_predict(X_scaled)
        
        # Atribuir fácies aos poços
        for i, well_name in enumerate(well_names):
            self.well_data[well_name]['facies'] = facies[i]
            
    def integrate_seismic_well_data(self, property_name, seismic_attribute):
        """
        Integra dados sísmicos com dados de poço.
        
        Args:
            property_name (str): Propriedade do poço para integrar
            seismic_attribute (str): Atributo sísmico para usar
        """
        if not self.seismic_data:
            raise ValueError("Dados sísmicos não carregados")
            
        # Coletar dados de poço
        well_points = []
        well_values = []
        
        for well_name, data in self.well_data.items():
            if property_name in data['logs'].columns:
                value = data['logs'][property_name].mean()
                x = data['logs'].iloc[0]['X']
                y = data['logs'].iloc[0]['Y']
                well_points.append([x, y])
                well_values.append(value)
                
        if not well_points:
            raise ValueError(f"Propriedade {property_name} não encontrada em nenhum poço")
            
        # Obter dados sísmicos nos pontos dos poços
        seismic_values = []
        for x, y in well_points:
            # Converter coordenadas para índices sísmicos
            ix = int((x - self.seismic_data['header']['SourceX']) / 
                    self.seismic_data['bin_headers']['SourceXInterval'])
            iy = int((y - self.seismic_data['header']['SourceY']) / 
                    self.seismic_data['bin_headers']['SourceYInterval'])
            
            if 0 <= ix < self.seismic_data['data'].shape[0] and \
               0 <= iy < self.seismic_data['data'].shape[1]:
                seismic_values.append(self.seismic_data['data'][ix, iy])
            else:
                seismic_values.append(np.nan)
                
        # Remover pontos com dados faltantes
        valid_idx = ~np.isnan(seismic_values)
        well_points = np.array(well_points)[valid_idx]
        well_values = np.array(well_values)[valid_idx]
        seismic_values = np.array(seismic_values)[valid_idx]
        
        # Calcular correlação
        correlation = np.corrcoef(well_values, seismic_values)[0, 1]
        
        return {
            'correlation': correlation,
            'well_points': well_points,
            'well_values': well_values,
            'seismic_values': seismic_values
        }
        
    def calculate_reservoir_parameters(self):
        """
        Calcula parâmetros do reservatório a partir dos dados disponíveis.
        """
        results = {}
        
        # Calcular parâmetros por poço
        for well_name, data in self.well_data.items():
            well_results = {}
            
            # Porosidade média
            if 'PHIT' in data['logs'].columns:
                well_results['porosity'] = data['logs']['PHIT'].mean()
                
            # Permeabilidade média
            if 'PERM' in data['logs'].columns:
                well_results['permeability'] = data['logs']['PERM'].mean()
                
            # Saturação de água média
            if 'SW' in data['logs'].columns:
                well_results['water_saturation'] = data['logs']['SW'].mean()
                
            # Espessura líquida
            if 'GR' in data['logs'].columns:
                # Assumir que GR > 100 é shale
                net_thickness = data['logs'][data['logs']['GR'] <= 100].shape[0]
                well_results['net_thickness'] = net_thickness
                
            results[well_name] = well_results
            
        return results
        
    def export_results(self, filename):
        """
        Exporta resultados para arquivo CSV.
        
        Args:
            filename (str): Nome do arquivo de saída
        """
        # Preparar dados para exportação
        data = []
        
        for well_name, results in self.calculate_reservoir_parameters().items():
            row = {'well_name': well_name}
            row.update(results)
            data.append(row)
            
        # Criar DataFrame e exportar
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False) 