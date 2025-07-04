import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import json
from datetime import datetime

class DataUploader:
    """Classe para upload e validação de dados de poços."""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.required_columns = {
            'q_oleo': float,
            'q_gas': float,
            'q_agua': float,
            'pressao': float,
            'data': 'datetime64[ns]'
        }
        self.data_cache = {}
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('DataUploader')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
        
    def validate_csv(self, file_path: str) -> Tuple[bool, List[str]]:
        """
        Valida arquivo CSV.
        
        Args:
            file_path: Caminho do arquivo CSV
            
        Returns:
            Tuple com status de validação e lista de erros
        """
        errors = []
        
        try:
            df = pd.read_csv(file_path)
            
            # Verifica colunas obrigatórias
            missing_columns = set(self.required_columns.keys()) - set(df.columns)
            if missing_columns:
                errors.append(f"Colunas ausentes: {', '.join(missing_columns)}")
                
            # Verifica tipos de dados
            for col, dtype in self.required_columns.items():
                if col in df.columns:
                    try:
                        if dtype == 'datetime64[ns]':
                            pd.to_datetime(df[col])
                        else:
                            df[col].astype(dtype)
                    except:
                        errors.append(f"Tipo de dado inválido para coluna {col}")
                        
            # Verifica valores nulos
            null_columns = df.columns[df.isnull().any()].tolist()
            if null_columns:
                errors.append(f"Colunas com valores nulos: {', '.join(null_columns)}")
                
            # Verifica valores negativos
            numeric_columns = [col for col, dtype in self.required_columns.items() 
                             if dtype in [float, int]]
            negative_columns = [col for col in numeric_columns 
                              if col in df.columns and (df[col] < 0).any()]
            if negative_columns:
                errors.append(f"Colunas com valores negativos: {', '.join(negative_columns)}")
                
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"Erro ao ler arquivo: {str(e)}")
            return False, errors
            
    def load_well_data(self, well_name: str, csv_files: List[str]) -> pd.DataFrame:
        """
        Carrega dados de múltiplos arquivos CSV.
        
        Args:
            well_name: Nome do poço
            csv_files: Lista de arquivos CSV
            
        Returns:
            DataFrame com dados combinados
        """
        dfs = []
        
        for file_path in csv_files:
            is_valid, errors = self.validate_csv(file_path)
            if not is_valid:
                self.logger.error(f"Erros de validação em {file_path}:")
                for error in errors:
                    self.logger.error(f"- {error}")
                continue
                
            df = pd.read_csv(file_path)
            df['well_name'] = well_name
            dfs.append(df)
            
        if not dfs:
            raise ValueError("Nenhum arquivo válido encontrado")
            
        combined_df = pd.concat(dfs, ignore_index=True)
        combined_df = combined_df.sort_values('data')
        
        # Cache dos dados
        self.data_cache[well_name] = combined_df
        
        return combined_df
        
    def get_data_preview(self, well_name: str, n_rows: int = 5) -> pd.DataFrame:
        """
        Retorna preview dos dados.
        
        Args:
            well_name: Nome do poço
            n_rows: Número de linhas
            
        Returns:
            DataFrame com preview
        """
        if well_name not in self.data_cache:
            raise ValueError(f"Dados do poço {well_name} não encontrados")
            
        return self.data_cache[well_name].head(n_rows)
        
    def get_well_statistics(self, well_name: str) -> Dict:
        """
        Retorna estatísticas dos dados.
        
        Args:
            well_name: Nome do poço
            
        Returns:
            Dicionário com estatísticas
        """
        if well_name not in self.data_cache:
            raise ValueError(f"Dados do poço {well_name} não encontrados")
            
        df = self.data_cache[well_name]
        
        stats = {
            'periodo': {
                'inicio': df['data'].min().strftime('%Y-%m-%d'),
                'fim': df['data'].max().strftime('%Y-%m-%d')
            },
            'q_oleo': {
                'media': df['q_oleo'].mean(),
                'max': df['q_oleo'].max(),
                'min': df['q_oleo'].min()
            },
            'q_gas': {
                'media': df['q_gas'].mean(),
                'max': df['q_gas'].max(),
                'min': df['q_gas'].min()
            },
            'q_agua': {
                'media': df['q_agua'].mean(),
                'max': df['q_agua'].max(),
                'min': df['q_agua'].min()
            }
        }
        
        return stats
        
    def export_to_database(self, well_name: str, db_connection):
        """
        Exporta dados para banco de dados.
        
        Args:
            well_name: Nome do poço
            db_connection: Conexão com banco de dados
        """
        if well_name not in self.data_cache:
            raise ValueError(f"Dados do poço {well_name} não encontrados")
            
        df = self.data_cache[well_name]
        
        # Implementar exportação para banco de dados
        pass
        
    def clear_cache(self, well_name: Optional[str] = None):
        """
        Limpa cache de dados.
        
        Args:
            well_name: Nome do poço (opcional)
        """
        if well_name:
            if well_name in self.data_cache:
                del self.data_cache[well_name]
        else:
            self.data_cache.clear() 