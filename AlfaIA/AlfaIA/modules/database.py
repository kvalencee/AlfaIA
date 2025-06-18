# modules/database.py - Versión Corregida

import mysql.connector
from mysql.connector import Error, pooling
import os
import hashlib
import secrets
from datetime import datetime, timedelta
import json
from contextlib import contextmanager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self):
        # CONFIGURACIONES MÚLTIPLES PARA PROBAR
        self.configs_to_try = [
            # Configuración 1: Usuario específico de ALFAIA (recomendado)
            {
                'host': 'localhost',
                'database': 'alfaia',
                'user': 'alfaia_user',
                'password': 'alfaia2024',
                'port': 3306,
                'charset': 'utf8mb4',
                'collation': 'utf8mb4_unicode_ci',
                'autocommit': False,
                'auth_plugin': 'mysql_native_password',
                'raise_on_warnings': False,
                'use_unicode': True,
                'connect_timeout': 10,
                'sql_mode': 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO'
            },
            # Configuración 2: Root con mysql_native_password
            {
                'host': 'localhost',
                'database': 'alfaia',
                'user': 'root',
                'password': 'tired2019',
                'port': 3306,
                'charset': 'utf8mb4',
                'collation': 'utf8mb4_unicode_ci',
                'autocommit': False,
                'auth_plugin': 'mysql_native_password',
                'raise_on_warnings': False,
                'use_unicode': True,
                'connect_timeout': 10,
                'sql_mode': 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO'
            },
            # Configuración 3: Root sin auth_plugin específico
            {
                'host': 'localhost',
                'database': 'alfaia',
                'user': 'root',
                'password': 'tired2019',
                'port': 3306,
                'charset': 'utf8mb4',
                'collation': 'utf8mb4_unicode_ci',
                'autocommit': False,
                'raise_on_warnings': False,
                'use_unicode': True,
                'connect_timeout': 10
            }
        ]

        self.config = None  # Se establecerá con la configuración que funcione

        self.pool = None
        self._initialize_connection()

    def _initialize_connection(self):
        """Inicializar conexión probando múltiples configuraciones"""

        # Verificar si MySQL está ejecutándose
        if not self._check_mysql_service():
            logger.error("❌ MySQL no está ejecutándose. Ejecuta: net start mysql")
            raise Exception("MySQL service not running")

        logger.info("🔄 Intentando conectar a MySQL con múltiples configuraciones...")

        for i, config in enumerate(self.configs_to_try):
            try:
                logger.info(f"Probando configuración {i + 1}: usuario '{config['user']}'")

                # Intentar crear el pool con esta configuración
                self.pool = mysql.connector.pooling.MySQLConnectionPool(
                    pool_name=f'alfaia_pool_{i}',
                    pool_size=5,
                    pool_reset_session=True,
                    **config
                )

                # Probar la conexión
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT DATABASE() as db_name, USER() as user_name, VERSION() as version")
                    result = cursor.fetchone()
                    logger.info(f"✅ Conectado exitosamente: {result}")
                    cursor.close()

                # Si llegamos aquí, la conexión fue exitosa
                self.config = config
                logger.info(f"✅ Usando configuración {i + 1} exitosamente")
                self._setup_initial_data()
                return

            except mysql.connector.Error as e:
                if e.errno == 1049:  # Database doesn't exist
                    logger.warning(f"⚠️  Base de datos 'alfaia' no existe con configuración {i + 1}")
                    try:
                        self._create_database_with_config(config)
                        # Intentar de nuevo con la base de datos creada
                        self.pool = mysql.connector.pooling.MySQLConnectionPool(
                            pool_name=f'alfaia_pool_{i}_retry',
                            pool_size=5,
                            pool_reset_session=True,
                            **config
                        )
                        self.config = config
                        logger.info(f"✅ Base de datos creada y conexión establecida con configuración {i + 1}")
                        self._setup_initial_data()
                        return
                    except Exception as create_error:
                        logger.error(f"❌ Error creando base de datos con configuración {i + 1}: {create_error}")
                        continue
                elif e.errno == 1045:  # Access denied
                    logger.warning(f"❌ Configuración {i + 1}: Acceso denegado para usuario '{config['user']}'")
                    continue
                elif "caching_sha2_password" in str(e):
                    logger.warning(f"❌ Configuración {i + 1}: Problema de autenticación - {e}")
                    continue
                else:
                    logger.warning(f"❌ Configuración {i + 1}: Error MySQL - {e}")
                    continue
            except Exception as e:
                logger.warning(f"❌ Configuración {i + 1}: Error general - {e}")
                continue

        # Si llegamos aquí, ninguna configuración funcionó
        logger.error("❌ No se pudo establecer conexión con ninguna configuración")
        logger.error("💡 Soluciones sugeridas:")
        logger.error("   1. Ejecutar el script SQL de corrección de autenticación")
        logger.error("   2. Verificar que MySQL esté ejecutándose: net start mysql")
        logger.error("   3. Verificar las credenciales de usuario")
        logger.error("   4. Crear usuario alfaia_user con mysql_native_password")

        raise Exception("No se pudo conectar a MySQL con ninguna configuración")

    def _check_mysql_service(self):
        """Verificar si MySQL está ejecutándose - Versión mejorada"""
        try:
            # Método 1: Intentar conexión directa sin base de datos
            import mysql.connector
            test_config = {
                'host': 'localhost',
                'user': 'root',
                'password': 'tired2019',
                'port': 3306,
                'connect_timeout': 5
            }

            test_conn = mysql.connector.connect(**test_config)
            test_conn.close()
            return True

        except mysql.connector.Error as e:
            logger.warning(f"MySQL no accesible: {e}")
            return False
        except Exception as e:
            logger.warning(f"Error verificando MySQL: {e}")

            # Método 2: Verificar servicios de Windows
            try:
                import subprocess
                result = subprocess.run(['sc', 'query', 'mysql80'],
                                        capture_output=True, text=True, timeout=5)
                if 'RUNNING' in result.stdout:
                    return True

                # También probar mysql
                result = subprocess.run(['sc', 'query', 'mysql'],
                                        capture_output=True, text=True, timeout=5)
                if 'RUNNING' in result.stdout:
                    return True

            except:
                pass

            return False

    def _create_database_with_config(self, config):
        """Crear la base de datos usando una configuración específica"""
        try:
            # Configuración sin especificar base de datos
            temp_config = {k: v for k, v in config.items() if k != 'database'}

            temp_conn = mysql.connector.connect(**temp_config)
            cursor = temp_conn.cursor()

            # Crear base de datos
            cursor.execute("CREATE DATABASE IF NOT EXISTS alfaia CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            logger.info("✅ Base de datos 'alfaia' creada/verificada")

            cursor.close()
            temp_conn.close()

        except Exception as e:
            logger.error(f"❌ Error creando base de datos: {e}")
            raise

    def _setup_initial_data(self):
        """Verificar y configurar datos iniciales"""
        try:
            # Verificar si las tablas existen
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SHOW TABLES LIKE 'usuarios'")
                tables_exist = cursor.fetchone()
                cursor.close()

            if not tables_exist:
                logger.warning("⚠️  Tablas no encontradas.")
                logger.info("💡 Ejecuta el script SQL desde MySQL Workbench o consola:")
                logger.info("   mysql -u root -p alfaia < database_structure.sql")
                return

            logger.info("✅ Tablas encontradas en la base de datos")

            # Verificar usuario demo
            existing_demo = self.execute_query(
                "SELECT id FROM usuarios WHERE username = %s",
                ('demo_user',),
                fetch='one'
            )

            if not existing_demo:
                logger.info("🔧 Creando usuario demo...")
                self._create_demo_user()

        except Exception as e:
            logger.warning(f"⚠️  Error en configuración inicial: {e}")

    def _create_demo_user(self):
        """Crear usuario demo"""
        try:
            # Usar bcrypt para hash de contraseña
            demo_password = self.hash_password('demo123')

            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Insertar usuario
                cursor.execute("""
                    INSERT INTO usuarios (username, email, password_hash, nombre, apellido)
                    VALUES (%s, %s, %s, %s, %s)
                """, ('demo_user', 'demo@alfaia.com', demo_password, 'Usuario', 'Demo'))

                user_id = cursor.lastrowid

                # Crear progreso inicial
                cursor.execute("INSERT INTO progreso_usuario (usuario_id) VALUES (%s)", (user_id,))

                # Crear configuración inicial
                cursor.execute("INSERT INTO configuraciones_usuario (usuario_id) VALUES (%s)", (user_id,))

                conn.commit()
                logger.info("✅ Usuario demo creado: demo_user / demo123")

        except Exception as e:
            logger.error(f"❌ Error creando usuario demo: {e}")

    @contextmanager
    def get_connection(self):
        """Context manager para obtener conexiones del pool"""
        connection = None
        try:
            if not self.pool:
                raise Exception("Pool de conexiones no inicializado")

            connection = self.pool.get_connection()
            yield connection

        except mysql.connector.Error as e:
            if connection and connection.is_connected():
                connection.rollback()
            logger.error(f"❌ Error en conexión MySQL: {e}")
            raise
        except Exception as e:
            if connection and connection.is_connected():
                connection.rollback()
            logger.error(f"❌ Error general en conexión: {e}")
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()

    def test_connection(self):
        """Probar conexión a la base de datos"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                cursor.close()
                return result and result[0] == 1
        except Exception as e:
            logger.error(f"❌ Error en test de conexión: {e}")
            return False

    def execute_query(self, query, params=None, fetch=False):
        """Ejecutar query con manejo de errores mejorado"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(query, params or ())

                if fetch:
                    if fetch == 'one':
                        result = cursor.fetchone()
                    else:
                        result = cursor.fetchall()
                    cursor.close()
                    return result
                else:
                    connection.commit()
                    last_id = cursor.lastrowid
                    cursor.close()
                    return last_id if last_id else True

        except mysql.connector.Error as e:
            logger.error(f"❌ Error MySQL en query: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            return None
        except Exception as e:
            logger.error(f"❌ Error general en query: {e}")
            return None

    # ==================== MÉTODOS DE USUARIO ====================

    def crear_usuario(self, username, email, password, nombre, apellido, fecha_nacimiento=None):
        """Crear un nuevo usuario"""
        try:
            # Verificar si el usuario ya existe
            if self.obtener_usuario_por_username(username):
                return {"success": False, "message": "El nombre de usuario ya existe"}

            if self.obtener_usuario_por_email(email):
                return {"success": False, "message": "El email ya está registrado"}

            # Hash de la contraseña
            password_hash = self.hash_password(password)

            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Insertar usuario
                cursor.execute("""
                    INSERT INTO usuarios (username, email, password_hash, nombre, apellido, fecha_nacimiento)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (username, email, password_hash, nombre, apellido, fecha_nacimiento))

                user_id = cursor.lastrowid

                # Crear progreso inicial
                cursor.execute("INSERT INTO progreso_usuario (usuario_id) VALUES (%s)", (user_id,))

                # Crear configuración inicial
                cursor.execute("INSERT INTO configuraciones_usuario (usuario_id) VALUES (%s)", (user_id,))

                conn.commit()
                logger.info(f"Usuario creado exitosamente: {username}")

                return {"success": True, "user_id": user_id, "message": "Usuario creado exitosamente"}

        except Exception as e:
            logger.error(f"Error creando usuario: {e}")
            return {"success": False, "message": "Error interno del servidor"}

    def autenticar_usuario(self, username, password):
        """Autenticar usuario con username/email y contraseña"""
        try:
            # Buscar por username o email
            query = """
                SELECT id, username, email, password_hash, nombre, apellido, activo
                FROM usuarios 
                WHERE (username = %s OR email = %s) AND activo = TRUE
            """
            user = self.execute_query(query, (username, username), fetch='one')

            if user and self.verify_password(password, user['password_hash']):
                # Actualizar último acceso
                self.execute_query(
                    "UPDATE usuarios SET ultimo_acceso = CURRENT_TIMESTAMP WHERE id = %s",
                    (user['id'],)
                )

                # Crear sesión
                token = self.crear_sesion(user['id'])

                return {
                    "success": True,
                    "user": {
                        "id": user['id'],
                        "username": user['username'],
                        "email": user['email'],
                        "nombre": user['nombre'],
                        "apellido": user['apellido']
                    },
                    "token": token
                }
            else:
                return {"success": False, "message": "Credenciales incorrectas"}

        except Exception as e:
            logger.error(f"Error autenticando usuario: {e}")
            return {"success": False, "message": "Error interno del servidor"}

    def obtener_usuario_por_username(self, username):
        """Obtener usuario por username"""
        query = "SELECT * FROM usuarios WHERE username = %s AND activo = TRUE"
        return self.execute_query(query, (username,), fetch='one')

    def obtener_usuario_por_email(self, email):
        """Obtener usuario por email"""
        query = "SELECT * FROM usuarios WHERE email = %s AND activo = TRUE"
        return self.execute_query(query, (email,), fetch='one')

    def obtener_usuario_por_id(self, user_id):
        """Obtener usuario por ID"""
        query = "SELECT * FROM usuarios WHERE id = %s AND activo = TRUE"
        return self.execute_query(query, (user_id,), fetch='one')

    def crear_sesion(self, user_id, ip_address=None, user_agent=None):
        """Crear una nueva sesión para el usuario"""
        try:
            token = secrets.token_urlsafe(32)
            fecha_expiracion = datetime.now() + timedelta(days=30)

            query = """
                INSERT INTO sesiones (usuario_id, token, ip_address, user_agent, fecha_expiracion)
                VALUES (%s, %s, %s, %s, %s)
            """
            params = (user_id, token, ip_address, user_agent, fecha_expiracion)

            if self.execute_query(query, params):
                return token
            return None

        except Exception as e:
            logger.error(f"Error creando sesión: {e}")
            return None

    def validar_sesion(self, token):
        """Validar si una sesión es válida y activa"""
        try:
            query = """
                SELECT s.usuario_id, u.username, u.nombre, u.apellido, u.email
                FROM sesiones s
                JOIN usuarios u ON s.usuario_id = u.id
                WHERE s.token = %s 
                AND s.activa = TRUE 
                AND s.fecha_expiracion > NOW()
                AND u.activo = TRUE
            """
            return self.execute_query(query, (token,), fetch='one')

        except Exception as e:
            logger.error(f"Error validando sesión: {e}")
            return None

    def cerrar_sesion(self, token):
        """Cerrar una sesión específica"""
        try:
            query = "UPDATE sesiones SET activa = FALSE WHERE token = %s"
            return self.execute_query(query, (token,))
        except Exception as e:
            logger.error(f"Error cerrando sesión: {e}")
            return False

    def cerrar_todas_sesiones(self, user_id):
        """Cerrar todas las sesiones de un usuario"""
        try:
            query = "UPDATE sesiones SET activa = FALSE WHERE usuario_id = %s"
            return self.execute_query(query, (user_id,))
        except Exception as e:
            logger.error(f"Error cerrando todas las sesiones: {e}")
            return False

    def obtener_progreso_usuario(self, user_id):
        """Obtener el progreso completo del usuario"""
        try:
            # Progreso general
            query_progreso = "SELECT * FROM progreso_usuario WHERE usuario_id = %s"
            progreso = self.execute_query(query_progreso, (user_id,), fetch='one')

            if not progreso:
                # Crear progreso si no existe
                self.execute_query("INSERT INTO progreso_usuario (usuario_id) VALUES (%s)", (user_id,))
                progreso = self.execute_query(query_progreso, (user_id,), fetch='one')

            # Logros
            query_logros = """
                SELECT nombre_logro, descripcion, icono, categoria, fecha_obtenido 
                FROM logros 
                WHERE usuario_id = %s 
                ORDER BY fecha_obtenido DESC
            """
            logros = self.execute_query(query_logros, (user_id,), fetch='all') or []

            # Ejercicios recientes
            query_ejercicios = """
                SELECT tipo_ejercicio, nombre_ejercicio, puntos_obtenidos, 
                       precision_porcentaje, fecha_completado
                FROM ejercicios_realizados 
                WHERE usuario_id = %s 
                ORDER BY fecha_completado DESC 
                LIMIT 10
            """
            ejercicios_recientes = self.execute_query(query_ejercicios, (user_id,), fetch='all') or []

            # Estadísticas semanales
            query_semanales = """
                SELECT fecha, ejercicios_completados, tiempo_estudiado_minutos, 
                       puntos_obtenidos, precision_promedio
                FROM estadisticas_diarias 
                WHERE usuario_id = %s 
                AND fecha >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                ORDER BY fecha DESC
            """
            estadisticas_semanales = self.execute_query(query_semanales, (user_id,), fetch='all') or []

            return {
                "progreso": progreso,
                "logros": logros,
                "ejercicios_recientes": ejercicios_recientes,
                "estadisticas_semanales": estadisticas_semanales
            }

        except Exception as e:
            logger.error(f"Error obteniendo progreso del usuario {user_id}: {e}")
            return None

    def registrar_ejercicio_completado(self, user_id, tipo_ejercicio, nombre_ejercicio,
                                       puntos_obtenidos, precision, tiempo_empleado, datos_adicionales=None):
        """Registrar un ejercicio completado"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Insertar ejercicio
                cursor.execute("""
                    INSERT INTO ejercicios_realizados 
                    (usuario_id, tipo_ejercicio, nombre_ejercicio, puntos_obtenidos, 
                     precision_porcentaje, tiempo_empleado_segundos, datos_adicionales)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (user_id, tipo_ejercicio, nombre_ejercicio, puntos_obtenidos,
                      precision, tiempo_empleado, json.dumps(datos_adicionales) if datos_adicionales else None))

                ejercicio_id = cursor.lastrowid

                # Actualizar estadísticas usando procedimiento almacenado
                cursor.callproc('ActualizarEstadisticasUsuario',
                                (user_id, puntos_obtenidos, precision, tiempo_empleado))

                # Verificar logros
                cursor.callproc('VerificarLogros', (user_id,))

                conn.commit()
                return ejercicio_id

        except Exception as e:
            logger.error(f"Error registrando ejercicio: {e}")
            return None

    def obtener_configuracion_usuario(self, user_id):
        """Obtener configuración del usuario"""
        try:
            query = "SELECT * FROM configuraciones_usuario WHERE usuario_id = %s"
            config = self.execute_query(query, (user_id,), fetch='one')

            if not config:
                # Crear configuración por defecto
                self.execute_query("INSERT INTO configuraciones_usuario (usuario_id) VALUES (%s)", (user_id,))
                config = self.execute_query(query, (user_id,), fetch='one')

            return config

        except Exception as e:
            logger.error(f"Error obteniendo configuración: {e}")
            return None

    def actualizar_configuracion_usuario(self, user_id, configuraciones):
        """Actualizar configuración del usuario"""
        try:
            # Construir query dinámicamente basado en las configuraciones proporcionadas
            campos_permitidos = ['velocidad_lectura', 'dificultad_preferida', 'tema_preferido',
                                 'notificaciones_activas', 'sonidos_activos', 'configuracion_json']

            set_clauses = []
            params = []

            for campo, valor in configuraciones.items():
                if campo in campos_permitidos:
                    set_clauses.append(f"{campo} = %s")
                    if campo == 'configuracion_json' and isinstance(valor, dict):
                        params.append(json.dumps(valor))
                    else:
                        params.append(valor)

            if not set_clauses:
                return False

            params.append(user_id)
            query = f"UPDATE configuraciones_usuario SET {', '.join(set_clauses)} WHERE usuario_id = %s"

            return self.execute_query(query, params)

        except Exception as e:
            logger.error(f"Error actualizando configuración: {e}")
            return False

    @staticmethod
    def hash_password(password):
        """Hash de contraseña usando bcrypt"""
        try:
            import bcrypt
            return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        except ImportError:
            logger.error("bcrypt no está instalado. Usando hash simple (NO SEGURO)")
            import hashlib
            return hashlib.sha256(password.encode('utf-8')).hexdigest()

    @staticmethod
    def verify_password(password, password_hash):
        """Verificar contraseña"""
        try:
            import bcrypt
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except ImportError:
            # Fallback para hash simple
            import hashlib
            return hashlib.sha256(password.encode('utf-8')).hexdigest() == password_hash


# ==================== INICIALIZACIÓN SEGURA ====================

def create_database_manager():
    """Crear instancia del manejador de base de datos con manejo de errores"""
    try:
        db = DatabaseManager()
        if db.test_connection():
            logger.info("✅ Sistema de base de datos inicializado correctamente")
            return db
        else:
            logger.error("❌ Sistema de base de datos no funcional")
            return None
    except Exception as e:
        logger.error(f"❌ Error crítico inicializando base de datos: {e}")
        logger.error("💡 Posibles soluciones:")
        logger.error("   1. Verifica que MySQL esté ejecutándose: net start mysql")
        logger.error("   2. Verifica las credenciales en modules/database.py")
        logger.error("   3. Ejecuta el script SQL para crear la base de datos")
        logger.error("   4. Instala las dependencias: pip install -r requirements.txt")
        return None


# Inicialización global
db_manager = create_database_manager()
