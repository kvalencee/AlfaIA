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
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


def init_user_session(user):
    """Inicializar sesión de usuario"""
    session.permanent = True
    session['user_id'] = user['id']
    session['username'] = user.get('username', '')
    session['nombre'] = user.get('nombre', 'Usuario')


def get_current_user():
    """Obtener usuario actual desde la sesión"""
    if 'user_id' not in session:
        return None

    if DB_AVAILABLE:
        try:
            return db_manager.get_user_by_id(session['user_id'])
        except Exception as e:
            logger.error(f"Error obteniendo usuario: {e}")
            return None
    else:
        return FALLBACK_USER


def get_fallback_stats():
    """Estadísticas por defecto sin base de datos"""
    return {
        'ejercicios_completados': 15,
        'precision_promedio': 85.5,
        'tiempo_total_horas': 12.5,
        'nivel_actual': 'Intermedio',
        'puntos_totales': 1250,
        'insignias_obtenidas': 3
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


# ==================== RUTAS DE JUEGOS CORREGIDAS ====================

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

        random.shuffle(preguntas)
        return render_template('juegos/trivia.html', preguntas=preguntas[:5])
    except Exception as e:
        logger.error(f"Error en juego de trivia: {e}")
        flash('Error cargando la trivia.', 'error')
        return redirect('/juegos')


@app.route('/juegos/crucigrama')
@login_required
def juego_crucigrama():
    """Juego de crucigrama"""
    try:
        nivel = request.args.get('nivel', 1, type=int)

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

        return render_template('juegos/crucigrama.html', crucigrama=crucigrama_data, nivel=nivel)
    except Exception as e:
        logger.error(f"Error en juego de crucigrama: {e}")
        flash('Error cargando el crucigrama.', 'error')
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