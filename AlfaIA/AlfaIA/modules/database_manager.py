# modules/database_manager.py - Gestor Real de Base de Datos
# Ubicación: AlfaIA/AlfaIA/modules/database_manager.py

import mysql.connector
from mysql.connector import pooling, Error
from contextlib import contextmanager
import bcrypt
import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self):
        self.pool = None
        self.is_connected = False
        self.connect()

    def connect(self):
        """Establecer conexión con la base de datos"""
        try:
            # Configuraciones de conexión a probar
            configs = [
                {
                    'host': 'localhost',
                    'database': 'alfaia',
                    'user': 'alfaia_user',
                    'password': 'alfaia2024',
                    'charset': 'utf8mb4',
                    'collation': 'utf8mb4_unicode_ci',
                    'autocommit': True,
                    'pool_name': 'alfaia_pool',
                    'pool_size': 5,
                    'pool_reset_session': True
                },
                {
                    'host': 'localhost',
                    'database': 'alfaia',
                    'user': 'root',
                    'password': 'tired2019',
                    'charset': 'utf8mb4',
                    'collation': 'utf8mb4_unicode_ci',
                    'autocommit': True,
                    'pool_name': 'alfaia_pool',
                    'pool_size': 5,
                    'pool_reset_session': True
                }
            ]

            for config in configs:
                try:
                    logger.info(f"Intentando conectar con usuario: {config['user']}")
                    self.pool = pooling.MySQLConnectionPool(**config)

                    # Probar la conexión
                    with self.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT 1")
                        cursor.fetchone()
                        cursor.close()

                    self.is_connected = True
                    logger.info(f"✅ Conexión exitosa a MySQL con usuario: {config['user']}")
                    return

                except Error as e:
                    logger.warning(f"⚠️ Error con usuario {config['user']}: {e}")
                    continue

            raise Exception("No se pudo conectar con ninguna configuración")

        except Exception as e:
            logger.error(f"❌ Error crítico conectando a base de datos: {e}")
            self.is_connected = False

    @contextmanager
    def get_connection(self):
        """Obtener conexión del pool"""
        connection = None
        try:
            if not self.pool:
                raise Exception("Pool de conexiones no disponible")

            connection = self.pool.get_connection()
            yield connection

        except Error as e:
            if connection and connection.is_connected():
                connection.rollback()
            logger.error(f"Error en conexión: {e}")
            raise

        finally:
            if connection and connection.is_connected():
                connection.close()

    def test_connection(self):
        """Probar si la conexión funciona"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                return result is not None
        except:
            return False

    def execute_query(self, query, params=None, fetch=None):
        """Ejecutar consulta en la base de datos"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(query, params or ())

                if fetch == 'all':
                    result = cursor.fetchall()
                elif fetch == 'one':
                    result = cursor.fetchone()
                else:
                    result = cursor.rowcount

                cursor.close()
                return result

        except Error as e:
            logger.error(f"Error ejecutando consulta: {e}")
            logger.error(f"Consulta: {query}")
            logger.error(f"Parámetros: {params}")
            raise

    def hash_password(self, password):
        """Crear hash de contraseña"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password, hashed):
        """Verificar contraseña"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    # ==================== MÉTODOS DE USUARIO ====================

    def get_user_by_username(self, username):
        """Obtener usuario por nombre de usuario"""
        return self.execute_query(
            "SELECT * FROM usuarios WHERE username = %s AND activo = 1",
            (username,),
            fetch='one'
        )

    def get_user_by_id(self, user_id):
        """Obtener usuario por ID"""
        return self.execute_query(
            "SELECT * FROM usuarios WHERE id = %s AND activo = 1",
            (user_id,),
            fetch='one'
        )

    def authenticate_user(self, username, password):
        """Autenticar usuario"""
        user = self.get_user_by_username(username)
        if user and self.verify_password(password, user['password_hash']):
            # Actualizar último acceso
            self.execute_query(
                "UPDATE usuarios SET ultimo_acceso = NOW() WHERE id = %s",
                (user['id'],)
            )
            return user
        return None

    # ==================== MÉTODOS DE PROGRESO ====================

    def get_user_progress(self, user_id):
        """Obtener progreso completo del usuario"""
        return self.execute_query(
            "SELECT * FROM progreso_usuario WHERE usuario_id = %s",
            (user_id,),
            fetch='one'
        )

    def get_user_statistics(self, user_id):
        """Obtener estadísticas del usuario"""
        progress = self.get_user_progress(user_id)
        if not progress:
            # Crear registro de progreso si no existe
            self.execute_query(
                "INSERT INTO progreso_usuario (usuario_id) VALUES (%s)",
                (user_id,)
            )
            progress = self.get_user_progress(user_id)

        # Obtener estadísticas adicionales
        total_exercises = self.execute_query(
            "SELECT COUNT(*) as total FROM ejercicios_realizados WHERE usuario_id = %s",
            (user_id,),
            fetch='one'
        )

        total_vocales = self.execute_query(
            "SELECT COUNT(*) as total FROM vocales_detectadas WHERE usuario_id = %s",
            (user_id,),
            fetch='one'
        )

        return {
            'ejercicios_completados': progress['ejercicios_completados'],
            'tiempo_total_minutos': progress['tiempo_total_minutos'],
            'precision_promedio': float(progress['precision_promedio']),
            'racha_dias': progress['racha_dias'],
            'puntos_totales': progress['puntos_totales'],
            'total_vocales': total_vocales['total'] if total_vocales else 0,
            'nivel_lectura': progress['nivel_lectura'],
            'nivel_ejercicios': progress['nivel_ejercicios'],
            'nivel_pronunciacion': progress['nivel_pronunciacion']
        }

    def get_exercises_by_user(self, user_id, limit=None):
        """Obtener ejercicios realizados por el usuario"""
        query = """
                SELECT tipo_ejercicio, \
                       nombre_ejercicio, \
                       puntos_obtenidos,
                       precision_porcentaje, \
                       tiempo_empleado_segundos, \
                       fecha_completado
                FROM ejercicios_realizados
                WHERE usuario_id = %s
                ORDER BY fecha_completado DESC \
                """
        if limit:
            query += f" LIMIT {limit}"

        return self.execute_query(query, (user_id,), fetch='all')

    def get_daily_stats(self, user_id, days=7):
        """Obtener estadísticas diarias de los últimos N días"""
        return self.execute_query("""
                                  SELECT fecha,
                                         ejercicios_completados,
                                         tiempo_estudiado_minutos,
                                         puntos_obtenidos,
                                         precision_promedio
                                  FROM estadisticas_diarias
                                  WHERE usuario_id = %s
                                    AND fecha >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                                  ORDER BY fecha DESC
                                  """, (user_id, days), fetch='all')

    def get_user_achievements(self, user_id):
        """Obtener logros del usuario"""
        return self.execute_query(
            "SELECT * FROM logros WHERE usuario_id = %s ORDER BY fecha_obtenido DESC",
            (user_id,),
            fetch='all'
        )

    def get_progress_levels(self, user_id):
        """Obtener progreso por niveles/módulos"""
        progress = self.get_user_progress(user_id)
        if not progress:
            return {}

        return {
            'lectura': {
                'nivel_actual': progress['nivel_lectura'],
                'progreso_porcentaje': min(75, (progress['ejercicios_completados'] * 5) % 100),
                'puntos_actuales': min(75, progress['ejercicios_completados'] * 3),
                'puntos_necesarios': 100
            },
            'ejercicios': {
                'nivel_actual': progress['nivel_ejercicios'],
                'progreso_porcentaje': min(60, (progress['ejercicios_completados'] * 4) % 100),
                'puntos_actuales': min(60, progress['ejercicios_completados'] * 2),
                'puntos_necesarios': 100
            },
            'pronunciacion': {
                'nivel_actual': progress['nivel_pronunciacion'],
                'progreso_porcentaje': min(30, (progress['ejercicios_completados'] * 2) % 100),
                'puntos_actuales': min(30, progress['ejercicios_completados']),
                'puntos_necesarios': 100
            },
            'juegos': {
                'nivel_actual': max(1, progress['nivel_ejercicios']),
                'progreso_porcentaje': min(85, (progress['ejercicios_completados'] * 6) % 100),
                'puntos_actuales': min(85, progress['ejercicios_completados'] * 4),
                'puntos_necesarios': 100
            }
        }

    # ==================== MÉTODOS DE EJERCICIOS ====================

    def save_exercise_result(self, user_id, exercise_type, exercise_name, points, accuracy, time_seconds,
                             additional_data=None):
        """Guardar resultado de ejercicio"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Insertar ejercicio realizado
                cursor.execute("""
                               INSERT INTO ejercicios_realizados
                               (usuario_id, tipo_ejercicio, nombre_ejercicio, puntos_obtenidos,
                                precision_porcentaje, tiempo_empleado_segundos, datos_adicionales)
                               VALUES (%s, %s, %s, %s, %s, %s, %s)
                               """, (user_id, exercise_type, exercise_name, points, accuracy, time_seconds,
                                     json.dumps(additional_data) if additional_data else None))

                # Llamar procedimiento para actualizar estadísticas
                cursor.callproc('ActualizarEstadisticasUsuario', [user_id, points, accuracy, time_seconds])

                conn.commit()
                cursor.close()

                logger.info(f"✅ Ejercicio guardado: {exercise_name} para usuario {user_id}")
                return True

        except Error as e:
            logger.error(f"❌ Error guardando ejercicio: {e}")
            return False

    def save_vocal_detection(self, user_id, vocal, frequency, detection_time, confidence, exercise_id=None):
        """Guardar detección de vocal"""
        try:
            self.execute_query("""
                               INSERT INTO vocales_detectadas
                               (usuario_id, ejercicio_id, vocal, frecuencia, tiempo_deteccion, confianza)
                               VALUES (%s, %s, %s, %s, %s, %s)
                               """, (user_id, exercise_id, vocal, frequency, detection_time, confidence))
            return True
        except:
            return False

    # ==================== MÉTODOS DE CONFIGURACIÓN ====================

    def get_user_settings(self, user_id):
        """Obtener configuraciones del usuario"""
        result = self.execute_query(
            "SELECT * FROM configuraciones_usuario WHERE usuario_id = %s",
            (user_id,),
            fetch='one'
        )

        if not result:
            # Crear configuración por defecto
            self.execute_query(
                "INSERT INTO configuraciones_usuario (usuario_id) VALUES (%s)",
                (user_id,)
            )
            result = self.execute_query(
                "SELECT * FROM configuraciones_usuario WHERE usuario_id = %s",
                (user_id,),
                fetch='one'
            )

        return result

    def update_user_settings(self, user_id, settings):
        """Actualizar configuraciones del usuario"""
        try:
            # Construir la consulta UPDATE dinámicamente
            set_clauses = []
            values = []

            for key, value in settings.items():
                if key in ['velocidad_lectura', 'dificultad_preferida', 'tema_preferido',
                           'notificaciones_activas', 'sonidos_activos']:
                    set_clauses.append(f"{key} = %s")
                    values.append(value)

            if set_clauses:
                query = f"""
                    UPDATE configuraciones_usuario 
                    SET {', '.join(set_clauses)}, fecha_actualizacion = NOW()
                    WHERE usuario_id = %s
                """
                values.append(user_id)

                self.execute_query(query, values)
                return True

            return False

        except Exception as e:
            logger.error(f"Error actualizando configuraciones: {e}")
            return False


# Instancia global del gestor de base de datos
db_manager = DatabaseManager()