# modules/database_manager.py
import mysql.connector
from mysql.connector import pooling, Error
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from contextlib import contextmanager
import hashlib
import secrets
from dataclasses import dataclass
import bcrypt

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Configuración de la base de datos"""
    host: str
    port: int
    database: str
    user: str
    password: str
    charset: str = 'utf8mb4'
    autocommit: bool = False
    pool_size: int = 10
    pool_name: str = "alfaia_pool"


class DatabaseManager:
    """
    Manager completo para la base de datos de AlfaIA
    Maneja todas las operaciones de usuarios, ejercicios, progreso y analytics
    """

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connection_pool = None
        self._init_connection_pool()

    def _init_connection_pool(self):
        """Inicializar pool de conexiones"""
        try:
            pool_config = {
                'pool_name': self.config.pool_name,
                'pool_size': self.config.pool_size,
                'pool_reset_session': True,
                'host': self.config.host,
                'port': self.config.port,
                'database': self.config.database,
                'user': self.config.user,
                'password': self.config.password,
                'charset': self.config.charset,
                'autocommit': self.config.autocommit,
                'time_zone': '+00:00',
                'sql_mode': 'TRADITIONAL',
                'use_unicode': True,
                'collation': 'utf8mb4_unicode_ci'
            }

            self.connection_pool = pooling.MySQLConnectionPool(**pool_config)
            logger.info("✅ Pool de conexiones inicializado correctamente")

        except Error as e:
            logger.error(f"❌ Error inicializando pool de conexiones: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """Context manager para obtener conexión del pool"""
        connection = None
        try:
            connection = self.connection_pool.get_connection()
            yield connection
        except Error as e:
            if connection and connection.is_connected():
                connection.rollback()
            logger.error(f"❌ Error en operación de base de datos: {e}")
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()

    def execute_query(self, query: str, params: tuple = None, fetch: str = None) -> Any:
        """
        Ejecutar consulta SQL

        Args:
            query: Consulta SQL
            params: Parámetros para la consulta
            fetch: 'one', 'all', 'many' o None

        Returns:
            Resultado de la consulta según el tipo de fetch
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(query, params or ())

                if fetch == 'one':
                    result = cursor.fetchone()
                elif fetch == 'all':
                    result = cursor.fetchall()
                elif fetch == 'many':
                    result = cursor.fetchmany()
                else:
                    # Para INSERT, UPDATE, DELETE
                    result = cursor.lastrowid if cursor.lastrowid else cursor.rowcount

                conn.commit()
                return result

            except Error as e:
                conn.rollback()
                logger.error(f"❌ Error ejecutando consulta: {e}")
                logger.error(f"Query: {query}")
                logger.error(f"Params: {params}")
                raise
            finally:
                cursor.close()

    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Ejecutar consulta con múltiples sets de parámetros"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.executemany(query, params_list)
                conn.commit()
                return cursor.rowcount
            except Error as e:
                conn.rollback()
                logger.error(f"❌ Error ejecutando consulta múltiple: {e}")
                raise
            finally:
                cursor.close()

    # =====================================================
    # MÉTODOS DE USUARIOS
    # =====================================================

    def create_user(self, user_data: Dict[str, Any]) -> int:
        """Crear nuevo usuario"""
        try:
            # Verificar que el usuario no exista
            existing_user = self.execute_query(
                "SELECT id FROM usuarios WHERE username = %s OR email = %s",
                (user_data['username'], user_data['email']),
                fetch='one'
            )

            if existing_user:
                raise ValueError("Usuario o email ya existe")

            # Hash de la contraseña
            password_hash = bcrypt.hashpw(
                user_data['password'].encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')

            # Insertar usuario
            query = """
                INSERT INTO usuarios (username, email, password_hash, nombre, apellido, 
                                    fecha_nacimiento, genero, nivel_educativo, pais, ciudad, telefono)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            user_id = self.execute_query(query, (
                user_data['username'],
                user_data['email'],
                password_hash,
                user_data['nombre'],
                user_data['apellido'],
                user_data.get('fecha_nacimiento'),
                user_data.get('genero'),
                user_data.get('nivel_educativo'),
                user_data.get('pais'),
                user_data.get('ciudad'),
                user_data.get('telefono')
            ))

            # Crear perfil de usuario
            self.create_user_profile(user_id, user_data.get('profile_data', {}))

            logger.info(f"✅ Usuario creado: {user_data['username']} (ID: {user_id})")
            return user_id

        except Exception as e:
            logger.error(f"❌ Error creando usuario: {e}")
            raise

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Autenticar usuario"""
        try:
            query = """
                SELECT id, username, email, password_hash, nombre, apellido, activo
                FROM usuarios 
                WHERE (username = %s OR email = %s) AND activo = TRUE
            """

            user = self.execute_query(query, (username, username), fetch='one')

            if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                # Actualizar última conexión
                self.execute_query(
                    "UPDATE usuarios SET ultima_conexion = NOW() WHERE id = %s",
                    (user['id'],)
                )

                # Remover password_hash del resultado
                del user['password_hash']

                logger.info(f"✅ Usuario autenticado: {username}")
                return user

            logger.warning(f"⚠️ Intento de autenticación fallido: {username}")
            return None

        except Exception as e:
            logger.error(f"❌ Error autenticando usuario: {e}")
            raise

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Obtener usuario por ID"""
        try:
            query = """
                SELECT u.id, u.username, u.email, u.nombre, u.apellido, u.fecha_nacimiento,
                       u.genero, u.nivel_educativo, u.pais, u.ciudad, u.telefono, u.activo,
                       u.fecha_registro, u.ultima_conexion,
                       p.nivel_lectura, p.nivel_escritura, p.nivel_pronunciacion,
                       p.puntos_totales, p.precision_promedio, p.racha_dias_consecutivos,
                       p.ejercicios_completados, p.tiempo_total_minutos, p.objetivo_diario_minutos,
                       p.objetivo_diario_ejercicios, p.estilo_aprendizaje
                FROM usuarios u
                LEFT JOIN perfiles_usuario p ON u.id = p.user_id
                WHERE u.id = %s AND u.activo = TRUE
            """

            user = self.execute_query(query, (user_id,), fetch='one')
            return user

        except Exception as e:
            logger.error(f"❌ Error obteniendo usuario {user_id}: {e}")
            raise

    def create_user_profile(self, user_id: int, profile_data: Dict[str, Any]) -> bool:
        """Crear perfil de usuario"""
        try:
            query = """
                INSERT INTO perfiles_usuario (
                    user_id, objetivo_diario_minutos, objetivo_diario_ejercicios,
                    estilo_aprendizaje, preferencias_json, configuracion_json
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """

            preferencias = json.dumps(profile_data.get('preferencias', {}))
            configuracion = json.dumps(profile_data.get('configuracion', {}))

            self.execute_query(query, (
                user_id,
                profile_data.get('objetivo_diario_minutos', 30),
                profile_data.get('objetivo_diario_ejercicios', 5),
                profile_data.get('estilo_aprendizaje', 'mixto'),
                preferencias,
                configuracion
            ))

            logger.info(f"✅ Perfil creado para usuario {user_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error creando perfil para usuario {user_id}: {e}")
            raise

    def update_user_profile(self, user_id: int, profile_data: Dict[str, Any]) -> bool:
        """Actualizar perfil de usuario"""
        try:
            # Construir query dinámicamente
            fields = []
            values = []

            allowed_fields = [
                'nivel_lectura', 'nivel_escritura', 'nivel_pronunciacion',
                'objetivo_diario_minutos', 'objetivo_diario_ejercicios',
                'estilo_aprendizaje', 'preferencias_json', 'configuracion_json'
            ]

            for field in allowed_fields:
                if field in profile_data:
                    fields.append(f"{field} = %s")
                    if field.endswith('_json'):
                        values.append(json.dumps(profile_data[field]))
                    else:
                        values.append(profile_data[field])

            if not fields:
                return True

            fields.append("fecha_actualizacion = NOW()")
            values.append(user_id)

            query = f"""
                UPDATE perfiles_usuario 
                SET {', '.join(fields)}
                WHERE user_id = %s
            """

            self.execute_query(query, tuple(values))

            logger.info(f"✅ Perfil actualizado para usuario {user_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error actualizando perfil para usuario {user_id}: {e}")
            raise

    # =====================================================
    # MÉTODOS DE CATEGORÍAS Y CONTENIDO
    # =====================================================

    def get_categories(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Obtener categorías disponibles"""
        try:
            where_condition = "WHERE activa = TRUE" if active_only else ""

            query = f"""
                SELECT id, nombre, descripcion, icono, color, nivel_minimo, nivel_maximo,
                       orden_visualizacion, palabras_clave, metadatos_json
                FROM categorias
                {where_condition}
                ORDER BY orden_visualizacion, nombre
            """

            categories = self.execute_query(query, fetch='all')

            # Parsear campos JSON
            for category in categories:
                category['palabras_clave'] = json.loads(category['palabras_clave'] or '[]')
                category['metadatos'] = json.loads(category['metadatos_json'] or '{}')
                del category['metadatos_json']

            return categories

        except Exception as e:
            logger.error(f"❌ Error obteniendo categorías: {e}")
            raise

    def get_content_by_criteria(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Obtener contenidos por criterios"""
        try:
            where_conditions = ["ct.activo = TRUE"]
            params = []

            if 'categoria_id' in criteria:
                where_conditions.append("ct.categoria_id = %s")
                params.append(criteria['categoria_id'])

            if 'nivel' in criteria:
                where_conditions.append("ct.nivel = %s")
                params.append(criteria['nivel'])

            if 'tipo_contenido' in criteria:
                where_conditions.append("ct.tipo_contenido = %s")
                params.append(criteria['tipo_contenido'])

            if 'min_longitud' in criteria:
                where_conditions.append("ct.longitud_palabras >= %s")
                params.append(criteria['min_longitud'])

            if 'max_longitud' in criteria:
                where_conditions.append("ct.longitud_palabras <= %s")
                params.append(criteria['max_longitud'])

            limit = criteria.get('limit', 10)
            order_by = criteria.get('order_by', 'ct.veces_usado ASC, RAND()')

            query = f"""
                SELECT ct.*, c.nombre as categoria_nombre
                FROM contenidos_texto ct
                LEFT JOIN categorias c ON ct.categoria_id = c.id
                WHERE {' AND '.join(where_conditions)}
                ORDER BY {order_by}
                LIMIT %s
            """

            params.append(limit)
            contents = self.execute_query(query, tuple(params), fetch='all')

            # Parsear campos JSON
            for content in contents:
                content['palabras_clave'] = json.loads(content['palabras_clave'] or '[]')
                content['temas'] = json.loads(content['temas'] or '[]')
                content['metadatos_contenido'] = json.loads(content['metadatos_contenido'] or '{}')

            return contents

        except Exception as e:
            logger.error(f"❌ Error obteniendo contenidos: {e}")
            raise

    def get_questions_by_content(self, content_id: int) -> List[Dict[str, Any]]:
        """Obtener preguntas de un contenido específico"""
        try:
            query = """
                SELECT p.*, GROUP_CONCAT(
                    CONCAT(o.id, ':', o.texto_opcion, ':', o.es_correcta, ':', o.orden_opcion)
                    ORDER BY o.orden_opcion SEPARATOR '||'
                ) as opciones_data
                FROM preguntas p
                LEFT JOIN opciones_respuesta o ON p.id = o.pregunta_id
                WHERE p.contenido_id = %s AND p.activa = TRUE
                GROUP BY p.id
                ORDER BY p.orden_en_contenido
            """

            questions = self.execute_query(query, (content_id,), fetch='all')

            # Procesar opciones
            for question in questions:
                opciones = []
                if question['opciones_data']:
                    for opcion_str in question['opciones_data'].split('||'):
                        parts = opcion_str.split(':')
                        if len(parts) >= 4:
                            opciones.append({
                                'id': int(parts[0]),
                                'texto': parts[1],
                                'es_correcta': parts[2] == '1',
                                'orden': int(parts[3])
                            })

                question['opciones'] = opciones
                question['respuesta_correcta'] = next(
                    (i for i, op in enumerate(opciones) if op['es_correcta']), 0
                )
                del question['opciones_data']

            return questions

        except Exception as e:
            logger.error(f"❌ Error obteniendo preguntas para contenido {content_id}: {e}")
            raise

    def create_content(self, content_data: Dict[str, Any]) -> int:
        """Crear nuevo contenido de texto"""
        try:
            # Calcular métricas del contenido
            content_data['longitud_palabras'] = len(content_data['contenido'].split())
            content_data['tiempo_estimado_segundos'] = self._calculate_reading_time(content_data['contenido'])

            query = """
                INSERT INTO contenidos_texto (
                    titulo, contenido, categoria_id, nivel, tipo_contenido,
                    longitud_palabras, tiempo_estimado_segundos, palabras_clave,
                    temas, edad_recomendada_min, edad_recomendada_max,
                    autor, fuente, licencia
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            content_id = self.execute_query(query, (
                content_data['titulo'],
                content_data['contenido'],
                content_data.get('categoria_id'),
                content_data['nivel'],
                content_data.get('tipo_contenido', 'cuento'),
                content_data['longitud_palabras'],
                content_data['tiempo_estimado_segundos'],
                json.dumps(content_data.get('palabras_clave', [])),
                json.dumps(content_data.get('temas', [])),
                content_data.get('edad_recomendada_min', 6),
                content_data.get('edad_recomendada_max', 99),
                content_data.get('autor'),
                content_data.get('fuente'),
                content_data.get('licencia', 'uso_educativo')
            ))

            logger.info(f"✅ Contenido creado: {content_data['titulo']} (ID: {content_id})")
            return content_id

        except Exception as e:
            logger.error(f"❌ Error creando contenido: {e}")
            raise

    # =====================================================
    # MÉTODOS DE EJERCICIOS
    # =====================================================

    def create_exercise(self, exercise_data: Dict[str, Any]) -> int:
        """Crear nuevo ejercicio"""
        try:
            # Generar código único
            codigo_ejercicio = self._generate_exercise_code(exercise_data['tipo_ejercicio'])

            query = """
                INSERT INTO ejercicios (
                    codigo_ejercicio, tipo_ejercicio, nombre, descripcion, contenido_id,
                    categoria_id, nivel, configuracion_json, datos_ejercicio, puntos_base,
                    tiempo_limite_segundos, intentos_maximos, requiere_microfono,
                    requiere_teclado, instrucciones, consejos_json, creado_por
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            exercise_id = self.execute_query(query, (
                codigo_ejercicio,
                exercise_data['tipo_ejercicio'],
                exercise_data['nombre'],
                exercise_data.get('descripcion'),
                exercise_data.get('contenido_id'),
                exercise_data.get('categoria_id'),
                exercise_data['nivel'],
                json.dumps(exercise_data.get('configuracion', {})),
                json.dumps(exercise_data.get('datos_ejercicio', {})),
                exercise_data.get('puntos_base', 50),
                exercise_data.get('tiempo_limite_segundos', 300),
                exercise_data.get('intentos_maximos', 3),
                exercise_data.get('requiere_microfono', False),
                exercise_data.get('requiere_teclado', True),
                exercise_data.get('instrucciones'),
                json.dumps(exercise_data.get('consejos', [])),
                exercise_data.get('creado_por')
            ))

            logger.info(f"✅ Ejercicio creado: {codigo_ejercicio} (ID: {exercise_id})")
            return exercise_id

        except Exception as e:
            logger.error(f"❌ Error creando ejercicio: {e}")
            raise

    def get_exercise_by_criteria(self, criteria: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Obtener ejercicio por criterios específicos"""
        try:
            where_conditions = ["e.activo = TRUE"]
            params = []

            if 'tipo_ejercicio' in criteria:
                where_conditions.append("e.tipo_ejercicio = %s")
                params.append(criteria['tipo_ejercicio'])

            if 'nivel' in criteria:
                where_conditions.append("e.nivel = %s")
                params.append(criteria['nivel'])

            if 'categoria_id' in criteria:
                where_conditions.append("e.categoria_id = %s")
                params.append(criteria['categoria_id'])

            if 'exclude_completed_by_user' in criteria:
                where_conditions.append("""
                    e.id NOT IN (
                        SELECT DISTINCT ejercicio_id 
                        FROM resultados_ejercicios 
                        WHERE user_id = %s AND completado = TRUE
                    )
                """)
                params.append(criteria['exclude_completed_by_user'])

            order_by = criteria.get('order_by', 'RAND()')

            query = f"""
                SELECT e.*, c.nombre as categoria_nombre, ct.titulo as contenido_titulo
                FROM ejercicios e
                LEFT JOIN categorias c ON e.categoria_id = c.id
                LEFT JOIN contenidos_texto ct ON e.contenido_id = ct.id
                WHERE {' AND '.join(where_conditions)}
                ORDER BY {order_by}
                LIMIT 1
            """

            exercise = self.execute_query(query, tuple(params), fetch='one')

            if exercise:
                # Parsear campos JSON
                exercise['configuracion'] = json.loads(exercise['configuracion_json'] or '{}')
                exercise['datos_ejercicio'] = json.loads(exercise['datos_ejercicio'] or '{}')
                exercise['consejos'] = json.loads(exercise['consejos_json'] or '[]')

            return exercise

        except Exception as e:
            logger.error(f"❌ Error obteniendo ejercicio por criterios: {e}")
            raise

    # =====================================================
    # MÉTODOS DE RESULTADOS
    # =====================================================

    def save_exercise_result(self, result_data: Dict[str, Any]) -> int:
        """Guardar resultado de ejercicio"""
        try:
            # Generar ID de sesión si no existe
            sesion_id = result_data.get('sesion_id', self._generate_session_id())

            query = """
                INSERT INTO resultados_ejercicios (
                    user_id, ejercicio_id, sesion_id, intento_numero, fecha_inicio,
                    fecha_finalizacion, tiempo_empleado_segundos, precision_porcentaje,
                    puntos_obtenidos, puntos_bonus, completado, respuestas_json,
                    metricas_detalladas, errores_cometidos, dispositivo_usado,
                    navegador, ip_address, metadatos_sesion
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            result_id = self.execute_query(query, (
                result_data['user_id'],
                result_data['ejercicio_id'],
                sesion_id,
                result_data.get('intento_numero', 1),
                result_data.get('fecha_inicio', datetime.now()),
                result_data.get('fecha_finalizacion', datetime.now()),
                result_data.get('tiempo_empleado_segundos', 0),
                result_data.get('precision_porcentaje', 0.0),
                result_data.get('puntos_obtenidos', 0),
                result_data.get('puntos_bonus', 0),
                result_data.get('completado', True),
                json.dumps(result_data.get('respuestas', {})),
                json.dumps(result_data.get('metricas_detalladas', {})),
                json.dumps(result_data.get('errores_cometidos', [])),
                result_data.get('dispositivo_usado'),
                result_data.get('navegador'),
                result_data.get('ip_address'),
                json.dumps(result_data.get('metadatos_sesion', {}))
            ))

            # Guardar respuestas detalladas si existen
            if 'respuestas_detalladas' in result_data:
                self._save_detailed_answers(result_id, result_data['respuestas_detalladas'])

            logger.info(f"✅ Resultado guardado: {result_id} para usuario {result_data['user_id']}")
            return result_id

        except Exception as e:
            logger.error(f"❌ Error guardando resultado de ejercicio: {e}")
            raise

    def _save_detailed_answers(self, result_id: int, detailed_answers: List[Dict[str, Any]]):
        """Guardar respuestas detalladas"""
        try:
            query = """
                INSERT INTO respuestas_detalladas (
                    resultado_id, pregunta_id, opcion_seleccionada_id, respuesta_texto,
                    es_correcta, tiempo_respuesta_segundos, intentos_pregunta,
                    puntos_pregunta, dificultad_percibida, confianza_respuesta,
                    metadatos_respuesta
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            params_list = []
            for answer in detailed_answers:
                params_list.append((
                    result_id,
                    answer.get('pregunta_id'),
                    answer.get('opcion_seleccionada_id'),
                    answer.get('respuesta_texto'),
                    answer.get('es_correcta', False),
                    answer.get('tiempo_respuesta_segundos', 0),
                    answer.get('intentos_pregunta', 1),
                    answer.get('puntos_pregunta', 0),
                    answer.get('dificultad_percibida'),
                    answer.get('confianza_respuesta'),
                    json.dumps(answer.get('metadatos', {}))
                ))

            if params_list:
                self.execute_many(query, params_list)

        except Exception as e:
            logger.error(f"❌ Error guardando respuestas detalladas: {e}")
            raise

    def get_user_exercise_history(self, user_id: int, tipo_ejercicio: str = None,
                                  limit: int = 50) -> List[Dict[str, Any]]:
        """Obtener historial de ejercicios del usuario"""
        try:
            where_conditions = ["r.user_id = %s"]
            params = [user_id]

            if tipo_ejercicio:
                where_conditions.append("e.tipo_ejercicio = %s")
                params.append(tipo_ejercicio)

            query = f"""
                SELECT r.*, e.nombre as ejercicio_nombre, e.tipo_ejercicio, e.nivel,
                       c.nombre as categoria_nombre
                FROM resultados_ejercicios r
                JOIN ejercicios e ON r.ejercicio_id = e.id
                WHERE r.user_id = %s
                AND r.fecha_inicio >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            """

            summary = self.execute_query(query, (user_id,), fetch='one')

            # Obtener logros desbloqueados
            logros_query = """
                SELECT COUNT(*) as total_logros, 
                       COALESCE(SUM(l.puntos_recompensa), 0) as puntos_logros
                FROM logros_desbloqueados ld
                JOIN logros l ON ld.logro_id = l.id
                WHERE ld.user_id = %s
            """

            logros_data = self.execute_query(logros_query, (user_id,), fetch='one')

            # Combinar datos
            if summary:
                summary.update(logros_data or {})
            else:
                summary = logros_data or {}

            return summary

        except Exception as e:
            logger.error(f"❌ Error obteniendo resumen de progreso: {e}")
            raise

    def get_user_progress_by_type(self, user_id: int) -> Dict[str, Dict[str, Any]]:
        """Obtener progreso del usuario por tipo de ejercicio"""
        try:
            query = """
                SELECT 
                    tipo_ejercicio,
                    nivel_actual,
                    ejercicios_completados,
                    tiempo_total_segundos,
                    precision_promedio,
                    mejor_precision,
                    racha_aciertos_consecutivos,
                    puntos_categoria,
                    ultima_actividad
                FROM progreso_usuario
                WHERE user_id = %s
            """

            results = self.execute_query(query, (user_id,), fetch='all')

            # Organizar por tipo de ejercicio
            progress_by_type = {}
            for result in results:
                tipo = result['tipo_ejercicio']
                progress_by_type[tipo] = result

            return progress_by_type

        except Exception as e:
            logger.error(f"❌ Error obteniendo progreso por tipo: {e}")
            raise

    def update_user_progress(self, user_id: int, exercise_result: Dict[str, Any]):
        """Actualizar progreso del usuario después de completar ejercicio"""
        try:
            # Usar procedimiento almacenado si existe, sino lógica manual
            with self.get_connection() as conn:
                cursor = conn.cursor()
                try:
                    cursor.callproc('sp_actualizar_perfil_usuario', [user_id])
                    conn.commit()
                except Error:
                    # Si no existe el procedimiento, usar lógica manual
                    self._manual_progress_update(user_id, exercise_result)
                finally:
                    cursor.close()

            logger.info(f"✅ Progreso actualizado para usuario {user_id}")

        except Exception as e:
            logger.error(f"❌ Error actualizando progreso: {e}")
            raise

    def _manual_progress_update(self, user_id: int, exercise_result: Dict[str, Any]):
        """Actualización manual de progreso"""
        try:
            # Calcular estadísticas generales
            stats_query = """
                SELECT 
                    COUNT(CASE WHEN completado = TRUE THEN 1 END) as total_ejercicios,
                    COALESCE(AVG(CASE WHEN completado = TRUE THEN precision_porcentaje END), 0) as precision_promedio,
                    COALESCE(SUM(CASE WHEN completado = TRUE THEN puntos_obtenidos + puntos_bonus END), 0) as puntos_totales,
                    COALESCE(SUM(CASE WHEN completado = TRUE THEN tiempo_empleado_segundos END), 0) as tiempo_total
                FROM resultados_ejercicios
                WHERE user_id = %s
            """

            stats = self.execute_query(stats_query, (user_id,), fetch='one')

            # Actualizar perfil general
            update_profile_query = """
                UPDATE perfiles_usuario 
                SET 
                    ejercicios_completados = %s,
                    precision_promedio = %s,
                    puntos_totales = %s,
                    tiempo_total_minutos = %s,
                    fecha_actualizacion = NOW()
                WHERE user_id = %s
            """

            self.execute_query(update_profile_query, (
                stats['total_ejercicios'],
                stats['precision_promedio'],
                stats['puntos_totales'],
                round(stats['tiempo_total'] / 60),
                user_id
            ))

            # Actualizar progreso específico por tipo de ejercicio
            self._update_progress_by_exercise_type(user_id, exercise_result)

        except Exception as e:
            logger.error(f"❌ Error en actualización manual de progreso: {e}")
            raise

    def _update_progress_by_exercise_type(self, user_id: int, exercise_result: Dict[str, Any]):
        """Actualizar progreso específico por tipo de ejercicio"""
        try:
            tipo_ejercicio = exercise_result.get('tipo_ejercicio')
            categoria_id = exercise_result.get('categoria_id')

            if not tipo_ejercicio:
                return

            # Obtener estadísticas del tipo específico
            tipo_stats_query = """
                SELECT 
                    COUNT(CASE WHEN r.completado = TRUE THEN 1 END) as ejercicios_completados,
                    COALESCE(AVG(CASE WHEN r.completado = TRUE THEN r.precision_porcentaje END), 0) as precision_promedio,
                    COALESCE(MAX(CASE WHEN r.completado = TRUE THEN r.precision_porcentaje END), 0) as mejor_precision,
                    COALESCE(SUM(CASE WHEN r.completado = TRUE THEN r.tiempo_empleado_segundos END), 0) as tiempo_total,
                    COALESCE(SUM(CASE WHEN r.completado = TRUE THEN r.puntos_obtenidos END), 0) as puntos_categoria
                FROM resultados_ejercicios r
                JOIN ejercicios e ON r.ejercicio_id = e.id
                WHERE r.user_id = %s AND e.tipo_ejercicio = %s
            """

            params = [user_id, tipo_ejercicio]
            if categoria_id:
                tipo_stats_query += " AND e.categoria_id = %s"
                params.append(categoria_id)

            tipo_stats = self.execute_query(tipo_stats_query, tuple(params), fetch='one')

            # Calcular nivel recomendado
            nivel_actual = self._calculate_recommended_level(user_id, tipo_ejercicio)

            # Insertar o actualizar progreso
            progress_query = """
                INSERT INTO progreso_usuario (
                    user_id, tipo_ejercicio, categoria_id, nivel_actual,
                    ejercicios_completados, tiempo_total_segundos, precision_promedio,
                    mejor_precision, puntos_categoria, ultima_actividad
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE
                    nivel_actual = VALUES(nivel_actual),
                    ejercicios_completados = VALUES(ejercicios_completados),
                    tiempo_total_segundos = VALUES(tiempo_total_segundos),
                    precision_promedio = VALUES(precision_promedio),
                    mejor_precision = VALUES(mejor_precision),
                    puntos_categoria = VALUES(puntos_categoria),
                    ultima_actividad = NOW(),
                    fecha_actualizacion = NOW()
            """

            self.execute_query(progress_query, (
                user_id,
                tipo_ejercicio,
                categoria_id,
                nivel_actual,
                tipo_stats['ejercicios_completados'],
                tipo_stats['tiempo_total'],
                tipo_stats['precision_promedio'],
                tipo_stats['mejor_precision'],
                tipo_stats['puntos_categoria']
            ))

        except Exception as e:
            logger.error(f"❌ Error actualizando progreso por tipo de ejercicio: {e}")
            raise

    def _calculate_recommended_level(self, user_id: int, tipo_ejercicio: str) -> int:
        """Calcular nivel recomendado basado en el rendimiento reciente"""
        try:
            # Obtener precisiones recientes (últimos 5 ejercicios)
            recent_query = """
                SELECT r.precision_porcentaje, e.nivel
                FROM resultados_ejercicios r
                JOIN ejercicios e ON r.ejercicio_id = e.id
                WHERE r.user_id = %s 
                AND e.tipo_ejercicio = %s
                AND r.completado = TRUE
                ORDER BY r.fecha_inicio DESC
                LIMIT 5
            """

            recent_results = self.execute_query(recent_query, (user_id, tipo_ejercicio), fetch='all')

            if not recent_results:
                return 1

            nivel_actual = max(result['nivel'] for result in recent_results)
            precision_promedio = sum(result['precision_porcentaje'] for result in recent_results) / len(recent_results)

            # Lógica de recomendación
            if precision_promedio >= 85 and len(recent_results) >= 3:
                return min(nivel_actual + 1, 5)  # Subir nivel
            elif precision_promedio < 60:
                return max(nivel_actual - 1, 1)  # Bajar nivel
            else:
                return nivel_actual  # Mantener nivel

        except Exception as e:
            logger.error(f"❌ Error calculando nivel recomendado: {e}")
            return 1

    def get_learning_analytics(self, user_id: int, days_back: int = 30) -> Dict[str, Any]:
        """Obtener analytics detallados del aprendizaje del usuario"""
        try:
            # Análisis de patrones de aprendizaje
            patterns_query = """
                SELECT 
                    HOUR(fecha_inicio) as hora_dia,
                    DAYOFWEEK(fecha_inicio) as dia_semana,
                    AVG(precision_porcentaje) as precision_promedio,
                    COUNT(*) as ejercicios_realizados,
                    AVG(tiempo_empleado_segundos) as tiempo_promedio
                FROM resultados_ejercicios
                WHERE user_id = %s 
                AND completado = TRUE
                AND fecha_inicio >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY HOUR(fecha_inicio), DAYOFWEEK(fecha_inicio)
                ORDER BY precision_promedio DESC
            """

            patterns = self.execute_query(patterns_query, (user_id, days_back), fetch='all')

            # Análisis de dificultades por tipo de pregunta
            difficulties_query = """
                SELECT 
                    p.tipo_pregunta,
                    COUNT(*) as total_preguntas,
                    SUM(CASE WHEN rd.es_correcta = TRUE THEN 1 ELSE 0 END) as respuestas_correctas,
                    AVG(rd.tiempo_respuesta_segundos) as tiempo_promedio_respuesta,
                    AVG(CASE WHEN rd.es_correcta = TRUE THEN 100 ELSE 0 END) as porcentaje_acierto
                FROM respuestas_detalladas rd
                JOIN resultados_ejercicios r ON rd.resultado_id = r.id
                JOIN preguntas p ON rd.pregunta_id = p.id
                WHERE r.user_id = %s
                AND r.fecha_inicio >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY p.tipo_pregunta
                ORDER BY porcentaje_acierto ASC
            """

            difficulties = self.execute_query(difficulties_query, (user_id, days_back), fetch='all')

            # Evolución temporal del rendimiento
            evolution_query = """
                SELECT 
                    DATE(fecha_inicio) as fecha,
                    AVG(precision_porcentaje) as precision_dia,
                    COUNT(*) as ejercicios_dia,
                    SUM(tiempo_empleado_segundos) as tiempo_total_dia
                FROM resultados_ejercicios
                WHERE user_id = %s 
                AND completado = TRUE
                AND fecha_inicio >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY DATE(fecha_inicio)
                ORDER BY fecha ASC
            """

            evolution = self.execute_query(evolution_query, (user_id, days_back), fetch='all')

            # Análisis de streaks y constancia
            streak_data = self._calculate_learning_streaks(user_id)

            return {
                'learning_patterns': patterns,
                'difficulty_analysis': difficulties,
                'performance_evolution': evolution,
                'streak_analysis': streak_data,
                'generated_at': datetime.now().isoformat(),
                'period_days': days_back
            }

        except Exception as e:
            logger.error(f"❌ Error obteniendo analytics de aprendizaje: {e}")
            raise

    def _calculate_learning_streaks(self, user_id: int) -> Dict[str, Any]:
        """Calcular rachas de aprendizaje del usuario"""
        try:
            # Obtener días únicos con actividad
            activity_query = """
                SELECT DISTINCT DATE(fecha_inicio) as fecha_actividad
                FROM resultados_ejercicios
                WHERE user_id = %s AND completado = TRUE
                ORDER BY fecha_actividad DESC
            """

            activity_dates = self.execute_query(activity_query, (user_id,), fetch='all')

            if not activity_dates:
                return {
                    'current_streak': 0,
                    'longest_streak': 0,
                    'total_active_days': 0,
                    'last_activity': None
                }

            # Convertir a lista de fechas
            dates = [row['fecha_actividad'] for row in activity_dates]

            # Calcular racha actual
            current_streak = 0
            today = datetime.now().date()

            for i, date in enumerate(dates):
                expected_date = today - timedelta(days=i)
                if date == expected_date:
                    current_streak += 1
                else:
                    break

            # Calcular racha más larga
            longest_streak = 1
            current_temp_streak = 1

            for i in range(1, len(dates)):
                if dates[i - 1] - dates[i] == timedelta(days=1):
                    current_temp_streak += 1
                    longest_streak = max(longest_streak, current_temp_streak)
                else:
                    current_temp_streak = 1

            return {
                'current_streak': current_streak,
                'longest_streak': longest_streak,
                'total_active_days': len(dates),
                'last_activity': dates[0].isoformat() if dates else None
            }

        except Exception as e:
            logger.error(f"❌ Error calculando rachas de aprendizaje: {e}")
            return {
                'current_streak': 0,
                'longest_streak': 0,
                'total_active_days': 0,
                'last_activity': None
            }

    def generate_progress_report(self, user_id: int, report_type: str = 'weekly') -> Dict[str, Any]:
        """Generar reporte completo de progreso"""
        try:
            # Determinar periodo basado en tipo de reporte
            days_back = {
                'daily': 1,
                'weekly': 7,
                'monthly': 30,
                'quarterly': 90
            }.get(report_type, 7)

            # Obtener datos base
            user_data = self.get_user_by_id(user_id)
            progress_summary = self.get_user_progress_summary(user_id)
            progress_by_type = self.get_user_progress_by_type(user_id)
            achievements = self.get_user_achievements(user_id)
            analytics = self.get_learning_analytics(user_id, days_back)

            # Calcular insights y recomendaciones
            insights = self._generate_progress_insights(progress_summary, analytics)
            recommendations = self._generate_personalized_recommendations(user_id, analytics)

            # Generar metas sugeridas
            suggested_goals = self._generate_suggested_goals(user_id, progress_summary)

            return {
                'report_type': report_type,
                'period_days': days_back,
                'user_info': {
                    'id': user_data['id'],
                    'username': user_data['username'],
                    'nombre_completo': f"{user_data['nombre']} {user_data['apellido']}"
                },
                'summary': progress_summary,
                'progress_by_type': progress_by_type,
                'achievements': achievements,
                'analytics': analytics,
                'insights': insights,
                'recommendations': recommendations,
                'suggested_goals': suggested_goals,
                'generated_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Error generando reporte de progreso: {e}")
            raise

    def _generate_progress_insights(self, progress_summary: Dict[str, Any],
                                    analytics: Dict[str, Any]) -> List[str]:
        """Generar insights automáticos del progreso"""
        insights = []

        try:
            # Análisis de precisión
            precision = progress_summary.get('precision_promedio', 0)
            if precision >= 90:
                insights.append("Tienes una precisión excepcional. ¡Eres muy consistente!")
            elif precision >= 75:
                insights.append("Tu precisión es buena. Sigue manteniendo este nivel.")
            elif precision >= 60:
                insights.append("Tu precisión está mejorando. Continúa practicando regularmente.")
            else:
                insights.append("Hay oportunidades de mejora en precisión. Tómate más tiempo en cada ejercicio.")

            # Análisis de constancia
            streak_data = analytics.get('streak_analysis', {})
            current_streak = streak_data.get('current_streak', 0)

            if current_streak >= 7:
                insights.append(f"¡Increíble! Llevas {current_streak} días de práctica consecutiva.")
            elif current_streak >= 3:
                insights.append(f"Buen ritmo con {current_streak} días consecutivos. Sigue así.")
            else:
                insights.append("Intenta establecer una rutina diaria de práctica.")

            # Análisis de dificultades
            difficulties = analytics.get('difficulty_analysis', [])
            if difficulties:
                most_difficult = min(difficulties, key=lambda x: x['porcentaje_acierto'])
                if most_difficult['porcentaje_acierto'] < 60:
                    insights.append(f"Las preguntas de tipo '{most_difficult['tipo_pregunta']}' son tu mayor desafío.")

            # Análisis de patrones de aprendizaje
            patterns = analytics.get('learning_patterns', [])
            if patterns:
                best_pattern = max(patterns, key=lambda x: x['precision_promedio'])
                insights.append(f"Rindes mejor durante las {best_pattern['hora_dia']}:00 horas.")

        except Exception as e:
            logger.error(f"❌ Error generando insights: {e}")
            insights.append("Continúa practicando para obtener más insights personalizados.")

        return insights[:5]  # Máximo 5 insights

    def _generate_personalized_recommendations(self, user_id: int, analytics: Dict[str, Any]) -> List[str]:
        """Generar recomendaciones personalizadas"""
        recommendations = []

        try:
            # Recomendaciones basadas en dificultades
            difficulties = analytics.get('difficulty_analysis', [])
            if difficulties:
                most_difficult = min(difficulties, key=lambda x: x['porcentaje_acierto'])
                if most_difficult['porcentaje_acierto'] < 70:
                    recommendations.append(
                        f"Practica más ejercicios que incluyan preguntas {most_difficult['tipo_pregunta']}")

            # Recomendaciones basadas en patrones temporales
            patterns = analytics.get('learning_patterns', [])
            if patterns:
                best_hour = max(patterns, key=lambda x: x['precision_promedio'])['hora_dia']
                recommendations.append(f"Programa tus sesiones de estudio alrededor de las {best_hour}:00")

            # Recomendaciones basadas en streaks
            streak_data = analytics.get('streak_analysis', {})
            if streak_data.get('current_streak', 0) < 3:
                recommendations.append("Establece recordatorios diarios para mantener constancia")

            # Recomendaciones basadas en progreso general
            evolution = analytics.get('performance_evolution', [])
            if len(evolution) > 1:
                recent_trend = evolution[-3:] if len(evolution) >= 3 else evolution
                avg_recent = sum(day['precision_dia'] for day in recent_trend) / len(recent_trend)

                if len(evolution) > 3:
                    earlier_trend = evolution[-6:-3] if len(evolution) >= 6 else evolution[:-3]
                    avg_earlier = sum(day['precision_dia'] for day in earlier_trend) / len(earlier_trend)

                    if avg_recent > avg_earlier + 5:
                        recommendations.append("¡Vas por buen camino! Tu rendimiento está mejorando")
                    elif avg_recent < avg_earlier - 5:
                        recommendations.append("Considera tomar un breve descanso y volver con energía renovada")

        except Exception as e:
            logger.error(f"❌ Error generando recomendaciones: {e}")
            recommendations.append("Continúa practicando regularmente para mejorar tus habilidades")

        return recommendations[:4]  # Máximo 4 recomendaciones

    def _generate_suggested_goals(self, user_id: int, progress_summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generar metas sugeridas para el usuario"""
        goals = []

        try:
            current_precision = progress_summary.get('precision_promedio', 0)
            current_exercises = progress_summary.get('ejercicios_completados', 0)

            # Meta de precisión
            if current_precision < 80:
                target_precision = min(current_precision + 10, 85)
                goals.append({
                    'type': 'precision',
                    'title': f'Alcanzar {target_precision}% de precisión',
                    'description': 'Mejora tu precisión promedio en ejercicios',
                    'target_value': target_precision,
                    'current_value': current_precision,
                    'difficulty': 'medium'
                })

            # Meta de ejercicios
            weekly_target = max(7, current_exercises // 4)  # Al menos 7 por semana
            goals.append({
                'type': 'consistency',
                'title': f'Completar {weekly_target} ejercicios esta semana',
                'description': 'Mantén una práctica constante',
                'target_value': weekly_target,
                'current_value': 0,  # Se resetea semanalmente
                'difficulty': 'easy'
            })

            # Meta de racha
            goals.append({
                'type': 'streak',
                'title': 'Practicar 5 días consecutivos',
                'description': 'Establece una rutina de estudio diaria',
                'target_value': 5,
                'current_value': 0,  # Se calcula dinámicamente
                'difficulty': 'medium'
            })

            # Meta de exploración
            goals.append({
                'type': 'exploration',
                'title': 'Probar 3 tipos de ejercicios diferentes',
                'description': 'Diversifica tu aprendizaje explorando nuevos ejercicios',
                'target_value': 3,
                'current_value': 0,  # Se calcula dinámicamente
                'difficulty': 'easy'
            })

        except Exception as e:
            logger.error(f"❌ Error generando metas sugeridas: {e}")

        return goals

    # =====================================================
    # MÉTODOS DE LOGROS
    # =====================================================

    def check_and_unlock_achievements(self, user_id: int) -> List[Dict[str, Any]]:
        """Verificar y desbloquear logros"""
        try:
            # Ejecutar procedimiento almacenado si existe
            with self.get_connection() as conn:
                cursor = conn.cursor()
                try:
                    cursor.callproc('sp_verificar_logros', [user_id])
                    conn.commit()
                except Error:
                    # Si no existe el procedimiento, usar lógica manual
                    self._manual_achievement_check(user_id)
                finally:
                    cursor.close()

            # Obtener logros recién desbloqueados (últimas 24 horas)
            query = """
                SELECT ld.*, l.nombre, l.descripcion, l.puntos_recompensa, l.icono
                FROM logros_desbloqueados ld
                JOIN logros l ON ld.logro_id = l.id
                WHERE ld.user_id = %s 
                AND ld.fecha_desbloqueo >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                ORDER BY ld.fecha_desbloqueo DESC
            """

            new_achievements = self.execute_query(query, (user_id,), fetch='all')

            return new_achievements

        except Exception as e:
            logger.error(f"❌ Error verificando logros: {e}")
            raise

    def _manual_achievement_check(self, user_id: int):
        """Verificación manual de logros si no hay procedimientos almacenados"""
        try:
            # Obtener logros pendientes
            pending_achievements = self.execute_query("""
                SELECT l.id, l.codigo_logro, l.condiciones_json, l.puntos_recompensa
                FROM logros l
                WHERE l.activo = TRUE
                AND l.id NOT IN (
                    SELECT logro_id FROM logros_desbloqueados WHERE user_id = %s
                )
            """, (user_id,), fetch='all')

            for achievement in pending_achievements:
                should_unlock = False
                codigo = achievement['codigo_logro']

                # Verificar condiciones específicas
                if codigo == 'primer_ejercicio':
                    count = self.execute_query(
                        "SELECT COUNT(*) as count FROM resultados_ejercicios WHERE user_id = %s AND completado = TRUE",
                        (user_id,), fetch='one'
                    )['count']
                    should_unlock = count >= 1

                elif codigo == 'lectura_principiante':
                    count = self.execute_query("""
                        SELECT COUNT(*) as count FROM resultados_ejercicios r 
                        JOIN ejercicios e ON r.ejercicio_id = e.id 
                        WHERE r.user_id = %s AND r.completado = TRUE AND e.tipo_ejercicio = 'lectura'
                    """, (user_id,), fetch='one')['count']
                    should_unlock = count >= 5

                elif codigo == 'precision_perfecta':
                    count = self.execute_query(
                        "SELECT COUNT(*) as count FROM resultados_ejercicios WHERE user_id = %s AND precision_porcentaje = 100",
                        (user_id,), fetch='one'
                    )['count']
                    should_unlock = count >= 1

                # Desbloquear si cumple condiciones
                if should_unlock:
                    self._unlock_achievement(user_id, achievement['id'], achievement['puntos_recompensa'])

        except Exception as e:
            logger.error(f"❌ Error en verificación manual de logros: {e}")

    def _unlock_achievement(self, user_id: int, logro_id: int, puntos_recompensa: int):
        """Desbloquear logro específico"""
        try:
            # Verificar que no esté ya desbloqueado
            existing = self.execute_query(
                "SELECT id FROM logros_desbloqueados WHERE user_id = %s AND logro_id = %s",
                (user_id, logro_id), fetch='one'
            )

            if existing:
                return

            # Desbloquear logro
            self.execute_query("""
                INSERT INTO logros_desbloqueados (user_id, logro_id, contexto_desbloqueo) 
                VALUES (%s, %s, %s)
            """, (user_id, logro_id,
                  json.dumps({'fecha': datetime.now().isoformat(), 'puntos_otorgados': puntos_recompensa})))

            # Actualizar puntos del usuario
            self.execute_query("""
                UPDATE perfiles_usuario 
                SET puntos_totales = puntos_totales + %s
                WHERE user_id = %s
            """, (puntos_recompensa, user_id))

            logger.info(f"✅ Logro desbloqueado para usuario {user_id}: {logro_id}")

        except Exception as e:
            logger.error(f"❌ Error desbloqueando logro: {e}")

    def get_user_achievements(self, user_id: int) -> Dict[str, Any]:
        """Obtener todos los logros del usuario"""
        try:
            # Logros desbloqueados
            unlocked_query = """
                SELECT l.*, ld.fecha_desbloqueo, ld.contexto_desbloqueo
                FROM logros_desbloqueados ld
                JOIN logros l ON ld.logro_id = l.id
                WHERE ld.user_id = %s
                ORDER BY ld.fecha_desbloqueo DESC
            """

            unlocked = self.execute_query(unlocked_query, (user_id,), fetch='all')

            # Logros disponibles (no desbloqueados)
            available_query = """
                SELECT l.*
                FROM logros l
                WHERE l.activo = TRUE
                AND l.id NOT IN (
                    SELECT logro_id FROM logros_desbloqueados WHERE user_id = %s
                )
                ORDER BY l.categoria_logro, l.puntos_recompensa
            """

            available = self.execute_query(available_query, (user_id,), fetch='all')

            return {
                'unlocked': unlocked,
                'available': available,
                'total_unlocked': len(unlocked),
                'total_points': sum(achievement.get('puntos_recompensa', 0) for achievement in unlocked)
            }

        except Exception as e:
            logger.error(f"❌ Error obteniendo logros del usuario: {e}")
            raise

    # =====================================================
    # MÉTODOS DE NOTIFICACIONES
    # =====================================================

    def create_notification(self, notification_data: Dict[str, Any]) -> int:
        """Crear notificación"""
        try:
            query = """
                INSERT INTO notificaciones (
                    user_id, tipo_notificacion, titulo, mensaje, datos_json,
                    fecha_programada, canal, prioridad
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            notification_id = self.execute_query(query, (
                notification_data['user_id'],
                notification_data['tipo_notificacion'],
                notification_data['titulo'],
                notification_data['mensaje'],
                json.dumps(notification_data.get('datos', {})),
                notification_data.get('fecha_programada'),
                notification_data.get('canal', 'app'),
                notification_data.get('prioridad', 'normal')
            ))

            logger.info(f"✅ Notificación creada: {notification_id}")
            return notification_id

        except Exception as e:
            logger.error(f"❌ Error creando notificación: {e}")
            raise

    def get_user_notifications(self, user_id: int, unread_only: bool = False,
                               limit: int = 20) -> List[Dict[str, Any]]:
        """Obtener notificaciones del usuario"""
        try:
            where_conditions = ["user_id = %s", "activa = TRUE"]
            params = [user_id]

            if unread_only:
                where_conditions.append("leida = FALSE")

            query = f"""
                SELECT * FROM notificaciones
                WHERE {' AND '.join(where_conditions)}
                ORDER BY fecha_creacion DESC
                LIMIT %s
            """

            params.append(limit)
            notifications = self.execute_query(query, tuple(params), fetch='all')

            # Parsear campos JSON
            for notification in notifications:
                notification['datos'] = json.loads(notification['datos_json'] or '{}')

            return notifications

        except Exception as e:
            logger.error(f"❌ Error obteniendo notificaciones: {e}")
            raise

    def mark_notification_as_read(self, notification_id: int, user_id: int) -> bool:
        """Marcar notificación como leída"""
        try:
            query = """
                UPDATE notificaciones 
                SET leida = TRUE, fecha_leida = NOW()
                WHERE id = %s AND user_id = %s
            """

            rows_affected = self.execute_query(query, (notification_id, user_id))
            return rows_affected > 0

        except Exception as e:
            logger.error(f"❌ Error marcando notificación como leída: {e}")
            raise

    # =====================================================
    # MÉTODOS DE ANALYTICS
    # =====================================================

    def save_metric(self, metric_data: Dict[str, Any]):
        """Guardar métrica de analytics"""
        try:
            query = """
                INSERT INTO analytics_metricas (
                    user_id, tipo_metrica, nombre_metrica, valor_numerico,
                    valor_texto, contexto_json, fecha_metrica, agregacion
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            self.execute_query(query, (
                metric_data.get('user_id'),
                metric_data['tipo_metrica'],
                metric_data['nombre_metrica'],
                metric_data.get('valor_numerico'),
                metric_data.get('valor_texto'),
                json.dumps(metric_data.get('contexto', {})),
                metric_data.get('fecha_metrica', datetime.now().date()),
                metric_data.get('agregacion', 'diaria')
            ))

        except Exception as e:
            logger.error(f"❌ Error guardando métrica: {e}")
            # No re-raise para métricas, no debe interrumpir la aplicación
            pass

    def get_analytics_data(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Obtener datos de analytics"""
        try:
            where_conditions = []
            params = []

            if 'user_id' in criteria:
                where_conditions.append("user_id = %s")
                params.append(criteria['user_id'])

            if 'tipo_metrica' in criteria:
                where_conditions.append("tipo_metrica = %s")
                params.append(criteria['tipo_metrica'])

            if 'fecha_inicio' in criteria:
                where_conditions.append("fecha_metrica >= %s")
                params.append(criteria['fecha_inicio'])

            if 'fecha_fin' in criteria:
                where_conditions.append("fecha_metrica <= %s")
                params.append(criteria['fecha_fin'])

            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

            query = f"""
                SELECT * FROM analytics_metricas
                {where_clause}
                ORDER BY fecha_metrica DESC, hora_metrica DESC
                LIMIT %s
            """

            params.append(criteria.get('limit', 100))
            analytics = self.execute_query(query, tuple(params), fetch='all')

            # Parsear campos JSON
            for metric in analytics:
                metric['contexto'] = json.loads(metric['contexto_json'] or '{}')
                metric['metadatos'] = json.loads(metric['metadatos'] or '{}')

            return analytics

        except Exception as e:
            logger.error(f"❌ Error obteniendo datos de analytics: {e}")
            raise

    def get_dashboard_stats(self, user_id: int) -> Dict[str, Any]:
        """Obtener estadísticas para el dashboard"""
        try:
            # Estadísticas generales del usuario
            general_stats = self.get_user_progress_summary(user_id)

            # Actividad reciente (últimos 7 días)
            activity_query = """
                SELECT 
                    DATE(fecha_inicio) as fecha,
                    COUNT(*) as ejercicios_dia,
                    AVG(precision_porcentaje) as precision_promedio_dia,
                    SUM(tiempo_empleado_segundos) as tiempo_total_dia
                FROM resultados_ejercicios
                WHERE user_id = %s 
                AND completado = TRUE
                AND fecha_inicio >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                GROUP BY DATE(fecha_inicio)
                ORDER BY fecha DESC
            """

            activity_data = self.execute_query(activity_query, (user_id,), fetch='all')

            # Progreso por tipo de ejercicio
            progress_by_type = self.get_user_progress_by_type(user_id)

            # Ranking del usuario
            ranking_query = """
                SELECT user_rank, total_users FROM (
                    SELECT 
                        u.id,
                        RANK() OVER (ORDER BY p.puntos_totales DESC) as user_rank,
                        COUNT(*) OVER() as total_users
                    FROM usuarios u
                    JOIN perfiles_usuario p ON u.id = p.user_id
                    WHERE u.activo = TRUE
                ) ranked
                WHERE id = %s
            """

            ranking_data = self.execute_query(ranking_query, (user_id,), fetch='one')

            return {
                'general_stats': general_stats,
                'activity_last_7_days': activity_data,
                'progress_by_type': progress_by_type,
                'ranking': ranking_data,
                'generated_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas de dashboard: {e}")
            raise

    # =====================================================
    # MÉTODOS DE CONFIGURACIÓN
    # =====================================================

    def get_system_config(self, key: str = None) -> Dict[str, Any]:
        """Obtener configuración del sistema"""
        try:
            if key:
                query = "SELECT * FROM configuraciones_sistema WHERE clave = %s"
                config = self.execute_query(query, (key,), fetch='one')

                if config:
                    return self._parse_config_value(config)
                return None
            else:
                query = "SELECT * FROM configuraciones_sistema ORDER BY categoria_config, clave"
                configs = self.execute_query(query, fetch='all')

                parsed_configs = {}
                for config in configs:
                    parsed_configs[config['clave']] = self._parse_config_value(config)

                return parsed_configs

        except Exception as e:
            logger.error(f"❌ Error obteniendo configuración del sistema: {e}")
            raise

    def get_user_config(self, user_id: int, key: str = None) -> Dict[str, Any]:
        """Obtener configuración del usuario"""
        try:
            if key:
                query = "SELECT * FROM configuraciones_usuario WHERE user_id = %s AND clave = %s"
                config = self.execute_query(query, (user_id, key), fetch='one')

                if config:
                    return self._parse_config_value(config)
                return None
            else:
                query = """
                    SELECT * FROM configuraciones_usuario 
                    WHERE user_id = %s 
                    ORDER BY categoria_config, clave
                """
                configs = self.execute_query(query, (user_id,), fetch='all')

                parsed_configs = {}
                for config in configs:
                    parsed_configs[config['clave']] = self._parse_config_value(config)

                return parsed_configs

        except Exception as e:
            logger.error(f"❌ Error obteniendo configuración del usuario: {e}")
            raise

    def set_user_config(self, user_id: int, key: str, value: Any, tipo_valor: str = 'string') -> bool:
        """Establecer configuración del usuario"""
        try:
            # Convertir valor según el tipo
            if tipo_valor == 'json':
                db_value = json.dumps(value)
            else:
                db_value = str(value)

            query = """
                INSERT INTO configuraciones_usuario (user_id, clave, valor, tipo_valor)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                valor = VALUES(valor), 
                tipo_valor = VALUES(tipo_valor),
                fecha_actualizacion = NOW()
            """

            self.execute_query(query, (user_id, key, db_value, tipo_valor))

            logger.info(f"✅ Configuración actualizada: {key} para usuario {user_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error estableciendo configuración del usuario: {e}")
            raise

    # =====================================================
    # MÉTODOS AUXILIARES
    # =====================================================

    def _generate_exercise_code(self, tipo_ejercicio: str) -> str:
        """Generar código único para ejercicio"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_part = secrets.token_hex(4).upper()
        return f"{tipo_ejercicio.upper()}_{timestamp}_{random_part}"

    def _generate_session_id(self) -> str:
        """Generar ID único para sesión"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_part = secrets.token_hex(8)
        return f"SES_{timestamp}_{random_part}"

    def _calculate_reading_time(self, content: str, wpm: int = 200) -> int:
        """Calcular tiempo estimado de lectura en segundos"""
        word_count = len(content.split())
        reading_time_minutes = word_count / wpm
        return int(reading_time_minutes * 60)

    def _parse_config_value(self, config: Dict[str, Any]) -> Any:
        """Parsear valor de configuración según su tipo"""
        valor = config['valor']
        tipo = config['tipo_valor']

        if tipo == 'integer':
            return int(valor)
        elif tipo == 'float':
            return float(valor)
        elif tipo == 'boolean':
            return valor.lower() in ('true', '1', 'yes', 'on')
        elif tipo == 'json':
            return json.loads(valor)
        else:
            return valor

    # =====================================================
    # MÉTODOS DE MANTENIMIENTO
    # =====================================================

    def get_database_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de la base de datos"""
        try:
            stats = {}

            # Contadores de tablas principales
            tables = [
                'usuarios', 'ejercicios', 'resultados_ejercicios',
                'contenidos_texto', 'categorias', 'logros', 'notificaciones'
            ]

            for table in tables:
                count_query = f"SELECT COUNT(*) as total FROM {table}"
                result = self.execute_query(count_query, fetch='one')
                stats[f"total_{table}"] = result['total']

            # Usuarios activos (última semana)
            active_users_query = """
                SELECT COUNT(DISTINCT user_id) as usuarios_activos_semana
                FROM resultados_ejercicios
                WHERE fecha_inicio >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            """
            active_users = self.execute_query(active_users_query, fetch='one')
            stats.update(active_users)

            # Ejercicios completados hoy
            exercises_today_query = """
                SELECT COUNT(*) as ejercicios_hoy
                FROM resultados_ejercicios
                WHERE DATE(fecha_inicio) = CURDATE() AND completado = TRUE
            """
            exercises_today = self.execute_query(exercises_today_query, fetch='one')
            stats.update(exercises_today)

            return stats

        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas de BD: {e}")
            raise

    def health_check(self) -> Dict[str, Any]:
        """Verificar salud de la base de datos"""
        try:
            health = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'checks': {}
            }

            # Test básico de conexión
            try:
                test_query = "SELECT 1 as test"
                self.execute_query(test_query, fetch='one')
                health['checks']['connection'] = True
            except Exception as e:
                health['checks']['connection'] = False
                health['status'] = 'unhealthy'
                health['connection_error'] = str(e)

            # Verificar pool de conexiones
            try:
                health['checks']['pool_size'] = self.connection_pool.pool_size
                health['checks']['pool_name'] = self.connection_pool.pool_name
            except Exception as e:
                health['checks']['pool_error'] = str(e)

            return health

        except Exception as e:
            return {
                'status': 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }

    def close_connections(self):
        """Cerrar todas las conexiones del pool"""
        try:
            # En mysql-connector-python, el pool se cierra automáticamente
            # cuando el objeto es destruido
            self.connection_pool = None
            logger.info("✅ Pool de conexiones cerrado")
        except Exception as e:
            logger.error(f"❌ Error cerrando conexiones: {e}")


# =====================================================
# FACTORY FUNCTION
# =====================================================

def create_database_manager(host: str, port: int, database: str,
                            user: str, password: str, **kwargs) -> DatabaseManager:
    """Factory function para crear DatabaseManager"""
    config = DatabaseConfig(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
        **kwargs
    )

    return DatabaseManager(config)


# =====================================================
# EJEMPLO DE USO
# =====================================================

if __name__ == "__main__":
    # Configuración de ejemplo
    db_config = {
        'host': 'localhost',
        'port': 3306,
        'database': 'alfaia_db',
        'user': 'root',
        'password': 'tired2019'
    }

    try:
        # Crear manager
        db_manager = create_database_manager(**db_config)

        # Test de salud
        health = db_manager.health_check()
        print(f"Health Check: {health}")

        # Obtener estadísticas
        stats = db_manager.get_database_stats()
        print(f"Database Stats: {stats}")

        print("✅ Database Manager inicializado correctamente")

    except Exception as e:
        print(f"❌ Error inicializando Database Manager: {e}")

