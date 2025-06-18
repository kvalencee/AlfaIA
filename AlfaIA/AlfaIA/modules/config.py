# modules/config.py - Configuración del Sistema AlfaIA
# Ubicación: AlfaIA/AlfaIA/modules/config.py

import os
import json
import logging
from datetime import timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manejador de configuración centralizado para AlfaIA"""

    def __init__(self, config_file: str = "config/app_config.json"):
        self.config_file = config_file
        self.config = {}
        self._load_default_config()
        self._load_config_file()
        self._load_environment_variables()

    def _load_default_config(self):
        """Cargar configuración por defecto"""
        self.config = {
            # === CONFIGURACIÓN DE LA APLICACIÓN ===
            "app": {
                "name": "AlfaIA",
                "version": "1.0.0",
                "debug": True,
                "host": "127.0.0.1",
                "port": 5000,
                "secret_key": "alfaia-secret-key-2025-change-in-production",
                "max_content_length": 16 * 1024 * 1024,  # 16MB
                "upload_folder": "static/uploads",
                "session_lifetime_days": 7
            },

            # === CONFIGURACIÓN DE BASE DE DATOS ===
            "database": {
                "host": "localhost",
                "port": 3306,
                "database": "alfaia",
                "user": "alfaia_user",
                "password": "alfaia2024",
                "charset": "utf8mb4",
                "collation": "utf8mb4_unicode_ci",
                "pool_size": 10,
                "pool_timeout": 30,
                "max_retries": 3,
                "retry_delay": 1.0
            },

            # === CONFIGURACIÓN DE AUDIO ===
            "audio": {
                "sample_rate": 44100,
                "frame_size": 2048,
                "hop_length": 512,
                "confidence_threshold": 0.6,
                "energy_threshold": 0.01,
                "max_recording_time": 30,  # segundos
                "supported_formats": ["wav", "mp3", "flac", "ogg"],
                "temp_audio_lifetime": 300,  # 5 minutos
                "vocal_formants": {
                    "A": {"f1": 730, "f2": 1090},
                    "E": {"f1": 530, "f2": 1840},
                    "I": {"f1": 270, "f2": 2290},
                    "O": {"f1": 570, "f2": 840},
                    "U": {"f1": 440, "f2": 1020}
                }
            },

            # === CONFIGURACIÓN DE EJERCICIOS ===
            "ejercicios": {
                "niveles_maximos": {
                    "lectura": 5,
                    "ejercicios": 4,
                    "pronunciacion": 3,
                    "juegos": 3
                },
                "puntos_base": {
                    "lectura": 10,
                    "ejercicios": 15,
                    "pronunciacion": 20,
                    "juegos": 25
                },
                "tiempo_limite_segundos": {
                    "ordenar_frase": 120,
                    "completar_palabra": 60,
                    "pronunciacion": 30,
                    "memoria": 300,
                    "ahorcado": 180,
                    "trivia": 45
                },
                "intentos_maximos": {
                    "ahorcado": 6,
                    "pronunciacion": 3,
                    "completar_palabra": 3
                },
                "precision_minima_para_avanzar": 70.0
            },

            # === CONFIGURACIÓN DE RETROALIMENTACIÓN ===
            "retroalimentacion": {
                "frecuencia_evaluacion_dias": 7,
                "umbrales_precision": {
                    "excelente": 90.0,
                    "bueno": 70.0,
                    "regular": 50.0
                },
                "mensajes_motivacionales": True,
                "sugerencias_personalizadas": True,
                "reportes_automaticos": True
            },

            # === CONFIGURACIÓN DE PROGRESO ===
            "progreso": {
                "backup_interval_hours": 24,
                "historial_dias_conservar": 365,
                "racha_maxima_dias": 365,
                "puntos_para_subir_nivel": {
                    1: 100,
                    2: 250,
                    3: 500,
                    4: 1000,
                    5: 2000
                },
                "logros_disponibles": {
                    "primer_ejercicio": {"puntos": 10, "descripcion": "Completar primer ejercicio"},
                    "racha_7_dias": {"puntos": 50, "descripcion": "7 días consecutivos practicando"},
                    "racha_30_dias": {"puntos": 200, "descripcion": "30 días consecutivos practicando"},
                    "precision_perfecta": {"puntos": 25, "descripcion": "100% de precisión en un ejercicio"},
                    "nivel_2": {"puntos": 100, "descripcion": "Alcanzar nivel 2"},
                    "nivel_3": {"puntos": 250, "descripcion": "Alcanzar nivel 3"},
                    "ejercicios_100": {"puntos": 300, "descripcion": "Completar 100 ejercicios"},
                    "maestro_pronunciacion": {"puntos": 500,
                                              "descripcion": "Dominar todos los ejercicios de pronunciación"}
                }
            },

            # === CONFIGURACIÓN DE SEGURIDAD ===
            "security": {
                "password_min_length": 8,
                "password_require_uppercase": True,
                "password_require_lowercase": True,
                "password_require_numbers": True,
                "password_require_symbols": False,
                "session_timeout_minutes": 60,
                "max_login_attempts": 5,
                "lockout_duration_minutes": 15,
                "csrf_protection": True
            },

            # === CONFIGURACIÓN DE LOGGING ===
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file_path": "logs/alfaia.log",
                "max_file_size_mb": 10,
                "backup_count": 5,
                "console_output": True
            },

            # === CONFIGURACIÓN DE ARCHIVOS ===
            "files": {
                "allowed_extensions": ["jpg", "jpeg", "png", "gif", "wav", "mp3", "flac"],
                "max_file_size_mb": 10,
                "temp_folder": "temp",
                "backup_folder": "backups",
                "cleanup_interval_hours": 24
            },

            # === CONFIGURACIÓN DE JUEGOS ===
            "juegos": {
                "memoria": {
                    "pares_por_nivel": {1: 6, 2: 8, 3: 12},
                    "tiempo_mostrar_cartas": 2,
                    "bonificacion_velocidad": 1.5
                },
                "ahorcado": {
                    "vidas_iniciales": 6,
                    "pista_disponible": True,
                    "penalizacion_pista": 0.8
                },
                "trivia": {
                    "preguntas_por_sesion": 10,
                    "tiempo_respuesta_segundos": 30,
                    "puntos_respuesta_rapida": 2.0
                }
            }
        }

    def _load_config_file(self):
        """Cargar configuración desde archivo JSON"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    self._merge_config(file_config)
                logger.info(f"✅ Configuración cargada desde {self.config_file}")
            else:
                logger.info(f"📄 Archivo de configuración no encontrado: {self.config_file}")
                self._create_default_config_file()
        except Exception as e:
            logger.error(f"❌ Error cargando configuración: {e}")

    def _load_environment_variables(self):
        """Cargar configuración desde variables de entorno"""
        env_mapping = {
            'ALFAIA_DEBUG': ('app.debug', bool),
            'ALFAIA_SECRET_KEY': ('app.secret_key', str),
            'ALFAIA_DB_HOST': ('database.host', str),
            'ALFAIA_DB_PORT': ('database.port', int),
            'ALFAIA_DB_USER': ('database.user', str),
            'ALFAIA_DB_PASSWORD': ('database.password', str),
            'ALFAIA_DB_DATABASE': ('database.database', str),
            'ALFAIA_LOG_LEVEL': ('logging.level', str),
            'ALFAIA_UPLOAD_FOLDER': ('app.upload_folder', str)
        }

        for env_var, (config_path, data_type) in env_mapping.items():
            value = os.environ.get(env_var)
            if value:
                try:
                    if data_type == bool:
                        value = value.lower() in ('true', '1', 'yes', 'on')
                    elif data_type == int:
                        value = int(value)

                    self._set_nested_config(config_path, value)
                    logger.info(f"✅ Variable de entorno aplicada: {env_var}")
                except Exception as e:
                    logger.error(f"❌ Error procesando variable {env_var}: {e}")

    def _merge_config(self, new_config: Dict[str, Any]):
        """Combinar nueva configuración con la existente"""

        def merge_dicts(base_dict, new_dict):
            for key, value in new_dict.items():
                if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                    merge_dicts(base_dict[key], value)
                else:
                    base_dict[key] = value

        merge_dicts(self.config, new_config)

    def _set_nested_config(self, path: str, value: Any):
        """Establecer valor en configuración anidada usando notación de puntos"""
        keys = path.split('.')
        current = self.config

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def _create_default_config_file(self):
        """Crear archivo de configuración por defecto"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            logger.info(f"✅ Archivo de configuración creado: {self.config_file}")
        except Exception as e:
            logger.error(f"❌ Error creando archivo de configuración: {e}")

    def get(self, path: str, default: Any = None) -> Any:
        """Obtener valor de configuración usando notación de puntos"""
        try:
            keys = path.split('.')
            current = self.config

            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return default

            return current
        except Exception:
            return default

    def set(self, path: str, value: Any) -> bool:
        """Establecer valor de configuración"""
        try:
            self._set_nested_config(path, value)
            return True
        except Exception as e:
            logger.error(f"Error estableciendo configuración {path}: {e}")
            return False

    def save_config(self) -> bool:
        """Guardar configuración actual en archivo"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            logger.info("✅ Configuración guardada exitosamente")
            return True
        except Exception as e:
            logger.error(f"❌ Error guardando configuración: {e}")
            return False

    def get_database_config(self) -> Dict[str, Any]:
        """Obtener configuración de base de datos"""
        return self.get('database', {})

    def get_audio_config(self) -> Dict[str, Any]:
        """Obtener configuración de audio"""
        return self.get('audio', {})

    def get_security_config(self) -> Dict[str, Any]:
        """Obtener configuración de seguridad"""
        return self.get('security', {})

    def get_flask_config(self) -> Dict[str, Any]:
        """Obtener configuración para Flask"""
        app_config = self.get('app', {})
        security_config = self.get('security', {})

        return {
            'SECRET_KEY': app_config.get('secret_key'),
            'DEBUG': app_config.get('debug', False),
            'MAX_CONTENT_LENGTH': app_config.get('max_content_length'),
            'UPLOAD_FOLDER': app_config.get('upload_folder'),
            'PERMANENT_SESSION_LIFETIME': timedelta(days=app_config.get('session_lifetime_days', 7)),
            'SESSION_COOKIE_SECURE': not app_config.get('debug', True),
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'Lax',
            'WTF_CSRF_ENABLED': security_config.get('csrf_protection', True)
        }

    def validate_config(self) -> Dict[str, Any]:
        """Validar configuración actual"""
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'missing_required': []
        }

        required_configs = [
            'app.secret_key',
            'database.host',
            'database.user',
            'database.password',
            'database.database'
        ]

        # Verificar configuraciones requeridas
        for config_path in required_configs:
            value = self.get(config_path)
            if not value:
                validation_results['missing_required'].append(config_path)
                validation_results['valid'] = False

        # Validaciones específicas
        if self.get('app.secret_key') == 'alfaia-secret-key-2025-change-in-production':
            validation_results['warnings'].append(
                'Se está usando la clave secreta por defecto. Cámbiala en producción.')

        if self.get('app.debug') and self.get('security.session_timeout_minutes', 0) > 480:  # 8 horas
            validation_results['warnings'].append('Timeout de sesión muy largo para modo debug.')

        # Verificar configuración de audio
        sample_rate = self.get('audio.sample_rate')
        if sample_rate and sample_rate not in [22050, 44100, 48000]:
            validation_results['warnings'].append(f'Sample rate {sample_rate} no es estándar.')

        return validation_results

    def reset_to_defaults(self):
        """Restablecer configuración a valores por defecto"""
        self.config.clear()
        self._load_default_config()
        logger.info("🔄 Configuración restablecida a valores por defecto")

    def get_all_config(self) -> Dict[str, Any]:
        """Obtener toda la configuración actual"""
        return self.config.copy()

    def export_config(self, file_path: str) -> bool:
        """Exportar configuración a archivo"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            logger.info(f"✅ Configuración exportada a {file_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Error exportando configuración: {e}")
            return False


# === FUNCIONES UTILITARIAS ===

def create_directories():
    """Crear directorios necesarios basados en la configuración"""
    config = ConfigManager()

    directories = [
        config.get('app.upload_folder', 'static/uploads'),
        config.get('files.temp_folder', 'temp'),
        config.get('files.backup_folder', 'backups'),
        'logs',
        'data',
        'config'
    ]

    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"📁 Directorio creado/verificado: {directory}")
        except Exception as e:
            logger.error(f"❌ Error creando directorio {directory}: {e}")


def setup_logging(config_manager: ConfigManager):
    """Configurar logging basado en la configuración"""
    log_config = config_manager.get('logging', {})

    log_level = getattr(logging, log_config.get('level', 'INFO').upper())
    log_format = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_file = log_config.get('file_path', 'logs/alfaia.log')

    # Configurar logging
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler() if log_config.get('console_output', True) else logging.NullHandler()
        ]
    )

    logger.info("📝 Sistema de logging configurado")


# === INSTANCIA GLOBAL ===

# Crear instancia global del manejador de configuración
config_manager = ConfigManager()

# Crear directorios necesarios
create_directories()

# Configurar logging
setup_logging(config_manager)

# Validar configuración al inicializar
validation_result = config_manager.validate_config()
if not validation_result['valid']:
    logger.error("❌ Configuración inválida:")
    for error in validation_result['errors']:
        logger.error(f"   - {error}")
    for missing in validation_result['missing_required']:
        logger.error(f"   - Falta configuración requerida: {missing}")

for warning in validation_result['warnings']:
    logger.warning(f"⚠️ {warning}")

if validation_result['valid']:
    logger.info("✅ Configuración validada correctamente")

# === EJEMPLO DE USO ===

if __name__ == "__main__":
    # Ejemplo de uso del ConfigManager
    print("=== SISTEMA DE CONFIGURACIÓN ALFAIA ===")

    # Obtener configuraciones específicas
    db_config = config_manager.get_database_config()
    print(f"Base de datos: {db_config['host']}:{db_config['port']}")

    audio_config = config_manager.get_audio_config()
    print(f"Sample rate de audio: {audio_config['sample_rate']}")

    # Modificar configuración
    config_manager.set('app.debug', False)
    print(f"Debug mode: {config_manager.get('app.debug')}")

    # Validar configuración
    validation = config_manager.validate_config()
    print(f"Configuración válida: {validation['valid']}")

    # Guardar cambios
    config_manager.save_config()
    print("Configuración guardada")