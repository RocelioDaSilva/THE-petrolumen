import jwt # PyJWT for token generation/validation
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import psycopg2 # Assuming user data might be in the same DB
from psycopg2 import sql, extras
from werkzeug.security import generate_password_hash, check_password_hash # For password hashing

# This AuthManager is conceptual and might interact with the DatabaseManager
# or a separate user database. For simplicity, some DB interactions are sketched out here.

class AuthManager:
    def __init__(self, secret_key: str,
                 access_token_expire_minutes: int = 30,
                 db_params: Optional[Dict[str, str]] = None):
        """
        Initializes the AuthManager.
        secret_key: Key for encoding/decoding JWTs. KEEP THIS SECRET.
        access_token_expire_minutes: Lifetime of an access token.
        db_params: Optional dictionary for database connection if users are stored in DB.
                   e.g., {'db_name': 'users_db', 'user': 'admin', ...}
        """
        if not secret_key:
            raise ValueError("SECRET_KEY must be set for AuthManager.")
        self.secret_key = secret_key
        self.algorithm = "HS256"
        self.access_token_expire_minutes = access_token_expire_minutes

        self.db_params = db_params
        self.conn = None
        self.cursor = None
        # If db_params are provided, one might want to establish a connection here
        # or do it on-demand within methods.
        if self.db_params:
            self._connect_db() # Try to connect if params are given

    def _connect_db(self):
        """Connects to the user database if parameters are provided."""
        if not self.db_params:
            # print("No database parameters provided for AuthManager. User operations will be in-memory or disabled.")
            return False # Indicating no DB connection is made/attempted

        try:
            self.conn = psycopg2.connect(
                dbname=self.db_params.get("db_name", "petrolumen_users"), # Default user DB name
                user=self.db_params.get("user"),
                password=self.db_params.get("password"),
                host=self.db_params.get("host", "localhost"),
                port=self.db_params.get("port", "5432")
            )
            self.cursor = self.conn.cursor(cursor_factory=extras.RealDictCursor)
            print("AuthManager successfully connected to user database.")
            self._ensure_user_table_exists()
            return True
        except psycopg2.Error as e:
            print(f"AuthManager error connecting to user database: {e}")
            self.conn = None
            self.cursor = None
            return False

    def _ensure_user_table_exists(self):
        """Creates the users table if it doesn't exist."""
        if not self.conn or not self.cursor:
            # print("No database connection for AuthManager to create user table.")
            return

        user_table_sql = """
        CREATE TABLE IF NOT EXISTS app_users (
            user_id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """
        try:
            self.cursor.execute(user_table_sql)
            self.conn.commit()
            # print("User table 'app_users' ensured to exist.")
        except psycopg2.Error as e:
            print(f"Error creating/checking 'app_users' table: {e}")
            self.conn.rollback()


    def close_db_connection(self):
        """Closes the database connection if open."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        # print("AuthManager database connection closed.")

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Generates a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[dict]:
        """Verifies a JWT token. Returns payload if valid, None otherwise."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            # Could add more checks here, e.g., if user_id from payload is still valid/active in DB
            return payload
        except jwt.ExpiredSignatureError:
            print("Token has expired.")
            return None
        except jwt.InvalidTokenError:
            print("Invalid token.")
            return None
        except Exception as e:
            print(f"Token verification error: {e}")
            return None


    def create_user(self, username: str, email: str, password: str, is_admin: bool = False) -> Optional[dict]:
        """Creates a new user in the database."""
        if not self.conn or self.cursor is None:
            if not self._connect_db(): # Try to connect if not already
                 print("Database not connected. Cannot create user.")
                 return None

        hashed_pw = generate_password_hash(password)
        query = sql.SQL("""
            INSERT INTO app_users (username, email, hashed_password, is_admin)
            VALUES (%s, %s, %s, %s)
            RETURNING user_id, username, email, is_admin, created_at;
        """)
        try:
            self.cursor.execute(query, (username, email, hashed_pw, is_admin))
            new_user = self.cursor.fetchone()
            self.conn.commit()
            print(f"User '{username}' created successfully.")
            return dict(new_user) if new_user else None
        except psycopg2.IntegrityError as e: # Handles unique constraint violations (username/email)
            print(f"Error creating user '{username}': {e}. Username or email might already exist.")
            self.conn.rollback()
            return None
        except psycopg2.Error as e:
            print(f"Database error creating user '{username}': {e}")
            self.conn.rollback()
            return None

    def get_user_by_username(self, username: str) -> Optional[dict]:
        """Retrieves a user by their username from the database."""
        if not self.conn or self.cursor is None:
            if not self._connect_db():
                print("Database not connected. Cannot get user.")
                return None

        query = sql.SQL("SELECT user_id, username, email, hashed_password, is_admin, is_active FROM app_users WHERE username = %s;")
        try:
            self.cursor.execute(query, (username,))
            user_data = self.cursor.fetchone()
            return dict(user_data) if user_data else None
        except psycopg2.Error as e:
            print(f"Database error fetching user '{username}': {e}")
            return None

    def authenticate_user(self, username: str, password_to_check: str) -> Optional[dict]:
        """
        Authenticates a user. Returns user data (excluding password) if successful, None otherwise.
        """
        user_db_data = self.get_user_by_username(username)

        if not user_db_data:
            print(f"Authentication failed: User '{username}' not found.")
            return None

        if not user_db_data.get('is_active', True): # Default to active if not present
            print(f"Authentication failed: User '{username}' is inactive.")
            return None

        hashed_password_from_db = user_db_data.get('hashed_password')
        if not hashed_password_from_db or not check_password_hash(hashed_password_from_db, password_to_check):
            print(f"Authentication failed: Invalid password for user '{username}'.")
            return None

        # Authentication successful
        print(f"User '{username}' authenticated successfully.")
        # Return user data, but remove sensitive info like hashed_password
        user_info_for_token = {
            "user_id": user_db_data["user_id"],
            "username": user_db_data["username"],
            "email": user_db_data.get("email"),
            "is_admin": user_db_data.get("is_admin", False)
        }
        return user_info_for_token


# Example Usage:
if __name__ == '__main__':
    # IMPORTANT: For this example to run, you need PostgreSQL running.
    # The user specified in db_creds needs permission to connect to 'petrolumen_test_auth_db'
    # and create tables. You might need to create the user and grant permissions in PostgreSQL first.
    # E.g., CREATE USER auth_user WITH PASSWORD 'auth_pass';
    #       CREATE DATABASE petrolumen_test_auth_db OWNER auth_user; (or grant create on existing)

    db_credentials = {
        "db_name": "petrolumen_test_auth_db",
        "user": "your_auth_user",      # Replace with your PostgreSQL username for auth DB
        "password": "your_auth_password", # Replace with your PostgreSQL password for auth DB
        "host": "localhost",
        "port": "5432"
    }

    # Use a strong, unique secret key in a real application, ideally from environment variables.
    SECRET_KEY = "my-super-secret-key-for-testing-only"

    auth_manager = AuthManager(secret_key=SECRET_KEY, db_params=db_credentials)

    if not auth_manager.conn: # Check if DB connection was successful
        print("\nFailed to connect to the database for AuthManager. Some operations will not work.")
        print("Please ensure PostgreSQL is running and credentials/permissions are correct.")
    else:
        print("\n--- Testing User Creation ---")
        # Create a new user
        new_user = auth_manager.create_user("testuser", "test@example.com", "StrongP@sswOrd123")
        if new_user:
            print(f"New user created: {new_user['username']}, ID: {new_user['user_id']}")

        # Try creating a duplicate user
        auth_manager.create_user("testuser", "test2@example.com", "anotherpassword") # Should fail or warn

        print("\n--- Testing User Authentication ---")
        # Authenticate the user - correct password
        authenticated_user_info = auth_manager.authenticate_user("testuser", "StrongP@sswOrd123")
        if authenticated_user_info:
            print(f"Authentication successful for: {authenticated_user_info['username']}")

            print("\n--- Testing Token Generation & Verification ---")
            # Create an access token for the authenticated user
            # The 'sub' (subject) claim is often used for the user identifier (username or ID)
            token_data = {"sub": authenticated_user_info['username'], "user_id": authenticated_user_info['user_id'], "roles": ["user"]}
            if authenticated_user_info.get('is_admin'):
                token_data["roles"].append("admin")

            access_token = auth_manager.create_access_token(data=token_data)
            print(f"Generated Access Token: {access_token}")

            # Verify the token
            payload = auth_manager.verify_token(access_token)
            if payload:
                print(f"Token verified. Payload: {payload}")
                print(f"Token subject (username): {payload.get('sub')}")
                print(f"Token issued at: {datetime.fromtimestamp(payload.get('iat'), tz=timezone.utc)}")
                print(f"Token expires at: {datetime.fromtimestamp(payload.get('exp'), tz=timezone.utc)}")
            else:
                print("Token verification failed.")

        else:
            print("Authentication failed for 'testuser' with correct password. Check logic.")

        # Authenticate with wrong password
        print("\n--- Testing Authentication Failure (Wrong Password) ---")
        auth_manager.authenticate_user("testuser", "wrongpassword")

        # Authenticate non-existent user
        print("\n--- Testing Authentication Failure (User Not Found) ---")
        auth_manager.authenticate_user("nonexistentuser", "anypassword")

        # Clean up (optional): Drop the user table or the test database
        # if auth_manager.cursor and auth_manager.conn:
        #     try:
        #         print("\nCleaning up: Dropping app_users table...")
        #         auth_manager.cursor.execute("DROP TABLE IF EXISTS app_users CASCADE;")
        #         auth_manager.conn.commit()
        #         print("app_users table dropped.")
        #     except psycopg2.Error as e:
        #         print(f"Error dropping table: {e}")
        #         auth_manager.conn.rollback()

        # Close DB connection when done with AuthManager instance
        auth_manager.close_db_connection()

    print("\nAuthManager example finished.")

```
