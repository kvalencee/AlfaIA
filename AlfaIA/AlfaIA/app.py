# app.py - Aplicación AlfaIA con Base de Datos Real
# Ubicación: AlfaIA/AlfaIA/app.py

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_cors import CORS
import os
import logging
from datetime import datetime, timedelta
import json

# Importar gestor de base de datos
try:
    from modules.database_manager import db_manager

    DB_AVAILABLE = db_manager.is_connected
except ImportError as e:
    logging.error(f"Error importando database_manager: {e}")
    DB_AVAILABLE = False
    db_manager = None

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
        # Para demostración, redirigir al login
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


def get_fallback_progress_data():
    """Datos de progreso por defecto cuando no hay BD"""
    return {
        'estadisticas': {
            'ejercicios_completados': 0,
            'tiempo_total_minutos': 0,
            'precision_promedio': 0.0,
            'racha_dias': 0,
            'puntos_totales': 0
        },
        'niveles': {
            'lectura': {'nivel': 1, 'puntos': 0, 'desbloqueado': True},
            'ejercicios': {'nivel': 1, 'puntos': 0, 'desbloqueado': True},
            'pronunciacion': {'nivel': 1, 'puntos': 0, 'desbloqueado': True}
        }
    }


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


@app.route('/progreso')
@login_required
def progreso():
    """Página de progreso del usuario con datos reales"""
    user = get_current_user()

    if DB_AVAILABLE and user:
        try:
            # Obtener datos reales de la base de datos
            estadisticas = db_manager.get_user_statistics(user['id'])
            progreso_niveles = db_manager.get_progress_levels(user['id'])
            ejercicios_recientes = db_manager.get_exercises_by_user(user['id'], 10)
            estadisticas_diarias = db_manager.get_daily_stats(user['id'], 7)
            logros = db_manager.get_user_achievements(user['id'])

            # Generar insights basados en datos reales
            insights = generate_real_insights(estadisticas, ejercicios_recientes)
            recomendaciones = generate_real_recommendations(estadisticas, progreso_niveles)

            datos_progreso = {
                'estadisticas': estadisticas,
                'progreso_niveles': progreso_niveles,
                'reporte': {
                    'mensaje_principal': get_progress_message(estadisticas),
                    'insights': insights,
                    'recomendaciones': recomendaciones
                },
                'historial_semanal': format_daily_stats(estadisticas_diarias),
                'logros': logros
            }

        except Exception as e:
            logger.error(f"Error obteniendo datos de progreso: {e}")
            datos_progreso = get_fallback_progress_report()
    else:
        datos_progreso = get_fallback_progress_report()

    return render_template('progreso.html',
                           user=user,
                           progreso=datos_progreso,
                           estadisticas=datos_progreso['estadisticas'],
                           progreso_niveles=datos_progreso['progreso_niveles'],
                           reporte=datos_progreso['reporte'],
                           historial_semanal=datos_progreso['historial_semanal'])


def generate_real_insights(estadisticas, ejercicios_recientes):
    """Generar insights basados en datos reales"""
    insights = []

    if estadisticas['ejercicios_completados'] > 0:
        if estadisticas['precision_promedio'] >= 85:
            insights.append(f"¡Excelente! Tu precisión promedio es del {estadisticas['precision_promedio']:.1f}%")
        elif estadisticas['precision_promedio'] >= 70:
            insights.append(f"Buen trabajo, tu precisión es del {estadisticas['precision_promedio']:.1f}%")
        else:
            insights.append(f"Tu precisión actual es del {estadisticas['precision_promedio']:.1f}%, puedes mejorar")

    if estadisticas['racha_dias'] > 0:
        insights.append(f"Llevas {estadisticas['racha_dias']} días de racha consecutiva")

    if estadisticas['tiempo_total_minutos'] > 60:
        horas = estadisticas['tiempo_total_minutos'] / 60
        insights.append(f"Has dedicado {horas:.1f} horas al aprendizaje")

    if estadisticas['ejercicios_completados'] >= 10:
        insights.append("Has completado más de 10 ejercicios, ¡sigue así!")

    if not insights:
        insights.append("¡Bienvenido! Comienza a practicar para ver tu progreso")

    return insights


def generate_real_recommendations(estadisticas, progreso_niveles):
    """Generar recomendaciones basadas en datos reales"""
    recomendaciones = []

    # Analizar niveles más bajos
    niveles = [(k, v['nivel_actual']) for k, v in progreso_niveles.items()]
    nivel_mas_bajo = min(niveles, key=lambda x: x[1])

    if nivel_mas_bajo[1] < 2:
        recomendaciones.append(f"Enfócate en ejercicios de {nivel_mas_bajo[0]} para subir de nivel")

    if estadisticas['precision_promedio'] < 70:
        recomendaciones.append("Practica más despacio para mejorar tu precisión")

    if estadisticas['racha_dias'] == 0:
        recomendaciones.append("Intenta practicar todos los días para crear una racha")

    if estadisticas['ejercicios_completados'] < 5:
        recomendaciones.append("Completa al menos 5 ejercicios para desbloquear más funciones")

    recomendaciones.append("Dedica 15 minutos diarios para ver mejores resultados")

    return recomendaciones


def get_progress_message(estadisticas):
    """Generar mensaje principal de progreso"""
    if estadisticas['ejercicios_completados'] == 0:
        return "¡Bienvenido a AlfaIA! Comienza tu aventura de aprendizaje"
    elif estadisticas['precision_promedio'] >= 85:
        return "¡Excelente progreso! Eres un estudiante ejemplar"
    elif estadisticas['ejercicios_completados'] >= 10:
        return "¡Buen trabajo! Estás progresando constantemente"
    else:
        return "Sigue practicando, cada ejercicio te acerca a tu meta"


def format_daily_stats(estadisticas_diarias):
    """Formatear estadísticas diarias para la plantilla"""
    if not estadisticas_diarias:
        # Generar datos de ejemplo para la semana actual
        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        return [{'dia': dia, 'ejercicios': 0, 'tiempo': 0, 'puntos': 0} for dia in dias]

    # Convertir datos reales
    formatted = []
    for stat in estadisticas_diarias:
        formatted.append({
            'dia': stat['fecha'].strftime('%A') if hasattr(stat['fecha'], 'strftime') else str(stat['fecha']),
            'ejercicios': stat['ejercicios_completados'],
            'tiempo': stat['tiempo_estudiado_minutos'],
            'puntos': stat['puntos_obtenidos']
        })

    return formatted


def get_fallback_progress_report():
    """Reporte de progreso por defecto"""
    return {
        'estadisticas': {
            'ejercicios_completados': 0,
            'precision_promedio': 0.0,
            'racha_dias': 0,
            'total_vocales': 0,
            'tiempo_total_minutos': 0,
            'puntos_totales': 0
        },
        'progreso_niveles': {
            'lectura': {'nivel_actual': 1, 'progreso_porcentaje': 0, 'puntos_actuales': 0, 'puntos_necesarios': 100},
            'ejercicios': {'nivel_actual': 1, 'progreso_porcentaje': 0, 'puntos_actuales': 0, 'puntos_necesarios': 100},
            'pronunciacion': {'nivel_actual': 1, 'progreso_porcentaje': 0, 'puntos_actuales': 0,
                              'puntos_necesarios': 100},
            'juegos': {'nivel_actual': 1, 'progreso_porcentaje': 0, 'puntos_actuales': 0, 'puntos_necesarios': 100}
        },
        'reporte': {
            'mensaje_principal': '¡Bienvenido! Comienza a practicar para ver tu progreso',
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
    ejercicios_pendientes = [
        {'tipo': 'ordenar_frase', 'titulo': 'Ordenar palabras', 'dificultad': 2, 'url': '/ejercicios/ordenar-frase'},
        {'tipo': 'completar_palabra', 'titulo': 'Completar palabras', 'dificultad': 1,
         'url': '/ejercicios/completar-palabra'},
        {'tipo': 'pronunciacion', 'titulo': 'Pronunciar vocales', 'dificultad': 1, 'url': '/ejercicios/pronunciacion'},
        {'tipo': 'lectura', 'titulo': 'Lectura comprensiva', 'dificultad': 2, 'url': '/ejercicios/lectura'},
        {'tipo': 'trivia', 'titulo': 'Pregunta del día', 'dificultad': 3, 'url': '/juegos/trivia'}
    ]
    return render_template('ejercicios/diario.html', ejercicios=ejercicios_pendientes)


@app.route('/ejercicios/lectura')
@login_required
def ejercicios_lectura():
    """Ejercicios de lectura comprensiva"""
    ejercicio_actual = {
        'titulo': 'El Día en el Parque',
        'texto': 'María salió temprano hacia el parque. El sol brillaba intensamente y los pájaros cantaban en los árboles. Decidió sentarse en un banco cerca del lago para leer su libro favorito.',
        'preguntas': [
            {
                'pregunta': '¿A dónde fue María?',
                'opciones': ['A la biblioteca', 'Al parque', 'A la escuela', 'A casa'],
                'respuesta_correcta': 'Al parque'
            },
            {
                'pregunta': '¿Cómo estaba el tiempo?',
                'opciones': ['Lluvioso', 'Nublado', 'Soleado', 'Ventoso'],
                'respuesta_correcta': 'Soleado'
            }
        ],
        'nivel': 2,
        'puntos_posibles': 20
    }
    return render_template('ejercicios/lectura.html', ejercicio=ejercicio_actual)


# Alias para compatibilidad
@app.route('/lectura')
@login_required
def lectura():
    return redirect(url_for('ejercicios_lectura'))


@app.route('/ejercicios/pronunciacion')
@login_required
def ejercicios_pronunciacion():
    """Ejercicios de pronunciación"""
    ejercicio_actual = {
        'tipo': 'vocales',
        'palabras': [
            {'palabra': 'casa', 'audio_url': '/static/audio/casa.mp3'},
            {'palabra': 'mesa', 'audio_url': '/static/audio/mesa.mp3'},
            {'palabra': 'piso', 'audio_url': '/static/audio/piso.mp3'},
            {'palabra': 'lobo', 'audio_url': '/static/audio/lobo.mp3'},
            {'palabra': 'luna', 'audio_url': '/static/audio/luna.mp3'}
        ],
        'instrucciones': 'Escucha cada palabra y repítela en voz alta',
        'nivel': 1,
        'puntos_posibles': 15
    }
    return render_template('ejercicios/pronunciacion.html', ejercicio=ejercicio_actual)


@app.route('/ejercicios/ortografia')
@login_required
def ejercicios_ortografia():
    """Ejercicios de ortografía"""
    ejercicio_actual = {
        'tipo': 'completar_palabras',
        'palabras': [
            {'incompleta': 'c_sa', 'completa': 'casa', 'pista': 'Lugar donde vives'},
            {'incompleta': 'esc_ela', 'completa': 'escuela', 'pista': 'Lugar donde estudias'},
            {'incompleta': 'fam_lia', 'completa': 'familia', 'pista': 'Tus seres queridos'},
            {'incompleta': 'am_go', 'completa': 'amigo', 'pista': 'Persona que te quiere'},
        ],
        'instrucciones': 'Completa las palabras agregando la vocal faltante',
        'nivel': 1,
        'puntos_posibles': 25
    }
    return render_template('ejercicios/ortografia.html', ejercicio=ejercicio_actual)


@app.route('/ejercicios/ordenar-frase')
@login_required
def ordenar_frase():
    """Ejercicio de ordenar frases"""
    nivel = request.args.get('nivel', 1, type=int)
    ejercicio = {
        'frase_correcta': 'El gato come pescado',
        'palabras_desordenadas': ['pescado', 'El', 'come', 'gato'],
        'nivel': nivel,
        'puntos': nivel * 10
    }
    return render_template('ejercicios/ordenar_frase.html', ejercicio=ejercicio)


@app.route('/ejercicios/completar-palabra')
@login_required
def completar_palabra():
    """Ejercicio de completar palabras"""
    nivel = request.args.get('nivel', 1, type=int)
    ejercicio = {
        'palabra_incompleta': 'c_sa',
        'palabra_completa': 'casa',
        'nivel': nivel,
        'puntos': 15,
        'pista': 'Lugar donde vives'
    }
    return render_template('ejercicios/completar_palabra.html', ejercicio=ejercicio)


# ==================== RUTAS DE JUEGOS ====================

@app.route('/juegos')
@login_required
def juegos():
    """Página principal de juegos"""
    juegos_disponibles = [
        {
            'id': 'memoria',
            'nombre': 'Juego de Memoria',
            'descripcion': 'Encuentra las parejas de palabras',
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
            'descripcion': 'Responde preguntas sobre diferentes temas',
            'icono': 'question-circle',
            'url': '/juegos/trivia',
            'dificultad': 'Variada',
            'jugadores': '1',
            'tiempo': '10-15 min'
        }
    ]
    return render_template('juegos.html', juegos=juegos_disponibles)


@app.route('/juegos/rapido')
@login_required
def juego_rapido():
    """Juego rápido aleatorio"""
    import random
    juegos_disponibles = [
        {'nombre': 'Memoria', 'url': '/juegos/memoria'},
        {'nombre': 'Ahorcado', 'url': '/juegos/ahorcado'},
        {'nombre': 'Trivia', 'url': '/juegos/trivia'}
    ]
    juego_seleccionado = random.choice(juegos_disponibles)
    return redirect(juego_seleccionado['url'])


@app.route('/juegos/memoria')
@login_required
def juego_memoria():
    """Juego de memoria"""
    nivel = request.args.get('nivel', 1, type=int)
    pares = [
        ('Gato', 'Felino'), ('Perro', 'Canino'), ('Sol', 'Estrella'),
        ('Casa', 'Hogar'), ('Libro', 'Lectura'), ('Agua', 'Líquido')
    ]
    return render_template('juegos/memoria.html', pares=pares[:3 * nivel], nivel=nivel)


@app.route('/juegos/ahorcado')
@login_required
def juego_ahorcado():
    """Juego del ahorcado"""
    nivel = request.args.get('nivel', 1, type=int)
    palabras = [
        {'palabra': 'GATO', 'pista': 'Animal doméstico que dice miau'},
        {'palabra': 'CASA', 'pista': 'Lugar donde vives'},
        {'palabra': 'ESCUELA', 'pista': 'Lugar donde aprendes'},
    ]
    import random
    palabra_data = random.choice(palabras)
    return render_template('juegos/ahorcado.html', palabra_data=palabra_data, nivel=nivel)


@app.route('/juegos/trivia')
@login_required
def juego_trivia():
    """Juego de trivia"""
    preguntas = [
        {
            'pregunta': '¿Cuántas vocales tiene el español?',
            'opciones': ['3', '5', '7', '10'],
            'respuesta_correcta': '5'
        },
        {
            'pregunta': '¿Qué palabra es un sinónimo de "grande"?',
            'opciones': ['pequeño', 'enorme', 'medio', 'chico'],
            'respuesta_correcta': 'enorme'
        }
    ]
    return render_template('juegos/trivia.html', preguntas=preguntas)


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

        if DB_AVAILABLE:
            # Guardar en base de datos
            success = db_manager.save_exercise_result(
                user['id'], ejercicio_tipo, ejercicio_nombre,
                puntos_obtenidos, precision, tiempo_segundos, datos_adicionales
            )

            if success:
                # Obtener estadísticas actualizadas
                estadisticas = db_manager.get_user_statistics(user['id'])

                return jsonify({
                    'success': True,
                    'message': '¡Ejercicio completado exitosamente!',
                    'data': {
                        'puntos_obtenidos': puntos_obtenidos,
                        'nuevo_total_puntos': estadisticas['puntos_totales'],
                        'precision': precision,
                        'nivel_actualizado': False  # TODO: implementar lógica de niveles
                    }
                })
            else:
                return jsonify({'success': False, 'message': 'Error guardando ejercicio'})
        else:
            # Modo sin base de datos
            return jsonify({
                'success': True,
                'message': '¡Ejercicio completado! (Modo sin BD)',
                'data': {
                    'puntos_obtenidos': puntos_obtenidos,
                    'nuevo_total_puntos': puntos_obtenidos,
                    'precision': precision,
                    'nivel_actualizado': False
                }
            })

    except Exception as e:
        logger.error(f"Error completando ejercicio: {e}")
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
                return jsonify({'success': True, 'message': 'Configuración actualizada'})
            else:
                return jsonify({'success': False, 'message': 'Error actualizando configuración'})
        else:
            return jsonify({'success': True, 'message': 'Configuración guardada (modo sin BD)'})

    except Exception as e:
        logger.error(f"Error actualizando configuración: {e}")
        return jsonify({'success': False, 'message': 'Error interno del servidor'})


# ==================== RUTAS DE DESARROLLO ====================

@app.route('/debug/database')
def debug_database():
    """Información de debug sobre la base de datos"""
    if not app.debug:
        return "Debug deshabilitado", 403

    info = {
        'database_available': DB_AVAILABLE,
        'connection_test': db_manager.test_connection() if db_manager else False,
        'session_user': session.get('user_id'),
        'current_user': get_current_user()
    }

    return jsonify(info)


@app.route('/test-session')
def test_session():
    """Ruta para probar sesiones"""
    return jsonify({
        'session_active': 'user_id' in session,
        'session_data': dict(session) if session else {},
        'current_user': get_current_user(),
        'database_connected': DB_AVAILABLE
    })


# ==================== MANEJO DE ERRORES ====================

@app.errorhandler(404)
def not_found(error):
    try:
        return render_template('errors/404.html'), 404
    except:
        return '<h1>404 - Página no encontrada</h1><a href="/">Volver al inicio</a>', 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Error interno: {error}")
    try:
        return render_template('errors/500.html'), 500
    except:
        return '<h1>500 - Error del servidor</h1><a href="/">Volver al inicio</a>', 500


# ==================== CONTEXTO GLOBAL ====================

@app.context_processor
def inject_globals():
    """Inyectar variables globales en todas las plantillas"""
    return {
        'user': get_current_user(),
        'is_logged_in': 'user_id' in session,
        'current_year': datetime.now().year,
        'app_name': 'AlfaIA',
        'app_version': '1.0.0',
        'database_connected': DB_AVAILABLE
    }


# ==================== INICIALIZACIÓN ====================

if __name__ == '__main__':
    # Verificar directorios
    for directory in ['logs', 'data', 'static/uploads', 'templates/errors']:
        os.makedirs(directory, exist_ok=True)

    logger.info("🚀 Iniciando AlfaIA...")

    if DB_AVAILABLE:
        logger.info("✅ Conectado a base de datos MySQL")
    else:
        logger.warning("⚠️ Ejecutando sin base de datos (modo de demostración)")
        logger.warning("   Para conectar BD: 1) Instala MySQL, 2) Ejecuta database_structure.sql")

    logger.info("💡 Usuario demo disponible: demo_user / demo123")

    # Ejecutar aplicación
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True,
        threaded=True
    )