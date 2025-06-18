# app.py - Archivo Principal Completo de AlfaIA
# Ubicación: AlfaIA/AlfaIA/app.py

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_cors import CORS
import os
import logging
from datetime import datetime, timedelta
import json

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

# Datos de usuario de demostración
DEMO_USER = {
    'id': 1,
    'username': 'demo_user',
    'password': 'demo123',
    'nombre': 'Juan',
    'apellido': 'Pérez',
    'email': 'juan@alfaia.com'
}

DEMO_PROGRESS = {
    'estadisticas': {
        'ejercicios_completados': 15,
        'tiempo_total_minutos': 120,
        'precision_promedio': 85.5,
        'racha_dias': 5,
        'puntos_totales': 450
    },
    'niveles': {
        'lectura': {'nivel': 2, 'puntos': 75, 'desbloqueado': True},
        'ejercicios': {'nivel': 2, 'puntos': 60, 'desbloqueado': True},
        'pronunciacion': {'nivel': 1, 'puntos': 30, 'desbloqueado': True}
    }
}


# ==================== FUNCIONES AUXILIARES ====================

def get_current_user():
    """Obtener usuario actual de la sesión"""
    if 'user_id' in session:
        return DEMO_USER
    return None


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


def init_demo_session():
    """Inicializar sesión de demostración"""
    session['user_id'] = DEMO_USER['id']
    session['username'] = DEMO_USER['username']
    session['nombre'] = DEMO_USER['nombre']
    session['apellido'] = DEMO_USER['apellido']
    session['email'] = DEMO_USER['email']
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
    """Página de login"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username', '').strip()
        password = data.get('password', '')

        # Verificar credenciales de demostración
        if username == DEMO_USER['username'] and password == DEMO_USER['password']:
            init_demo_session()

            if request.is_json:
                return jsonify({'success': True, 'redirect': url_for('dashboard')})

            flash('¡Bienvenido de vuelta!', 'success')
            return redirect(url_for('dashboard'))
        else:
            message = 'Credenciales incorrectas. Usa: demo_user / demo123'
            if request.is_json:
                return jsonify({'success': False, 'message': message})
            flash(message, 'error')

    return render_template('auth/login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Página de registro"""
    if request.method == 'POST':
        # Para demostración, simplemente iniciar sesión
        init_demo_session()
        flash('¡Registro exitoso! Bienvenido a AlfaIA.', 'success')
        return redirect(url_for('dashboard'))

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
    """Dashboard principal del usuario"""
    user = get_current_user()
    return render_template('dashboard.html',
                           user=user,
                           progreso=DEMO_PROGRESS)


# ==================== RUTAS DE EJERCICIOS ====================

@app.route('/ejercicios')
@login_required
def ejercicios():
    """Página principal de ejercicios"""
    return render_template('ejercicios.html')


@app.route('/ejercicios/diario')
@login_required
def ejercicio_diario():
    """Ejercicio diario"""
    ejercicios_pendientes = [
        {'tipo': 'ordenar_frase', 'titulo': 'Ordenar palabras', 'dificultad': 2},
        {'tipo': 'completar_palabra', 'titulo': 'Completar palabras', 'dificultad': 1},
        {'tipo': 'pronunciacion', 'titulo': 'Pronunciar vocales', 'dificultad': 1},
        {'tipo': 'lectura', 'titulo': 'Lectura comprensiva', 'dificultad': 2},
        {'tipo': 'trivia', 'titulo': 'Pregunta del día', 'dificultad': 3}
    ]
    return render_template('ejercicio_diario.html', ejercicios=ejercicios_pendientes)


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
    return render_template('ordenar_frase.html', ejercicio=ejercicio)


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
    return render_template('completar_palabra.html', ejercicio=ejercicio)


# ==================== RUTAS DE JUEGOS ====================

@app.route('/juegos')
@login_required
def juegos():
    """Página principal de juegos"""
    return render_template('juegos.html')


@app.route('/juegos/rapido')
@login_required
def juego_rapido():
    """Juego rápido aleatorio"""
    juegos_disponibles = [
        {'nombre': 'Memoria', 'url': '/juegos/memoria', 'icono': 'brain'},
        {'nombre': 'Ahorcado', 'url': '/juegos/ahorcado', 'icono': 'spell-check'},
        {'nombre': 'Trivia', 'url': '/juegos/trivia', 'icono': 'question-circle'}
    ]
    import random
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
    return render_template('juego_memoria.html', pares=pares[:3 * nivel], nivel=nivel)


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
    return render_template('juego_ahorcado.html', palabra_data=palabra_data, nivel=nivel)


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
            'opciones': ['Pequeño', 'Enorme', 'Rápido', 'Bonito'],
            'respuesta_correcta': 'Enorme'
        }
    ]
    import random
    pregunta = random.choice(preguntas)
    return render_template('juego_trivia.html', pregunta=pregunta)


# ==================== RUTAS DE PRONUNCIACIÓN ====================

@app.route('/pronunciacion')
@login_required
def pronunciacion():
    """Página principal de pronunciación"""
    return render_template('pronunciacion.html')


@app.route('/pronunciacion/vocales')
@login_required
def pronunciacion_vocales():
    """Ejercicio de pronunciación de vocales"""
    ejercicio = {
        'texto': 'A E I O U',
        'tipo': 'vocales',
        'nivel': 1,
        'puntos': 15,
        'instrucciones': 'Pronuncia claramente cada vocal'
    }
    return render_template('pronunciacion_vocales.html', ejercicio=ejercicio)


@app.route('/pronunciacion/trabalenguas')
@login_required
def pronunciacion_trabalenguas():
    """Ejercicio de trabalenguas"""
    trabalenguas = [
        "Tres tristes tigres tragaban trigo en un trigal",
        "Pepe Pecas pica papas con un pico",
        "El perro de San Roque no tiene rabo"
    ]
    import random
    ejercicio = {
        'texto': random.choice(trabalenguas),
        'nivel': 2,
        'puntos': 25,
        'instrucciones': 'Repite el trabalenguas claramente'
    }
    return render_template('trabalenguas.html', ejercicio=ejercicio)


# ==================== RUTAS DE LECTURA ====================

@app.route('/lectura')
@login_required
def lectura():
    """Página principal de lectura"""
    return render_template('lectura.html')


@app.route('/lectura/continuar')
@login_required
def continuar_leccion():
    """Continuar lección actual"""
    leccion = {
        'capitulo': 3,
        'titulo': 'Verbos Irregulares',
        'contenido': 'Los verbos irregulares son aquellos que no siguen las reglas normales de conjugación...',
        'progreso': 65
    }
    return render_template('lectura_guiada.html', leccion=leccion)


@app.route('/lectura/guiada')
@login_required
def lectura_guiada():
    """Lectura guiada"""
    nivel = request.args.get('nivel', 1, type=int)
    tema = request.args.get('tema', 'general')

    textos = {
        'general': 'La lectura es una habilidad fundamental que nos permite acceder al conocimiento...',
        'aventura': 'En una tierra lejana, había un valiente caballero que buscaba el tesoro perdido...',
        'ciencia': 'Los científicos han descubierto que las plantas pueden comunicarse entre sí...'
    }

    ejercicio = {
        'texto': textos.get(tema, textos['general']),
        'nivel': nivel,
        'tema': tema,
        'preguntas': [
            '¿Cuál es la idea principal del texto?',
            '¿Qué palabras nuevas aprendiste?'
        ]
    }
    return render_template('lectura_guiada.html', ejercicio=ejercicio)


# ==================== RUTAS DE EVALUACIÓN ====================

@app.route('/evaluacion')
@login_required
def nueva_evaluacion():
    """Nueva evaluación"""
    evaluacion = {
        'tipo': 'comprension_lectora',
        'tiempo_estimado': 15,
        'preguntas': 10,
        'nivel': 'intermedio'
    }
    return render_template('evaluacion.html', evaluacion=evaluacion)


# ==================== RUTAS DE PROGRESO ====================

@app.route('/progreso')
@login_required
def progreso():
    """Página de progreso del usuario"""
    user = get_current_user()
    datos = DEMO_PROGRESS
    return render_template('progreso.html', progreso=datos, user=user)


@app.route('/logros')
@login_required
def logros():
    """Página de logros"""
    logros_obtenidos = [
        {'nombre': 'Primer Ejercicio', 'descripcion': 'Completaste tu primer ejercicio', 'icono': '🎯'},
        {'nombre': 'Racha de 5 días', 'descripcion': '5 días consecutivos practicando', 'icono': '🔥'},
        {'nombre': 'Perfeccionista', 'descripcion': '100% de precisión en un ejercicio', 'icono': '💯'}
    ]
    return render_template('logros.html', logros=logros_obtenidos)


# ==================== API ROUTES ====================

@app.route('/api/ejercicios/verificar', methods=['POST'])
@login_required
def verificar_ejercicio():
    """API para verificar respuestas de ejercicios"""
    try:
        data = request.get_json()
        tipo_ejercicio = data.get('tipo')
        respuesta = data.get('respuesta')
        respuesta_correcta = data.get('respuesta_correcta')

        es_correcto = False
        puntos = 0

        if tipo_ejercicio == 'ordenar_frase':
            es_correcto = respuesta.strip().lower() == respuesta_correcta.strip().lower()
            puntos = 10 if es_correcto else 0
        elif tipo_ejercicio == 'completar_palabra':
            es_correcto = respuesta.strip().lower() == respuesta_correcta.strip().lower()
            puntos = 15 if es_correcto else 0

        return jsonify({
            'success': True,
            'correcto': es_correcto,
            'puntos': puntos,
            'mensaje': '¡Correcto!' if es_correcto else 'Intenta de nuevo'
        })

    except Exception as e:
        logger.error(f"Error verificando ejercicio: {e}")
        return jsonify({'success': False, 'message': 'Error interno del servidor'})


@app.route('/api/progreso')
@login_required
def api_progreso():
    """API para obtener progreso del usuario"""
    try:
        return jsonify({'success': True, 'data': DEMO_PROGRESS})
    except Exception as e:
        logger.error(f"Error obteniendo progreso: {e}")
        return jsonify({'success': False, 'message': 'Error obteniendo progreso'})


# ==================== RUTAS DE CONFIGURACIÓN ====================

@app.route('/configuracion')
@login_required
def configuracion():
    """Página de configuración"""
    config_usuario = {
        'velocidad_lectura': 'normal',
        'dificultad_preferida': 2,
        'tema_preferido': 'general',
        'notificaciones_activas': True,
        'sonidos_activos': True
    }
    return render_template('configuracion.html', configuraciones=config_usuario)


@app.route('/perfil')
@login_required
def perfil():
    """Página de perfil del usuario"""
    user = get_current_user()
    return render_template('perfil.html', user=user)


# ==================== MANEJO DE ERRORES ====================

@app.errorhandler(404)
def not_found(error):
    try:
        return render_template('errors/404.html'), 404
    except:
        return '<h1>404 - Página no encontrada</h1><a href="/">Volver</a>', 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Error interno: {error}")
    try:
        return render_template('errors/500.html'), 500
    except:
        return '<h1>500 - Error del servidor</h1><a href="/">Volver</a>', 500


@app.errorhandler(403)
def forbidden(error):
    try:
        return render_template('errors/403.html'), 403
    except:
        return '<h1>403 - Acceso denegado</h1><a href="/">Volver</a>', 403


# ==================== CONTEXTO GLOBAL ====================

@app.context_processor
def inject_globals():
    """Inyectar variables globales en todas las plantillas"""
    return {
        'user': get_current_user(),
        'is_logged_in': 'user_id' in session,
        'current_year': datetime.now().year,
        'app_name': 'AlfaIA',
        'app_version': '1.0.0'
    }


# ==================== RUTAS DE DESARROLLO ====================

@app.route('/test-session')
def test_session():
    """Ruta para probar sesiones (solo desarrollo)"""
    return jsonify({
        'session_active': 'user_id' in session,
        'session_data': dict(session) if session else {},
        'current_user': get_current_user()
    })


@app.route('/clear-session')
def clear_session():
    """Limpiar sesión (solo desarrollo)"""
    session.clear()
    return jsonify({'message': 'Sesión limpiada', 'redirect': '/'})


# ==================== INICIALIZACIÓN ====================

if __name__ == '__main__':
    # Verificar directorios
    for directory in ['logs', 'data', 'static/uploads', 'templates/errors']:
        os.makedirs(directory, exist_ok=True)

    logger.info("🚀 Iniciando AlfaIA...")
    logger.info("✅ Sistema iniciado correctamente")

    # Inicializar sesión de demostración automáticamente para testing
    with app.test_request_context():
        with app.test_client() as client:
            logger.info("💡 Sistema listo - Usuario demo disponible: demo_user / demo123")

    # Ejecutar aplicación
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True,
        threaded=True
    )