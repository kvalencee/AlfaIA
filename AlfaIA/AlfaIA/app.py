# app.py - Aplicación AlfaIA Completa y Corregida
# Ubicación: AlfaIA/AlfaIA/app.py

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_cors import CORS
import os
import logging
from datetime import datetime, timedelta
import json
import random

# Importar gestor de base de datos
try:
    from modules.database_manager import db_manager

    DB_AVAILABLE = db_manager.is_connected if db_manager else False
except ImportError as e:
    logging.error(f"Error importando database_manager: {e}")
    DB_AVAILABLE = False
    db_manager = None

# Importar generador de juegos y ejercicios
try:
    from modules.juegos_interactivos import JuegosInteractivos
    from modules.generador_ejercicios import GeneradorEjercicios

    juegos_generator = JuegosInteractivos()
    ejercicios_generator = GeneradorEjercicios()
    JUEGOS_AVAILABLE = True
except ImportError as e:
    logging.error(f"Error importando juegos_interactivos: {e}")
    JUEGOS_AVAILABLE = False
    juegos_generator = None
    ejercicios_generator = None

# Configurar logging básico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar Flask
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'alfaia-secret-key-2025-super-secure')

# Configuración CORS
CORS(app, origins=['http://localhost:5000', 'http://127.0.0.1:5000'])

# Configuración de la aplicación
app.config.update(
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,
    UPLOAD_FOLDER='static/uploads'
)

# Crear directorios necesarios
os.makedirs('logs', exist_ok=True)
os.makedirs('data', exist_ok=True)
os.makedirs('static/uploads', exist_ok=True)
os.makedirs('templates/errors', exist_ok=True)

# Datos de respaldo si no hay base de datos
FALLBACK_USER = {
    'id': 1,
    'username': 'demo_user',
    'nombre': 'Usuario',
    'apellido': 'Demo',
    'email': 'demo@alfaia.com'
}


# ==================== FUNCIONES AUXILIARES ====================

def get_current_user():
    """Obtener usuario actual de la sesión"""
    if 'user_id' not in session:
        return None

    user_id = session['user_id']

    if DB_AVAILABLE:
        try:
            user = db_manager.get_user_by_id(user_id)
            return user
        except Exception as e:
            logger.error(f"Error obteniendo usuario de BD: {e}")
            # Fallback a datos de sesión
            return {
                'id': session.get('user_id'),
                'username': session.get('username'),
                'nombre': session.get('nombre'),
                'apellido': session.get('apellido'),
                'email': session.get('email')
            }
    else:
        # Modo sin base de datos
        return FALLBACK_USER if user_id == 1 else None


def login_required(f):
    """Decorador para requerir login"""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


def init_user_session(user):
    """Inicializar sesión de usuario"""
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['nombre'] = user['nombre']
    session['apellido'] = user['apellido']
    session['email'] = user['email']
    session.permanent = True


def get_fallback_progress_data():
    """Datos de progreso por defecto cuando no hay BD"""
    return {
        'estadisticas': {
            'ejercicios_completados': 0,
            'tiempo_total_minutos': 0,
            'precision_promedio': 0.0,
            'racha_dias': 0,
            'puntos_totales': 0,
            'nivel_lectura': 1,
            'nivel_ejercicios': 1,
            'nivel_pronunciacion': 1
        },
        'niveles': {
            'lectura': {'nivel': 1, 'puntos': 0, 'desbloqueado': True},
            'ejercicios': {'nivel': 1, 'puntos': 0, 'desbloqueado': True},
            'pronunciacion': {'nivel': 1, 'puntos': 0, 'desbloqueado': True}
        },
        'feedback': {
            'mensaje_principal': 'Comienza a practicar para ver tu progreso',
            'insights': ['Conecta la base de datos para ver estadísticas reales'],
            'recomendaciones': ['Configura la base de datos MySQL', 'Ejecuta el script database_structure.sql']
        },
        'historial_semanal': [
            {'dia': 'Lunes', 'ejercicios': 0, 'tiempo': 0, 'puntos': 0},
            {'dia': 'Martes', 'ejercicios': 0, 'tiempo': 0, 'puntos': 0},
            {'dia': 'Miércoles', 'ejercicios': 0, 'tiempo': 0, 'puntos': 0},
            {'dia': 'Jueves', 'ejercicios': 0, 'tiempo': 0, 'puntos': 0},
            {'dia': 'Viernes', 'ejercicios': 0, 'tiempo': 0, 'puntos': 0},
            {'dia': 'Sábado', 'ejercicios': 0, 'tiempo': 0, 'puntos': 0},
            {'dia': 'Domingo', 'ejercicios': 0, 'tiempo': 0, 'puntos': 0}
        ],
        'logros': []
    }


def get_fallback_progress_data_complete():
    """Datos completos de progreso por defecto cuando no hay BD"""
    estadisticas = {
        'ejercicios_completados': 0,
        'tiempo_total_minutos': 0,
        'precision_promedio': 0.0,
        'racha_dias': 0,
        'puntos_totales': 0,
        'nivel_lectura': 1,
        'nivel_ejercicios': 1,
        'nivel_pronunciacion': 1,
        'total_vocales': 0,
        'logros_count': 0
    }

    progreso_niveles = {
        'lectura': {'nivel': 1, 'puntos': 0, 'progreso_porcentaje': 0},
        'ejercicios': {'nivel': 1, 'puntos': 0, 'progreso_porcentaje': 0},
        'pronunciacion': {'nivel': 1, 'puntos': 0, 'progreso_porcentaje': 0},
        'juegos': {'nivel': 1, 'puntos': 0, 'progreso_porcentaje': 0}
    }

    ejercicios_recientes = []
    logros = []

    reporte = {
        'mensaje_principal': 'Comienza a practicar para ver tu progreso',
        'nivel_actual': 1,
        'puntos_totales': 0,
        'tiempo_total_horas': 0.0,
        'insights': ['Conecta la base de datos para ver estadísticas reales'],
        'recomendaciones': ['Configura la base de datos MySQL', 'Ejecuta el script database_structure.sql']
    }

    return estadisticas, progreso_niveles, ejercicios_recientes, logros, reporte


def get_fallback_profile_stats():
    """Estadísticas de perfil por defecto"""
    return {
        'fecha_registro': '2024-01-15',
        'total_ejercicios': 0,
        'tiempo_total_horas': 0.0,
        'nivel_actual': 'Principiante',
        'puntos_totales': 0,
        'insignias_obtenidas': 0
    }


def get_fallback_config():
    """Configuración por defecto"""
    return {
        'velocidad_lectura': 500,
        'dificultad_preferida': 'medio',
        'tema_preferido': 'brown',
        'notificaciones_activas': True,
        'sonidos_activos': True,
        'modo_oscuro': False,
        'idioma': 'es'
    }


# ==================== RUTAS PRINCIPALES ====================

@app.route('/')
def index():
    """Página principal"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login con autenticación real"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            message = 'Por favor ingresa usuario y contraseña'
            if request.is_json:
                return jsonify({'success': False, 'message': message})
            flash(message, 'error')
            return render_template('auth/login.html')

        # Autenticación con base de datos
        if DB_AVAILABLE:
            try:
                user = db_manager.authenticate_user(username, password)
                if user:
                    init_user_session(user)

                    if request.is_json:
                        return jsonify({'success': True, 'redirect': url_for('dashboard')})

                    flash(f'¡Bienvenido de vuelta, {user["nombre"]}!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    message = 'Credenciales incorrectas. Verifica tu usuario y contraseña.'

            except Exception as e:
                logger.error(f"Error en autenticación: {e}")
                message = 'Error del servidor. Intenta de nuevo.'
        else:
            # Modo fallback sin base de datos
            if username == 'demo_user' and password == 'demo123':
                init_user_session(FALLBACK_USER)

                if request.is_json:
                    return jsonify({'success': True, 'redirect': url_for('dashboard')})

                flash('¡Bienvenido! (Modo sin base de datos)', 'success')
                return redirect(url_for('dashboard'))
            else:
                message = 'Credenciales incorrectas. Usa: demo_user / demo123 (modo sin BD)'

        if request.is_json:
            return jsonify({'success': False, 'message': message})
        flash(message, 'error')

    return render_template('auth/login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Página de registro"""
    if request.method == 'POST':
        flash('El registro está deshabilitado. Usa el usuario demo para probar la aplicación.', 'info')
        return redirect(url_for('login'))

    return render_template('auth/register.html')


@app.route('/logout')
def logout():
    """Cerrar sesión"""
    session.clear()
    flash('Has cerrado sesión correctamente', 'info')
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal del usuario con datos reales"""
    user = get_current_user()

    if DB_AVAILABLE and user:
        try:
            # Obtener datos reales de la base de datos
            estadisticas = db_manager.get_user_statistics(user['id'])

            progreso_data = {
                'estadisticas': estadisticas,
                'niveles': {
                    'lectura': {'nivel': estadisticas['nivel_lectura'],
                                'puntos': min(75, estadisticas['ejercicios_completados'] * 3), 'desbloqueado': True},
                    'ejercicios': {'nivel': estadisticas['nivel_ejercicios'],
                                   'puntos': min(60, estadisticas['ejercicios_completados'] * 2), 'desbloqueado': True},
                    'pronunciacion': {'nivel': estadisticas['nivel_pronunciacion'],
                                      'puntos': min(30, estadisticas['ejercicios_completados']), 'desbloqueado': True}
                }
            }

        except Exception as e:
            logger.error(f"Error obteniendo datos del dashboard: {e}")
            # Fallback a datos por defecto
            progreso_data = get_fallback_progress_data()
    else:
        progreso_data = get_fallback_progress_data()

    return render_template('dashboard.html', user=user, progreso=progreso_data)


# ==================== RUTAS DE PERFIL Y CONFIGURACIÓN ====================

@app.route('/perfil')
@login_required
def perfil():
    """Página de perfil del usuario con datos reales"""
    user = get_current_user()

    if DB_AVAILABLE and user:
        try:
            estadisticas = db_manager.get_user_statistics(user['id'])
            logros = db_manager.get_user_achievements(user['id'])

            estadisticas_perfil = {
                'fecha_registro': user.get('fecha_registro', '2024-01-15'),
                'total_ejercicios': estadisticas['ejercicios_completados'],
                'tiempo_total_horas': round(estadisticas['tiempo_total_minutos'] / 60, 1),
                'nivel_actual': f"Nivel {max(estadisticas['nivel_lectura'], estadisticas['nivel_ejercicios'])}",
                'puntos_totales': estadisticas['puntos_totales'],
                'insignias_obtenidas': len(logros) if logros else 0
            }

        except Exception as e:
            logger.error(f"Error obteniendo datos del perfil: {e}")
            estadisticas_perfil = get_fallback_profile_stats()
    else:
        estadisticas_perfil = get_fallback_profile_stats()

    return render_template('perfil.html', user=user, estadisticas=estadisticas_perfil)


@app.route('/configuracion')
@login_required
def configuracion():
    """Página de configuración con datos reales"""
    user = get_current_user()

    if DB_AVAILABLE and user:
        try:
            config = db_manager.get_user_settings(user['id'])
            config_usuario = {
                'velocidad_lectura': config.get('velocidad_lectura', 500),
                'dificultad_preferida': config.get('dificultad_preferida', 'medio'),
                'tema_preferido': config.get('tema_preferido', 'brown'),
                'notificaciones_activas': config.get('notificaciones_activas', True),
                'sonidos_activos': config.get('sonidos_activos', True),
                'modo_oscuro': False,
                'idioma': 'es'
            }
        except Exception as e:
            logger.error(f"Error obteniendo configuraciones: {e}")
            config_usuario = get_fallback_config()
    else:
        config_usuario = get_fallback_config()

    return render_template('configuracion.html', configuraciones=config_usuario)


# ==================== RUTA DE PROGRESO CORREGIDA ====================

@app.route('/progreso')
@app.route('/mostrar_progreso')  # Alias para compatibilidad
@login_required
def mostrar_progreso():
    """Página de progreso del usuario con datos reales - RUTA CORREGIDA"""
    user = get_current_user()

    if DB_AVAILABLE and user:
        try:
            # Obtener datos reales de la base de datos
            estadisticas = db_manager.get_user_statistics(user['id'])
            progreso_niveles = db_manager.get_progress_levels(user['id'])
            ejercicios_recientes = db_manager.get_exercises_by_user(user['id'], limit=10)
            logros = db_manager.get_user_achievements(user['id'])

            # Crear reporte de progreso
            reporte = {
                'mensaje_principal': f"Has completado {estadisticas['ejercicios_completados']} ejercicios con {estadisticas['precision_promedio']:.1f}% de precisión promedio.",
                'nivel_actual': max(estadisticas['nivel_lectura'], estadisticas['nivel_ejercicios'],
                                    estadisticas['nivel_pronunciacion']),
                'puntos_totales': estadisticas['puntos_totales'],
                'tiempo_total_horas': round(estadisticas['tiempo_total_minutos'] / 60, 1),
                'insights': [
                    f"Tu fuerte es la {'lectura' if estadisticas['nivel_lectura'] >= max(estadisticas['nivel_ejercicios'], estadisticas['nivel_pronunciacion']) else 'práctica' if estadisticas['nivel_ejercicios'] >= estadisticas['nivel_pronunciacion'] else 'pronunciación'}",
                    f"Has mantenido una racha de {estadisticas['racha_dias']} días",
                    f"Tu precisión promedio es {'excelente' if estadisticas['precision_promedio'] >= 90 else 'muy buena' if estadisticas['precision_promedio'] >= 80 else 'buena' if estadisticas['precision_promedio'] >= 70 else 'mejorable'}"
                ],
                'recomendaciones': [
                    "Intenta practicar al menos 15 minutos diarios",
                    "Varía entre diferentes tipos de ejercicios",
                    "Revisa tus errores más comunes"
                ]
            }

        except Exception as e:
            logger.error(f"Error obteniendo progreso: {e}")
            # Fallback a datos por defecto
            estadisticas, progreso_niveles, ejercicios_recientes, logros, reporte = get_fallback_progress_data_complete()
    else:
        estadisticas, progreso_niveles, ejercicios_recientes, logros, reporte = get_fallback_progress_data_complete()

    return render_template('progreso.html',
                           user=user,
                           estadisticas=estadisticas,
                           progreso_niveles=progreso_niveles,
                           ejercicios_recientes=ejercicios_recientes,
                           logros=logros,
                           reporte=reporte)


# ==================== RUTAS DE EJERCICIOS ====================

@app.route('/ejercicios')
@login_required
def ejercicios():
    """Página principal de ejercicios"""
    tipos_ejercicios = [
        {
            'id': 'diario',
            'nombre': 'Ejercicio Diario',
            'descripcion': 'Rutina diaria de ejercicios personalizados',
            'icono': 'calendar-day',
            'url': '/ejercicios/diario',
            'dificultad': 'Variada',
            'tiempo': '15 min'
        },
        {
            'id': 'lectura',
            'nombre': 'Lectura Comprensiva',
            'descripcion': 'Mejora tu comprensión lectora',
            'icono': 'book-open',
            'url': '/ejercicios/lectura',
            'dificultad': 'Intermedio',
            'tiempo': '10 min'
        },
        {
            'id': 'pronunciacion',
            'nombre': 'Pronunciación',
            'descripcion': 'Practica la pronunciación correcta',
            'icono': 'microphone',
            'url': '/ejercicios/pronunciacion',
            'dificultad': 'Básico',
            'tiempo': '8 min'
        },
        {
            'id': 'ortografia',
            'nombre': 'Ortografía',
            'descripcion': 'Ejercicios de escritura correcta',
            'icono': 'spell-check',
            'url': '/ejercicios/ortografia',
            'dificultad': 'Intermedio',
            'tiempo': '12 min'
        }
    ]
    return render_template('ejercicios.html', ejercicios=tipos_ejercicios)


@app.route('/ejercicios/diario')
@login_required
def ejercicio_diario():
    """Ejercicio diario"""
    nivel = request.args.get('nivel', 1, type=int)

    ejercicios_pendientes = [
        {
            'tipo': 'ordenar_frase',
            'titulo': 'Ordenar palabras',
            'url': url_for('ordenar_frase', nivel=nivel)
        },
        {
            'tipo': 'completar_palabra',
            'titulo': 'Completar palabras',
            'url': url_for('completar_palabra', nivel=nivel)
        },
        {
            'tipo': 'pronunciacion',
            'titulo': 'Pronunciar vocales',
            'url': url_for('ejercicio_pronunciacion', nivel=nivel)
        },
        {
            'tipo': 'lectura',
            'titulo': 'Lectura comprensiva',
            'url': url_for('ejercicios_lectura', nivel=nivel)
        }
    ]

    return render_template('ejercicios/diario.html', ejercicios=ejercicios_pendientes)


@app.route('/ejercicios/lectura')
@app.route('/lectura')  # Alias para compatibilidad con dashboard
@login_required
def ejercicios_lectura():
    """Ejercicios de lectura comprensiva"""
    nivel = request.args.get('nivel', 1, type=int)
    tema = request.args.get('tema', 'general')

    ejercicio_actual = ejercicios_generator.generar_lectura_guiada(nivel, tema)

    return render_template('ejercicios/lectura.html', ejercicio=ejercicio_actual)


@app.route('/ejercicios/pronunciacion')
@login_required
def ejercicio_pronunciacion():
    """Ejercicios de pronunciación"""
    nivel = request.args.get('nivel', 1, type=int)
    tipo = request.args.get('tipo', 'vocales')

    ejercicio_actual = ejercicios_generator.generar_ejercicio_pronunciacion(tipo, nivel)

    return render_template('ejercicios/pronunciacion.html', ejercicio=ejercicio_actual)


@app.route('/ejercicios/ortografia')
@login_required
def ejercicio_ortografia():
    """Ejercicios de ortografía"""
    ejercicio_actual = {
        'palabras': [
            {'incorrecta': 'kasa', 'correcta': 'casa'},
            {'incorrecta': 'gato', 'correcta': 'gato'},
            {'incorrecta': 'arbol', 'correcta': 'árbol'},
            {'incorrecta': 'lapiz', 'correcta': 'lápiz'}
        ],
        'nivel': 1,
        'puntos_posibles': 25
    }
    return render_template('ejercicios/ortografia.html', ejercicio=ejercicio_actual)


@app.route('/ejercicios/ordenar-frase')
@login_required
def ordenar_frase():
    """Ejercicio de ordenar frases"""
    nivel = request.args.get('nivel', 1, type=int)
    ejercicio = ejercicios_generator.generar_ordena_frase(nivel)
    return render_template('ejercicios/ordenar_frase.html', ejercicio=ejercicio)


@app.route('/ejercicios/completar-palabra')
@login_required
def completar_palabra():
    """Ejercicio de completar palabras"""
    nivel = request.args.get('nivel', 1, type=int)
    ejercicio = ejercicios_generator.generar_completa_palabra(nivel)
    return render_template('ejercicios/completar_palabra.html', ejercicio=ejercicio)


# ==================== RUTAS DE JUEGOS CORREGIDAS ====================

@app.route('/juegos')
@login_required
def juegos():
    """Página principal de juegos - RUTA CORREGIDA"""
    juegos_disponibles = [
        {
            'id': 'memoria',
            'nombre': 'Juego de Memoria',
            'descripcion': 'Encuentra las parejas de palabras sinónimas',
            'icono': 'brain',
            'url': '/juegos/memoria',
            'dificultad': 'Fácil',
            'jugadores': '1',
            'tiempo': '5-10 min'
        },
        {
            'id': 'ahorcado',
            'nombre': 'Ahorcado',
            'descripcion': 'Adivina la palabra letra por letra',
            'icono': 'spell-check',
            'url': '/juegos/ahorcado',
            'dificultad': 'Medio',
            'jugadores': '1',
            'tiempo': '3-7 min'
        },
        {
            'id': 'trivia',
            'nombre': 'Trivia Educativa',
            'descripcion': 'Responde preguntas sobre diferentes temas educativos',
            'icono': 'question-circle',
            'url': '/juegos/trivia',
            'dificultad': 'Variada',
            'jugadores': '1',
            'tiempo': '10-15 min'
        },
        {
            'id': 'crucigrama',
            'nombre': 'Crucigrama',
            'descripcion': 'Completa el crucigrama con las palabras correctas',
            'icono': 'th',
            'url': '/juegos/crucigrama',
            'dificultad': 'Intermedio',
            'jugadores': '1',
            'tiempo': '15-20 min'
        }
    ]
    return render_template('juegos.html', juegos=juegos_disponibles)


@app.route('/juegos/memoria')
@login_required
def juego_memoria():
    """Juego de memoria - RUTA CORREGIDA"""
    try:
        nivel = request.args.get('nivel', 1, type=int)

        # Usar generador de juegos si está disponible
        if JUEGOS_AVAILABLE and juegos_generator:
            juego_data = juegos_generator.generar_ahorcado(nivel)
            return render_template('juegos/ahorcado.html',
                                   palabra_data=juego_data,
                                   nivel=nivel)
        else:
            # Palabras por nivel por defecto
            palabras_por_nivel = {
                1: [
                    {'palabra': 'GATO', 'pista': 'Animal doméstico que dice miau'},
                    {'palabra': 'CASA', 'pista': 'Lugar donde vives'},
                    {'palabra': 'SOL', 'pista': 'Estrella que nos da luz'},
                    {'palabra': 'MAR', 'pista': 'Agua salada muy grande'}
                ],
                2: [
                    {'palabra': 'ESCUELA', 'pista': 'Lugar donde los niños aprenden'},
                    {'palabra': 'FAMILIA', 'pista': 'Papá, mamá e hijos'},
                    {'palabra': 'JARDIN', 'pista': 'Lugar con plantas y flores'},
                    {'palabra': 'MUSICA', 'pista': 'Arte de los sonidos'}
                ],
                3: [
                    {'palabra': 'NAVEGACION', 'pista': 'Acción de dirigir una embarcación'},
                    {'palabra': 'COMPRENSION', 'pista': 'Capacidad de entender algo'},
                    {'palabra': 'EXTRAORDINARIO', 'pista': 'Algo fuera de lo común'},
                    {'palabra': 'REFRIGERADOR', 'pista': 'Electrodoméstico para enfriar'}
                ]
            }

            palabras = palabras_por_nivel.get(nivel, palabras_por_nivel[1])
            palabra_data = random.choice(palabras)

            return render_template('juegos/ahorcado.html',
                                   palabra_data=palabra_data,
                                   nivel=nivel)
    except Exception as e:
        logger.error(f"Error generando juego de ahorcado: {e}")
        flash('Error cargando el juego. Inténtalo de nuevo.', 'error')
        return redirect('/juegos')


@app.route('/juegos/trivia')
@login_required
def juego_trivia():
    """Juego de trivia - RUTA CORREGIDA"""
    try:
        categoria = request.args.get('categoria', None)
        nivel = request.args.get('nivel', 1, type=int)

        if JUEGOS_AVAILABLE and juegos_generator:
            # Generar múltiples preguntas para la sesión
            preguntas = []
            categorias_disponibles = juegos_generator.obtener_categorias_trivia()

            # Generar 5-8 preguntas aleatorias
            num_preguntas = random.randint(5, 8)
            for _ in range(num_preguntas):
                cat_aleatoria = categoria if categoria else random.choice(categorias_disponibles)
                pregunta = juegos_generator.generar_trivia(cat_aleatoria, nivel)
                preguntas.append(pregunta)

            return render_template('juegos/trivia.html', preguntas=preguntas)
        else:
            # Preguntas de trivia por defecto
            preguntas = [
                {
                    'pregunta': '¿Cuántas vocales tiene el español?',
                    'opciones': ['3', '5', '7', '10'],
                    'respuesta_correcta': '5',
                    'explicacion': 'El español tiene 5 vocales: a, e, i, o, u'
                },
                {
                    'pregunta': '¿Qué palabra es un sinónimo de "grande"?',
                    'opciones': ['pequeño', 'enorme', 'medio', 'chico'],
                    'respuesta_correcta': 'enorme',
                    'explicacion': 'Enorme significa de gran tamaño, igual que grande'
                },
                {
                    'pregunta': '¿Cuál es el plural de "lápiz"?',
                    'opciones': ['lápizes', 'lápices', 'lapizes', 'lapices'],
                    'respuesta_correcta': 'lápices',
                    'explicacion': 'El plural correcto de lápiz es lápices'
                },
                {
                    'pregunta': '¿Qué tipo de palabra es "rápidamente"?',
                    'opciones': ['sustantivo', 'adjetivo', 'adverbio', 'verbo'],
                    'respuesta_correcta': 'adverbio',
                    'explicacion': 'Las palabras terminadas en -mente son adverbios'
                },
                {
                    'pregunta': '¿Cuál lleva tilde?',
                    'opciones': ['cancion', 'corazon', 'árbol', 'feliz'],
                    'respuesta_correcta': 'árbol',
                    'explicacion': 'Árbol lleva tilde por ser una palabra grave terminada en consonante que no es n o s'
                }
            ]

            # Mezclar preguntas
            random.shuffle(preguntas)

            return render_template('juegos/trivia.html', preguntas=preguntas[:5])
    except Exception as e:
        logger.error(f"Error generando trivia: {e}")
        flash('Error cargando la trivia. Inténtalo de nuevo.', 'error')
        return redirect('/juegos')


@app.route('/juegos/crucigrama')
@login_required
def juego_crucigrama():
    """Juego de crucigrama - RUTA CORREGIDA"""
    try:
        nivel = request.args.get('nivel', 1, type=int)

        if JUEGOS_AVAILABLE and juegos_generator:
            crucigrama_data = juegos_generator.generar_crucigrama(nivel)
            return render_template('juegos/crucigrama.html',
                                   crucigrama=crucigrama_data,
                                   nivel=nivel)
        else:
            # Crucigrama simple por defecto
            crucigrama_data = {
                "titulo": "Crucigrama Básico",
                "tamaño": 8,
                "grid": [
                    ["", "", "", "C", "", "", "", ""],
                    ["", "", "", "A", "", "", "", ""],
                    ["G", "A", "T", "O", "", "", "", ""],
                    ["", "", "", "L", "", "", "", ""],
                    ["", "", "", "O", "", "", "", ""],
                    ["", "", "", "R", "", "", "", ""],
                    ["", "", "", "", "", "", "", ""],
                    ["", "", "", "", "", "", "", ""]
                ],
                "palabras": [
                    {
                        "palabra": "GATO",
                        "fila": 2,
                        "columna": 0,
                        "direccion": "horizontal",
                        "pista": "Animal doméstico que dice miau",
                        "numero": 1
                    },
                    {
                        "palabra": "CALOR",
                        "fila": 0,
                        "columna": 3,
                        "direccion": "vertical",
                        "pista": "Sensación de temperatura alta",
                        "numero": 2
                    }
                ],
                "puntos": 100
            }

            return render_template('juegos/crucigrama.html',
                                   crucigrama=crucigrama_data,
                                   nivel=nivel)
    except Exception as e:
        logger.error(f"Error generando crucigrama: {e}")
        flash('Error cargando el crucigrama. Inténtalo de nuevo.', 'error')
        return redirect('/juegos')


@app.route('/juegos/rapido')
@login_required
def juego_rapido():
    """Juego rápido aleatorio - RUTA CORREGIDA"""
    juegos_disponibles = [
        '/juegos/memoria',
        '/juegos/ahorcado',
        '/juegos/trivia'
    ]
    juego_seleccionado = random.choice(juegos_disponibles)
    return redirect(juego_seleccionado)


# ==================== OTRAS RUTAS IMPORTANTES ====================

@app.route('/logros')
@login_required
def logros():
    """Página de logros con datos reales"""
    user = get_current_user()

    if DB_AVAILABLE and user:
        try:
            logros_obtenidos = db_manager.get_user_achievements(user['id'])
            if not logros_obtenidos:
                logros_obtenidos = []
        except Exception as e:
            logger.error(f"Error obteniendo logros: {e}")
            logros_obtenidos = []
    else:
        logros_obtenidos = []

    return render_template('logros.html', logros=logros_obtenidos)


# ==================== API ROUTES CON BASE DE DATOS ====================

@app.route('/api/ejercicios/completar', methods=['POST'])
@login_required
def api_completar_ejercicio():
    """API para completar ejercicio y guardar en BD"""
    try:
        data = request.get_json()
        user = get_current_user()

        if not user:
            return jsonify({'success': False, 'message': 'Usuario no encontrado'})

        ejercicio_tipo = data.get('tipo', 'lectura')
        ejercicio_nombre = data.get('nombre', 'Ejercicio')
        puntos_obtenidos = data.get('puntos', 0)
        precision = data.get('precision', 0)
        tiempo_segundos = data.get('tiempo_segundos', 0)
        datos_adicionales = data.get('datos_adicionales', {})

        # Detectar si es un juego y usar el sistema mejorado de guardado
        if ejercicio_tipo in ['memoria', 'ahorcado', 'trivia', 'crucigrama']:
            return save_game_result_to_db(
                user['id'], ejercicio_tipo, ejercicio_nombre,
                puntos_obtenidos, precision, tiempo_segundos, datos_adicionales
            )

        # Para ejercicios regulares, usar el sistema original
        if DB_AVAILABLE:
            success = db_manager.save_exercise_result(
                user['id'], ejercicio_tipo, ejercicio_nombre,
                puntos_obtenidos, precision, tiempo_segundos, datos_adicionales
            )

            if success:
                estadisticas = db_manager.get_user_statistics(user['id'])
                return jsonify({
                    'success': True,
                    'message': '¡Ejercicio completado exitosamente!',
                    'data': {
                        'puntos_obtenidos': puntos_obtenidos,
                        'nuevo_total_puntos': estadisticas.get('puntos_totales', puntos_obtenidos),
                        'precision': precision
                    }
                })
            else:
                return jsonify({'success': False, 'message': 'Error guardando ejercicio'})
        else:
            return jsonify({
                'success': True,
                'message': '¡Ejercicio completado! (modo offline)',
                'data': {
                    'puntos_obtenidos': puntos_obtenidos,
                    'precision': precision
                }
            })

    except Exception as e:
        logger.error(f"Error completando ejercicio: {e}")
        return jsonify({'success': False, 'message': 'Error interno del servidor'})


def save_game_result_to_db(user_id, game_type, game_name, points, accuracy, time_seconds, additional_data):
    """Función auxiliar para guardar resultados de juegos en la base de datos"""
    try:
        if DB_AVAILABLE:
            # Guardar en base de datos
            success = db_manager.save_exercise_result(
                user_id, game_type, game_name, points, accuracy, time_seconds, additional_data
            )

            if success:
                # Obtener estadísticas actualizadas
                estadisticas = db_manager.get_user_statistics(user_id)

                # Verificar si se desbloquearon logros
                try:
                    # Llamar al procedimiento de verificación de logros
                    with db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.callproc('VerificarLogros', [user_id])
                        conn.commit()
                        cursor.close()
                except Exception as e:
                    logger.warning(f"Error verificando logros: {e}")

                return jsonify({
                    'success': True,
                    'message': f'¡Juego completado exitosamente! Ganaste {points} puntos.',
                    'data': {
                        'puntos_obtenidos': points,
                        'nuevo_total_puntos': estadisticas.get('puntos_totales', points),
                        'precision': accuracy,
                        'tiempo_empleado': time_seconds,
                        'estadisticas_actualizadas': estadisticas
                    }
                })
            else:
                return jsonify({'success': False, 'message': 'Error guardando resultado del juego'})
        else:
            # Modo sin base de datos
            return jsonify({
                'success': True,
                'message': f'¡Juego completado! Ganaste {points} puntos (modo offline)',
                'data': {
                    'puntos_obtenidos': points,
                    'precision': accuracy,
                    'tiempo_empleado': time_seconds
                }
            })

    except Exception as e:
        logger.error(f"Error guardando resultado del juego: {e}")
        return jsonify({'success': False, 'message': 'Error interno del servidor'})


@app.route('/api/progreso')
@login_required
def api_progreso():
    """API para obtener progreso del usuario"""
    try:
        user = get_current_user()

        if not user:
            return jsonify({'success': False, 'message': 'Usuario no encontrado'})

        if DB_AVAILABLE:
            estadisticas = db_manager.get_user_statistics(user['id'])
            return jsonify({'success': True, 'data': estadisticas})
        else:
            return jsonify({'success': True, 'data': get_fallback_progress_data()['estadisticas']})

    except Exception as e:
        logger.error(f"Error obteniendo progreso: {e}")
        return jsonify({'success': False, 'message': 'Error obteniendo progreso'})


@app.route('/api/configuracion', methods=['POST'])
@login_required
def api_actualizar_configuracion():
    """API para actualizar configuración del usuario"""
    try:
        user = get_current_user()
        data = request.get_json()

        if not user:
            return jsonify({'success': False, 'message': 'Usuario no encontrado'})

        if DB_AVAILABLE:
            success = db_manager.update_user_settings(user['id'], data)
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Configuración actualizada exitosamente'
                })
            else:
                return jsonify({'success': False, 'message': 'Error actualizando configuración'})
        else:
            return jsonify({
                'success': True,
                'message': 'Configuración guardada localmente (modo offline)'
            })

    except Exception as e:
        logger.error(f"Error actualizando configuración: {e}")
        return jsonify({'success': False, 'message': 'Error interno del servidor'})


# ==================== MANEJO DE ERRORES ====================

@app.errorhandler(404)
def page_not_found(error):
    """Página de error 404"""
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Página de error 500"""
    return render_template('errors/500.html'), 500


@app.errorhandler(403)
def forbidden(error):
    """Página de error 403"""
    return render_template('errors/403.html'), 403


# ==================== FILTROS DE TEMPLATE ====================

@app.template_filter('tojsonfilter')
def to_json_filter(obj):
    """Filtro para convertir objetos Python a JSON en templates"""
    return json.dumps(obj, ensure_ascii=False)


# ==================== CONTEXTO GLOBAL DE TEMPLATES ====================

@app.context_processor
def inject_global_vars():
    """Inyectar variables globales a todos los templates"""
    return {
        'DB_AVAILABLE': DB_AVAILABLE,
        'JUEGOS_AVAILABLE': JUEGOS_AVAILABLE,
        'current_year': datetime.now().year
    }


# ==================== INICIALIZACIÓN Y MAIN ====================

if __name__ == '__main__':
    # Información de inicio
    print("🚀 Iniciando AlfaIA...")
    print(f"📊 Base de datos: {'✅ Conectada' if DB_AVAILABLE else '❌ No disponible'}")
    print(f"🎮 Generador de juegos: {'✅ Disponible' if JUEGOS_AVAILABLE else '❌ No disponible'}")
    print(f"🌐 Servidor: http://127.0.0.1:5000")

    # Ejecutar la aplicación
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True,
        use_reloader=True
    )
