# app.py - AlfaIA Sistema de Alfabetización con IA - Versión Modernizada
# Versión: 2.0.0
# Fecha: Enero 2025

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_cors import CORS
import os
import logging
from datetime import datetime, timedelta
import json
import random
import traceback
from functools import wraps
from typing import Dict, Any, Optional

# ==================== IMPORTACIONES DE MÓDULOS ====================

# Configuración moderna
try:
    from modules.config import config, initialize_config, get_database_config

    CONFIG_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ Sistema de configuración moderno cargado")
except ImportError as e:
    CONFIG_AVAILABLE = False
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.error(f"❌ Error cargando configuración: {e}")

# Database Manager moderno
try:
    from modules.database_manager import DatabaseManager, DatabaseConfig
    from modules.config import get_database_config

    # Inicializar Database Manager con configuración moderna
    if CONFIG_AVAILABLE:
        db_config = get_database_config()
        db_manager = DatabaseManager(db_config)
        DB_AVAILABLE = True
        logger.info("✅ Database Manager moderno inicializado")
    else:
        # Configuración de fallback
        fallback_config = DatabaseConfig(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 3306)),
            database=os.getenv('DB_NAME', 'alfaia_db'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', 'tired2019')
        )
        db_manager = DatabaseManager(fallback_config)
        DB_AVAILABLE = True
        logger.warning("⚠️ Database Manager con configuración de fallback")

except Exception as e:
    logger.error(f"❌ Error inicializando Database Manager: {e}")
    DB_AVAILABLE = False
    db_manager = None

# Módulos de ejercicios
try:
    from modules.ejercicios_lectura import EjerciciosLectura
    from modules.juegos_interactivos import JuegosInteractivos
    from modules.generador_ejercicios import GeneradorEjercicios

    ejercicios_lectura = EjerciciosLectura()
    juegos_generator = JuegosInteractivos()
    ejercicios_generator = GeneradorEjercicios()
    EJERCICIOS_AVAILABLE = True
    logger.info("✅ Módulos de ejercicios cargados")
except ImportError as e:
    logger.error(f"⚠️ Error cargando módulos de ejercicios: {e}")
    EJERCICIOS_AVAILABLE = False
    ejercicios_lectura = None
    juegos_generator = None
    ejercicios_generator = None

# ==================== CONFIGURACIÓN DE FLASK ====================

# Inicializar Flask
app = Flask(__name__)

# Configuración desde sistema moderno o fallback
if CONFIG_AVAILABLE:
    app.config.update({
        'SECRET_KEY': config.get('security.secret_key', 'alfaia-fallback-key-2025'),
        'DEBUG': config.get('app.debug', False),
        'TESTING': config.get('app.testing', False),
        'SESSION_COOKIE_SECURE': config.get('security.session_cookie_secure', False),
        'SESSION_COOKIE_HTTPONLY': config.get('security.session_cookie_httponly', True),
        'SESSION_COOKIE_SAMESITE': config.get('security.session_cookie_samesite', 'Lax'),
        'PERMANENT_SESSION_LIFETIME': timedelta(hours=config.get('security.session_timeout_hours', 24)),
        'MAX_CONTENT_LENGTH': config.get('media.max_upload_size', 16 * 1024 * 1024),
        'UPLOAD_FOLDER': config.get('media.upload_folder', 'static/uploads'),
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'JSON_AS_ASCII': False
    })

    # Configurar CORS desde configuración
    cors_origins = config.get('security.cors_origins', ['http://localhost:5000', 'http://127.0.0.1:5000'])
    CORS(app, origins=cors_origins)

    logger.info(f"✅ Flask configurado con configuración moderna")
    logger.info(f"   Debug: {app.config['DEBUG']}")
    logger.info(f"   Upload folder: {app.config['UPLOAD_FOLDER']}")

else:
    # Configuración de fallback
    app.config.update({
        'SECRET_KEY': os.environ.get('SECRET_KEY', 'alfaia-fallback-key-2025'),
        'DEBUG': os.environ.get('FLASK_DEBUG', 'False').lower() == 'true',
        'SESSION_COOKIE_SECURE': False,
        'SESSION_COOKIE_HTTPONLY': True,
        'SESSION_COOKIE_SAMESITE': 'Lax',
        'PERMANENT_SESSION_LIFETIME': timedelta(days=7),
        'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,
        'UPLOAD_FOLDER': 'static/uploads'
    })

    CORS(app, origins=['http://localhost:5000', 'http://127.0.0.1:5000'])
    logger.warning("⚠️ Flask configurado con configuración de fallback")

# ==================== CONFIGURACIÓN DE LOGGING ====================

if CONFIG_AVAILABLE:
    log_level = getattr(logging, config.get('logging.level', 'INFO').upper())
    log_format = config.get('logging.format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(config.get('logging.file', 'logs/alfaia.log')),
            logging.StreamHandler()
        ]
    )
else:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

# Crear directorios necesarios
required_directories = [
    'logs', 'data', 'static/uploads', 'templates/errors',
    'static/css', 'static/js', 'static/images', 'temp'
]

for directory in required_directories:
    os.makedirs(directory, exist_ok=True)

# ==================== DATOS DE FALLBACK ====================

FALLBACK_USER = {
    'id': 1,
    'username': 'demo_user',
    'nombre': 'Usuario',
    'apellido': 'Demo',
    'email': 'demo@alfaia.com',
    'nivel_lectura': 1,
    'nivel_escritura': 1,
    'nivel_pronunciacion': 1,
    'puntos_totales': 100,
    'activo': True
}

FALLBACK_STATS = {
    'ejercicios_completados': 15,
    'tiempo_total_minutos': 60,
    'precision_promedio': 87.5,
    'racha_dias_consecutivos': 5,
    'puntos_totales': 450,
    'nivel_lectura': 2,
    'nivel_escritura': 2,
    'nivel_pronunciacion': 1,
    'progreso_semanal': [10, 15, 8, 20, 12, 18, 25]
}

FALLBACK_CATEGORIES = [
    {'id': 1, 'nombre': 'Vocales', 'descripcion': 'Ejercicios con vocales', 'tipo': 'pronunciacion'},
    {'id': 2, 'nombre': 'Consonantes', 'descripcion': 'Ejercicios con consonantes', 'tipo': 'pronunciacion'},
    {'id': 3, 'nombre': 'Palabras Básicas', 'descripcion': 'Vocabulario fundamental', 'tipo': 'lectura'},
    {'id': 4, 'nombre': 'Oraciones Simples', 'descripcion': 'Estructura de oraciones', 'tipo': 'lectura'}
]


# ==================== DECORADORES Y FUNCIONES AUXILIARES ====================

def login_required(f):
    """Decorador para rutas que requieren autenticación"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """Decorador para rutas que requieren permisos de administrador"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user or not user.get('es_admin', False):
            flash('No tienes permisos para acceder a esta página.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)

    return decorated_function


def get_current_user() -> Optional[Dict[str, Any]]:
    """Obtener datos del usuario actual"""
    if 'user_id' not in session:
        return None

    user_id = session['user_id']

    if DB_AVAILABLE and db_manager:
        try:
            user = db_manager.get_user_by_id(user_id)
            if not user:
                session.clear()
                return None
            return user
        except Exception as e:
            logger.error(f"Error obteniendo usuario {user_id}: {e}")
            # Fallback para usuario demo
            if user_id == 1:
                return FALLBACK_USER
            return None
    else:
        # Modo sin base de datos
        if user_id == 1:
            return FALLBACK_USER
        return None


def init_user_session(user: Dict[str, Any]) -> None:
    """Inicializar la sesión del usuario"""
    session.permanent = True
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['nombre'] = user['nombre']
    session['apellido'] = user['apellido']
    session['email'] = user['email']
    session['nivel_lectura'] = user.get('nivel_lectura', 1)
    session['nivel_escritura'] = user.get('nivel_escritura', 1)
    session['nivel_pronunciacion'] = user.get('nivel_pronunciacion', 1)

    logger.info(f"✅ Sesión inicializada para usuario: {user['username']}")


def get_user_stats(user_id: int) -> Dict[str, Any]:
    """Obtener estadísticas del usuario"""
    if DB_AVAILABLE and db_manager:
        try:
            return db_manager.get_user_progress_summary(user_id)
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return FALLBACK_STATS
    return FALLBACK_STATS


def get_user_config(user_id: int) -> Dict[str, Any]:
    """Obtener configuración del usuario"""
    if DB_AVAILABLE and db_manager:
        try:
            return db_manager.get_user_config(user_id) or {}
        except Exception as e:
            logger.error(f"Error obteniendo configuración: {e}")
            return {}
    return {}


def handle_error(error_type: str, error: Exception, user_context: str = ""):
    """Manejar errores de manera centralizada"""
    error_id = f"ERR_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"

    logger.error(f"Error {error_id} [{error_type}] {user_context}: {str(error)}")
    logger.error(f"Traceback: {traceback.format_exc()}")

    return {
        'error_id': error_id,
        'error_type': error_type,
        'message': str(error),
        'timestamp': datetime.now().isoformat()
    }


# ==================== RUTAS PRINCIPALES ====================

@app.route('/')
def index():
    """Página de inicio"""
    try:
        user = get_current_user()

        # Obtener estadísticas generales si hay usuario
        stats = None
        if user:
            stats = get_user_stats(user['id'])

        # Verificar estado del sistema
        system_status = {
            'database': DB_AVAILABLE,
            'exercises': EJERCICIOS_AVAILABLE,
            'config': CONFIG_AVAILABLE
        }

        return render_template('index.html',
                               user=user,
                               stats=stats,
                               system_status=system_status)

    except Exception as e:
        error_info = handle_error('INDEX_ERROR', e)
        return render_template('errors/500.html', error=error_info), 500


@app.route('/about')
def about():
    """Página de información sobre AlfaIA"""
    try:
        # Obtener estadísticas del sistema si está disponible
        system_info = {}
        if DB_AVAILABLE and db_manager:
            try:
                system_info = db_manager.get_database_stats()
            except:
                pass

        return render_template('about.html', system_info=system_info)

    except Exception as e:
        error_info = handle_error('ABOUT_ERROR', e)
        return render_template('errors/500.html', error=error_info), 500


# ==================== AUTENTICACIÓN ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de inicio de sesión"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')

            if not username or not password:
                flash('Por favor, completa todos los campos.', 'warning')
                return render_template('login.html', db_available=DB_AVAILABLE)

            # Autenticación
            user = None
            if DB_AVAILABLE and db_manager:
                try:
                    user = db_manager.authenticate_user(username, password)
                except Exception as e:
                    logger.error(f"Error en autenticación: {e}")
                    flash('Error de conexión. Intenta nuevamente.', 'error')
                    return render_template('login.html', db_available=DB_AVAILABLE)
            else:
                # Modo demo sin base de datos
                if username == 'demo_user' and password == 'demo123':
                    user = FALLBACK_USER

            if user:
                init_user_session(user)

                # Verificar y desbloquear logros de conexión
                if DB_AVAILABLE and db_manager:
                    try:
                        db_manager.check_and_unlock_achievements(user['id'], 'login')
                    except Exception as e:
                        logger.warning(f"Error verificando logros: {e}")

                flash(f'¡Bienvenido de nuevo, {user["nombre"]}!', 'success')

                # Redirección
                next_page = request.form.get('next') or request.args.get('next')
                if next_page and next_page.startswith('/'):
                    return redirect(next_page)
                return redirect(url_for('dashboard'))
            else:
                flash('Usuario o contraseña incorrectos.', 'error')

        except Exception as e:
            error_info = handle_error('LOGIN_ERROR', e, f"Usuario: {username}")
            flash('Error interno. Intenta nuevamente.', 'error')

    return render_template('login.html', db_available=DB_AVAILABLE)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Página de registro de nuevos usuarios"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            # Validar datos
            required_fields = ['username', 'email', 'password', 'confirm_password', 'nombre', 'apellido']
            user_data = {}

            for field in required_fields:
                value = request.form.get(field, '').strip()
                if not value:
                    flash(f'El campo {field} es obligatorio.', 'warning')
                    return render_template('register.html')
                user_data[field] = value

            # Validar contraseñas
            if user_data['password'] != user_data['confirm_password']:
                flash('Las contraseñas no coinciden.', 'warning')
                return render_template('register.html')

            if len(user_data['password']) < 6:
                flash('La contraseña debe tener al menos 6 caracteres.', 'warning')
                return render_template('register.html')

            # Datos opcionales
            optional_fields = ['fecha_nacimiento', 'genero', 'nivel_educativo', 'pais', 'ciudad', 'telefono']
            for field in optional_fields:
                user_data[field] = request.form.get(field, '').strip() or None

            # Crear usuario
            if DB_AVAILABLE and db_manager:
                try:
                    user_id = db_manager.create_user(user_data)

                    # Crear perfil inicial
                    profile_data = {
                        'objetivo_diario_minutos': 30,
                        'objetivo_diario_ejercicios': 5,
                        'estilo_aprendizaje': 'mixto'
                    }
                    db_manager.create_user_profile(user_id, profile_data)

                    # Obtener usuario creado
                    user = db_manager.get_user_by_id(user_id)
                    init_user_session(user)

                    # Crear notificación de bienvenida
                    try:
                        db_manager.create_notification(
                            user_id=user_id,
                            tipo='bienvenida',
                            titulo='¡Bienvenido a AlfaIA!',
                            mensaje='Comienza tu viaje de aprendizaje con nosotros.',
                            datos_json={'first_login': True}
                        )
                    except Exception as e:
                        logger.warning(f"Error creando notificación de bienvenida: {e}")

                    flash('¡Cuenta creada exitosamente! Bienvenido a AlfaIA.', 'success')
                    return redirect(url_for('dashboard'))

                except ValueError as e:
                    flash(str(e), 'error')
                except Exception as e:
                    error_info = handle_error('REGISTER_ERROR', e, f"Usuario: {user_data['username']}")
                    flash('Error creando la cuenta. Intenta nuevamente.', 'error')
            else:
                flash('Registro no disponible en modo demo.', 'warning')

        except Exception as e:
            error_info = handle_error('REGISTER_FORM_ERROR', e)
            flash('Error procesando el formulario.', 'error')

    return render_template('register.html')


@app.route('/logout')
def logout():
    """Cerrar sesión"""
    username = session.get('username', 'Usuario')
    session.clear()
    flash(f'Hasta luego, {username}. ¡Vuelve pronto!', 'info')
    return redirect(url_for('index'))


# ==================== DASHBOARD Y PERFIL ====================

@app.route('/dashboard')
@login_required
def dashboard():
    """Panel principal del usuario"""
    try:
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))

        # Obtener estadísticas del usuario
        stats = get_user_stats(user['id'])

        # Obtener notificaciones no leídas
        notifications = []
        if DB_AVAILABLE and db_manager:
            try:
                notifications = db_manager.get_user_notifications(user['id'], unread_only=True, limit=5)
            except Exception as e:
                logger.warning(f"Error obteniendo notificaciones: {e}")

        # Obtener logros recientes
        recent_achievements = []
        if DB_AVAILABLE and db_manager:
            try:
                recent_achievements = db_manager.get_user_achievements(user['id'], limit=3)
            except Exception as e:
                logger.warning(f"Error obteniendo logros: {e}")

        # Actividad reciente
        recent_activity = []
        if DB_AVAILABLE and db_manager:
            try:
                recent_activity = db_manager.get_user_recent_activity(user['id'], limit=5)
            except Exception as e:
                logger.warning(f"Error obteniendo actividad reciente: {e}")

        # Recomendaciones de ejercicios
        recommended_exercises = []
        if EJERCICIOS_AVAILABLE:
            try:
                # Lógica de recomendaciones basada en nivel y progreso
                user_level = user.get('nivel_lectura', 1)
                if user_level <= 2:
                    recommended_exercises = [
                        {'tipo': 'lectura', 'nombre': 'Lectura Básica', 'dificultad': 'facil'},
                        {'tipo': 'pronunciacion', 'nombre': 'Práctica de Vocales', 'dificultad': 'facil'},
                    ]
                else:
                    recommended_exercises = [
                        {'tipo': 'lectura', 'nombre': 'Comprensión Avanzada', 'dificultad': 'medio'},
                        {'tipo': 'ortografia', 'nombre': 'Ortografía Intermedia', 'dificultad': 'medio'},
                    ]
            except Exception as e:
                logger.warning(f"Error generando recomendaciones: {e}")

        return render_template('dashboard.html',
                               user=user,
                               stats=stats,
                               notifications=notifications,
                               recent_achievements=recent_achievements,
                               recent_activity=recent_activity,
                               recommended_exercises=recommended_exercises,
                           db_available=DB_AVAILABLE)

    except Exception as e:
        error_info = handle_error('DASHBOARD_ERROR', e, f"Usuario: {session.get('username')}")
        return render_template('errors/500.html', error=error_info), 500


@app.route('/profile')
@login_required
def profile():
    """Página de perfil del usuario"""
    try:
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))

        # Obtener configuración del usuario
        user_config = get_user_config(user['id'])

        # Obtener estadísticas detalladas
        detailed_stats = get_user_stats(user['id'])

        # Obtener historial de logros
        achievements = []
        if DB_AVAILABLE and db_manager:
            try:
                achievements = db_manager.get_user_achievements(user['id'])
            except Exception as e:
                logger.warning(f"Error obteniendo logros: {e}")

        return render_template('profile.html',
                               user=user,
                               user_config=user_config,
                               detailed_stats=detailed_stats,
                               achievements=achievements)

    except Exception as e:
        error_info = handle_error('PROFILE_ERROR', e, f"Usuario: {session.get('username')}")
        return render_template('errors/500.html', error=error_info), 500


@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    """Actualizar perfil del usuario"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'message': 'Usuario no encontrado'})

        # Obtener datos del formulario
        profile_data = {
            'nombre': request.form.get('nombre', '').strip(),
            'apellido': request.form.get('apellido', '').strip(),
            'email': request.form.get('email', '').strip(),
            'telefono': request.form.get('telefono', '').strip(),
            'ciudad': request.form.get('ciudad', '').strip(),
            'objetivo_diario_minutos': int(request.form.get('objetivo_diario_minutos', 30)),
            'objetivo_diario_ejercicios': int(request.form.get('objetivo_diario_ejercicios', 5)),
            'estilo_aprendizaje': request.form.get('estilo_aprendizaje', 'mixto')
        }

        # Validar datos básicos
        if not profile_data['nombre'] or not profile_data['apellido'] or not profile_data['email']:
            return jsonify({'success': False, 'message': 'Nombre, apellido y email son obligatorios'})

        # Actualizar en base de datos
        if DB_AVAILABLE and db_manager:
            try:
                # Actualizar datos del usuario
                success = db_manager.update_user_profile(user['id'], profile_data)

                if success:
                    # Actualizar sesión
                    session['nombre'] = profile_data['nombre']
                    session['apellido'] = profile_data['apellido']
                    session['email'] = profile_data['email']

                    return jsonify({'success': True, 'message': 'Perfil actualizado exitosamente'})
                else:
                    return jsonify({'success': False, 'message': 'Error actualizando el perfil'})

            except Exception as e:
                logger.error(f"Error actualizando perfil: {e}")
                return jsonify({'success': False, 'message': 'Error interno del servidor'})
        else:
            return jsonify({'success': False, 'message': 'Funcionalidad no disponible en modo demo'})

    except Exception as e:
        error_info = handle_error('UPDATE_PROFILE_ERROR', e, f"Usuario: {session.get('username')}")
        return jsonify({'success': False, 'message': 'Error procesando la actualización'})


# ==================== EJERCICIOS ====================

@app.route('/ejercicios')
@login_required
def ejercicios():
    """Página principal de ejercicios"""
    try:
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))

        # Obtener categorías disponibles
        categories = []
        if DB_AVAILABLE and db_manager:
            try:
                categories = db_manager.get_categories()
            except Exception as e:
                logger.warning(f"Error obteniendo categorías: {e}")
                categories = FALLBACK_CATEGORIES
        else:
            categories = FALLBACK_CATEGORIES

        # Obtener progreso por tipo de ejercicio
        exercise_progress = {}
        if DB_AVAILABLE and db_manager:
            try:
                exercise_progress = db_manager.get_exercise_progress_by_type(user['id'])
            except Exception as e:
                logger.warning(f"Error obteniendo progreso: {e}")

        # Tipos de ejercicios disponibles
        exercise_types = [
            {
                'id': 'lectura',
                'nombre': 'Lectura',
                'descripcion': 'Ejercicios de comprensión lectora',
                'icon': 'book',
                'dificultad': user.get('nivel_lectura', 1),
                'disponible': EJERCICIOS_AVAILABLE
            },
            {
                'id': 'pronunciacion',
                'nombre': 'Pronunciación',
                'descripcion': 'Práctica de pronunciación y fonética',
                'icon': 'microphone',
                'dificultad': user.get('nivel_pronunciacion', 1),
                'disponible': EJERCICIOS_AVAILABLE
            },
            {
                'id': 'memoria',
                'nombre': 'Memoria',
                'descripcion': 'Juegos de memoria y retención',
                'icon': 'brain',
                'dificultad': 1,
                'disponible': EJERCICIOS_AVAILABLE
            },
            {
                'id': 'ahorcado',
                'nombre': 'Ahorcado',
                'descripcion': 'Juego del ahorcado educativo',
                'icon': 'game',
                'dificultad': 1,
                'disponible': EJERCICIOS_AVAILABLE
            },
            {
                'id': 'trivia',
                'nombre': 'Trivia',
                'descripcion': 'Preguntas y respuestas educativas',
                'icon': 'question',
                'dificultad': 1,
                'disponible': EJERCICIOS_AVAILABLE
            },
            {
                'id': 'completar_palabra',
                'nombre': 'Completar Palabra',
                'descripcion': 'Completa las palabras faltantes',
                'icon': 'edit',
                'dificultad': 1,
                'disponible': EJERCICIOS_AVAILABLE
            },
            {
                'id': 'ordenar_frase',
                'nombre': 'Ordenar Frase',
                'descripcion': 'Ordena las palabras para formar frases',
                'icon': 'sort',
                'dificultad': 1,
                'disponible': EJERCICIOS_AVAILABLE
            },
            {
                'id': 'ortografia',
                'nombre': 'Ortografía',
                'descripcion': 'Ejercicios de escritura y ortografía',
                'icon': 'spell-check',
                'dificultad': user.get('nivel_escritura', 1),
                'disponible': EJERCICIOS_AVAILABLE
            }
        ]

        return render_template('ejercicios.html',
                               user=user,
                               categories=categories,
                               exercise_types=exercise_types,
                               exercise_progress=exercise_progress)

    except Exception as e:
        error_info = handle_error('EJERCICIOS_ERROR', e, f"Usuario: {session.get('username')}")
        return render_template('errors/500.html', error=error_info), 500


# ==================== RUTAS DE EJERCICIOS ESPECÍFICOS ====================

@app.route('/ejercicios/lectura')
@login_required
def ejercicios_lectura():
    """Ejercicios de lectura"""
    try:
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))

        # Obtener configuración de lectura
        lectura_config = {}
        if CONFIG_AVAILABLE:
            lectura_config = config.get_exercise_config('lectura')

        # Obtener contenidos para lectura
        contenidos = []
        if DB_AVAILABLE and db_manager:
            try:
                contenidos = db_manager.get_content_by_criteria(
                    tipo_contenido='lectura',
                    nivel_dificultad=user.get('nivel_lectura', 1),
                    limit=10
                )
            except Exception as e:
                logger.warning(f"Error obteniendo contenidos: {e}")

        return render_template('ejercicios/lectura.html',
                               user=user,
                               contenidos=contenidos,
                               config=lectura_config)

    except Exception as e:
        error_info = handle_error('LECTURA_ERROR', e, f"Usuario: {session.get('username')}")
        return render_template('errors/500.html', error=error_info), 500


@app.route('/ejercicios/pronunciacion')
@login_required
def ejercicios_pronunciacion():
    """Ejercicios de pronunciación"""
    try:
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))

        # Obtener configuración de pronunciación
        pronunciacion_config = {}
        if CONFIG_AVAILABLE:
            pronunciacion_config = config.get_exercise_config('pronunciacion')

        # Obtener ejercicios de pronunciación
        ejercicios_pronunciacion = []
        if DB_AVAILABLE and db_manager:
            try:
                ejercicios_pronunciacion = db_manager.get_content_by_criteria(
                    tipo_contenido='pronunciacion',
                    nivel_dificultad=user.get('nivel_pronunciacion', 1),
                    limit=10
                )
            except Exception as e:
                logger.warning(f"Error obteniendo ejercicios de pronunciación: {e}")

        return render_template('ejercicios/pronunciacion.html',
                               user=user,
                               ejercicios=ejercicios_pronunciacion,
                               config=pronunciacion_config)

    except Exception as e:
        error_info = handle_error('PRONUNCIACION_ERROR', e, f"Usuario: {session.get('username')}")
        return render_template('errors/500.html', error=error_info), 500


@app.route('/ejercicios/memoria')
@login_required
def ejercicios_memoria():
    """Juegos de memoria"""
    try:
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))

        # Configuración del juego de memoria
        memoria_config = {
            'niveles': [
                {'nivel': 1, 'pares': 4, 'tiempo_limite': 60},
                {'nivel': 2, 'pares': 6, 'tiempo_limite': 90},
                {'nivel': 3, 'pares': 8, 'tiempo_limite': 120}
            ]
        }

        return render_template('ejercicios/memoria.html',
                               user=user,
                               config=memoria_config)

    except Exception as e:
        error_info = handle_error('MEMORIA_ERROR', e, f"Usuario: {session.get('username')}")
        return render_template('errors/500.html', error=error_info), 500


@app.route('/ejercicios/ahorcado')
@login_required
def ejercicios_ahorcado():
    """Juego del ahorcado"""
    try:
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))

        # Obtener palabras para el ahorcado
        palabras = []
        if DB_AVAILABLE and db_manager:
            try:
                palabras = db_manager.get_content_by_criteria(
                    tipo_contenido='palabra',
                    nivel_dificultad=user.get('nivel_lectura', 1),
                    limit=20
                )
            except Exception as e:
                logger.warning(f"Error obteniendo palabras: {e}")
                # Palabras de fallback
                palabras = [
                    {'contenido': 'CASA', 'descripcion': 'Lugar donde vivimos'},
                    {'contenido': 'AGUA', 'descripcion': 'Líquido vital'},
                    {'contenido': 'LIBRO', 'descripcion': 'Objeto para leer'},
                    {'contenido': 'ESCUELA', 'descripcion': 'Lugar de aprendizaje'}
                ]

        return render_template('ejercicios/ahorcado.html',
                               user=user,
                               palabras=palabras)

    except Exception as e:
        error_info = handle_error('AHORCADO_ERROR', e, f"Usuario: {session.get('username')}")
        return render_template('errors/500.html', error=error_info), 500


@app.route('/ejercicios/trivia')
@login_required
def ejercicios_trivia():
    """Juego de trivia"""
    try:
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))

        # Obtener preguntas de trivia
        preguntas = []
        if DB_AVAILABLE and db_manager:
            try:
                preguntas = db_manager.get_content_by_criteria(
                    tipo_contenido='trivia',
                    nivel_dificultad=user.get('nivel_lectura', 1),
                    limit=10
                )
            except Exception as e:
                logger.warning(f"Error obteniendo preguntas: {e}")

        return render_template('ejercicios/trivia.html',
                               user=user,
                               preguntas=preguntas)

    except Exception as e:
        error_info = handle_error('TRIVIA_ERROR', e, f"Usuario: {session.get('username')}")
        return render_template('errors/500.html', error=error_info), 500


@app.route('/ejercicios/completar_palabra')
@login_required
def ejercicios_completar_palabra():
    """Ejercicios de completar palabra"""
    try:
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))

        # Obtener ejercicios de completar palabra
        ejercicios = []
        if DB_AVAILABLE and db_manager:
            try:
                ejercicios = db_manager.get_content_by_criteria(
                    tipo_contenido='completar_palabra',
                    nivel_dificultad=user.get('nivel_escritura', 1),
                    limit=10
                )
            except Exception as e:
                logger.warning(f"Error obteniendo ejercicios: {e}")

        return render_template('ejercicios/completar_palabra.html',
                               user=user,
                               ejercicios=ejercicios)

    except Exception as e:
        error_info = handle_error('COMPLETAR_PALABRA_ERROR', e, f"Usuario: {session.get('username')}")
        return render_template('errors/500.html', error=error_info), 500


@app.route('/ejercicios/ordenar_frase')
@login_required
def ejercicios_ordenar_frase():
    """Ejercicios de ordenar frases"""
    try:
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))

        # Obtener ejercicios de ordenar frases
        ejercicios = []
        if DB_AVAILABLE and db_manager:
            try:
                ejercicios = db_manager.get_content_by_criteria(
                    tipo_contenido='ordenar_frase',
                    nivel_dificultad=user.get('nivel_lectura', 1),
                    limit=10
                )
            except Exception as e:
                logger.warning(f"Error obteniendo ejercicios: {e}")

        return render_template('ejercicios/ordenar_frase.html',
                               user=user,
                               ejercicios=ejercicios)

    except Exception as e:
        error_info = handle_error('ORDENAR_FRASE_ERROR', e, f"Usuario: {session.get('username')}")
        return render_template('errors/500.html', error=error_info), 500


@app.route('/ejercicios/ortografia')
@login_required
def ejercicios_ortografia():
    """Ejercicios de ortografía"""
    try:
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))

        # Obtener ejercicios de ortografía
        ejercicios = []
        if DB_AVAILABLE and db_manager:
            try:
                ejercicios = db_manager.get_content_by_criteria(
                    tipo_contenido='ortografia',
                    nivel_dificultad=user.get('nivel_escritura', 1),
                    limit=10
                )
            except Exception as e:
                logger.warning(f"Error obteniendo ejercicios: {e}")

        return render_template('ejercicios/ortografia.html',
                               user=user,
                               ejercicios=ejercicios)

    except Exception as e:
        error_info = handle_error('ORTOGRAFIA_ERROR', e, f"Usuario: {session.get('username')}")
        return render_template('errors/500.html', error=error_info), 500


# ==================== API ENDPOINTS ====================

@app.route('/api/exercise/start', methods=['POST'])
@login_required
def api_start_exercise():
    """API para iniciar un ejercicio"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'message': 'Usuario no autenticado'})

        data = request.get_json()
        exercise_type = data.get('exercise_type')
        exercise_id = data.get('exercise_id')
        config_data = data.get('config', {})

        if not exercise_type:
            return jsonify({'success': False, 'message': 'Tipo de ejercicio requerido'})

        # Crear sesión de ejercicio
        if DB_AVAILABLE and db_manager:
            try:
                session_id = db_manager.create_exercise_session(
                    user_id=user['id'],
                    exercise_type=exercise_type,
                    exercise_id=exercise_id,
                    config_data=config_data
                )

                return jsonify({
                    'success': True,
                    'session_id': session_id,
                    'message': 'Ejercicio iniciado'
                })

            except Exception as e:
                logger.error(f"Error creando sesión de ejercicio: {e}")
                return jsonify({'success': False, 'message': 'Error interno'})
        else:
            # Modo demo - generar ID temporal
            session_id = f"demo_{int(datetime.now().timestamp())}"
            return jsonify({
                'success': True,
                'session_id': session_id,
                'message': 'Ejercicio iniciado (modo demo)'
            })

    except Exception as e:
        error_info = handle_error('API_START_EXERCISE_ERROR', e, f"Usuario: {session.get('username')}")
        return jsonify({'success': False, 'message': 'Error procesando solicitud'})


@app.route('/api/exercise/submit', methods=['POST'])
@login_required
def api_submit_exercise():
    """API para enviar resultado de ejercicio"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'message': 'Usuario no autenticado'})

        data = request.get_json()
        session_id = data.get('session_id')
        answers = data.get('answers', {})
        time_spent = data.get('time_spent', 0)
        completed = data.get('completed', False)

        if not session_id:
            return jsonify({'success': False, 'message': 'ID de sesión requerido'})

        # Guardar resultado
        if DB_AVAILABLE and db_manager:
            try:
                result_id = db_manager.save_exercise_result(
                    session_id=session_id,
                    user_id=user['id'],
                    answers=answers,
                    time_spent=time_spent,
                    completed=completed
                )

                # Verificar logros
                achievements = db_manager.check_and_unlock_achievements(
                    user['id'],
                    'exercise_completed',
                    {'exercise_type': data.get('exercise_type')}
                )

                return jsonify({
                    'success': True,
                    'result_id': result_id,
                    'achievements': achievements,
                    'message': 'Resultado guardado'
                })

            except Exception as e:
                logger.error(f"Error guardando resultado: {e}")
                return jsonify({'success': False, 'message': 'Error guardando resultado'})
        else:
            return jsonify({
                'success': True,
                'message': 'Resultado procesado (modo demo)'
            })

    except Exception as e:
        error_info = handle_error('API_SUBMIT_EXERCISE_ERROR', e, f"Usuario: {session.get('username')}")
        return jsonify({'success': False, 'message': 'Error procesando resultado'})


@app.route('/api/user/stats')
@login_required
def api_user_stats():
    """API para obtener estadísticas del usuario"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'message': 'Usuario no autenticado'})

        stats = get_user_stats(user['id'])

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        error_info = handle_error('API_USER_STATS_ERROR', e, f"Usuario: {session.get('username')}")
        return jsonify({'success': False, 'message': 'Error obteniendo estadísticas'})


@app.route('/api/user/progress')
@login_required
def api_user_progress():
    """API para obtener progreso detallado del usuario"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'message': 'Usuario no autenticado'})

        progress_data = {}
        if DB_AVAILABLE and db_manager:
            try:
                progress_data = db_manager.get_dashboard_stats(user['id'])
            except Exception as e:
                logger.warning(f"Error obteniendo progreso: {e}")
                progress_data = {'error': 'No disponible'}

        return jsonify({
            'success': True,
            'progress': progress_data
        })

    except Exception as e:
        error_info = handle_error('API_USER_PROGRESS_ERROR', e, f"Usuario: {session.get('username')}")
        return jsonify({'success': False, 'message': 'Error obteniendo progreso'})


@app.route('/api/notifications')
@login_required
def api_notifications():
    """API para obtener notificaciones del usuario"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'message': 'Usuario no autenticado'})

        notifications = []
        if DB_AVAILABLE and db_manager:
            try:
                unread_only = request.args.get('unread_only', 'false').lower() == 'true'
                limit = int(request.args.get('limit', 20))

                notifications = db_manager.get_user_notifications(
                    user['id'],
                    unread_only=unread_only,
                    limit=limit
                )
            except Exception as e:
                logger.warning(f"Error obteniendo notificaciones: {e}")

        return jsonify({
            'success': True,
            'notifications': notifications
        })

    except Exception as e:
        error_info = handle_error('API_NOTIFICATIONS_ERROR', e, f"Usuario: {session.get('username')}")
        return jsonify({'success': False, 'message': 'Error obteniendo notificaciones'})


@app.route('/api/notifications/<int:notification_id>/mark_read', methods=['POST'])
@login_required
def api_mark_notification_read(notification_id):
    """API para marcar notificación como leída"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'message': 'Usuario no autenticado'})

        if DB_AVAILABLE and db_manager:
            try:
                success = db_manager.mark_notification_as_read(notification_id, user['id'])
                return jsonify({
                    'success': success,
                    'message': 'Notificación marcada como leída' if success else 'Error marcando notificación'
                })
            except Exception as e:
                logger.error(f"Error marcando notificación: {e}")
                return jsonify({'success': False, 'message': 'Error interno'})
        else:
            return jsonify({'success': True, 'message': 'Procesado (modo demo)'})

    except Exception as e:
        error_info = handle_error('API_MARK_NOTIFICATION_ERROR', e, f"Usuario: {session.get('username')}")
        return jsonify({'success': False, 'message': 'Error procesando solicitud'})


# ==================== RUTAS DE ADMINISTRACIÓN ====================

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    """Panel de administración"""
    try:
        user = get_current_user()

        # Obtener estadísticas del sistema
        system_stats = {}
        if DB_AVAILABLE and db_manager:
            try:
                system_stats = db_manager.get_database_stats()
                system_health = db_manager.health_check()
                system_stats['health'] = system_health
            except Exception as e:
                logger.warning(f"Error obteniendo estadísticas del sistema: {e}")

        return render_template('admin/dashboard.html',
                               user=user,
                               system_stats=system_stats)

    except Exception as e:
        error_info = handle_error('ADMIN_DASHBOARD_ERROR', e, f"Usuario: {session.get('username')}")
        return render_template('errors/500.html', error=error_info), 500


# ==================== RUTAS DE PROGRESO Y ESTADÍSTICAS ====================

@app.route('/progreso')
@login_required
def progreso():
    """Página de progreso del usuario"""
    try:
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))

        # Obtener estadísticas detalladas
        detailed_stats = get_user_stats(user['id'])

        # Obtener progreso por categorías
        progress_by_category = {}
        if DB_AVAILABLE and db_manager:
            try:
                progress_by_category = db_manager.get_progress_by_category(user['id'])
            except Exception as e:
                logger.warning(f"Error obteniendo progreso por categoría: {e}")

        # Obtener historial de ejercicios
        exercise_history = []
        if DB_AVAILABLE and db_manager:
            try:
                exercise_history = db_manager.get_user_exercise_history(user['id'], limit=20)
            except Exception as e:
                logger.warning(f"Error obteniendo historial: {e}")

        return render_template('progreso.html',
                               user=user,
                               detailed_stats=detailed_stats,
                               progress_by_category=progress_by_category,
                               exercise_history=exercise_history)

    except Exception as e:
        error_info = handle_error('PROGRESO_ERROR', e, f"Usuario: {session.get('username')}")
        return render_template('errors/500.html', error=error_info), 500


@app.route('/logros')
@login_required
def logros():
    """Página de logros del usuario"""
    try:
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))

        # Obtener logros del usuario
        user_achievements = []
        available_achievements = []

        if DB_AVAILABLE and db_manager:
            try:
                user_achievements = db_manager.get_user_achievements(user['id'])
                available_achievements = db_manager.get_available_achievements()
            except Exception as e:
                logger.warning(f"Error obteniendo logros: {e}")

        return render_template('logros.html',
                               user=user,
                               user_achievements=user_achievements,
                               available_achievements=available_achievements)

    except Exception as e:
        error_info = handle_error('LOGROS_ERROR', e, f"Usuario: {session.get('username')}")
        return render_template('errors/500.html', error=error_info), 500


# ==================== CONFIGURACIÓN ====================

@app.route('/configuracion')
@login_required
def configuracion():
    """Página de configuración del usuario"""
    try:
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))

        # Obtener configuración actual
        user_config = get_user_config(user['id'])

        # Configuración del sistema disponible
        system_config = {}
        if CONFIG_AVAILABLE:
            try:
                system_config = {
                    'themes': config.get('ui.available_themes', ['light', 'dark']),
                    'languages': config.get('app.supported_languages', ['es', 'en']),
                    'difficulty_levels': config.get('exercises.difficulty_levels', ['facil', 'medio', 'dificil'])
                }
            except Exception as e:
                logger.warning(f"Error obteniendo configuración del sistema: {e}")

        return render_template('configuracion.html',
                               user=user,
                               user_config=user_config,
                               system_config=system_config)

    except Exception as e:
        error_info = handle_error('CONFIGURACION_ERROR', e, f"Usuario: {session.get('username')}")
        return render_template('errors/500.html', error=error_info), 500


@app.route('/update_config', methods=['POST'])
@login_required
def update_config():
    """Actualizar configuración del usuario"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'message': 'Usuario no autenticado'})

        # Obtener datos de configuración
        config_data = {
            'velocidad_lectura': int(request.form.get('velocidad_lectura', 500)),
            'dificultad_preferida': request.form.get('dificultad_preferida', 'medio'),
            'tema_preferido': request.form.get('tema_preferido', 'light'),
            'notificaciones_activas': request.form.get('notificaciones_activas') == 'on',
            'sonidos_activos': request.form.get('sonidos_activos') == 'on',
            'idioma_preferido': request.form.get('idioma_preferido', 'es')
        }

        # Guardar configuración
        if DB_AVAILABLE and db_manager:
            try:
                success = db_manager.update_user_config(user['id'], config_data)

                if success:
                    return jsonify({'success': True, 'message': 'Configuración actualizada'})
                else:
                    return jsonify({'success': False, 'message': 'Error actualizando configuración'})

            except Exception as e:
                logger.error(f"Error actualizando configuración: {e}")
                return jsonify({'success': False, 'message': 'Error interno'})
        else:
            return jsonify({'success': True, 'message': 'Configuración guardada (modo demo)'})

    except Exception as e:
        error_info = handle_error('UPDATE_CONFIG_ERROR', e, f"Usuario: {session.get('username')}")
        return jsonify({'success': False, 'message': 'Error procesando configuración'})


# ==================== MANEJO DE ERRORES ====================

@app.errorhandler(404)
def not_found_error(error):
    """Manejar error 404"""
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Manejar error 500"""
    error_info = handle_error('INTERNAL_SERVER_ERROR', error)
    return render_template('errors/500.html', error=error_info), 500


@app.errorhandler(403)
def forbidden_error(error):
    """Manejar error 403"""
    return render_template('errors/403.html'), 403


# ==================== RUTAS DE SISTEMA ====================

@app.route('/health')
def health_check():
    """Endpoint de health check para monitoreo"""
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0',
            'components': {
                'database': 'healthy' if DB_AVAILABLE else 'unavailable',
                'exercises': 'healthy' if EJERCICIOS_AVAILABLE else 'unavailable',
                'config': 'healthy' if CONFIG_AVAILABLE else 'fallback'
            }
        }

        # Verificar salud de la base de datos
        if DB_AVAILABLE and db_manager:
            try:
                db_health = db_manager.health_check()
                health_status['components']['database_details'] = db_health
            except Exception as e:
                health_status['components']['database'] = 'unhealthy'
                health_status['components']['database_error'] = str(e)

        # Determinar estado general
        if health_status['components']['database'] == 'unhealthy':
            health_status['status'] = 'degraded'

        return jsonify(health_status)

    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500


@app.route('/system/info')
def system_info():
    """Información del sistema"""
    try:
        info = {
            'name': 'AlfaIA',
            'version': '2.0.0',
            'description': 'Sistema Avanzado de Alfabetización con IA',
            'environment': config.get('app.environment', 'unknown') if CONFIG_AVAILABLE else 'fallback',
            'components': {
                'database_manager': 'available' if DB_AVAILABLE else 'unavailable',
                'exercise_modules': 'available' if EJERCICIOS_AVAILABLE else 'unavailable',
                'modern_config': 'available' if CONFIG_AVAILABLE else 'fallback',
            },
            'features': {
                'user_authentication': True,
                'progress_tracking': DB_AVAILABLE,
                'achievements': DB_AVAILABLE,
                'notifications': DB_AVAILABLE,
                'analytics': DB_AVAILABLE,
                'exercise_variety': EJERCICIOS_AVAILABLE
            }
        }

        return jsonify(info)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== CONTEXTO DE TEMPLATES ====================

@app.context_processor
def inject_globals():
    """Inyectar variables globales en templates"""
    return {
        'current_user': get_current_user(),
        'system_available': {
            'database': DB_AVAILABLE,
            'exercises': EJERCICIOS_AVAILABLE,
            'config': CONFIG_AVAILABLE
        },
        'app_version': '2.0.0',
        'current_year': datetime.now().year
    }


# ==================== INICIALIZACIÓN ====================

def initialize_app():
    """Inicializar aplicación y verificar dependencias"""
    try:
        logger.info("🚀 Inicializando AlfaIA v2.0.0...")

        # Verificar configuración
        if CONFIG_AVAILABLE:
            logger.info("✅ Sistema de configuración moderno cargado")
        else:
            logger.warning("⚠️ Usando configuración de fallback")

        # Verificar base de datos
        if DB_AVAILABLE and db_manager:
            try:
                health = db_manager.health_check()
                if health['status'] == 'healthy':
                    logger.info("✅ Base de datos conectada y saludable")
                else:
                    logger.warning("⚠️ Base de datos con problemas")
            except Exception as e:
                logger.error(f"❌ Error verificando base de datos: {e}")
        else:
            logger.warning("⚠️ Base de datos no disponible - modo limitado")

        # Verificar módulos de ejercicios
        if EJERCICIOS_AVAILABLE:
            logger.info("✅ Módulos de ejercicios cargados")
        else:
            logger.warning("⚠️ Módulos de ejercicios no disponibles")

        logger.info("🎯 AlfaIA inicializado correctamente")
        return True

    except Exception as e:
        logger.error(f"❌ Error inicializando aplicación: {e}")
        return False


# ==================== MAIN ====================

if __name__ == '__main__':
    try:
        # Inicializar aplicación
        if not initialize_app():
            logger.error("❌ Fallo en la inicialización - cerrando aplicación")
            exit(1)

        # Obtener configuración de servidor
        host = '0.0.0.0'
        port = 5000
        debug = False

        if CONFIG_AVAILABLE:
            host = config.get('app.host', '0.0.0.0')
            port = config.get('app.port', 5000)
            debug = config.get('app.debug', False)
        else:
            host = os.getenv('HOST', '0.0.0.0')
            port = int(os.getenv('PORT', 5000))
            debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

        # Mostrar información de inicio
        logger.info("=" * 60)
        logger.info("🎓 ALFAIA - Sistema de Alfabetización con IA")
        logger.info("=" * 60)
        logger.info(f"🌐 Servidor: http://{host}:{port}")
        logger.info(f"🔧 Debug: {debug}")
        logger.info(f"💾 Base de datos: {'✅ Conectada' if DB_AVAILABLE else '❌ No disponible'}")
        logger.info(f"🎮 Ejercicios: {'✅ Disponibles' if EJERCICIOS_AVAILABLE else '❌ No disponibles'}")
        logger.info(f"⚙️ Configuración: {'✅ Moderna' if CONFIG_AVAILABLE else '⚠️ Fallback'}")
        logger.info("=" * 60)

        if not DB_AVAILABLE:
            logger.warning("⚠️ MODO LIMITADO: La aplicación funcionará con funcionalidades básicas")
            logger.warning("   - Usuario demo: demo_user / demo123")
            logger.warning("   - Funciones sin persistencia de datos")

        logger.info("🚀 Iniciando servidor Flask...")

        # Ejecutar aplicación
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True,
            use_reloader=debug
        )

    except KeyboardInterrupt:
        logger.info("🛑 Aplicación detenida por el usuario")
    except Exception as e:
        logger.error(f"❌ Error fatal al iniciar la aplicación: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        # Cleanup
        if DB_AVAILABLE and db_manager:
            try:
                db_manager.close_connections()
                logger.info("✅ Conexiones de base de datos cerradas")
            except Exception as e:
                logger.warning(f"⚠️ Error cerrando conexiones: {e}")

        logger.info("👋 AlfaIA finalizado correctamente")
