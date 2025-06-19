# fix_database_name.py - Corregir inconsistencias de nombre de BD
import mysql.connector
import os


def fix_database_name():
    """Corregir el nombre de base de datos en todo el proyecto"""
    print("🔧 CORRIGIENDO NOMBRE DE BASE DE DATOS")
    print("=" * 50)

    # 1. Verificar qué bases de datos existen
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='tired2019',
            charset='utf8mb4'
        )

        cursor = connection.cursor()
        cursor.execute("SHOW DATABASES LIKE 'alfaia%'")
        databases = cursor.fetchall()

        print(f"📊 Bases de datos encontradas: {[db[0] for db in databases]}")

        # Determinar cuál usar (preferir alfaia_db)
        if ('alfaia_db',) in databases:
            target_db = 'alfaia_db'
            print(f"✅ Usando base de datos existente: {target_db}")
        elif ('alfaia',) in databases:
            target_db = 'alfaia'
            print(f"✅ Usando base de datos existente: {target_db}")
        else:
            # Crear alfaia_db
            print("📂 Creando alfaia_db...")
            cursor.execute("CREATE DATABASE alfaia_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            target_db = 'alfaia_db'
            print(f"✅ Base de datos creada: {target_db}")

        cursor.close()
        connection.close()

    except Exception as e:
        print(f"❌ Error conectando a MySQL: {e}")
        return False

    # 2. Actualizar archivos de configuración
    print(f"\n🔧 Actualizando configuración para usar: {target_db}")

    # Actualizar modules/config.py
    config_content = f'''# Configuración corregida - Base de datos unificada
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
    pool_name: str = "alfaia_pool"

class TempConfig:
    def __init__(self):
        self.environment = 'development'

    def get(self, key_path: str, default: Any = None) -> Any:
        values = {{
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
            'database.database': '{target_db}',  # ← NOMBRE UNIFICADO
            'database.user': 'root',
            'database.password': os.getenv('DB_PASSWORD', 'tired2019'),
            'database.charset': 'utf8mb4',
            'database.pool_size': 10,
            'logging.level': 'INFO',
            'logging.file': 'logs/alfaia.log',
            'logging.format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        }}
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
            pool_name="alfaia_pool"
        )

    def get_exercise_config(self, exercise_type: str) -> Dict[str, Any]:
        return {{'default_timeout_seconds': 300, 'max_attempts': 3}}

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

    # Escribir configuración actualizada
    with open('modules/config.py', 'w', encoding='utf-8') as f:
        f.write(config_content)
    print("✅ modules/config.py actualizado")

    # 3. Actualizar variables de entorno
    env_content = f'''SECRET_KEY=alfaia_secret_key_2025_super_secure
JWT_SECRET=alfaia_jwt_secret_2025_super_secure
DB_PASSWORD=tired2019
FLASK_ENV=development
DB_HOST=localhost
DB_PORT=3306
DB_NAME={target_db}
DB_USER=root
'''

    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    print("✅ .env actualizado")

    # 4. Verificar que la base de datos tenga tablas
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='tired2019',
            database=target_db,
            charset='utf8mb4'
        )

        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        print(f"\n📋 Tablas en {target_db}: {len(tables)} encontradas")

        if len(tables) == 0:
            print("⚠️ No hay tablas. Necesitas ejecutar:")
            print(f"   mysql -u root -ptired2019 {target_db} < database_structure.sql")
        else:
            print("✅ Base de datos contiene tablas")

            # Verificar usuario demo
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'demo_user'")
            demo_count = cursor.fetchone()[0]

            if demo_count > 0:
                print("✅ Usuario demo_user encontrado")
            else:
                print("⚠️ Usuario demo no encontrado, creando...")
                create_demo_user(cursor, connection)

        cursor.close()
        connection.close()

    except Exception as e:
        print(f"❌ Error verificando tablas: {e}")
        return False

    print(f"\n🎉 ¡CORRECCIÓN COMPLETADA!")
    print(f"✅ Base de datos unificada: {target_db}")
    print(f"✅ Configuración actualizada")
    print(f"✅ Variables de entorno configuradas")
    print(f"\n🚀 Reinicia el servidor: python app.py")

    return True


def create_demo_user(cursor, connection):
    """Crear usuario demo si no existe"""
    try:
        import bcrypt

        # Hash de la contraseña
        password_hash = bcrypt.hashpw('demo123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Insertar usuario
        cursor.execute("""
            INSERT INTO usuarios (username, email, password_hash, nombre, apellido)
            VALUES (%s, %s, %s, %s, %s)
        """, ('demo_user', 'demo@alfaia.com', password_hash, 'Usuario', 'Demo'))

        connection.commit()
        print("✅ Usuario demo creado: demo_user / demo123")

    except Exception as e:
        print(f"❌ Error creando usuario demo: {e}")


if __name__ == "__main__":
    fix_database_name()