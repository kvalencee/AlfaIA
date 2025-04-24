from flask import Flask, render_template, request, jsonify
import os
import uuid
from modules.procesarAudio import procesarAudio

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/lectura")
def lectura():
    return render_template("lecturaGuiada.html")

@app.route("/ejercicios")
def ejercicios():
    return "Página de ejercicios en construcción"

@app.route("/otros")
def otros():
    return "Página de otros recursos en construcción"

@app.route("/upload", methods=["POST"])
def upload_audio():
    if "audio" not in request.files:
        return jsonify({"error": "No se recibió audio"}), 400
    
    audio_file = request.files["audio"]
    
    # Validar que el archivo tiene una extensión de audio válida
    if not audio_file.filename.lower().endswith(".webm"):
        return jsonify({"error": "Formato de archivo no permitido"}), 400
    
    # Crear el directorio si no existe
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    # Guardar con un nombre único para evitar sobrescribir
    file_name = f"grabacion_{uuid.uuid4().hex}.webm"
    file_path = f"{UPLOAD_FOLDER}/{file_name}"
    audio_file.save(file_path)
    
    try:
        # Llama a la función para procesar el archivo
        resultados = procesarAudio(file_path)
        if resultados:
            # Filtrar resultados para excluir vocales "Desconocido"
            resultados_filtrados = [
                {
                    "tiempo": resultado["inicio"],
                    "frecuencia": resultado["frecuencia_dominante"],
                    "vocal": resultado["vocal"]
                }
                for resultado in resultados
                if resultado["vocal"] != "Desconocido"
            ]

            # Imprimir resultados en la consola
            for resultado in resultados_filtrados:
                print(f"Tiempo: {resultado['tiempo']:.2f} s, Frecuencia: {resultado['frecuencia']:.2f} Hz, Vocal: {resultado['vocal']}")

            # Devolver respuesta JSON
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
