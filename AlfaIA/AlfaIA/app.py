# app.py - Versión corregida para Flask 2.2+

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import os
import uuid
import random
import time
from datetime import datetime, timedelta

# Importar módulos personalizados
from modules.procesarAudio import procesarAudio
from modules.generador_ejercicios import GeneradorEjercicios
from modules.retroalimentacion import SistemaRetroalimentacion
from modules.juegos_interactivos import JuegosInteractivos

# Importar módulos de base de datos y autenticación
try:
    from modules.database import db_manager
    from modules.auth import auth_manager

    DB_AVAILABLE = db_manager is not None
except Exception as e:
    print(f"⚠️  Base de datos no disponible: {e}")
    print("🔄 Ejecutando en modo sin base de datos...")
    DB_AVAILABLE = False
    db_manager = None
    auth_manager = None

app = Flask(__name__)
app.secret_key = 'm1_cl4v3_d3s3gur1d4d_muy_s3cur4_p4r4_4lf41a'
app.permanent_session_lifetime = timedelta(days=30)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Hacer disponible enumerate en los templates
app.jinja_env.globals.update(enumerate=enumerate)

# Inicializar sistemas
generador = GeneradorEjercicios()
retroalimentacion = SistemaRetroalimentacion()
juegos = JuegosInteractivos()


# ==================== FUNCIONES DE INICIALIZACIÓN ====================

def init_database():
    """Inicializar base de datos si está disponible"""
    if DB_AVAILABLE and db_manager:
        try:
            if db_manager.test_connection():
                print("✅ Conexión a la base de datos MySQL establecida correctamente")
                return True
            else:
                print("❌ Error: No se pudo conectar a la base de datos MySQL")
                return False
        except Exception as e:
            print(f"❌ Error crítico en la base de datos: {e}")
            return False
    else:
        print("⚠️  Ejecutando sin base de datos - funcionalidad limitada")
        return False


# ==================== DECORADOR DE AUTENTICACIÓN SIMPLIFICADO ====================

def login_required_simple(f):
    """Decorador simple para requerir login cuando DB no está disponible"""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if DB_AVAILABLE and auth_manager:
            return auth_manager.login_required(f)(*args, **kwargs)
        else:
            # Sin base de datos, permitir acceso con sesión simple
            if 'simple_user' not in session:
                session['simple_user'] = {
                    'id': 1,
                    'username': 'demo_user',
                    'nombre': 'Usuario Demo'
                }
            return f(*args, **kwargs)

    return decorated_function


# ==================== RUTAS DE AUTENTICACIÓN ====================

@app.route("/login", methods=['GET', 'POST'])
def login():
    if not DB_AVAILABLE:
        # Modo sin base de datos - login automático
        session['simple_user'] = {
            'id': 1,
            'username': 'demo_user',
            'nombre': 'Usuario Demo'
        }
        flash('Modo demo activado - Base de datos no disponible', 'info')
        return redirect(url_for('dashboard'))

    # Si está loggeado, redirigir al dashboard
    if auth_manager.is_logged_in():
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember_me = 'remember_me' in request.form

        if not username or not password:
            flash('Por favor, completa todos los campos.', 'error')
            return render_template('auth/login.html')

        result = auth_manager.login_user(username, password, remember_me)

        if result['success']:
            flash(result['message'], 'success')
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('dashboard'))
        else:
            flash(result['message'], 'error')

    return render_template('auth/login.html')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if not DB_AVAILABLE:
        flash('Registro no disponible - Base de datos no conectada', 'warning')
        return redirect(url_for('login'))

    if auth_manager.is_logged_in():
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        user_data = {
            'username': request.form.get('username', '').strip(),
            'email': request.form.get('email', '').strip(),
            'password': request.form.get('password', ''),
            'confirm_password': request.form.get('confirm_password', ''),
            'nombre': request.form.get('nombre', '').strip(),
            'apellido': request.form.get('apellido', '').strip(),
            'fecha_nacimiento': request.form.get('fecha_nacimiento') or None,
            'auto_login': True
        }

        result = auth_manager.register_user(user_data)

        if result['success']:
            flash(result['message'], 'success')
            if result.get('auto_logged_in'):
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('login'))
        else:
            flash(result['message'], 'error')
            return render_template('auth/register.html', errors=result.get('errors', {}))

    return render_template('auth/register.html')


@app.route("/logout")
def logout():
    if DB_AVAILABLE and auth_manager:
        result = auth_manager.logout_user()
        flash(result['message'], 'success' if result['success'] else 'error')
    else:
        session.clear()
        flash('Sesión cerrada', 'success')

    return redirect(url_for('login'))


# ==================== RUTAS PRINCIPALES ====================

@app.route("/")
def index():
    if not DB_AVAILABLE:
        return redirect(url_for('dashboard'))

    if not auth_manager.is_logged_in():
        return redirect(url_for('login'))

    return redirect(url_for('dashboard'))


@app.route("/dashboard")
@login_required_simple
def dashboard():
    # Estadísticas por defecto
    estadisticas = {
        'ejercicios_completados': 0,
        'precision_promedio': 0,
        'racha_dias': 0,
        'total_vocales': 0,
        'logros_count': 0,
        'niveles': {
            'lectura': {'nivel': 1, 'puntos': 0},
            'ejercicios': {'nivel': 1, 'puntos': 0},
            'pronunciacion': {'nivel': 1, 'puntos': 0}
        }
    }

    user_info = {'username': 'demo_user', 'nombre': 'Usuario Demo'}
    progreso_data = None

    if DB_AVAILABLE and auth_manager:
        # Obtener progreso del usuario real
        progreso_data = auth_manager.get_user_progress()
        user_info = auth_manager.get_session_info()

        if progreso_data and progreso_data['progreso']:
            progreso = progreso_data['progreso']
            estadisticas.update({
                'ejercicios_completados': progreso['ejercicios_completados'],
                'precision_promedio': float(progreso['precision_promedio']) if progreso['precision_promedio'] else 0,
                'racha_dias': progreso['racha_dias'],
                'logros_count': len(progreso_data.get('logros', [])),
                'niveles': {
                    'lectura': {'nivel': progreso['nivel_lectura'], 'puntos': progreso['puntos_totales']},
                    'ejercicios': {'nivel': progreso['nivel_ejercicios'], 'puntos': progreso['puntos_totales']},
                    'pronunciacion': {'nivel': progreso['nivel_pronunciacion'], 'puntos': progreso['puntos_totales']}
                }
            })

    return render_template("index.html",
                           estadisticas=estadisticas,
                           user=user_info,
                           progreso_data=progreso_data,
                           db_available=DB_AVAILABLE)


@app.route("/lectura")
@login_required_simple
def lectura():
    nivel_usuario = 1
    velocidad_lectura = 500

    if DB_AVAILABLE and auth_manager:
        settings = auth_manager.get_user_settings()
        if settings:
            progreso = auth_manager.get_user_progress()
            if progreso and progreso['progreso']:
                nivel_usuario = progreso['progreso']['nivel_lectura']
            velocidad_lectura = settings.get('velocidad_lectura', 500)

    ejercicio_lectura = generador.generar_lectura_guiada(nivel_usuario)
    ejercicio_lectura['velocidad_ms'] = velocidad_lectura

    return render_template("lecturaGuiada.html",
                           ejercicio=ejercicio_lectura,
                           nivel=nivel_usuario)


@app.route("/ejercicios")
@login_required_simple
def ejercicios():
    estadisticas = {
        'ejercicios_completados': 0,
        'precision_promedio': 0,
        'racha_dias': 0,
        'logros_count': 0
    }

    user_info = {'username': 'demo_user', 'nombre': 'Usuario Demo'}

    if DB_AVAILABLE and auth_manager:
        progreso_data = auth_manager.get_user_progress()
        user_info = auth_manager.get_session_info()

        if progreso_data and progreso_data['progreso']:
            progreso = progreso_data['progreso']
            estadisticas.update({
                'ejercicios_completados': progreso['ejercicios_completados'],
                'precision_promedio': float(progreso['precision_promedio']) if progreso['precision_promedio'] else 0,
                'racha_dias': progreso['racha_dias'],
                'logros_count': len(progreso_data.get('logros', []))
            })

    return render_template('ejercicios.html',
                           estadisticas=estadisticas,
                           user=user_info)


@app.route('/ordena_la_frase', methods=['GET', 'POST'])
@login_required_simple
def ordena_la_frase():
    mensaje = ""
    color = ""
    retroalimentacion_data = None

    if request.method == 'POST':
        respuesta = request.form['respuesta']
        frase_correcta = session.get('frase_actual', '')
        tiempo_inicio = session.get('tiempo_inicio', time.time())
        tiempo_respuesta = time.time() - tiempo_inicio

        # Calcular estadísticas del ejercicio
        stats_ejercicio = generador.obtener_estadisticas_ejercicio(respuesta, frase_correcta)
        precision = stats_ejercicio["precision"]

        # Calcular puntos
        puntos = retroalimentacion.calcular_puntos_bonus(precision, tiempo_respuesta, es_racha=True)

        # Registrar en base de datos si está disponible
        if DB_AVAILABLE and auth_manager:
            auth_manager.update_user_progress(
                tipo_ejercicio='ejercicios',
                nombre_ejercicio='Ordenar Frases',
                puntos=puntos,
                precision=precision,
                tiempo=int(tiempo_respuesta),
                datos_extra={'frase_correcta': frase_correcta, 'respuesta_usuario': respuesta}
            )

        # Generar retroalimentación
        retroalimentacion_data = retroalimentacion.generar_retroalimentacion(
            precision,
            "ejercicios",
            es_primera_vez=False
        )

        mensaje = retroalimentacion_data["mensaje_principal"]
        color = retroalimentacion_data["color"]

        # Limpiar sesión
        session.pop('frase_actual', None)
        session.pop('tiempo_inicio', None)

    # Obtener nivel del usuario
    nivel_usuario = 1
    if DB_AVAILABLE and auth_manager:
        progreso_data = auth_manager.get_user_progress()
        if progreso_data and progreso_data['progreso']:
            nivel_usuario = progreso_data['progreso']['nivel_ejercicios']

    ejercicio = generador.generar_ordena_frase(nivel_usuario)

    # Guardar en sesión
    session['frase_actual'] = ejercicio["frase_correcta"]
    session['tiempo_inicio'] = time.time()

    return render_template('ordena.html',
                           desordenada=ejercicio["palabras_desordenadas"],
                           mensaje=mensaje,
                           color=color,
                           retroalimentacion=retroalimentacion_data,
                           nivel=nivel_usuario,
                           puntos_posibles=ejercicio["puntos"])


@app.route('/completa_la_palabra', methods=['GET', 'POST'])
@login_required_simple
def completa_la_palabra():
    mensaje = ""
    color = ""
    retroalimentacion_data = None

    if request.method == 'POST':
        respuesta = request.form['respuesta']
        completa = session.get('palabra_actual', '')
        tiempo_inicio = session.get('tiempo_inicio', time.time())
        tiempo_respuesta = time.time() - tiempo_inicio

        # Verificar respuesta
        es_correcto = respuesta.strip().lower() == completa.lower()
        precision = 100 if es_correcto else 0

        # Calcular puntos
        puntos = retroalimentacion.calcular_puntos_bonus(precision, tiempo_respuesta, es_racha=True)

        # Registrar ejercicio si DB disponible
        if DB_AVAILABLE and auth_manager:
            auth_manager.update_user_progress(
                tipo_ejercicio='ejercicios',
                nombre_ejercicio='Completar Palabras',
                puntos=puntos,
                precision=precision,
                tiempo=int(tiempo_respuesta),
                datos_extra={'palabra_correcta': completa, 'respuesta_usuario': respuesta}
            )

        # Generar retroalimentación
        retroalimentacion_data = retroalimentacion.generar_retroalimentacion(precision, "ejercicios",
                                                                             es_primera_vez=False)

        mensaje = retroalimentacion_data["mensaje_principal"]
        color = retroalimentacion_data["color"]

        if not es_correcto:
            mensaje += f" La palabra era: '{completa}'"

        # Limpiar sesión
        session.pop('palabra_actual', None)
        session.pop('tiempo_inicio', None)

    # Obtener nivel del usuario
    nivel_usuario = 1
    if DB_AVAILABLE and auth_manager:
        progreso_data = auth_manager.get_user_progress()
        if progreso_data and progreso_data['progreso']:
            nivel_usuario = progreso_data['progreso']['nivel_ejercicios']

    ejercicio = generador.generar_completa_palabra(nivel_usuario)

    # Guardar en sesión
    session['palabra_actual'] = ejercicio["palabra_completa"]
    session['tiempo_inicio'] = time.time()

    return render_template('completa.html',
                           incompleta=ejercicio["palabra_incompleta"],
                           pista=ejercicio["pista"],
                           mensaje=mensaje,
                           color=color,
                           retroalimentacion=retroalimentacion_data,
                           nivel=nivel_usuario,
                           puntos_posibles=ejercicio["puntos"])


@app.route('/ejercicio_pronunciacion')
@login_required_simple
def ejercicio_pronunciacion():
    nivel_pronunciacion = 1

    if DB_AVAILABLE and auth_manager:
        progreso_data = auth_manager.get_user_progress()
        if progreso_data and progreso_data['progreso']:
            progreso = progreso_data['progreso']
            if progreso['nivel_lectura'] >= 2 or progreso['nivel_ejercicios'] >= 2:
                nivel_pronunciacion = max(1, progreso['nivel_pronunciacion'])

    tipo_ejercicio = request.args.get('tipo', 'vocales')
    ejercicio = generador.generar_ejercicio_pronunciacion(tipo_ejercicio, nivel_pronunciacion)

    return render_template('pronunciacion.html',
                           ejercicio=ejercicio,
                           nivel=nivel_pronunciacion)


@app.route('/trabalenguas')
@login_required_simple
def trabalenguas():
    nivel_usuario = 1
    if DB_AVAILABLE and auth_manager:
        progreso_data = auth_manager.get_user_progress()
        if progreso_data and progreso_data['progreso']:
            nivel_usuario = progreso_data['progreso']['nivel_pronunciacion']

    ejercicio = generador.generar_trabalenguas(nivel_usuario)

    return render_template('trabalenguas.html',
                           ejercicio=ejercicio,
                           nivel=nivel_usuario)


@app.route('/progreso')
@login_required_simple
def mostrar_progreso():
    # Estadísticas por defecto
    estadisticas = {
        'ejercicios_completados': 0,
        'precision_promedio': 0,
        'racha_dias': 0,
        'total_vocales': 0,
        'logros_count': 0
    }

    progreso_niveles = {
        'lectura': {'nivel_actual': 1, 'puntos_actuales': 0, 'puntos_necesarios': 50, 'progreso_porcentaje': 0},
        'ejercicios': {'nivel_actual': 1, 'puntos_actuales': 0, 'puntos_necesarios': 50, 'progreso_porcentaje': 0},
        'pronunciacion': {'nivel_actual': 1, 'puntos_actuales': 0, 'puntos_necesarios': 50, 'progreso_porcentaje': 0}
    }

    logros = []
    reporte = {
        'mensaje_principal': '¡Comienza tu viaje de aprendizaje!',
        'insights': ['Completa ejercicios para ver tu progreso'],
        'recomendaciones': ['Comienza con ejercicios básicos', 'Practica regularmente']
    }

    user_info = {'username': 'demo_user', 'nombre': 'Usuario Demo'}

    if DB_AVAILABLE and auth_manager:
        progreso_data = auth_manager.get_user_progress()
        user_info = auth_manager.get_session_info()

        if progreso_data and progreso_data['progreso']:
            progreso = progreso_data['progreso']

            # Actualizar estadísticas
            estadisticas.update({
                'ejercicios_completados': progreso['ejercicios_completados'],
                'precision_promedio': float(progreso['precision_promedio']) if progreso['precision_promedio'] else 0,
                'racha_dias': progreso['racha_dias'],
                'logros_count': len(progreso_data.get('logros', []))
            })

            # Calcular progreso de niveles
            for tipo in ['lectura', 'ejercicios', 'pronunciacion']:
                nivel_campo = f'nivel_{tipo}'
                nivel_actual = progreso.get(nivel_campo, 1)
                puntos_necesarios = nivel_actual * 50
                puntos_actuales = min(progreso['puntos_totales'], puntos_necesarios)
                progreso_porcentaje = (puntos_actuales / puntos_necesarios) * 100 if puntos_necesarios > 0 else 0

                progreso_niveles[tipo] = {
                    'nivel_actual': nivel_actual,
                    'puntos_actuales': puntos_actuales,
                    'puntos_necesarios': puntos_necesarios,
                    'progreso_porcentaje': round(progreso_porcentaje, 1)
                }

            # Obtener logros
            logros = progreso_data.get('logros', [])

            # Generar reporte personalizado
            reporte = retroalimentacion.generar_reporte_progreso({
                'ejercicios_completados': progreso['ejercicios_completados'],
                'precision_promedio': float(progreso['precision_promedio']) if progreso['precision_promedio'] else 0,
                'racha_dias': progreso['racha_dias']
            })

    return render_template('progreso.html',
                           estadisticas=estadisticas,
                           reporte=reporte,
                           progreso_niveles=progreso_niveles,
                           logros=logros,
                           user=user_info)


# ==================== RUTAS PARA JUEGOS ====================

@app.route('/juego_memoria')
@login_required_simple
def juego_memoria():
    nivel_usuario = 1
    if DB_AVAILABLE and auth_manager:
        progreso_data = auth_manager.get_user_progress()
        if progreso_data and progreso_data['progreso']:
            nivel_usuario = progreso_data['progreso']['nivel_ejercicios']

    juego_data = juegos.generar_juego_memoria(nivel_usuario)
    session['juego_memoria'] = juego_data
    session['juego_memoria_inicio'] = time.time()

    return render_template('juego_memoria.html',
                           juego=juego_data,
                           nivel=nivel_usuario)


@app.route('/verificar_memoria', methods=['POST'])
@login_required_simple
def verificar_memoria():
    data = request.get_json()
    carta1_id = data.get('carta1')
    carta2_id = data.get('carta2')

    juego_data = session.get('juego_memoria', {})
    cartas = juego_data.get('cartas', [])

    # Encontrar las cartas
    carta1 = next((c for c in cartas if c['id'] == carta1_id), None)
    carta2 = next((c for c in cartas if c['id'] == carta2_id), None)

    if carta1 and carta2:
        es_par = carta1['par'] == carta2['par']

        if es_par:
            # Marcar como encontradas
            carta1['encontrada'] = True
            carta2['encontrada'] = True

            # Verificar si el juego está completo
            juego_completo = all(c['encontrada'] for c in cartas)

            if juego_completo:
                tiempo_usado = time.time() - session.get('juego_memoria_inicio', time.time())
                puntos = juegos.calcular_puntos_juego(
                    'memoria',
                    juego_data['nivel'],
                    100,
                    tiempo_usado,
                    juego_data['tiempo_limite']
                )

                # Registrar en la base de datos si está disponible
                if DB_AVAILABLE and auth_manager:
                    auth_manager.update_user_progress(
                        tipo_ejercicio='memoria',
                        nombre_ejercicio='Juego de Memoria',
                        puntos=puntos,
                        precision=100,
                        tiempo=int(tiempo_usado),
                        datos_extra={'nivel': juego_data['nivel'], 'tiempo_limite': juego_data['tiempo_limite']}
                    )

                return jsonify({
                    'es_par': True,
                    'juego_completo': True,
                    'puntos': puntos,
                    'tiempo_usado': round(tiempo_usado, 1)
                })

        # Actualizar sesión
        session['juego_memoria'] = juego_data

        return jsonify({
            'es_par': es_par,
            'juego_completo': False
        })

    return jsonify({'error': 'Cartas no encontradas'}), 400


# ==================== RUTAS DE AUDIO ====================

@app.route("/upload", methods=["POST"])
@login_required_simple
def upload_audio():
    if "audio" not in request.files:
        return jsonify({"error": "No se recibió audio"}), 400

    audio_file = request.files["audio"]

    if not audio_file.filename.lower().endswith(".webm"):
        return jsonify({"error": "Formato de archivo no permitido"}), 400

    file_name = f"grabacion_{uuid.uuid4().hex}.webm"
    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    audio_file.save(file_path)

    try:
        resultados = procesarAudio(file_path)
        if resultados:
            # Filtrar solo vocales válidas
            resultados_filtrados = [
                {
                    "tiempo": resultado["inicio"],
                    "frecuencia": resultado["frecuencia_dominante"],
                    "vocal": resultado["vocal"],
                    "confianza": resultado.get("confianza", 0.5)
                }
                for resultado in resultados
                if resultado["vocal"] != "Desconocido"
            ]

            # Registrar en base de datos si está disponible
            if resultados_filtrados and DB_AVAILABLE and auth_manager:
                puntos = len(resultados_filtrados) * 5
                precision = min(100, len(resultados_filtrados) * 10)

                auth_manager.update_user_progress(
                    tipo_ejercicio='pronunciacion',
                    nombre_ejercicio='Detección de Vocales',
                    puntos=puntos,
                    precision=precision,
                    tiempo=5,
                    datos_extra={'total_vocales': len(resultados_filtrados)}
                )

            # Generar retroalimentación
            vocales_detectadas = [r["vocal"] for r in resultados_filtrados]
            feedback_pronunciacion = retroalimentacion.generar_retroalimentacion_pronunciacion(
                vocales_detectadas
            )

            return jsonify({
                "mensaje": "Audio procesado con éxito",
                "resultados": resultados_filtrados,
                "retroalimentacion": feedback_pronunciacion
            })
        else:
            return jsonify({
                "mensaje": "No se encontraron resultados válidos en el audio.",
                "retroalimentacion": {
                    "mensaje": "No se detectó audio claro",
                    "consejos": ["Verifica que el micrófono funcione", "Habla más cerca del micrófono"],
                    "color": "warning"
                }
            }), 404
    except Exception as e:
        return jsonify({
            "mensaje": "Error al procesar el archivo de audio",
            "error": str(e)
        }), 500
    finally:
        # Limpiar archivo temporal
        try:
            os.remove(file_path)
        except:
            pass


# ==================== RUTAS DE API ====================

@app.route('/api/estadisticas')
@login_required_simple
def api_estadisticas():
    """API para obtener estadísticas actualizadas"""
    estadisticas = {
        'ejercicios_completados': 0,
        'precision_promedio': 0,
        'racha_dias': 0,
        'total_vocales': 0,
        'logros_count': 0
    }

    if DB_AVAILABLE and auth_manager:
        progreso_data = auth_manager.get_user_progress()

        if progreso_data and progreso_data['progreso']:
            progreso = progreso_data['progreso']
            estadisticas.update({
                'ejercicios_completados': progreso['ejercicios_completados'],
                'precision_promedio': float(progreso['precision_promedio']) if progreso['precision_promedio'] else 0,
                'racha_dias': progreso['racha_dias'],
                'logros_count': len(progreso_data.get('logros', []))
            })

    return jsonify(estadisticas)


@app.route('/api/user_info')
@login_required_simple
def api_user_info():
    """API para obtener información del usuario actual"""
    if DB_AVAILABLE and auth_manager:
        return jsonify(auth_manager.get_session_info())
    else:
        return jsonify({
            'user_id': 1,
            'username': 'demo_user',
            'nombre': 'Usuario Demo',
            'logged_in': True,
            'demo_mode': True
        })


@app.route('/api/test_db')
def test_db():
    """Probar conexión a base de datos"""
    if DB_AVAILABLE and db_manager:
        try:
            if db_manager.test_connection():
                return jsonify({'status': 'success', 'message': 'Base de datos conectada'})
            else:
                return jsonify({'status': 'error', 'message': 'No se pudo conectar a la base de datos'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})
    else:
        return jsonify({'status': 'error', 'message': 'Base de datos no disponible'})


# ==================== MANEJO DE ERRORES ====================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(e):
    return render_template('errors/500.html'), 500


@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403


# ==================== CONTEXTO GLOBAL ====================

@app.context_processor
def inject_user():
    """Inyectar información del usuario en todos los templates"""
    if DB_AVAILABLE and auth_manager:
        return {
            'current_user': auth_manager.get_session_info(),
            'is_logged_in': auth_manager.is_logged_in(),
            'db_available': True
        }
    else:
        return {
            'current_user': session.get('simple_user', {'username': 'demo_user', 'nombre': 'Usuario Demo'}),
            'is_logged_in': True,
            'db_available': False
        }


# ==================== INICIALIZACIÓN DE LA APLICACIÓN ====================

@app.before_request
def before_request():
    """Función que se ejecuta antes de cada request"""
    # Inicializar base de datos en la primera request si no está inicializada
    if not hasattr(app, '_db_initialized'):
        app._db_initialized = True
        init_database()


# ==================== FUNCIÓN PRINCIPAL ====================

if __name__ == "__main__":
    print("🚀 INICIANDO ALFAIA...")
    print("=" * 50)

    # Verificar estado de la base de datos
    db_status = init_database()

    if db_status:
        print("✅ Modo completo: Base de datos conectada")
        print("🔐 Autenticación: Activada")
        print("💾 Progreso persistente: Activado")
    else:
        print("⚠️  Modo demo: Base de datos no disponible")
        print("🔓 Autenticación: Simplificada")
        print("💾 Progreso persistente: Desactivado")

    print("🌐 Servidor: http://localhost:5000")
    print("=" * 50)

    app.run(debug=True, host='0.0.0.0', port=5000)