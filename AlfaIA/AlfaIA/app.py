from flask import Flask, render_template, request, jsonify, session
import os
import uuid
import random
from modules.procesarAudio import procesarAudio

app = Flask(__name__)
app.secret_key = 'm1_cl4v3_d3s3gur1d4d'
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

phrases = [
    "El gato duerme tranquilo",
    "Hoy vamos al parque",
    "Me gusta comer helado",
    "El perro corre rápido",
    "Ella canta muy bonito",
    "Papá cocina la cena",
    "El sol brilla fuerte",
    "Vamos a la playa mañana"
]

words = [
    ("ca_a", "casa"),
    ("ni_o", "niño"),
    ("per_o", "perro"),
    ("sol_", "sola"),
    ("ma_o", "mano"),
    ("c_mera", "cámara"),
    ("c_mion", "camion"),
    ("pe_ota", "pelota"),
    ("_ebra", "cebra"),
    ("_afari", "safari")
]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/lectura")
def lectura():
    return render_template("lecturaGuiada.html")

@app.route("/ejercicios")
def ejercicios():
    return render_template('ejercicios.html')

@app.route('/ordena_la_frase', methods=['GET', 'POST'])
def ordena_la_frase():
    mensaje = ""
    color = ""
    if request.method == 'POST':
        respuesta = request.form['respuesta']
        frase_correcta = session.get('frase_actual', '')
        if respuesta.strip().lower() == frase_correcta.lower():
            mensaje = "✅ ¡Correcto!"
            color = "success"
        else:
            mensaje = f"❌ Intenta de nuevo. La respuesta era: '{frase_correcta}'"
            color = "danger"
        session.pop('frase_actual', None)
    frase = random.choice(phrases)
    session['frase_actual'] = frase
    desordenada = random.sample(frase.split(), len(frase.split()))
    return render_template('ordena.html', desordenada=desordenada, mensaje=mensaje, color=color)

@app.route('/completa_la_palabra', methods=['GET', 'POST'])
def completa_la_palabra():
    mensaje = ""
    color = ""
    if request.method == 'POST':
        respuesta = request.form['respuesta']
        completa = session.get('palabra_actual', '')
        if respuesta.strip().lower() == completa.lower():
            mensaje = "✅ ¡Muy bien!"
            color = "success"
        else:
            mensaje = f"❌ Vuelve a intentarlo. La palabra era: '{completa}'"
            color = "danger"
        session.pop('palabra_actual', None)
    incompleta, completa = random.choice(words)
    session['palabra_actual'] = completa
    return render_template('completa.html', incompleta=incompleta, mensaje=mensaje, color=color)

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
            resultados_filtrados = [
                {
                    "tiempo": resultado["inicio"],
                    "frecuencia": resultado["frecuencia_dominante"],
                    "vocal": resultado["vocal"]
                }
                for resultado in resultados
                if resultado["vocal"] != "Desconocido"
            ]
            return jsonify({
                "mensaje": "Audio procesado con éxito",
                "resultados": resultados_filtrados
            })
        else:
            return jsonify({
                "mensaje": "No se encontraron resultados válidos en el audio."
            }), 404
    except Exception as e:
        return jsonify({
            "mensaje": "Error al procesar el archivo de audio",
            "error": str(e)
        }), 500

if __name__ == "__main__":
    app.run(debug=True)
