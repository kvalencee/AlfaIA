# modules/auth.py
from functools import wraps
from flask import session, request, redirect, url_for, flash, jsonify
from modules.database import db_manager
import logging

logger = logging.getLogger(__name__)


class AuthManager:
    def __init__(self):
        self.db = db_manager

    def login_required(self, f):
        """Decorador para requerir login"""

        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                # Si es una petición AJAX, devolver JSON
                if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'error': 'Authentication required', 'redirect': url_for('login')}), 401
                flash('Debes iniciar sesión para acceder a esta página.', 'warning')
                return redirect(url_for('login'))

            # Verificar que la sesión siga siendo válida
            user = self.get_current_user()
            if not user:
                session.clear()
                if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'error': 'Session expired', 'redirect': url_for('login')}), 401
                flash('Tu sesión ha expirado. Por favor, inicia sesión nuevamente.', 'warning')
                return redirect(url_for('login'))

            return f(*args, **kwargs)

        return decorated_function

    def admin_required(self, f):
        """Decorador para requerir permisos de administrador"""

        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = self.get_current_user()
            if not user or not user.get('is_admin', False):
                if request.is_json:
                    return jsonify({'error': 'Admin access required'}), 403
                flash('No tienes permisos para acceder a esta página.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)

        return decorated_function

    def login_user(self, username, password, remember_me=False):
        """Iniciar sesión de usuario"""
        try:
            result = self.db.autenticar_usuario(username, password)

            if result['success']:
                user = result['user']

                # Guardar información en la sesión
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['nombre'] = user['nombre']
                session['apellido'] = user['apellido']
                session['email'] = user['email']
                session['token'] = result['token']

                # Configurar duración de la sesión
                if remember_me:
                    session.permanent = True

                # Obtener IP y User Agent para logging
                ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
                user_agent = request.headers.get('User-Agent')

                logger.info(f"Usuario {username} inició sesión desde {ip_address}")

                return {
                    'success': True,
                    'message': f'Bienvenido, {user["nombre"]}!',
                    'user': user
                }
            else:
                return result

        except Exception as e:
            logger.error(f"Error en login_user: {e}")
            return {'success': False, 'message': 'Error interno del servidor'}

    def logout_user(self):
        """Cerrar sesión del usuario"""
        try:
            # Cerrar sesión en la base de datos
            if 'token' in session:
                self.db.cerrar_sesion(session['token'])

            # Limpiar la sesión
            username = session.get('username', 'Usuario')
            session.clear()

            logger.info(f"Usuario {username} cerró sesión")

            return {
                'success': True,
                'message': 'Sesión cerrada exitosamente'
            }

        except Exception as e:
            logger.error(f"Error en logout_user: {e}")
            session.clear()  # Limpiar sesión de todas formas
            return {'success': False, 'message': 'Error al cerrar sesión'}

    def register_user(self, user_data):
        """Registrar nuevo usuario"""
        try:
            # Validar datos
            validation_result = self.validate_registration_data(user_data)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'message': validation_result['message'],
                    'errors': validation_result.get('errors', {})
                }

            # Crear usuario en la base de datos
            result = self.db.crear_usuario(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                nombre=user_data['nombre'],
                apellido=user_data['apellido'],
                fecha_nacimiento=user_data.get('fecha_nacimiento')
            )

            if result['success']:
                logger.info(f"Nuevo usuario registrado: {user_data['username']}")

                # Opcionalmente, iniciar sesión automáticamente
                if user_data.get('auto_login', False):
                    login_result = self.login_user(user_data['username'], user_data['password'])
                    if login_result['success']:
                        result['auto_logged_in'] = True

            return result

        except Exception as e:
            logger.error(f"Error en register_user: {e}")
            return {'success': False, 'message': 'Error interno del servidor'}

    def get_current_user(self):
        """Obtener información del usuario actual"""
        if 'user_id' not in session:
            return None

        try:
            # Verificar que la sesión siga siendo válida
            if 'token' in session:
                session_data = self.db.validar_sesion(session['token'])
                if not session_data:
                    return None

            user = self.db.obtener_usuario_por_id(session['user_id'])
            if user:
                # Agregar información de la sesión
                user['session_info'] = {
                    'user_id': session.get('user_id'),
                    'username': session.get('username'),
                    'nombre': session.get('nombre'),
                    'apellido': session.get('apellido'),
                    'email': session.get('email')
                }

            return user

        except Exception as e:
            logger.error(f"Error obteniendo usuario actual: {e}")
            return None

    def get_user_progress(self, user_id=None):
        """Obtener progreso del usuario actual o especificado"""
        if not user_id:
            user_id = session.get('user_id')

        if not user_id:
            return None

        try:
            return self.db.obtener_progreso_usuario(user_id)
        except Exception as e:
            logger.error(f"Error obteniendo progreso del usuario {user_id}: {e}")
            return None

    def update_user_progress(self, tipo_ejercicio, nombre_ejercicio, puntos, precision, tiempo, datos_extra=None):
        """Actualizar progreso del usuario actual"""
        user_id = session.get('user_id')
        if not user_id:
            return False

        try:
            ejercicio_id = self.db.registrar_ejercicio_completado(
                user_id=user_id,
                tipo_ejercicio=tipo_ejercicio,
                nombre_ejercicio=nombre_ejercicio,
                puntos_obtenidos=puntos,
                precision=precision,
                tiempo_empleado=tiempo,
                datos_adicionales=datos_extra
            )

            return ejercicio_id is not None

        except Exception as e:
            logger.error(f"Error actualizando progreso: {e}")
            return False

    def validate_registration_data(self, data):
        """Validar datos de registro"""
        errors = {}

        # Validar username
        username = data.get('username', '').strip()
        if not username:
            errors['username'] = 'El nombre de usuario es requerido'
        elif len(username) < 3:
            errors['username'] = 'El nombre de usuario debe tener al menos 3 caracteres'
        elif len(username) > 50:
            errors['username'] = 'El nombre de usuario no puede tener más de 50 caracteres'
        elif not username.isalnum() and '_' not in username:
            errors['username'] = 'El nombre de usuario solo puede contener letras, números y guiones bajos'

        # Validar email
        email = data.get('email', '').strip()
        if not email:
            errors['email'] = 'El email es requerido'
        elif '@' not in email or '.' not in email:
            errors['email'] = 'El email no tiene un formato válido'
        elif len(email) > 100:
            errors['email'] = 'El email no puede tener más de 100 caracteres'

        # Validar contraseña
        password = data.get('password', '')
        if not password:
            errors['password'] = 'La contraseña es requerida'
        elif len(password) < 6:
            errors['password'] = 'La contraseña debe tener al menos 6 caracteres'
        elif len(password) > 100:
            errors['password'] = 'La contraseña no puede tener más de 100 caracteres'

        # Validar confirmación de contraseña
        confirm_password = data.get('confirm_password', '')
        if password != confirm_password:
            errors['confirm_password'] = 'Las contraseñas no coinciden'

        # Validar nombre
        nombre = data.get('nombre', '').strip()
        if not nombre:
            errors['nombre'] = 'El nombre es requerido'
        elif len(nombre) > 100:
            errors['nombre'] = 'El nombre no puede tener más de 100 caracteres'

        # Validar apellido
        apellido = data.get('apellido', '').strip()
        if not apellido:
            errors['apellido'] = 'El apellido es requerido'
        elif len(apellido) > 100:
            errors['apellido'] = 'El apellido no puede tener más de 100 caracteres'

        # Validar fecha de nacimiento (opcional)
        fecha_nacimiento = data.get('fecha_nacimiento')
        if fecha_nacimiento:
            try:
                from datetime import datetime
                fecha = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
                # Verificar que la fecha sea razonable (no futuro, no muy antigua)
                today = datetime.now().date()
                if fecha > today:
                    errors['fecha_nacimiento'] = 'La fecha de nacimiento no puede ser futura'
                elif (today - fecha).days > 36500:  # ~100 años
                    errors['fecha_nacimiento'] = 'La fecha de nacimiento no es válida'
            except ValueError:
                errors['fecha_nacimiento'] = 'Formato de fecha inválido (YYYY-MM-DD)'

        if errors:
            return {
                'valid': False,
                'message': 'Por favor, corrige los errores en el formulario',
                'errors': errors
            }

        return {'valid': True}

    def change_password(self, current_password, new_password):
        """Cambiar contraseña del usuario actual"""
        user_id = session.get('user_id')
        if not user_id:
            return {'success': False, 'message': 'Usuario no autenticado'}

        try:
            # Verificar contraseña actual
            user = self.db.obtener_usuario_por_id(user_id)
            if not user or not self.db.verify_password(current_password, user['password_hash']):
                return {'success': False, 'message': 'La contraseña actual es incorrecta'}

            # Validar nueva contraseña
            if len(new_password) < 6:
                return {'success': False, 'message': 'La nueva contraseña debe tener al menos 6 caracteres'}

            # Actualizar contraseña
            new_password_hash = self.db.hash_password(new_password)
            query = "UPDATE usuarios SET password_hash = %s WHERE id = %s"

            if self.db.execute_query(query, (new_password_hash, user_id)):
                # Cerrar todas las sesiones excepto la actual
                token_actual = session.get('token')
                self.db.cerrar_todas_sesiones(user_id)

                # Recrear sesión actual
                nuevo_token = self.db.crear_sesion(user_id)
                session['token'] = nuevo_token

                logger.info(f"Usuario {user['username']} cambió su contraseña")
                return {'success': True, 'message': 'Contraseña actualizada exitosamente'}
            else:
                return {'success': False, 'message': 'Error al actualizar la contraseña'}

        except Exception as e:
            logger.error(f"Error cambiando contraseña: {e}")
            return {'success': False, 'message': 'Error interno del servidor'}

    def update_user_profile(self, profile_data):
        """Actualizar perfil del usuario"""
        user_id = session.get('user_id')
        if not user_id:
            return {'success': False, 'message': 'Usuario no autenticado'}

        try:
            # Validar datos
            errors = {}

            nombre = profile_data.get('nombre', '').strip()
            if not nombre or len(nombre) > 100:
                errors['nombre'] = 'El nombre es requerido y no puede exceder 100 caracteres'

            apellido = profile_data.get('apellido', '').strip()
            if not apellido or len(apellido) > 100:
                errors['apellido'] = 'El apellido es requerido y no puede exceder 100 caracteres'

            email = profile_data.get('email', '').strip()
            if not email or '@' not in email:
                errors['email'] = 'El email es requerido y debe tener un formato válido'

            if errors:
                return {'success': False, 'message': 'Datos inválidos', 'errors': errors}

            # Verificar si el email ya existe para otro usuario
            existing_user = self.db.obtener_usuario_por_email(email)
            if existing_user and existing_user['id'] != user_id:
                return {'success': False, 'message': 'El email ya está en uso por otro usuario'}

            # Actualizar usuario
            query = """
                UPDATE usuarios 
                SET nombre = %s, apellido = %s, email = %s, fecha_nacimiento = %s
                WHERE id = %s
            """
            params = (
                nombre,
                apellido,
                email,
                profile_data.get('fecha_nacimiento'),
                user_id
            )

            if self.db.execute_query(query, params):
                # Actualizar datos de la sesión
                session['nombre'] = nombre
                session['apellido'] = apellido
                session['email'] = email

                logger.info(f"Usuario {session.get('username')} actualizó su perfil")
                return {'success': True, 'message': 'Perfil actualizado exitosamente'}
            else:
                return {'success': False, 'message': 'Error al actualizar el perfil'}

        except Exception as e:
            logger.error(f"Error actualizando perfil: {e}")
            return {'success': False, 'message': 'Error interno del servidor'}

    def get_user_settings(self):
        """Obtener configuraciones del usuario actual"""
        user_id = session.get('user_id')
        if not user_id:
            return None

        try:
            return self.db.obtener_configuracion_usuario(user_id)
        except Exception as e:
            logger.error(f"Error obteniendo configuraciones: {e}")
            return None

    def update_user_settings(self, settings):
        """Actualizar configuraciones del usuario actual"""
        user_id = session.get('user_id')
        if not user_id:
            return {'success': False, 'message': 'Usuario no autenticado'}

        try:
            if self.db.actualizar_configuracion_usuario(user_id, settings):
                return {'success': True, 'message': 'Configuraciones actualizadas exitosamente'}
            else:
                return {'success': False, 'message': 'Error al actualizar configuraciones'}

        except Exception as e:
            logger.error(f"Error actualizando configuraciones: {e}")
            return {'success': False, 'message': 'Error interno del servidor'}

    def is_logged_in(self):
        """Verificar si el usuario está loggeado"""
        return 'user_id' in session and self.get_current_user() is not None

    def get_session_info(self):
        """Obtener información de la sesión actual"""
        if not self.is_logged_in():
            return None

        return {
            'user_id': session.get('user_id'),
            'username': session.get('username'),
            'nombre': session.get('nombre'),
            'apellido': session.get('apellido'),
            'email': session.get('email'),
            'logged_in': True
        }


# Instancia global del manejador de autenticación
auth_manager = AuthManager()