# modules/database.py - Configuración simplificada

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
        # CAMBIA ESTOS VALORES POR TUS CREDENCIALES REALES
        self.config = {
            'host': 'localhost',
            'database': 'alfaia_db',
            'user': 'root',  # CAMBIA esto por tu usuario de MySQL
            'password': 'tired2019',  # CAMBIA esto por tu contraseña de MySQL
            'port': 3306,
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci',
            'autocommit': True,
            'auth_plugin': 'mysql_native_password',
            'raise_on_warnings': False,
            'use_unicode': True
        }

        # Intentar diferentes configuraciones si falla
        self.pool = None
        self._initialize_connection()

    def _initialize_connection(self):
        """Inicializar conexión probando diferentes configuraciones"""

        # Configuraciones a probar
        configs_to_try = [
            # Configuración original
            self.config.copy(),

            # Sin auth_plugin
            {**self.config, 'auth_plugin': None},

            # Sin base de datos (para crearla)
            {k: v for k, v in self.config.items() if k != 'database'},

            # Con SSL deshabilitado
            {**self.config, 'ssl_disabled': True}
        ]

        for i, config in enumerate(configs_to_try):
            try:
                logger.info(f"Intentando configuración {i + 1}...")

                # Si no incluye database, conectar sin ella primero
                if 'database' not in config:
                    temp_config = {k: v for k, v in config.items()
                                   if k not in ['pool_name', 'pool_size', 'pool_reset_session']}

                    # Crear conexión temporal para crear base de datos
                    temp_conn = mysql.connector.connect(**temp_config)
                    cursor = temp_conn.cursor()

                    # Crear base de datos
                    cursor.execute(
                        f"CREATE DATABASE IF NOT EXISTS {self.config['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                    logger.info(f"✅ Base de datos {self.config['database']} verificada/creada")

                    cursor.close()
                    temp_conn.close()

                    # Ahora usar configuración completa
                    config = self.config.copy()

                # Crear pool con configuración que funcionó
                pool_config = {
                    **config,
                    'pool_name': 'alfaia_pool',
                    'pool_size': 3,
                    'pool_reset_session': True
                }

                self.pool = mysql.connector.pooling.MySQLConnectionPool(**pool_config)

                # Probar conexión
                test_conn = self.pool.get_connection()
                cursor = test_conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                test_conn.close()

                logger.info(f"✅ Conexión exitosa con configuración {i + 1}")
                self._setup_initial_data()
                return

            except mysql.connector.Error as e:
                logger.warning(f"⚠️  Configuración {i + 1} falló: {e}")
                continue
            except Exception as e:
                logger.warning(f"⚠️  Error en configuración {i + 1}: {e}")
                continue

        # Si llegamos aquí, ninguna configuración funcionó
        logger.error("❌ No se pudo establecer conexión con ninguna configuración")
        logger.error("💡 Verifica:")
        logger.error("   1. MySQL está ejecutándose: net start mysql")
        logger.error("   2. Credenciales en modules/database.py son correctas")
        logger.error("   3. Usuario tiene permisos suficientes")

        raise Exception("No se pudo conectar a MySQL con ninguna configuración")

    def _setup_initial_data(self):
        """Configurar datos iniciales"""
        try:
            # Verificar si las tablas existen
            tables_exist = self.execute_query("SHOW TABLES LIKE 'usuarios'", fetch='one')

            if not tables_exist:
                logger.warning("⚠️  Tablas no encontradas. Necesitas ejecutar el script SQL primero.")
                logger.info("💡 Ejecuta: mysql -u root -p < database_structure.sql")
            else:
                logger.info("✅ Tablas de base de datos encontradas")

                # Crear usuario demo si no existe
                existing_demo = self.execute_query(
                    "SELECT id FROM usuarios WHERE username = 'demo_user'",
                    fetch='one'
                )

                if not existing_demo:
                    demo_password = self.hash_password('demo123')

                    user_id = self.execute_query("""
                        INSERT INTO usuarios (username, email, password_hash, nombre, apellido)
                        VALUES (%s, %s, %s, %s, %s)
                    """, ('demo_user', 'demo@alfaia.com', demo_password, 'Usuario', 'Demo'))

                    if user_id:
                        self.execute_query("INSERT INTO progreso_usuario (usuario_id) VALUES (%s)", (user_id,))
                        self.execute_query("INSERT INTO configuraciones_usuario (usuario_id) VALUES (%s)", (user_id,))
                        logger.info("✅ Usuario demo creado: demo_user / demo123")

        except Exception as e:
            logger.warning(f"⚠️  Error configurando datos iniciales: {e}")

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
                return result[0] == 1
        except Exception as e:
            logger.error(f"❌ Error en test de conexión: {e}")
            return False

    def execute_query(self, query, params=None, fetch=False):
        """Ejecutar query con manejo de errores"""
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
            return None
        except Exception as e:
            logger.error(f"❌ Error general en query: {e}")
            return None

    def execute_procedure(self, procedure_name, params=None):
        """Ejecutar procedimiento almacenado"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                cursor.callproc(procedure_name, params or ())
                connection.commit()
                cursor.close()
                return True
        except Exception as e:
            logger.error(f"❌ Error ejecutando procedimiento {procedure_name}: {e}")
            return False

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

            # Insertar usuario
            query = """
                INSERT INTO usuarios (username, email, password_hash, nombre, apellido, fecha_nacimiento)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            params = (username, email, password_hash, nombre, apellido, fecha_nacimiento)

            user_id = self.execute_query(query, params)

            if user_id:
                # Crear progreso inicial
                self.execute_query(
                    "INSERT INTO progreso_usuario (usuario_id) VALUES (%s)",
                    (user_id,)
                )

                # Crear configuración inicial
                self.execute_query(
                    "INSERT INTO configuraciones_usuario (usuario_id) VALUES (%s)",
                    (user_id,)
                )

                logger.info(f"Usuario creado exitosamente: {username}")
                return {"success": True, "user_id": user_id, "message": "Usuario creado exitosamente"}
            else:
                return {"success": False, "message": "Error al crear el usuario"}

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
                SELECT nombre_logro, descripcion, icono, fecha_obtenido 
                FROM logros 
                WHERE usuario_id = %s 
                ORDER BY fecha_obtenido DESC
            """
            logros = self.execute_query(query_logros, (user_id,), fetch='all') or []

            return {
                "progreso": progreso,
                "logros": logros,
                "estadisticas_semanales": [],
                "ejercicios_recientes": []
            }

        except Exception as e:
            logger.error(f"Error obteniendo progreso del usuario {user_id}: {e}")
            return None

    @staticmethod
    def hash_password(password):
        """Hash de contraseña usando bcrypt"""
        import bcrypt
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def verify_password(password, password_hash):
        """Verificar contraseña"""
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


# Inicialización segura
try:
    db_manager = DatabaseManager()
    if db_manager and db_manager.test_connection():
        logger.info("✅ Sistema de base de datos inicializado correctamente")
    else:
        logger.error("❌ Sistema de base de datos no funcional")
        db_manager = None
except Exception as e:
    logger.error(f"❌ Error crítico inicializando base de datos: {e}")
    db_manager = None