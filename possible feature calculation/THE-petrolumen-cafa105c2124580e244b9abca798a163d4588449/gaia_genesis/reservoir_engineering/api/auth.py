from typing import Dict, Optional
import jwt
from datetime import datetime, timedelta
import logging
from passlib.context import CryptContext
import psycopg2
from psycopg2.extras import RealDictCursor

class AuthManager:
    """Classe para gerenciamento de autenticação."""
    
    def __init__(self,
                 secret_key: str,
                 algorithm: str = "HS256",
                 access_token_expire_minutes: int = 30):
        """
        Inicializa gerenciador de autenticação.
        
        Args:
            secret_key: Chave secreta para JWT
            algorithm: Algoritmo de criptografia
            access_token_expire_minutes: Tempo de expiração do token
        """
        self.logger = self._setup_logger()
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.conn = None
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('AuthManager')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
        
    def connect_db(self,
                  host: str,
                  port: int,
                  database: str,
                  user: str,
                  password: str):
        """
        Conecta ao banco de dados.
        
        Args:
            host: Host do banco
            port: Porta
            database: Nome do banco
            user: Usuário
            password: Senha
        """
        try:
            self.conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password
            )
            self.logger.info("Conexão com banco de dados estabelecida")
        except Exception as e:
            self.logger.error(f"Erro ao conectar ao banco: {str(e)}")
            raise
            
    def create_tables(self):
        """Cria tabelas de usuários."""
        if not self.conn:
            raise ValueError("Conexão não estabelecida")
            
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    hashed_password VARCHAR(100) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    is_admin BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.conn.commit()
            self.logger.info("Tabela de usuários criada")
            
    def create_user(self,
                   username: str,
                   email: str,
                   password: str,
                   is_admin: bool = False) -> int:
        """
        Cria novo usuário.
        
        Args:
            username: Nome de usuário
            email: Email
            password: Senha
            is_admin: Se é administrador
            
        Returns:
            ID do usuário criado
        """
        if not self.conn:
            raise ValueError("Conexão não estabelecida")
            
        hashed_password = self.pwd_context.hash(password)
        
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (username, email, hashed_password, is_admin)
                VALUES (%s, %s, %s, %s)
                RETURNING user_id
            """, (username, email, hashed_password, is_admin))
            
            user_id = cur.fetchone()[0]
            self.conn.commit()
            
            self.logger.info(f"Usuário {username} criado com ID {user_id}")
            return user_id
            
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verifica senha.
        
        Args:
            plain_password: Senha em texto
            hashed_password: Senha criptografada
            
        Returns:
            True se senha correta
        """
        return self.pwd_context.verify(plain_password, hashed_password)
        
    def authenticate_user(self,
                         username: str,
                         password: str) -> Optional[Dict]:
        """
        Autentica usuário.
        
        Args:
            username: Nome de usuário
            password: Senha
            
        Returns:
            Dicionário com dados do usuário ou None
        """
        if not self.conn:
            raise ValueError("Conexão não estabelecida")
            
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT *
                FROM users
                WHERE username = %s
            """, (username,))
            
            user = cur.fetchone()
            
            if not user:
                return None
                
            if not self.verify_password(password, user['hashed_password']):
                return None
                
            return dict(user)
            
    def create_access_token(self,
                          data: Dict,
                          expires_delta: Optional[timedelta] = None) -> str:
        """
        Cria token de acesso.
        
        Args:
            data: Dados para token
            expires_delta: Tempo de expiração
            
        Returns:
            Token JWT
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
            
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        return encoded_jwt
        
    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verifica token.
        
        Args:
            token: Token JWT
            
        Returns:
            Dados do token ou None
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.PyJWTError:
            return None
            
    def get_user(self, user_id: int) -> Optional[Dict]:
        """
        Obtém dados de usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Dicionário com dados do usuário ou None
        """
        if not self.conn:
            raise ValueError("Conexão não estabelecida")
            
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT *
                FROM users
                WHERE user_id = %s
            """, (user_id,))
            
            user = cur.fetchone()
            return dict(user) if user else None
            
    def update_user(self,
                   user_id: int,
                   email: Optional[str] = None,
                   password: Optional[str] = None,
                   is_active: Optional[bool] = None,
                   is_admin: Optional[bool] = None):
        """
        Atualiza dados de usuário.
        
        Args:
            user_id: ID do usuário
            email: Novo email
            password: Nova senha
            is_active: Status ativo
            is_admin: Status admin
        """
        if not self.conn:
            raise ValueError("Conexão não estabelecida")
            
        updates = []
        params = []
        
        if email is not None:
            updates.append("email = %s")
            params.append(email)
        if password is not None:
            updates.append("hashed_password = %s")
            params.append(self.pwd_context.hash(password))
        if is_active is not None:
            updates.append("is_active = %s")
            params.append(is_active)
        if is_admin is not None:
            updates.append("is_admin = %s")
            params.append(is_admin)
            
        if updates:
            with self.conn.cursor() as cur:
                query = f"""
                    UPDATE users
                    SET {', '.join(updates)}
                    WHERE user_id = %s
                """
                params.append(user_id)
                
                cur.execute(query, params)
                self.conn.commit()
                
                self.logger.info(f"Usuário {user_id} atualizado")
                
    def delete_user(self, user_id: int):
        """
        Remove usuário.
        
        Args:
            user_id: ID do usuário
        """
        if not self.conn:
            raise ValueError("Conexão não estabelecida")
            
        with self.conn.cursor() as cur:
            cur.execute("""
                DELETE FROM users
                WHERE user_id = %s
            """, (user_id,))
            
            self.conn.commit()
            self.logger.info(f"Usuário {user_id} removido") 