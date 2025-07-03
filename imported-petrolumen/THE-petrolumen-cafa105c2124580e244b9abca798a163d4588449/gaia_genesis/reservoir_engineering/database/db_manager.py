import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime
import json
from pathlib import Path

class DatabaseManager:
    """Classe para gerenciamento de banco de dados."""
    
    def __init__(self,
                 host: str,
                 port: int,
                 database: str,
                 user: str,
                 password: str):
        """
        Inicializa conexão com banco de dados.
        
        Args:
            host: Host do banco
            port: Porta
            database: Nome do banco
            user: Usuário
            password: Senha
        """
        self.logger = self._setup_logger()
        self.connection_params = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }
        self.conn = None
        self.cache = {}
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('DatabaseManager')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
        
    def connect(self):
        """Estabelece conexão com banco de dados."""
        try:
            self.conn = psycopg2.connect(**self.connection_params)
            self.logger.info("Conexão estabelecida com sucesso")
        except Exception as e:
            self.logger.error(f"Erro ao conectar: {str(e)}")
            raise
            
    def disconnect(self):
        """Fecha conexão com banco de dados."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.logger.info("Conexão fechada")
            
    def create_tables(self):
        """Cria tabelas necessárias."""
        if not self.conn:
            raise ValueError("Conexão não estabelecida")
            
        with self.conn.cursor() as cur:
            # Tabela de poços
            cur.execute("""
                CREATE TABLE IF NOT EXISTS wells (
                    well_id SERIAL PRIMARY KEY,
                    well_name VARCHAR(100) UNIQUE NOT NULL,
                    field_name VARCHAR(100),
                    latitude FLOAT,
                    longitude FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de dados de produção
            cur.execute("""
                CREATE TABLE IF NOT EXISTS production_data (
                    data_id SERIAL PRIMARY KEY,
                    well_id INTEGER REFERENCES wells(well_id),
                    date TIMESTAMP NOT NULL,
                    oil_rate FLOAT,
                    gas_rate FLOAT,
                    water_rate FLOAT,
                    pressure FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Índices
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_production_well_date 
                ON production_data(well_id, date)
            """)
            
            self.conn.commit()
            self.logger.info("Tabelas criadas com sucesso")
            
    def insert_well(self,
                   well_name: str,
                   field_name: Optional[str] = None,
                   latitude: Optional[float] = None,
                   longitude: Optional[float] = None) -> int:
        """
        Insere novo poço.
        
        Args:
            well_name: Nome do poço
            field_name: Nome do campo
            latitude: Latitude
            longitude: Longitude
            
        Returns:
            ID do poço inserido
        """
        if not self.conn:
            raise ValueError("Conexão não estabelecida")
            
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO wells (well_name, field_name, latitude, longitude)
                VALUES (%s, %s, %s, %s)
                RETURNING well_id
            """, (well_name, field_name, latitude, longitude))
            
            well_id = cur.fetchone()[0]
            self.conn.commit()
            
            self.logger.info(f"Poço {well_name} inserido com ID {well_id}")
            return well_id
            
    def insert_production_data(self,
                             well_id: int,
                             data: pd.DataFrame):
        """
        Insere dados de produção.
        
        Args:
            well_id: ID do poço
            data: DataFrame com dados
        """
        if not self.conn:
            raise ValueError("Conexão não estabelecida")
            
        with self.conn.cursor() as cur:
            for _, row in data.iterrows():
                cur.execute("""
                    INSERT INTO production_data 
                    (well_id, date, oil_rate, gas_rate, water_rate, pressure)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    well_id,
                    row['data'],
                    row.get('q_oleo'),
                    row.get('q_gas'),
                    row.get('q_agua'),
                    row.get('pressao')
                ))
                
            self.conn.commit()
            self.logger.info(f"Dados de produção inseridos para poço {well_id}")
            
    def get_well_data(self,
                     well_name: str,
                     start_date: Optional[datetime] = None,
                     end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Obtém dados de um poço.
        
        Args:
            well_name: Nome do poço
            start_date: Data inicial
            end_date: Data final
            
        Returns:
            DataFrame com dados
        """
        if not self.conn:
            raise ValueError("Conexão não estabelecida")
            
        # Verifica cache
        cache_key = f"{well_name}_{start_date}_{end_date}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT p.*, w.well_name, w.field_name
                FROM production_data p
                JOIN wells w ON p.well_id = w.well_id
                WHERE w.well_name = %s
            """
            params = [well_name]
            
            if start_date:
                query += " AND p.date >= %s"
                params.append(start_date)
            if end_date:
                query += " AND p.date <= %s"
                params.append(end_date)
                
            query += " ORDER BY p.date"
            
            cur.execute(query, params)
            data = pd.DataFrame(cur.fetchall())
            
            # Atualiza cache
            self.cache[cache_key] = data
            
            return data
            
    def get_field_data(self,
                      field_name: str,
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Obtém dados de um campo.
        
        Args:
            field_name: Nome do campo
            start_date: Data inicial
            end_date: Data final
            
        Returns:
            DataFrame com dados
        """
        if not self.conn:
            raise ValueError("Conexão não estabelecida")
            
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT p.*, w.well_name, w.field_name
                FROM production_data p
                JOIN wells w ON p.well_id = w.well_id
                WHERE w.field_name = %s
            """
            params = [field_name]
            
            if start_date:
                query += " AND p.date >= %s"
                params.append(start_date)
            if end_date:
                query += " AND p.date <= %s"
                params.append(end_date)
                
            query += " ORDER BY w.well_name, p.date"
            
            cur.execute(query, params)
            return pd.DataFrame(cur.fetchall())
            
    def update_well(self,
                   well_id: int,
                   field_name: Optional[str] = None,
                   latitude: Optional[float] = None,
                   longitude: Optional[float] = None):
        """
        Atualiza dados de um poço.
        
        Args:
            well_id: ID do poço
            field_name: Nome do campo
            latitude: Latitude
            longitude: Longitude
        """
        if not self.conn:
            raise ValueError("Conexão não estabelecida")
            
        updates = []
        params = []
        
        if field_name is not None:
            updates.append("field_name = %s")
            params.append(field_name)
        if latitude is not None:
            updates.append("latitude = %s")
            params.append(latitude)
        if longitude is not None:
            updates.append("longitude = %s")
            params.append(longitude)
            
        if updates:
            with self.conn.cursor() as cur:
                query = f"""
                    UPDATE wells
                    SET {', '.join(updates)}
                    WHERE well_id = %s
                """
                params.append(well_id)
                
                cur.execute(query, params)
                self.conn.commit()
                
                self.logger.info(f"Poço {well_id} atualizado")
                
    def delete_well(self, well_id: int):
        """
        Remove um poço.
        
        Args:
            well_id: ID do poço
        """
        if not self.conn:
            raise ValueError("Conexão não estabelecida")
            
        with self.conn.cursor() as cur:
            # Remove dados de produção
            cur.execute("""
                DELETE FROM production_data
                WHERE well_id = %s
            """, (well_id,))
            
            # Remove poço
            cur.execute("""
                DELETE FROM wells
                WHERE well_id = %s
            """, (well_id,))
            
            self.conn.commit()
            self.logger.info(f"Poço {well_id} removido")
            
    def clear_cache(self):
        """Limpa cache de dados."""
        self.cache.clear()
        self.logger.info("Cache limpo") 