# fix_autocommit_error.py - Solución completa al error de DatabaseConfig
import re


def fix_database_manager():
    """Arreglar el Database Manager para que funcione con cualquier versión de DatabaseConfig"""
    print("🔧 ARREGLANDO ERROR DE AUTOCOMMIT EN DATABASE MANAGER")
    print("=" * 60)

    try:
        # Leer el database_manager.py actual
        with open('modules/database_manager.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # Buscar la inicialización del pool de conexiones
        pattern = r'pool_config = \{(.*?)\}'

        # Nueva configuración del pool sin usar autocommit directamente
        new_pool_config = """pool_config = {
                'pool_name': self.config.pool_name,
                'pool_size': self.config.pool_size,
                'pool_reset_session': True,
                'host': self.config.host,
                'port': self.config.port,
                'database': self.config.database,
                'user': self.config.user,
                'password': self.config.password,
                'charset': self.config.charset,
                'time_zone': '+00:00',
                'sql_mode': 'TRADITIONAL',
                'use_unicode': True,
                'collation': 'utf8mb4_unicode_ci'
            }

            # Agregar autocommit solo si está disponible en la config
            if hasattr(self.config, 'autocommit'):
                pool_config['autocommit'] = self.config.autocommit"""

        # Reemplazar la configuración del pool
        if 'pool_config = {' in content:
            content = re.sub(pattern, new_pool_config, content, flags=re.DOTALL)
            print("✅ Configuración del pool actualizada")
        else:
            print("⚠️ No se encontró la configuración del pool")

        # Guardar el archivo corregido
        with open('modules/database_manager.py', 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ database_manager.py corregido")

    except Exception as e:
        print(f"❌ Error arreglando database_manager.py: {e}")


def fix_config_module():
    """Asegurar que el módulo config tenga DatabaseConfig correcto"""
    print("\n🔧 ARREGLANDO MÓDULO CONFIG")
    print("=" * 40)

    config_content = '''# modules/config.py - Configuración completa corregida
import os
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Configuración completa de la base de datos"""
    host: str
    port: int
    database: str
    user: str
    password: str
    charset: str = 'utf8mb4'
    autocommit: bool = False
    pool_size: int = 10
    pool_name: str = "alfaia_pool"


class ModernConfig:
    """Configuración moderna y robusta para AlfaIA"""

    def __init__(self):
        self.environment = os.getenv('FLASK_ENV', 'development')
        self._config_data = self._load_default_config()

    def _load_default_config(self) -> Dict[str, Any]:
        """Cargar configuración por defecto"""
        return {
            # Seguridad
            'security.secret_key': os.getenv('SECRET_KEY', 'alfaia_secret_key_2025_super_secure'),
            'security.jwt_secret': os.getenv('JWT_SECRET', 'alfaia_jwt_secret_2025'),
            'security.session_timeout_hours': 24,
            'security.session_cookie_secure': False,
            'security.session_cookie_httponly': True,
            'security.session_cookie_samesite': 'Lax',

            # Aplicación
            'app.debug': self.environment == 'development',
            'app.host': '0.0.0.0',
            'app.port': 5000,
            'app.max_content_length': 16 * 1024 * 1024,  # 16MB

            # Base de datos - Múltiples configuraciones para probar
            'database.host': os.getenv('DB_HOST', 'localhost'),
            'database.port': int(os.getenv('DB_PORT', '3306')),
            'database.database': os.getenv('DB_NAME', 'alfaia_db'),
            'database.user': os.getenv('DB_USER', 'root'),
            'database.password': os.getenv('DB_PASSWORD', 'tired2019'),
            'database.charset': 'utf8mb4',
            'database.autocommit': False,
            'database.pool_size': 10,

            # Logging
            'logging.level': 'INFO',
            'logging.file': 'logs/alfaia.log',
            'logging.format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',

            # Ejercicios
            'exercises.default_timeout': 300,
            'exercises.max_attempts': 3,
            'exercises.save_interval': 30,
        }

    def get(self, key_path: str, default: Any = None) -> Any:
        """Obtener valor de configuración usando notación de punto"""
        return self._config_data.get(key_path, default)

    def get_database_config(self) -> DatabaseConfig:
        """Obtener configuración de base de datos como objeto DatabaseConfig"""
        return DatabaseConfig(
            host=self.get('database.host'),
            port=self.get('database.port'),
            database=self.get('database.database'),
            user=self.get('database.user'),
            password=self.get('database.password'),
            charset=self.get('database.charset'),
            autocommit=self.get('database.autocommit'),
            pool_size=self.get('database.pool_size'),
            pool_name="alfaia_pool"
        )

    def get_exercise_config(self, exercise_type: str) -> Dict[str, Any]:
        """Obtener configuración específica de ejercicios"""
        return {
            'default_timeout_seconds': self.get('exercises.default_timeout'),
            'max_attempts': self.get('exercises.max_attempts'),
            'save_interval_seconds': self.get('exercises.save_interval'),
            'exercise_type': exercise_type
        }

    def is_feature_enabled(self, feature_name: str) -> bool:
        """Verificar si una característica está habilitada"""
        feature_flags = {
            'advanced_analytics': True,
            'social_features': False,
            'ai_suggestions': True,
            'voice_exercises': True,
            'multiplayer_mode': False
        }
        return feature_flags.get(feature_name, False)


# =====================================================
# INSTANCIA GLOBAL DE CONFIGURACIÓN
# =====================================================

config = ModernConfig()


# =====================================================
# FUNCIONES DE CONVENIENCIA
# =====================================================

def get_config(key_path: str, default: Any = None):
    """Función de conveniencia para obtener configuración"""
    return config.get(key_path, default)


def get_database_config():
    """Función de conveniencia para obtener configuración de BD"""
    return config.get_database_config()


def get_exercise_config(exercise_type: str):
    """Función de conveniencia para configuración de ejercicios"""
    return config.get_exercise_config(exercise_type)


def is_feature_enabled(feature_name: str):
    """Función de conveniencia para verificar características"""
    return config.is_feature_enabled(feature_name)


def initialize_config():
    """Inicializar configuración - para compatibilidad"""
    return True


# =====================================================
# CONFIGURACIÓN DE LOGGING
# =====================================================

import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': config.get('logging.format')
        },
    },
    'handlers': {
        'default': {
            'level': config.get('logging.level'),
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': config.get('logging.level'),
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            'filename': config.get('logging.file'),
            'mode': 'a',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'file'],
            'level': config.get('logging.level'),
            'propagate': False
        }
    }
}

# Aplicar configuración de logging
logging.config.dictConfig(LOGGING_CONFIG)
'''

    try:
        # Crear directorio modules si no existe
        os.makedirs('modules', exist_ok=True)

        # Escribir el archivo de configuración
        with open('modules/config.py', 'w', encoding='utf-8') as f:
            f.write(config_content)

        print("✅ modules/config.py creado/actualizado")

    except Exception as e:
        print(f"❌ Error creando config.py: {e}")


def fix_app_imports():
    """Arreglar las importaciones en app.py para manejar errores"""
    print("\n🔧 ARREGLANDO IMPORTACIONES EN APP.PY")
    print("=" * 45)

    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # Buscar la sección de importación del database manager
        db_import_pattern = r'# Database Manager moderno.*?except.*?logger\.error.*?\n'

        new_db_import = '''# Database Manager moderno
try:
    from modules.database_manager import DatabaseManager
    from modules.config import get_database_config

    # Inicializar Database Manager con configuración moderna
    if CONFIG_AVAILABLE:
        try:
            db_config = get_database_config()
            db_manager = DatabaseManager(db_config)
            DB_AVAILABLE = True
            logger.info("✅ Database Manager moderno inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando Database Manager: {e}")
            db_manager = None
            DB_AVAILABLE = False
    else:
        logger.warning("⚠️ Configuración no disponible")
        db_manager = None
        DB_AVAILABLE = False

except ImportError as e:
    logger.error(f"❌ Error importando Database Manager: {e}")
    db_manager = None
    DB_AVAILABLE = False
except Exception as e:
    logger.error(f"❌ Error inicializando Database Manager: {e}")
    db_manager = None
    DB_AVAILABLE = False
'''

        # Reemplazar la importación del database manager
        if '# Database Manager moderno' in content:
            content = re.sub(db_import_pattern, new_db_import, content, flags=re.DOTALL)
            print("✅ Importaciones del Database Manager corregidas")

        # Guardar archivo
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ app.py actualizado")

    except Exception as e:
        print(f"❌ Error arreglando app.py: {e}")


def main():
    """Ejecutar todas las correcciones"""
    print("🚀 SOLUCIONANDO ERROR DE AUTOCOMMIT")
    print("=" * 60)

    # 1. Arreglar el módulo config
    fix_config_module()

    # 2. Arreglar database manager
    fix_database_manager()

    # 3. Arreglar importaciones en app.py
    fix_app_imports()

    print("\n" + "=" * 60)
    print("✅ TODAS LAS CORRECCIONES APLICADAS")
    print("=" * 60)
    print("🔄 Reinicia el servidor:")
    print("   python app.py")
    print("\n💡 Si sigue en modo demo, verifica:")
    print("   1. MySQL está ejecutándose: net start mysql")
    print("   2. Base de datos 'alfaia_db' existe")
    print("   3. Usuario 'root' tiene contraseña 'tired2019'")


if __name__ == "__main__":
    main()