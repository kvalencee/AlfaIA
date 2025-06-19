# fix_database.py - Arreglar DatabaseConfig
import shutil

# Configuración corregida
config_fixed = '''# Configuración corregida
import os
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    host: str
    port: int
    database: str
    user: str
    password: str
    charset: str = 'utf8mb4'
    pool_size: int = 10
    pool_name: str = "alfaia_pool"  # <- ESTO FALTABA

class TempConfig:
    def __init__(self):
        self.environment = 'development'

    def get(self, key_path: str, default: Any = None) -> Any:
        values = {
            'security.secret_key': os.getenv('SECRET_KEY', 'alfaia_secret_key_2025'),
            'security.jwt_secret': os.getenv('JWT_SECRET', 'alfaia_jwt_secret_2025'),
            'security.session_timeout_hours': 24,
            'security.session_cookie_secure': False,
            'security.session_cookie_httponly': True,
            'security.session_cookie_samesite': 'Lax',
            'app.debug': True,
            'app.host': '0.0.0.0',
            'app.port': 5000,
            'database.host': 'localhost',
            'database.port': 3306,
            'database.database': 'alfaia_db',
            'database.user': 'root',
            'database.password': os.getenv('DB_PASSWORD', 'tired2019'),
            'database.charset': 'utf8mb4',
            'database.pool_size': 10,
            'logging.level': 'INFO',
            'logging.file': 'logs/alfaia.log',
            'logging.format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        }
        return values.get(key_path, default)

    def get_database_config(self) -> DatabaseConfig:
        return DatabaseConfig(
            host=self.get('database.host'),
            port=self.get('database.port'),
            database=self.get('database.database'),
            user=self.get('database.user'),
            password=self.get('database.password'),
            charset=self.get('database.charset'),
            pool_size=self.get('database.pool_size'),
            pool_name="alfaia_pool"  # <- Y ESTO TAMBIÉN
        )

    def get_exercise_config(self, exercise_type: str) -> Dict[str, Any]:
        return {'default_timeout_seconds': 300, 'max_attempts': 3}

    def is_feature_enabled(self, feature_name: str) -> bool:
        return False

config = TempConfig()

def get_config(key_path: str, default: Any = None):
    return config.get(key_path, default)

def get_database_config():
    return config.get_database_config()

def get_exercise_config(exercise_type: str):
    return config.get_exercise_config(exercise_type)

def is_feature_enabled(feature_name: str):
    return config.is_feature_enabled(feature_name)

def initialize_config():
    return True
'''

# Reemplazar config
with open('modules/config.py', 'w', encoding='utf-8') as f:
    f.write(config_fixed)

print("✅ DatabaseConfig arreglado")
print("🔄 Reinicia el servidor: python app.py")