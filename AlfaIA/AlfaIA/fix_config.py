# fix_config.py - Solución simple para configuración
import os
import shutil

print("🔧 Solucionando configuración...")

# 1. Configurar variables de entorno
os.environ['SECRET_KEY'] = 'alfaia_secret_key_2025_super_secure'
os.environ['JWT_SECRET'] = 'alfaia_jwt_secret_2025_super_secure'
os.environ['DB_PASSWORD'] = 'tired2019'

# 2. Crear archivo .env
with open('.env', 'w') as f:
    f.write("""SECRET_KEY=alfaia_secret_key_2025_super_secure
JWT_SECRET=alfaia_jwt_secret_2025_super_secure
DB_PASSWORD=tired2019
FLASK_ENV=development
DB_HOST=localhost
DB_PORT=3306
DB_NAME=alfaia_db
DB_USER=root
""")

# 3. Crear configuración temporal
config_temp = '''# Configuración temporal
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
            pool_size=self.get('database.pool_size')
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

# 4. Hacer respaldo y reemplazar
if os.path.exists('modules/config.py'):
    shutil.copy('modules/config.py', 'modules/config_backup.py')

with open('modules/config.py', 'w', encoding='utf-8') as f:
    f.write(config_temp)

# 5. Crear directorios
os.makedirs('logs', exist_ok=True)
os.makedirs('config', exist_ok=True)

print("✅ Configuración arreglada")
print("🚀 Ahora ejecuta: python app.py")
print("🔑 Usuario demo: demo_user / demo123")