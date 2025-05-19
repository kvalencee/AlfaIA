from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import uuid
import random
import time
from modules.procesarAudio import procesarAudio
from modules.progreso_usuario import ProgresoUsuario
from modules.generador_ejercicios import GeneradorEjercicios
from modules.retroalimentacion import SistemaRetroalimentacion
from modules.juegos_interactivos import JuegosInteractivos

app = Flask(__name__)
app.secret_key = 'm1_cl4v3_d3s3gur1d4d'
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Hacer disponible enumerate en los templates
app.jinja_env.globals.update(enumerate=enumerate)

# Inicializar sistemas
progreso_sistema = ProgresoUsuario()
generador = GeneradorEjercicios()
retroalimentacion = SistemaRetroalimentacion()
juegos = JuegosInteractivos()


@app.route("/")
def index():
    # Obtener estadísticas para mostrar en la página principal
    stats = progreso_sistema.obtener_estadisticas()
    return render_template("index.html", estadisticas=stats)


@app.route("/lectura")
def lectura():
    # Obtener nivel actual del usuario
    nivel_usuario = progreso_sistema.progreso["niveles"]["lectura"]["nivel"]

    # Generar texto para lectura guiada
    ejercicio_lectura = generador.generar_lectura_guiada(nivel_usuario)

    return render_template("lecturaGuiada.html",
                           ejercicio=ejercicio_lectura,
                           nivel=nivel_usuario)


@app.route("/ejercicios")
def ejercicios():
    # Obtener progreso del usuario
    stats = progreso_sistema.obtener_estadisticas()
    return render_template('ejercicios.html', estadisticas=stats)


@app.route('/ordena_la_frase', methods=['GET', 'POST'])
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

        # Registrar ejercicio completado
        puntos = retroalimentacion.calcular_puntos_bonus(
            precision,
            tiempo_respuesta,
            es_racha=progreso_sistema.progreso["estadisticas"]["racha_dias"] > 0
        )
        progreso_sistema.registrar_ejercicio_completado("ejercicios", puntos, precision)

        # Generar retroalimentación
        retroalimentacion_data = retroalimentacion.generar_retroalimentacion(
            precision,
            "ejercicios",
            es_primera_vez=progreso_sistema.progreso["estadisticas"]["ejercicios_completados"] == 1
        )

        mensaje = retroalimentacion_data["mensaje_principal"]
        color = retroalimentacion_data["color"]

        # Limpiar sesión
        session.pop('frase_actual', None)
        session.pop('tiempo_inicio', None)

    # Obtener nivel del usuario para generar ejercicio apropiado
    nivel_usuario = progreso_sistema.progreso["niveles"]["ejercicios"]["nivel"]
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

        # Registrar ejercicio completado
        puntos = retroalimentacion.calcular_puntos_bonus(
            precision,
            tiempo_respuesta,
            es_racha=progreso_sistema.progreso["estadisticas"]["racha_dias"] > 0
        )
        progreso_sistema.registrar_ejercicio_completado("ejercicios", puntos, precision)

        # Generar retroalimentación
        retroalimentacion_data = retroalimentacion.generar_retroalimentacion(
            precision,
            "ejercicios",
            es_primera_vez=progreso_sistema.progreso["estadisticas"]["ejercicios_completados"] == 1
        )

        mensaje = retroalimentacion_data["mensaje_principal"]
        color = retroalimentacion_data["color"]

        if not es_correcto:
            mensaje += f" La palabra era: '{completa}'"

        # Limpiar sesión
        session.pop('palabra_actual', None)
        session.pop('tiempo_inicio', None)

    # Obtener nivel del usuario
    nivel_usuario = progreso_sistema.progreso["niveles"]["ejercicios"]["nivel"]
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
def ejercicio_pronunciacion():
    # Verificar si el módulo está desbloqueado
    if not progreso_sistema.progreso["niveles"]["pronunciacion"]["desbloqueado"]:
        return redirect(url_for('ejercicios'))

    nivel_usuario = progreso_sistema.progreso["niveles"]["pronunciacion"]["nivel"]
    tipo_ejercicio = request.args.get('tipo', 'vocales')

    ejercicio = generador.generar_ejercicio_pronunciacion(tipo_ejercicio, nivel_usuario)

    return render_template('pronunciacion.html',
                           ejercicio=ejercicio,
                           nivel=nivel_usuario)


@app.route('/trabalenguas')
def trabalenguas():
    nivel_usuario = progreso_sistema.progreso["niveles"]["pronunciacion"]["nivel"]
    ejercicio = generador.generar_trabalenguas(nivel_usuario)

    return render_template('trabalenguas.html',
                           ejercicio=ejercicio,
                           nivel=nivel_usuario)


@app.route('/progreso')
def mostrar_progreso():
    stats = progreso_sistema.obtener_estadisticas()
    reporte = retroalimentacion.generar_reporte_progreso(
        progreso_sistema.progreso["estadisticas"]
    )

    # Obtener progreso de niveles
    progreso_niveles = {}
    for tipo_ejercicio in ["lectura", "ejercicios", "pronunciacion"]:
        progreso_niveles[tipo_ejercicio] = progreso_sistema.obtener_progreso_nivel(tipo_ejercicio)

    return render_template('progreso.html',
                           estadisticas=stats,
                           reporte=reporte,
                           progreso_niveles=progreso_niveles,
                           logros=progreso_sistema.progreso["logros"])


# === RUTAS PARA NUEVOS JUEGOS ===

@app.route('/juego_memoria')
def juego_memoria():
    nivel_usuario = progreso_sistema.progreso["niveles"]["ejercicios"]["nivel"]
    juego_data = juegos.generar_juego_memoria(nivel_usuario)
    session['juego_memoria'] = juego_data
    session['juego_memoria_inicio'] = time.time()

    return render_template('juego_memoria.html',
                           juego=juego_data,
                           nivel=nivel_usuario)


@app.route('/verificar_memoria', methods=['POST'])
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
                    100,  # Precisión perfecta al completar
                    tiempo_usado,
                    juego_data['tiempo_limite']
                )
                progreso_sistema.registrar_ejercicio_completado("ejercicios", puntos, 100)

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


@app.route('/juego_ahorcado')
def juego_ahorcado():
    nivel_usuario = progreso_sistema.progreso["niveles"]["ejercicios"]["nivel"]
    juego_data = juegos.generar_ahorcado(nivel_usuario)
    session['juego_ahorcado'] = juego_data
    session['ahorcado_inicio'] = time.time()

    return render_template('juego_ahorcado.html',
                           juego=juego_data,
                           nivel=nivel_usuario)


@app.route('/adivinar_letra', methods=['POST'])
def adivinar_letra():
    data = request.get_json()
    letra = data.get('letra', '').upper()

    juego_data = session.get('juego_ahorcado', {})

    if not juego_data:
        return jsonify({'error': 'Juego no encontrado'}), 400

    resultado = juegos.actualizar_ahorcado(juego_data, letra)

    if resultado.get('ya_usada'):
        return jsonify({'error': 'Letra ya usada'}), 400

    # Generar palabra con espacios
    palabra_display = juegos.generar_palabra_con_espacios(
        juego_data['palabra'],
        juego_data['letras_adivinadas']
    )

    # Actualizar sesión
    session['juego_ahorcado'] = juego_data

    response = {
        'correcto': resultado['correcto'],
        'palabra_display': palabra_display,
        'letras_incorrectas': juego_data['letras_incorrectas'],
        'intentos_restantes': juego_data['intentos_restantes'],
        'juego_terminado': resultado['juego_terminado'],
        'palabra_completa': resultado['palabra_completa']
    }

    # Si el juego terminó, calcular puntos
    if resultado['juego_terminado']:
        tiempo_usado = time.time() - session.get('ahorcado_inicio', time.time())

        if resultado['palabra_completa']:
            # Victoria
            precision = max(50, 100 - (len(juego_data['letras_incorrectas']) * 15))
            puntos = juegos.calcular_puntos_juego('ahorcado', juego_data['nivel'], precision, tiempo_usado)
            progreso_sistema.registrar_ejercicio_completado("ejercicios", puntos, precision)
            response['puntos'] = puntos
            response['mensaje'] = f"¡Felicidades! Ganaste {puntos} puntos"
        else:
            # Derrota
            response['palabra_correcta'] = juego_data['palabra']
            response['mensaje'] = f"¡Mejor suerte la próxima vez! La palabra era: {juego_data['palabra']}"

    return jsonify(response)


@app.route('/juego_trivia')
def juego_trivia():
    nivel_usuario = progreso_sistema.progreso["niveles"]["ejercicios"]["nivel"]
    categoria = request.args.get('categoria', None)
    pregunta_data = juegos.generar_trivia(categoria, nivel_usuario)
    session['trivia_actual'] = pregunta_data
    session['trivia_inicio'] = time.time()

    return render_template('juego_trivia.html',
                           pregunta=pregunta_data,
                           nivel=nivel_usuario)


@app.route('/responder_trivia', methods=['POST'])
def responder_trivia():
    data = request.get_json()
    respuesta_usuario = data.get('respuesta')

    pregunta_data = session.get('trivia_actual', {})

    if not pregunta_data:
        return jsonify({'error': 'Pregunta no encontrada'}), 400

    es_correcto = juegos.verificar_respuesta_trivia(respuesta_usuario, pregunta_data['respuesta_correcta'])
    tiempo_usado = time.time() - session.get('trivia_inicio', time.time())

    response = {
        'correcto': es_correcto,
        'respuesta_correcta': pregunta_data['respuesta_correcta'],
        'explicacion': pregunta_data['explicacion'],
        'tiempo_usado': round(tiempo_usado, 1)
    }

    # Calcular puntos
    precision = 100 if es_correcto else 0
    puntos = juegos.calcular_puntos_juego('trivia', pregunta_data['nivel'], precision, tiempo_usado, 30)

    if es_correcto:
        progreso_sistema.registrar_ejercicio_completado("ejercicios", puntos, precision)
        response['puntos'] = puntos

    # Limpiar sesión
    session.pop('trivia_actual', None)
    session.pop('trivia_inicio', None)

    return jsonify(response)


@app.route('/juego_palabras_cruzadas')
def juego_palabras_cruzadas():
    nivel_usuario = progreso_sistema.progreso["niveles"]["ejercicios"]["nivel"]
    crucigrama_data = juegos.generar_crucigrama(nivel_usuario)
    session['crucigrama_actual'] = crucigrama_data
    session['crucigrama_inicio'] = time.time()

    return render_template('juego_crucigrama.html',
                           crucigrama=crucigrama_data,
                           nivel=nivel_usuario)


@app.route('/verificar_crucigrama', methods=['POST'])
def verificar_crucigrama():
    data = request.get_json()
    respuestas_usuario = data.get('respuestas', {})

    crucigrama_data = session.get('crucigrama_actual', {})

    if not crucigrama_data:
        return jsonify({'error': 'Crucigrama no encontrado'}), 400

    # Verificar cada palabra
    palabras_correctas = 0
    total_palabras = len(crucigrama_data['palabras'])

    for i, palabra_info in enumerate(crucigrama_data['palabras']):
        palabra_correcta = palabra_info['palabra']
        respuesta_usuario = respuestas_usuario.get(str(i), '').upper()

        if respuesta_usuario == palabra_correcta:
            palabras_correctas += 1

    # Calcular precisión
    precision = (palabras_correctas / total_palabras) * 100
    tiempo_usado = time.time() - session.get('crucigrama_inicio', time.time())

    # Calcular puntos
    puntos = juegos.calcular_puntos_juego('crucigrama', crucigrama_data['nivel'], precision, tiempo_usado, 300)

    if precision >= 50:  # Al menos 50% correcto para obtener puntos
        progreso_sistema.registrar_ejercicio_completado("ejercicios", puntos, precision)

    response = {
        'palabras_correctas': palabras_correctas,
        'total_palabras': total_palabras,
        'precision': round(precision, 1),
        'puntos': puntos if precision >= 50 else 0,
        'tiempo_usado': round(tiempo_usado, 1)
    }

    # Limpiar sesión
    session.pop('crucigrama_actual', None)
    session.pop('crucigrama_inicio', None)

    return jsonify(response)


@app.route("/upload", methods=["POST"])
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
                    "vocal": resultado["vocal"]
                }
                for resultado in resultados
                if resultado["vocal"] != "Desconocido"
            ]

            # Registrar vocales detectadas en el progreso
            vocales_detectadas = [r["vocal"] for r in resultados_filtrados]
            progreso_sistema.registrar_vocales_detectadas(vocales_detectadas)

            # Generar retroalimentación
            feedback_pronunciacion = retroalimentacion.generar_retroalimentacion_pronunciacion(
                vocales_detectadas
            )

            # Registrar ejercicio de pronunciación
            if len(vocales_detectadas) > 0:
                precision = min(100, len(vocales_detectadas) * 10)  # Máximo 100%
                puntos = len(vocales_detectadas) * 5
                progreso_sistema.registrar_ejercicio_completado("pronunciacion", puntos, precision)

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


@app.route('/api/estadisticas')
def api_estadisticas():
    """API para obtener estadísticas actualizadas"""
    stats = progreso_sistema.obtener_estadisticas()
    return jsonify(stats)


@app.route('/api/reiniciar_progreso', methods=['POST'])
def reiniciar_progreso():
    """Reiniciar progreso del usuario (para pruebas)"""
    global progreso_sistema
    progreso_sistema = ProgresoUsuario()
    return jsonify({"mensaje": "Progreso reiniciado correctamente"})


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500


if __name__ == "__main__":
    app.run(debug=True)