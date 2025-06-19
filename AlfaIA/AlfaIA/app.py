# app.py - Aplicación AlfaIA Completa y Funcional
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

def login_required(f):
    """Decorador para rutas que requieren autenticación"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder a esta página.', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)

    return decorated_function


def get_current_user():
    """Obtener datos del usuario actual"""
    if 'user_id' not in session:
        return None

    user_id = session['user_id']

    if DB_AVAILABLE:
        try:
            user = db_manager.get_user_by_id(user_id)
            if not user:
                session.clear()
                return None
            return user
        except Exception as e:
            logger.error(f"Error obteniendo usuario {user_id}: {e}")
            # Usar datos de fallback como respaldo
            if user_id == 1:
                return FALLBACK_USER
            return None
    else:
        # En modo sin base de datos, solo permitir usuario de demostración
        if user_id == 1:
            return FALLBACK_USER
        return None


def init_user_session(user):
    """Inicializar la sesión del usuario"""
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['nombre'] = user['nombre']
    session['apellido'] = user['apellido']
    session['email'] = user['email']
    session.permanent = True


def get_fallback_stats():
    """Obtener estadísticas de respaldo para modo sin BD"""
    return {
        'ejercicios_completados': 12,
        'tiempo_total_minutos': 45,
        'precision_promedio': 85.5,
        'racha_dias': 3,
        'puntos_totales': 250,
        'nivel_lectura': 2,
        'nivel_ejercicios': 2,
        'nivel_pronunciacion': 1
    }


def get_fallback_config():
    """Obtener configuración de respaldo para modo sin BD"""
    return {
        'velocidad_lectura': 500,
        'dificultad_preferida': 'medio',
        'tema_preferido': 'brown',
        'notificaciones_activas': True,
        'sonidos_activos': True
    }


# ==================== RUTAS PRINCIPALES ====================

@app.route('/')
def index():
    """Página de inicio"""
    user = get_current_user()
    return render_template('index.html', user=user)


@app.route('/about')
def about():
    """Página de información"""
    return render_template('about.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de inicio de sesión"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        message = ''

        if DB_AVAILABLE:
            try:
                user = db_manager.authenticate_user(username, password)
                if user:
                    init_user_session(user)
                    if request.is_json:
                        return jsonify({'success': True, 'redirect': url_for('dashboard')})
                    flash('¡Bienvenido de nuevo!', 'success')
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


@app.route('/logout')
def logout():
    """Cerrar sesión"""
    user_name = session.get('nombre', 'Usuario')
    session.clear()
    flash(f'¡Hasta luego, {user_name}!', 'info')
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal del usuario"""
    user = get_current_user()

    if DB_AVAILABLE and user:
        try:
            estadisticas = db_manager.get_user_statistics(user['id'])
            configuracion = db_manager.get_user_config(user['id'])
            logros_recientes = db_manager.get_recent_achievements(user['id'], limit=3)
        except Exception as e:
            logger.error(f"Error cargando datos del dashboard: {e}")
            estadisticas = get_fallback_stats()
            configuracion = get_fallback_config()
            logros_recientes = []
    else:
        estadisticas = get_fallback_stats()
        configuracion = get_fallback_config()
        logros_recientes = []

    return render_template('dashboard.html',
                           user=user,
                           stats=estadisticas,
                           config=configuracion,
                           logros=logros_recientes)


# ==================== RUTAS DE JUEGOS ====================

@app.route('/juegos')
@login_required
def juegos():
    """Página principal de juegos"""
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
    """Juego de memoria"""
    try:
        nivel = request.args.get('nivel', 1, type=int)

        # Datos por defecto para el juego de memoria
        pares_por_nivel = {
            1: [["Grande", "Enorme"], ["Pequeño", "Chico"], ["Bonito", "Hermoso"], ["Rápido", "Veloz"]],
            2: [["Feliz", "Alegre"], ["Triste", "Melancólico"], ["Fuerte", "Robusto"], ["Débil", "Frágil"],
                ["Caliente", "Cálido"], ["Frío", "Helado"]],
            3: [["Inteligente", "Listo"], ["Valiente", "Audaz"], ["Generoso", "Dadivoso"], ["Trabajador", "Laborioso"],
                ["Limpio", "Aseado"], ["Difícil", "Complicado"]]
        }

        pares = pares_por_nivel.get(nivel, pares_por_nivel[1])
        random.shuffle(pares)
        pares = pares[:min(6, len(pares))]  # Máximo 6 pares

        tiempo_limite = 60 + (nivel * 20)
        puntos_maximos = len(pares) * 20

        return render_template('juegos/memoria.html',
                               pares=pares,
                               nivel=nivel,
                               tiempo_limite=tiempo_limite,
                               puntos_maximos=puntos_maximos)
    except Exception as e:
        logger.error(f"Error en juego de memoria: {e}")
        flash('Error cargando el juego de memoria.', 'error')
        return redirect('/juegos')


@app.route('/juegos/ahorcado')
@login_required
def juego_ahorcado():
    """Juego de ahorcado"""
    try:
        nivel = request.args.get('nivel', 1, type=int)

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
        palabra_seleccionada = random.choice(palabras)

        juego_data = {
            'palabra': palabra_seleccionada['palabra'],
            'pista': palabra_seleccionada['pista'],
            'letras_adivinadas': [],
            'letras_incorrectas': [],
            'intentos_restantes': 6,
            'nivel': nivel,
            'puntos': len(palabra_seleccionada['palabra']) * 5
        }

        return render_template('juegos/ahorcado.html', juego=juego_data, nivel=nivel)
    except Exception as e:
        logger.error(f"Error en juego de ahorcado: {e}")
        flash('Error cargando el juego de ahorcado.', 'error')
        return redirect('/juegos')


@app.route('/juegos/trivia')
@login_required
def juego_trivia():
    """Juego de trivia"""
    try:
        nivel = request.args.get('nivel', 1, type=int)

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
                'opciones': ['lápizes', 'lápis', 'lápices', 'lapices'],
                'respuesta_correcta': 'lápices',
                'explicacion': 'Las palabras que terminan en z cambian a ces en plural'
            }
        ]

        # Seleccionar preguntas según nivel
        if nivel > 1:
            preguntas.extend([
                {
                    'pregunta': '¿Cuál de estas palabras tiene acento?',
                    'opciones': ['casa', 'mesa', 'arbol', 'azul'],
                    'respuesta_correcta': 'arbol',
                    'explicacion': 'La palabra correcta es "árbol" y lleva acento en la a'
                },
                {
                    'pregunta': '¿Qué signo va al principio de una pregunta en español?',
                    'opciones': ['¿', '¡', '?', '.'],
                    'respuesta_correcta': '¿',
                    'explicacion': 'Las preguntas en español empiezan con ¿ y terminan con ?'
                }
            ])

        # Mezclar preguntas
        random.shuffle(preguntas)
        preguntas = preguntas[:5]  # Limitar a 5 preguntas

        # Puntuación
        puntos_por_pregunta = 10 * nivel
        puntos_maximos = len(preguntas) * puntos_por_pregunta

        return render_template('juegos/trivia.html',
                               preguntas=preguntas,
                               nivel=nivel,
                               puntos_maximos=puntos_maximos,
                               puntos_por_pregunta=puntos_por_pregunta)
    except Exception as e:
        logger.error(f"Error en juego de trivia: {e}")
        flash('Error cargando el juego de trivia.', 'error')
        return redirect('/juegos')


@app.route('/juegos/crucigrama')
@login_required
def juego_crucigrama():
    """Juego de crucigrama"""
    try:
        nivel = request.args.get('nivel', 1, type=int)

        # Datos de ejemplo para el crucigrama
        crucigrama_data = {
            'nivel': nivel,
            'puntos_maximos': 50 * nivel,
            'mensaje': 'Crucigrama en desarrollo. Estará disponible próximamente.'
        }

        return render_template('juegos/crucigrama.html', crucigrama=crucigrama_data)
    except Exception as e:
        logger.error(f"Error en juego de crucigrama: {e}")
        flash('Error cargando el juego de crucigrama.', 'error')
        return redirect('/juegos')


@app.route('/juegos/rapido')
@login_required
def juego_rapido():
    """Juego rápido aleatorio"""
    juegos_disponibles = ['/juegos/memoria', '/juegos/ahorcado', '/juegos/trivia']
    juego_seleccionado = random.choice(juegos_disponibles)
    return redirect(juego_seleccionado)


# ==================== RUTAS DE EJERCICIOS ====================

@app.route('/ejercicios')
@login_required
def ejercicios():
    """Página principal de ejercicios"""
    user = get_current_user()
    return render_template('ejercicios.html', user=user)


@app.route('/ejercicios/lectura')
@app.route('/lectura')
@login_required
def ejercicios_lectura():
    """Ejercicios de lectura comprensiva"""
    nivel = request.args.get('nivel', 1, type=int)

    ejercicio_data = {
        'titulo': 'El Gato Aventurero',
        'texto': 'Había una vez un gato muy curioso llamado Michi. Un día decidió explorar el jardín de su casa. Encontró mariposas coloridas, flores bonitas y un pequeño estanque con peces dorados. Michi se divirtió mucho observando todo lo que había en el jardín.',
        'preguntas': [
            {
                'pregunta': '¿Cómo se llamaba el gato?',
                'opciones': ['Michi', 'Felix', 'Garfield', 'Tom'],
                'respuesta_correcta': 'Michi'
            },
            {
                'pregunta': '¿Qué encontró en el jardín?',
                'opciones': ['Solo flores', 'Mariposas, flores y un estanque', 'Solo mariposas', 'Solo un estanque'],
                'respuesta_correcta': 'Mariposas, flores y un estanque'
            },
            {
                'pregunta': '¿Cómo era el gato?',
                'opciones': ['Perezoso', 'Curioso', 'Tímido', 'Agresivo'],
                'respuesta_correcta': 'Curioso'
            }
        ],
        'nivel': nivel,
        'puntos_posibles': 30
    }

    return render_template('ejercicios/lectura.html', ejercicio=ejercicio_data)


@app.route('/ejercicios/pronunciacion')
@login_required
def ejercicios_pronunciacion():
    """Ejercicios de pronunciación"""
    tipo = request.args.get('tipo', 'vocales')
    nivel = request.args.get('nivel', 1, type=int)

    ejercicio_data = {
        'tipo': tipo,
        'nivel': nivel,
        'elementos': ['a', 'e', 'i', 'o', 'u'] if tipo == 'vocales' else ['ma', 'me', 'mi', 'mo', 'mu'],
        'instrucciones': 'Pronuncia claramente cada elemento cuando aparezca en pantalla.',
        'puntos_posibles': 25
    }

    return render_template('ejercicios/pronunciacion.html', ejercicio=ejercicio_data)


@app.route('/ejercicios/ortografia')
@login_required
def ejercicios_ortografia():
    """Ejercicios de ortografía"""
    ejercicio_data = {
        'palabras': [
            {'incorrecta': 'kasa', 'correcta': 'casa'},
            {'incorrecta': 'gato', 'correcta': 'gato'},
            {'incorrecta': 'arbol', 'correcta': 'árbol'},
            {'incorrecta': 'lapiz', 'correcta': 'lápiz'},
            {'incorrecta': 'nino', 'correcta': 'niño'},
            {'incorrecta': 'musica', 'correcta': 'música'}
        ],
        'nivel': 1,
        'puntos_posibles': 30
    }
    return render_template('ejercicios/ortografia.html', ejercicio=ejercicio_data)


@app.route('/ejercicios/vocabulario')
@login_required
def ejercicios_vocabulario():
    """Ejercicios de vocabulario"""
    nivel = request.args.get('nivel', 1, type=int)

    ejercicio_data = {
        'palabras': [
            {'palabra': 'FELIZ', 'definicion': 'Que siente alegría', 'sinonimos': ['alegre', 'contento', 'gozoso']},
            {'palabra': 'GRANDE', 'definicion': 'De mucho tamaño', 'sinonimos': ['enorme', 'gigante', 'inmenso']},
            {'palabra': 'RÁPIDO', 'definicion': 'Que se mueve con velocidad', 'sinonimos': ['veloz', 'ligero', 'ágil']},
            {'palabra': 'BONITO', 'definicion': 'Que es agradable a la vista',
             'sinonimos': ['hermoso', 'bello', 'lindo']}
        ],
        'nivel': nivel,
        'puntos_posibles': 40
    }

    return render_template('ejercicios/vocabulario.html', ejercicio=ejercicio_data)


@app.route('/ejercicios/completar-palabra')
@login_required
def ejercicios_completar_palabra():
    """Ejercicios de completar palabras"""
    nivel = request.args.get('nivel', 1, type=int)

    ejercicio_data = {
        'palabras': [
            {'palabra_incompleta': 'c_sa', 'palabra_completa': 'casa', 'pista': 'Lugar donde vives'},
            {'palabra_incompleta': 'g_to', 'palabra_completa': 'gato', 'pista': 'Animal doméstico que dice miau'},
            {'palabra_incompleta': 's_l', 'palabra_completa': 'sol', 'pista': 'Estrella que nos da luz'},
            {'palabra_incompleta': 'm_r', 'palabra_completa': 'mar', 'pista': 'Agua salada muy grande'},
            {'palabra_incompleta': 'l_z', 'palabra_completa': 'luz', 'pista': 'Lo contrario de oscuridad'}
        ],
        'nivel': nivel,
        'puntos_posibles': 25
    }

    return render_template('ejercicios/completar_palabra.html', ejercicio=ejercicio_data)


@app.route('/ejercicios/ordenar-frase')
@app.route('/ordenar-frase')
@login_required
def ordenar_frase():
    """Ejercicios de ordenar frases"""
    nivel = request.args.get('nivel', 1, type=int)

    # Si el generador de ejercicios está disponible, usarlo
    if JUEGOS_AVAILABLE and ejercicios_generator:
        try:
            ejercicio_data = ejercicios_generator.generar_ordena_frase(nivel)
        except Exception as e:
            logger.error(f"Error generando ejercicio de ordenar frase: {e}")
            ejercicio_data = None
    else:
        ejercicio_data = None

    # Si no se pudo generar, usar datos de ejemplo
    if not ejercicio_data:
        ejercicio_data = {
            "frase_correcta": "El gato juega con la pelota",
            "palabras_desordenadas": ["El", "pelota", "juega", "gato", "la", "con"],
            "nivel": nivel,
            "puntos": nivel * 10
        }

    return render_template('ejercicios/ordenar_frase.html', ejercicio=ejercicio_data)


@app.route('/completar-palabra')
@login_required
def completar_palabra():
    """Redirige a la ruta correcta de ejercicios de completar palabras"""
    return redirect(url_for('ejercicios_completar_palabra'))


@app.route('/ejercicio-diario')
@app.route('/ejercicios/diario')
@login_required
def ejercicio_diario():
    """Página de ejercicio diario personalizado"""
    user = get_current_user()

    # Obtener la fecha actual para mostrar los ejercicios del día
    hoy = datetime.now().strftime('%Y-%m-%d')

    # Crear ejercicios diarios de ejemplo (en producción, esto vendría de la base de datos)
    ejercicios = [
        {
            'tipo': 'ordenar_frase',
            'titulo': 'Ordenar las palabras',
            'descripcion': 'Organiza las palabras para formar una frase correcta.',
            'nivel': 1,
            'dificultad': 1,
            'puntos': 20,
            'url': url_for('ordenar_frase', nivel=1)
        },
        {
            'tipo': 'completar_palabra',
            'titulo': 'Completar palabras',
            'descripcion': 'Completa las palabras con las letras que faltan.',
            'nivel': 1,
            'dificultad': 1,
            'puntos': 15,
            'url': url_for('ejercicios_completar_palabra', nivel=1)
        },
        {
            'tipo': 'lectura',
            'titulo': 'Comprensión de lectura',
            'descripcion': 'Lee el texto y responde las preguntas.',
            'nivel': 2,
            'dificultad': 2,
            'puntos': 30,
            'url': url_for('ejercicios_lectura', nivel=2)
        },
        {
            'tipo': 'pronunciacion',
            'titulo': 'Práctica de pronunciación',
            'descripcion': 'Practica la pronunciación de vocales y consonantes.',
            'nivel': 1,
            'dificultad': 1,
            'puntos': 25,
            'url': url_for('ejercicios_pronunciacion')
        }
    ]

    # Estadísticas del usuario para hoy (en producción, esto vendría de la base de datos)
    estadisticas_diarias = {
        'ejercicios_completados': 0,
        'tiempo_total_minutos': 0,
        'puntos_obtenidos': 0,
        'precision_promedio': 0
    }

    # Si hay base de datos disponible, obtener datos reales
    if DB_AVAILABLE and user:
        try:
            # Aquí se obtendría la información real de la base de datos
            # ejercicios = db_manager.get_daily_exercises(user['id'])
            # estadisticas_diarias = db_manager.get_daily_stats(user['id'], hoy)
            pass
        except Exception as e:
            logger.error(f"Error cargando ejercicio diario: {e}")

    return render_template('ejercicios/diario.html',
                           user=user,
                           ejercicios=ejercicios,
                           estadisticas=estadisticas_diarias,
                           fecha=hoy)


# ==================== OTRAS RUTAS ====================

@app.route('/progreso')
@login_required
def mostrar_progreso():
    """Página de progreso del usuario"""
    user = get_current_user()

    if DB_AVAILABLE and user:
        try:
            progreso = db_manager.get_user_progress(user['id'])
            estadisticas = db_manager.get_user_statistics(user['id'])
        except Exception as e:
            logger.error(f"Error cargando progreso: {e}")
            progreso = {}
            estadisticas = get_fallback_stats()
    else:
        progreso = {}
        estadisticas = get_fallback_stats()

    return render_template('progreso.html', user=user, progreso=progreso, estadisticas=estadisticas)


@app.route('/logros')
@login_required
def logros():
    """Página de logros"""
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


# ==================== API ENDPOINTS ====================

@app.route('/api/ejercicios/completar', methods=['POST'])
@login_required
def api_completar_ejercicio():
    """Registrar ejercicio completado"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Usuario no autenticado'}), 401

    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'Datos no proporcionados'}), 400

        # Validar datos mínimos
        required_fields = ['tipo', 'nombre', 'puntos']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Campo requerido faltante: {field}'}), 400

        # Registro en base de datos
        if DB_AVAILABLE:
            try:
                resultado = db_manager.register_exercise_completion(
                    user_id=user['id'],
                    exercise_type=data['tipo'],
                    exercise_name=data['nombre'],
                    points=data['puntos'],
                    accuracy=data.get('precision', 0),
                    time_seconds=data.get('tiempo_segundos', 0),
                    additional_data=data.get('datos_adicionales', {})
                )
                if resultado:
                    return jsonify({'success': True, 'message': 'Ejercicio registrado correctamente'})
                else:
                    return jsonify({'success': False, 'error': 'Error registrando ejercicio'}), 500
            except Exception as e:
                logger.error(f"Error en API completar ejercicio: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        else:
            # Modo sin base de datos - simular éxito
            return jsonify({
                'success': True,
                'message': 'Ejercicio registrado (modo sin base de datos)',
                'data': {
                    'puntos': data['puntos'],
                    'precision': data.get('precision', 0),
                    'tiempo': data.get('tiempo_segundos', 0)
                }
            })

    except Exception as e:
        logger.error(f"Error general en API completar ejercicio: {e}")
        return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500


@app.route('/api/perfil/actualizar', methods=['POST'])
@login_required
def api_actualizar_perfil():
    """Actualizar perfil del usuario"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Usuario no autenticado'}), 401

    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'Datos no proporcionados'}), 400

        # Actualizar en base de datos
        if DB_AVAILABLE:
            try:
                resultado = db_manager.update_user_profile(user['id'], data)
                if resultado:
                    return jsonify({'success': True, 'message': 'Perfil actualizado correctamente'})
                else:
                    return jsonify({'success': False, 'error': 'Error actualizando perfil'}), 500
            except Exception as e:
                logger.error(f"Error en API actualizar perfil: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        else:
            # Modo sin base de datos - simular éxito
            return jsonify({
                'success': True,
                'message': 'Perfil actualizado (modo sin base de datos)',
                'data': data
            })

    except Exception as e:
        logger.error(f"Error general en API actualizar perfil: {e}")
        return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500


# ==================== MANEJO DE ERRORES ====================

@app.errorhandler(404)
def not_found(error):
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
    print("🚀 Iniciando AlfaIA...")
    print(f"📊 Base de datos: {'✅ Conectada' if DB_AVAILABLE else '❌ No disponible'}")
    print(f"🎮 Generador de juegos: {'✅ Disponible' if JUEGOS_AVAILABLE else '❌ No disponible'}")
    print(f"🌐 Servidor: http://127.0.0.1:5000")

    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=True)