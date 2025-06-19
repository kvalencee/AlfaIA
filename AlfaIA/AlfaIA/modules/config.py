# modules/config.py - Configuración actualizada para AlfaIA
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Configuración de base de datos"""
    host: str
    port: int
    database: str
    user: str
    password: str
    charset: str = 'utf8mb4'
    pool_size: int = 10


@dataclass
class RedisConfig:
    """Configuración de Redis para cache"""
    host: str = 'localhost'
    port: int = 6379
    password: Optional[str] = None
    db: int = 0


@dataclass
class SecurityConfig:
    """Configuración de seguridad"""
    secret_key: str
    jwt_secret: str
    password_salt_rounds: int = 12
    session_timeout_hours: int = 24
    max_login_attempts: int = 5
    login_attempt_window_minutes: int = 15


class ConfigManager:
    """
    Manager centralizado de configuración para AlfaIA
    Maneja configuraciones de desarrollo, testing y producción
    """

    def __init__(self, environment: str = None):
        self.environment = environment or os.getenv('FLASK_ENV', 'development')
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Cargar configuración según el entorno"""

        # Configuración base común
        base_config = {
            # === CONFIGURACIÓN DE LA APLICACIÓN ===
            'app': {
                'name': 'AlfaIA',
                'version': '2.0.0',
                'description': 'Sistema Avanzado de Alfabetización con IA',
                'debug': self.environment == 'development',
                'testing': self.environment == 'testing',
                'host': os.getenv('HOST', '0.0.0.0'),
                'port': int(os.getenv('PORT', 5000)),
                'timezone': 'America/Bogota',
                'default_language': 'es',
                'supported_languages': ['es', 'en'],
            },

            # === CONFIGURACIÓN DE BASE DE DATOS ===
            'database': {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', 3306)),
                'database': os.getenv('DB_NAME', 'alfaia_db'),
                'user': os.getenv('DB_USER', 'alfaia_user'),
                'password': os.getenv('DB_PASSWORD', ''),
                'charset': 'utf8mb4',
                'pool_size': int(os.getenv('DB_POOL_SIZE', 10)),
                'pool_recycle': 3600,
                'echo': self.environment == 'development',
                'backup_enabled': os.getenv('DB_BACKUP_ENABLED', 'true').lower() == 'true',
                'backup_schedule': '0 2 * * *',  # Diario a las 2 AM
            },

            # === CONFIGURACIÓN DE REDIS (CACHE) ===
            'redis': {
                'enabled': os.getenv('REDIS_ENABLED', 'false').lower() == 'true',
                'host': os.getenv('REDIS_HOST', 'localhost'),
                'port': int(os.getenv('REDIS_PORT', 6379)),
                'password': os.getenv('REDIS_PASSWORD'),
                'db': int(os.getenv('REDIS_DB', 0)),
                'cache_timeout': int(os.getenv('CACHE_TIMEOUT', 3600)),
                'session_timeout': int(os.getenv('SESSION_TIMEOUT', 86400)),
            },

            # === CONFIGURACIÓN DE SEGURIDAD ===
            'security': {
                'secret_key': os.getenv('SECRET_KEY', self._generate_secret_key()),
                'jwt_secret': os.getenv('JWT_SECRET_KEY', self._generate_secret_key()),
                'password_salt_rounds': int(os.getenv('PASSWORD_SALT_ROUNDS', 12)),
                'session_timeout_hours': int(os.getenv('SESSION_TIMEOUT_HOURS', 24)),
                'max_login_attempts': int(os.getenv('MAX_LOGIN_ATTEMPTS', 5)),
                'login_attempt_window_minutes': int(os.getenv('LOGIN_ATTEMPT_WINDOW', 15)),
                'csrf_enabled': os.getenv('CSRF_ENABLED', 'true').lower() == 'true',
                'cors_enabled': os.getenv('CORS_ENABLED', 'true').lower() == 'true',
                'cors_origins': os.getenv('CORS_ORIGINS', '*').split(','),
                'rate_limiting_enabled': os.getenv('RATE_LIMITING_ENABLED', 'true').lower() == 'true',
            },

            # === CONFIGURACIÓN DE LOGGING ===
            'logging': {
                'level': os.getenv('LOG_LEVEL', 'INFO'),
                'format': os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
                'file_enabled': os.getenv('LOG_FILE_ENABLED', 'true').lower() == 'true',
                'file_path': os.getenv('LOG_FILE_PATH', 'logs/alfaia.log'),
                'max_file_size': int(os.getenv('LOG_MAX_FILE_SIZE', 10485760)),  # 10MB
                'backup_count': int(os.getenv('LOG_BACKUP_COUNT', 5)),
                'sentry_enabled': os.getenv('SENTRY_ENABLED', 'false').lower() == 'true',
                'sentry_dsn': os.getenv('SENTRY_DSN'),
            },

            # === CONFIGURACIÓN DE EJERCICIOS ===
            'exercises': {
                'default_timeout_seconds': int(os.getenv('DEFAULT_EXERCISE_TIMEOUT', 300)),
                'max_attempts': int(os.getenv('MAX_EXERCISE_ATTEMPTS', 3)),
                'auto_save_interval_seconds': int(os.getenv('AUTO_SAVE_INTERVAL', 30)),
                'adaptive_difficulty': os.getenv('ADAPTIVE_DIFFICULTY', 'true').lower() == 'true',
                'ai_feedback_enabled': os.getenv('AI_FEEDBACK_ENABLED', 'true').lower() == 'true',
                'voice_recognition_enabled': os.getenv('VOICE_RECOGNITION_ENABLED', 'false').lower() == 'true',

                # Configuración por tipo de ejercicio
                'lectura': {
                    'words_per_minute_default': int(os.getenv('READING_WPM_DEFAULT', 200)),
                    'comprehension_threshold': float(os.getenv('READING_COMPREHENSION_THRESHOLD', 70.0)),
                    'auto_level_up_threshold': float(os.getenv('READING_LEVEL_UP_THRESHOLD', 85.0)),
                    'max_text_length_words': int(os.getenv('MAX_TEXT_LENGTH', 500)),
                },

                'pronunciacion': {
                    'max_recording_seconds': int(os.getenv('MAX_RECORDING_SECONDS', 30)),
                    'supported_audio_formats': ['wav', 'mp3', 'webm'],
                    'voice_analysis_enabled': os.getenv('VOICE_ANALYSIS_ENABLED', 'false').lower() == 'true',
                    'pronunciation_threshold': float(os.getenv('PRONUNCIATION_THRESHOLD', 75.0)),
                },

                'memoria': {
                    'default_cards': int(os.getenv('MEMORY_DEFAULT_CARDS', 12)),
                    'max_cards': int(os.getenv('MEMORY_MAX_CARDS', 24)),
                    'flip_timeout_seconds': int(os.getenv('MEMORY_FLIP_TIMEOUT', 2)),
                },

                'ahorcado': {
                    'max_wrong_attempts': int(os.getenv('HANGMAN_MAX_ATTEMPTS', 6)),
                    'hint_enabled': os.getenv('HANGMAN_HINTS_ENABLED', 'true').lower() == 'true',
                    'time_limit_seconds': int(os.getenv('HANGMAN_TIME_LIMIT', 180)),
                },
            },

            # === CONFIGURACIÓN DE GAMIFICACIÓN ===
            'gamification': {
                'points_enabled': os.getenv('POINTS_ENABLED', 'true').lower() == 'true',
                'achievements_enabled': os.getenv('ACHIEVEMENTS_ENABLED', 'true').lower() == 'true',
                'leaderboard_enabled': os.getenv('LEADERBOARD_ENABLED', 'true').lower() == 'true',
                'daily_goals_enabled': os.getenv('DAILY_GOALS_ENABLED', 'true').lower() == 'true',

                'points': {
                    'base_exercise_completion': int(os.getenv('POINTS_BASE_EXERCISE', 50)),
                    'perfect_score_bonus': int(os.getenv('POINTS_PERFECT_BONUS', 25)),
                    'streak_multiplier': float(os.getenv('POINTS_STREAK_MULTIPLIER', 1.5)),
                    'daily_goal_bonus': int(os.getenv('POINTS_DAILY_GOAL_BONUS', 100)),
                    'achievement_multiplier': float(os.getenv('POINTS_ACHIEVEMENT_MULTIPLIER', 2.0)),
                },

                'levels': {
                    'experience_per_level': int(os.getenv('EXPERIENCE_PER_LEVEL', 1000)),
                    'max_level': int(os.getenv('MAX_LEVEL', 50)),
                    'level_up_bonus_points': int(os.getenv('LEVEL_UP_BONUS', 200)),
                },
            },

            # === CONFIGURACIÓN DE IA Y ANALYTICS ===
            'ai': {
                'enabled': os.getenv('AI_ENABLED', 'true').lower() == 'true',
                'provider': os.getenv('AI_PROVIDER', 'openai'),  # openai, anthropic, local
                'api_key': os.getenv('AI_API_KEY'),
                'model': os.getenv('AI_MODEL', 'gpt-3.5-turbo'),
                'max_tokens': int(os.getenv('AI_MAX_TOKENS', 1000)),
                'temperature': float(os.getenv('AI_TEMPERATURE', 0.7)),
                'feedback_generation': os.getenv('AI_FEEDBACK_GENERATION', 'true').lower() == 'true',
                'content_generation': os.getenv('AI_CONTENT_GENERATION', 'false').lower() == 'true',
                'personalization': os.getenv('AI_PERSONALIZATION', 'true').lower() == 'true',
            },

            'analytics': {
                'enabled': os.getenv('ANALYTICS_ENABLED', 'true').lower() == 'true',
                'google_analytics_id': os.getenv('GOOGLE_ANALYTICS_ID'),
                'mixpanel_token': os.getenv('MIXPANEL_TOKEN'),
                'custom_events_enabled': os.getenv('CUSTOM_EVENTS_ENABLED', 'true').lower() == 'true',
                'user_tracking_enabled': os.getenv('USER_TRACKING_ENABLED', 'true').lower() == 'true',
                'performance_monitoring': os.getenv('PERFORMANCE_MONITORING', 'true').lower() == 'true',
                'data_retention_days': int(os.getenv('ANALYTICS_RETENTION_DAYS', 365)),
            },

            # === CONFIGURACIÓN DE ARCHIVOS Y MEDIA ===
            'media': {
                'upload_enabled': os.getenv('UPLOAD_ENABLED', 'true').lower() == 'true',
                'max_file_size_mb': int(os.getenv('MAX_FILE_SIZE_MB', 10)),
                'allowed_extensions': {
                    'images': ['jpg', 'jpeg', 'png', 'gif', 'webp'],
                    'audio': ['mp3', 'wav', 'ogg', 'webm'],
                    'documents': ['pdf', 'txt', 'docx'],
                },
                'upload_folder': os.getenv('UPLOAD_FOLDER', 'uploads'),
                'cdn_enabled': os.getenv('CDN_ENABLED', 'false').lower() == 'true',
                'cdn_url': os.getenv('CDN_URL'),
                'compression_enabled': os.getenv('COMPRESSION_ENABLED', 'true').lower() == 'true',
            },

            # === CONFIGURACIÓN DE EMAIL ===
            'email': {
                'enabled': os.getenv('EMAIL_ENABLED', 'false').lower() == 'true',
                'provider': os.getenv('EMAIL_PROVIDER', 'smtp'),  # smtp, sendgrid, mailgun
                'smtp_server': os.getenv('SMTP_SERVER', 'localhost'),
                'smtp_port': int(os.getenv('SMTP_PORT', 587)),
                'smtp_username': os.getenv('SMTP_USERNAME'),
                'smtp_password': os.getenv('SMTP_PASSWORD'),
                'smtp_use_tls': os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',
                'from_email': os.getenv('FROM_EMAIL', 'noreply@alfaia.com'),
                'from_name': os.getenv('FROM_NAME', 'AlfaIA'),
                'sendgrid_api_key': os.getenv('SENDGRID_API_KEY'),
                'mailgun_api_key': os.getenv('MAILGUN_API_KEY'),
                'mailgun_domain': os.getenv('MAILGUN_DOMAIN'),
            },

            # === CONFIGURACIÓN DE NOTIFICACIONES ===
            'notifications': {
                'enabled': os.getenv('NOTIFICATIONS_ENABLED', 'true').lower() == 'true',
                'push_notifications': os.getenv('PUSH_NOTIFICATIONS_ENABLED', 'false').lower() == 'true',
                'email_notifications': os.getenv('EMAIL_NOTIFICATIONS_ENABLED', 'false').lower() == 'true',
                'in_app_notifications': os.getenv('IN_APP_NOTIFICATIONS_ENABLED', 'true').lower() == 'true',
                'notification_retention_days': int(os.getenv('NOTIFICATION_RETENTION_DAYS', 30)),
                'max_notifications_per_user': int(os.getenv('MAX_NOTIFICATIONS_PER_USER', 100)),

                # Tipos de notificaciones
                'achievement_notifications': os.getenv('ACHIEVEMENT_NOTIFICATIONS', 'true').lower() == 'true',
                'progress_notifications': os.getenv('PROGRESS_NOTIFICATIONS', 'true').lower() == 'true',
                'reminder_notifications': os.getenv('REMINDER_NOTIFICATIONS', 'true').lower() == 'true',
                'social_notifications': os.getenv('SOCIAL_NOTIFICATIONS', 'false').lower() == 'true',
            },

            # === CONFIGURACIÓN DE API Y INTEGRACIONES ===
            'api': {
                'enabled': os.getenv('API_ENABLED', 'true').lower() == 'true',
                'version': os.getenv('API_VERSION', 'v1'),
                'rate_limit_per_minute': int(os.getenv('API_RATE_LIMIT', 60)),
                'rate_limit_per_hour': int(os.getenv('API_RATE_LIMIT_HOUR', 1000)),
                'authentication_required': os.getenv('API_AUTH_REQUIRED', 'true').lower() == 'true',
                'documentation_enabled': os.getenv('API_DOCS_ENABLED', 'true').lower() == 'true',
                'cors_enabled': os.getenv('API_CORS_ENABLED', 'true').lower() == 'true',
            },

            # === CONFIGURACIÓN DE MONITOREO ===
            'monitoring': {
                'health_check_enabled': os.getenv('HEALTH_CHECK_ENABLED', 'true').lower() == 'true',
                'metrics_enabled': os.getenv('METRICS_ENABLED', 'true').lower() == 'true',
                'prometheus_enabled': os.getenv('PROMETHEUS_ENABLED', 'false').lower() == 'true',
                'prometheus_port': int(os.getenv('PROMETHEUS_PORT', 9090)),
                'error_tracking_enabled': os.getenv('ERROR_TRACKING_ENABLED', 'true').lower() == 'true',
                'performance_tracking': os.getenv('PERFORMANCE_TRACKING', 'true').lower() == 'true',
                'database_monitoring': os.getenv('DB_MONITORING', 'true').lower() == 'true',
            },

            # === CONFIGURACIÓN DE FEATURES FLAGS ===
            'features': {
                'beta_features_enabled': os.getenv('BETA_FEATURES_ENABLED', 'false').lower() == 'true',
                'experimental_exercises': os.getenv('EXPERIMENTAL_EXERCISES', 'false').lower() == 'true',
                'social_features': os.getenv('SOCIAL_FEATURES', 'false').lower() == 'true',
                'multi_language_support': os.getenv('MULTI_LANGUAGE_SUPPORT', 'false').lower() == 'true',
                'offline_mode': os.getenv('OFFLINE_MODE', 'false').lower() == 'true',
                'progressive_web_app': os.getenv('PWA_ENABLED', 'true').lower() == 'true',
                'dark_mode': os.getenv('DARK_MODE_ENABLED', 'true').lower() == 'true',
                'accessibility_enhancements': os.getenv('ACCESSIBILITY_ENHANCED', 'true').lower() == 'true',
            },

            # === CONFIGURACIÓN DE DESARROLLO ===
            'development': {
                'auto_reload': self.environment == 'development',
                'debug_toolbar': self.environment == 'development',
                'profiler_enabled': os.getenv('PROFILER_ENABLED', 'false').lower() == 'true',
                'sql_debug': self.environment == 'development',
                'template_debug': self.environment == 'development',
                'mock_external_apis': os.getenv('MOCK_EXTERNAL_APIS', 'false').lower() == 'true',
                'seed_data_enabled': os.getenv('SEED_DATA_ENABLED', 'false').lower() == 'true',
            },
        }

        # Aplicar configuraciones específicas por entorno
        if self.environment == 'development':
            base_config.update(self._get_development_config())
        elif self.environment == 'testing':
            base_config.update(self._get_testing_config())
        elif self.environment == 'production':
            base_config.update(self._get_production_config())

        return base_config

    def _get_development_config(self) -> Dict[str, Any]:
        """Configuración específica para desarrollo"""
        return {
            'database': {
                'database': 'alfaia_dev',
                'echo': True,
                'pool_size': 5,
            },
            'security': {
                'csrf_enabled': False,
                'session_timeout_hours': 48,
            },
            'logging': {
                'level': 'DEBUG',
                'file_enabled': True,
            },
            'features': {
                'beta_features_enabled': True,
                'experimental_exercises': True,
            },
        }

    def _get_testing_config(self) -> Dict[str, Any]:
        """Configuración específica para testing"""
        return {
            'database': {
                'database': 'alfaia_test',
                'pool_size': 3,
                'echo': False,
            },
            'security': {
                'password_salt_rounds': 4,  # Más rápido para tests
            },
            'redis': {
                'db': 1,  # Base de datos diferente para tests
            },
            'email': {
                'enabled': False,
            },
            'notifications': {
                'enabled': False,
            },
            'ai': {
                'enabled': False,
            },
            'analytics': {
                'enabled': False,
            },
        }

    def _get_production_config(self) -> Dict[str, Any]:
        """Configuración específica para producción"""
        return {
            'app': {
                'debug': False,
            },
            'logging': {
                'level': 'WARNING',
                'sentry_enabled': True,
            },
            'security': {
                'csrf_enabled': True,
                'rate_limiting_enabled': True,
            },
            'monitoring': {
                'prometheus_enabled': True,
                'error_tracking_enabled': True,
            },
            'features': {
                'beta_features_enabled': False,
                'experimental_exercises': False,
            },
        }

    def _generate_secret_key(self) -> str:
        """Generar clave secreta aleatoria"""
        import secrets
        return secrets.token_urlsafe(32)

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Obtener valor de configuración usando notación de puntos

        Ejemplo:
            config.get('database.host')
            config.get('exercises.lectura.words_per_minute_default')
        """
        keys = key_path.split('.')
        value = self.config

        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key_path: str, value: Any) -> None:
        """
        Establecer valor de configuración usando notación de puntos
        """
        keys = key_path.split('.')
        target = self.config

        # Navegar hasta el penúltimo nivel
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]

        # Establecer el valor final
        target[keys[-1]] = value

    def get_database_config(self) -> DatabaseConfig:
        """Obtener configuración de base de datos como objeto"""
        db_config = self.get('database')
        return DatabaseConfig(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password'],
            charset=db_config['charset'],
            pool_size=db_config['pool_size']
        )

    def get_redis_config(self) -> RedisConfig:
        """Obtener configuración de Redis como objeto"""
        redis_config = self.get('redis')
        return RedisConfig(
            host=redis_config['host'],
            port=redis_config['port'],
            password=redis_config['password'],
            db=redis_config['db']
        )

    def get_security_config(self) -> SecurityConfig:
        """Obtener configuración de seguridad como objeto"""
        security_config = self.get('security')
        return SecurityConfig(
            secret_key=security_config['secret_key'],
            jwt_secret=security_config['jwt_secret'],
            password_salt_rounds=security_config['password_salt_rounds'],
            session_timeout_hours=security_config['session_timeout_hours'],
            max_login_attempts=security_config['max_login_attempts'],
            login_attempt_window_minutes=security_config['login_attempt_window_minutes']
        )

    def is_feature_enabled(self, feature_name: str) -> bool:
        """Verificar si una característica está habilitada"""
        return self.get(f'features.{feature_name}', False)

    def get_exercise_config(self, exercise_type: str) -> Dict[str, Any]:
        """Obtener configuración específica de un tipo de ejercicio"""
        base_config = self.get('exercises', {})
        specific_config = self.get(f'exercises.{exercise_type}', {})

        # Combinar configuración base con específica
        combined_config = {
            'default_timeout_seconds': base_config.get('default_timeout_seconds'),
            'max_attempts': base_config.get('max_attempts'),
            'auto_save_interval_seconds': base_config.get('auto_save_interval_seconds'),
            'adaptive_difficulty': base_config.get('adaptive_difficulty'),
            'ai_feedback_enabled': base_config.get('ai_feedback_enabled'),
        }
        combined_config.update(specific_config)

        return combined_config

    def validate_config(self) -> Dict[str, Any]:
        """Validar configuración y retornar errores si los hay"""
        errors = []
        warnings = []

        # Validaciones críticas
        if not self.get('database.password') and self.environment == 'production':
            errors.append("Password de base de datos requerido en producción")

        if not self.get('security.secret_key'):
            errors.append("Secret key es requerido")

        if self.get('ai.enabled') and not self.get('ai.api_key'):
            warnings.append("IA habilitada pero no se configuró API key")

        if self.get('email.enabled') and not self.get('email.smtp_username'):
            warnings.append("Email habilitado pero no se configuró SMTP")

        # Validaciones de rangos
        if self.get('database.pool_size', 0) < 1:
            errors.append("Pool size de base de datos debe ser mayor a 0")

        if self.get('security.password_salt_rounds', 0) < 10 and self.environment == 'production':
            warnings.append("Salt rounds muy bajo para producción (recomendado: 12+)")

        # Validaciones de archivos/directorios
        upload_folder = self.get('media.upload_folder')
        if upload_folder and not os.path.exists(upload_folder):
            warnings.append(f"Directorio de uploads no existe: {upload_folder}")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def export_config(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Exportar configuración (opcionalmente sin datos sensibles)"""
        config_copy = self.config.copy()

        if not include_sensitive:
            # Remover datos sensibles
            sensitive_keys = [
                'database.password',
                'security.secret_key',
                'security.jwt_secret',
                'ai.api_key',
                'email.smtp_password',
                'email.sendgrid_api_key',
                'email.mailgun_api_key',
                'redis.password',
            ]

            for key_path in sensitive_keys:
                self._remove_key_from_dict(config_copy, key_path)

        return config_copy

    def _remove_key_from_dict(self, d: Dict[str, Any], key_path: str):
        """Remover clave de diccionario usando notación de puntos"""
        keys = key_path.split('.')
        target = d

        try:
            for key in keys[:-1]:
                target = target[key]

            if keys[-1] in target:
                target[keys[-1]] = '***HIDDEN***'
        except (KeyError, TypeError):
            pass

    def reload_config(self):
        """Recargar configuración"""
        self.config = self._load_config()
        logger.info(f"✅ Configuración recargada para entorno: {self.environment}")

    def __repr__(self) -> str:
        return f"ConfigManager(environment='{self.environment}')"


# =====================================================
# INSTANCIA GLOBAL DE CONFIGURACIÓN
# =====================================================

# Crear instancia global
config = ConfigManager()


# Funciones de conveniencia
def get_config(key_path: str, default: Any = None) -> Any:
    """Función de conveniencia para obtener configuración"""
    return config.get(key_path, default)


def is_feature_enabled(feature_name: str) -> bool:
    """Función de conveniencia para verificar features"""
    return config.is_feature_enabled(feature_name)


def get_database_config() -> DatabaseConfig:
    """Función de conveniencia para obtener configuración de BD"""
    return config.get_database_config()


def get_exercise_config(exercise_type: str) -> Dict[str, Any]:
    """Función de conveniencia para obtener configuración de ejercicios"""
    return config.get_exercise_config(exercise_type)


# =====================================================
# CONFIGURACIONES LEGACY PARA COMPATIBILIDAD
# =====================================================

class LegacyConfig:
    """Configuración legacy para mantener compatibilidad"""

    @staticmethod
    def get_config():
        """Obtener configuración en formato legacy"""
        return {
            # Base de datos
            'database': {
                'host': config.get('database.host'),
                'port': config.get('database.port'),
                'database': config.get('database.database'),
                'user': config.get('database.user'),
                'password': config.get('database.password'),
            },

            # Ejercicios
            'ejercicios': {
                'niveles_maximos': {
                    'lectura': 5,
                    'ejercicios': 4,
                    'pronunciacion': 3,
                    'juegos': 3
                },
                'puntos_base': {
                    'lectura': config.get('gamification.points.base_exercise_completion', 50),
                    'ejercicios': 15,
                    'pronunciacion': 20,
                    'juegos': 25
                },
                'tiempo_limite_segundos': {
                    'ordenar_frase': config.get('exercises.default_timeout_seconds', 120),
                    'completar_palabra': 60,
                    'pronunciacion': 30,
                    'memoria': 300,
                    'ahorcado': config.get('exercises.ahorcado.time_limit_seconds', 180),
                    'trivia': 45
                },
                'intentos_maximos': {
                    'ahorcado': config.get('exercises.ahorcado.max_wrong_attempts', 6),
                    'pronunciacion': 3,
                    'completar_palabra': 3
                },
                'precision_minima_para_avanzar': config.get('exercises.lectura.comprehension_threshold', 70.0)
            },

            # Retroalimentación
            'retroalimentacion': {
                'frecuencia_evaluacion_dias': 7,
                'umbrales_precision': {
                    'excelente': 90.0,
                    'bueno': 70.0,
                    'regular': 50.0
                },
                'mensajes_motivacionales': True,
                'sugerencias_personalizadas': True,
                'reportes_automaticos': config.get('analytics.enabled', True),
            },

            # Pronunciación
            'pronunciacion': {
                'max_recording_time': config.get('exercises.pronunciacion.max_recording_seconds', 30),
                'supported_formats': config.get('media.allowed_extensions.audio', ['wav', 'mp3', 'webm']),
                'temp_audio_lifetime': 300,
                'vocal_formants': {
                    'A': {'f1': 730, 'f2': 1090},
                    'E': {'f1': 530, 'f2': 1840},
                    'I': {'f1': 270, 'f2': 2290},
                    'O': {'f1': 570, 'f2': 840},
                    'U': {'f1': 440, 'f2': 1020}
                }
            },

            # Gamificación
            'gamificacion': {
                'puntos_habilitados': config.get('gamification.points_enabled', True),
                'logros_habilitados': config.get('gamification.achievements_enabled', True),
                'ranking_habilitado': config.get('gamification.leaderboard_enabled', True),
                'objetivos_diarios': config.get('gamification.daily_goals_enabled', True),
            },

            # Notificaciones
            'notificaciones': {
                'habilitadas': config.get('notifications.enabled', True),
                'tipos_habilitados': {
                    'logros': config.get('notifications.achievement_notifications', True),
                    'progreso': config.get('notifications.progress_notifications', True),
                    'recordatorios': config.get('notifications.reminder_notifications', True),
                },
                'retention_dias': config.get('notifications.notification_retention_days', 30),
            }
        }


# =====================================================
# INICIALIZACIÓN Y VALIDACIÓN
# =====================================================

def initialize_config():
    """Inicializar y validar configuración"""
    try:
        # Validar configuración
        validation = config.validate_config()

        if validation['errors']:
            logger.error("❌ Errores de configuración encontrados:")
            for error in validation['errors']:
                logger.error(f"  - {error}")
            raise ValueError("Configuración inválida")

        if validation['warnings']:
            logger.warning("⚠️ Advertencias de configuración:")
            for warning in validation['warnings']:
                logger.warning(f"  - {warning}")

        logger.info(f"✅ Configuración inicializada correctamente")
        logger.info(f"   Entorno: {config.environment}")
        logger.info(f"   Base de datos: {config.get('database.database')}")
        logger.info(f"   Debug: {config.get('app.debug')}")
        logger.info(f"   Features habilitadas: {sum(1 for k, v in config.get('features', {}).items() if v)}")

        return True

    except Exception as e:
        logger.error(f"❌ Error inicializando configuración: {e}")
        raise


# Inicializar configuración al importar el módulo
if __name__ != "__main__":
    initialize_config()

# =====================================================
# EJEMPLO DE USO
# =====================================================

if __name__ == "__main__":
    # Ejemplos de uso del ConfigManager

    print("=== CONFIGURACIÓN ALFAIA ===")
    print(f"Entorno: {config.environment}")
    print(f"Base de datos: {config.get('database.host')}:{config.get('database.port')}")
    print(f"Debug habilitado: {config.get('app.debug')}")
    print(f"IA habilitada: {config.get('ai.enabled')}")

    print("\n=== CONFIGURACIÓN DE EJERCICIOS ===")
    lectura_config = config.get_exercise_config('lectura')
    print(f"Palabras por minuto por defecto: {lectura_config.get('words_per_minute_default')}")
    print(f"Umbral de comprensión: {lectura_config.get('comprehension_threshold')}%")

    print("\n=== FEATURES HABILITADAS ===")
    features = config.get('features', {})
    for feature, enabled in features.items():
        status = "✅" if enabled else "❌"
        print(f"{status} {feature}")

    print("\n=== VALIDACIÓN ===")
    validation = config.validate_config()
    print(f"Configuración válida: {validation['valid']}")
    if validation['errors']:
        print("Errores:", validation['errors'])
    if validation['warnings']:
        print("Advertencias:", validation['warnings'])