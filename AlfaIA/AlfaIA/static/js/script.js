let mediaRecorder;
let audioChunks = [];
let isRecording = false;

// Elementos del DOM
const startBtn = document.getElementById("start");
const stopBtn = document.getElementById("stop");
const audioPlayer = document.getElementById("audio");
const vowelBox = document.getElementById("vowelBox");

// Configuración de la grabación
const recordingConfig = {
    audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
        sampleRate: 44100
    }
};

// Función para iniciar grabación
startBtn?.addEventListener("click", async () => {
    try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error("Tu navegador no soporta grabación de audio");
        }

        const stream = await navigator.mediaDevices.getUserMedia(recordingConfig);

        // Configurar MediaRecorder con mejor calidad
        const options = { mimeType: 'audio/webm;codecs=opus' };
        if (!MediaRecorder.isTypeSupported(options.mimeType)) {
            options.mimeType = 'audio/webm';
        }

        mediaRecorder = new MediaRecorder(stream, options);
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = async () => {
            // Detener todas las pistas de audio
            stream.getTracks().forEach(track => track.stop());

            const audioBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType });
            await uploadAndProcessAudio(audioBlob);

            // Reproducir audio grabado
            const audioURL = URL.createObjectURL(audioBlob);
            if (audioPlayer) {
                audioPlayer.src = audioURL;
            }
        };

        mediaRecorder.onerror = (event) => {
            console.error("Error en la grabación:", event.error);
            mostrarError("Error durante la grabación");
        };

        // Iniciar grabación
        mediaRecorder.start(100); // Capturar datos cada 100ms
        isRecording = true;
        updateUI(true);

        // Auto-stop después de 30 segundos (seguridad)
        setTimeout(() => {
            if (isRecording && mediaRecorder.state === "recording") {
                stopRecording();
                mostrarAdvertencia("Grabación automáticamente detenida después de 30 segundos");
            }
        }, 30000);

    } catch (error) {
        console.error("Error al acceder al micrófono:", error);
        mostrarError("No se pudo acceder al micrófono. Verifica los permisos.");
    }
});

// Función para detener grabación
stopBtn?.addEventListener("click", stopRecording);

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === "recording") {
        mediaRecorder.stop();
        isRecording = false;
        updateUI(false);
    }
}

// Actualizar interfaz durante grabación
function updateUI(recording) {
    if (startBtn && stopBtn) {
        startBtn.disabled = recording;
        stopBtn.disabled = !recording;

        if (recording) {
            startBtn.classList.add("recording");
            startBtn.textContent = "🔴 Grabando...";
        } else {
            startBtn.classList.remove("recording");
            startBtn.textContent = "🎤 Iniciar Grabación";
        }
    }
}

// Función para subir y procesar audio
async function uploadAndProcessAudio(audioBlob) {
    const formData = new FormData();
    formData.append("audio", audioBlob, "grabacion.webm");

    // Mostrar indicador de carga
    mostrarCargando();

    try {
        const response = await fetch("/upload", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Error del servidor: ${response.status}`);
        }

        const data = await response.json();

        if (data.resultados && data.resultados.length > 0) {
            mostrarVocalesUnaPorUna(data.resultados);
        } else {
            mostrarAdvertencia("No se detectaron vocales claras en la grabación");
        }

    } catch (error) {
        console.error("Error al procesar audio:", error);
        mostrarError("Error al procesar el audio. Intenta de nuevo.");
    } finally {
        ocultarCargando();
    }
}

// Función mejorada para mostrar vocales
function mostrarVocalesUnaPorUna(resultados) {
    if (!vowelBox) return;

    let index = 0;
    const vocales = resultados.map(r => r.vocal).filter(v => v !== "Desconocido");

    if (vocales.length === 0) {
        vowelBox.textContent = "No se detectaron vocales reconocibles";
        return;
    }

    vowelBox.textContent = "Analizando vocales...";

    function mostrarSiguienteVocal() {
        if (index < vocales.length) {
            // Agregar animación
            vowelBox.style.transform = "scale(1.1)";
            vowelBox.style.transition = "transform 0.2s";

            const vocal = vocales[index];
            const tiempo = resultados[index].inicio;

            vowelBox.innerHTML = `
                <div class="vocal-display">
                    <h3>Vocal detectada: <span class="vocal-letter">${vocal}</span></h3>
                    <small>Tiempo: ${tiempo.toFixed(1)}s</small>
                </div>
            `;

            // Restaurar escala
            setTimeout(() => {
                vowelBox.style.transform = "scale(1)";
            }, 200);

            index++;
            setTimeout(mostrarSiguienteVocal, 1000);
        } else {
            // Mostrar resumen final
            const conteoVocales = contarVocales(vocales);
            vowelBox.innerHTML = `
                <div class="resumen-vocales">
                    <h4>Resumen de vocales detectadas:</h4>
                    ${Object.entries(conteoVocales)
                        .map(([vocal, count]) => `<span class="vocal-count">${vocal}: ${count}</span>`)
                        .join(" | ")}
                </div>
            `;
        }
    }

    mostrarSiguienteVocal();
}

// Función para contar vocales
function contarVocales(vocales) {
    return vocales.reduce((acc, vocal) => {
        acc[vocal] = (acc[vocal] || 0) + 1;
        return acc;
    }, {});
}

// Funciones para mostrar mensajes
function mostrarError(mensaje) {
    mostrarMensaje(mensaje, "error");
}

function mostrarAdvertencia(mensaje) {
    mostrarMensaje(mensaje, "warning");
}

function mostrarMensaje(mensaje, tipo) {
    if (vowelBox) {
        vowelBox.className = `alert alert-${tipo === "error" ? "danger" : "warning"}`;
        vowelBox.textContent = mensaje;

        // Restaurar clase original después de 5 segundos
        setTimeout(() => {
            vowelBox.className = "";
        }, 5000);
    }
}

function mostrarCargando() {
    if (vowelBox) {
        vowelBox.innerHTML = `
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Procesando...</span>
            </div>
            <p class="mt-2">Procesando audio...</p>
        `;
    }
}

function ocultarCargando() {
    // La función mostrarVocalesUnaPorUna o mostrarMensaje se encargarán de limpiar
}

// === FUNCIONALIDAD DE LECTURA GUIADA ===

const textElement = document.getElementById("text");
const startReadingBtn = document.getElementById("startReading");

let readingText = "Esta es una prueba de lectura guiada. El texto aparecerá palabra por palabra para ayudarte a mejorar tu velocidad de lectura.";
let currentWordIndex = 0;
let readingInterval = null;
let isReading = false;

// Configuración de velocidad de lectura
const readingSpeeds = {
    lento: 800,
    normal: 500,
    rapido: 300
};

let currentSpeed = readingSpeeds.normal;

startReadingBtn?.addEventListener("click", function() {
    if (isReading) {
        stopReading();
    } else {
        startReading();
    }
});

function startReading() {
    if (!textElement) return;

    const words = readingText.split(" ");
    currentWordIndex = 0;
    isReading = true;

    // Limpiar texto y actualizar botón
    textElement.innerHTML = "";
    updateReadingButton();

    // Función para mostrar siguiente palabra
    function showNextWord() {
        if (currentWordIndex < words.length) {
            // Resaltar palabra actual y mostrar contexto
            const contextBefore = words.slice(Math.max(0, currentWordIndex - 2), currentWordIndex).join(" ");
            const currentWord = words[currentWordIndex];
            const contextAfter = words.slice(currentWordIndex + 1, Math.min(words.length, currentWordIndex + 3)).join(" ");

            textElement.innerHTML = `
                <span class="context-before">${contextBefore}</span>
                <span class="current-word">${currentWord}</span>
                <span class="context-after">${contextAfter}</span>
            `;

            currentWordIndex++;
        } else {
            stopReading();
            textElement.innerHTML += '<div class="mt-3"><em>¡Lectura completada! 🎉</em></div>';
        }
    }

    // Iniciar lectura
    readingInterval = setInterval(showNextWord, currentSpeed);
    showNextWord(); // Mostrar primera palabra inmediatamente
}

function stopReading() {
    if (readingInterval) {
        clearInterval(readingInterval);
        readingInterval = null;
    }
    isReading = false;
    updateReadingButton();
}

function updateReadingButton() {
    if (startReadingBtn) {
        if (isReading) {
            startReadingBtn.textContent = "⏹ Detener Lectura";
            startReadingBtn.className = "btn btn-danger mt-3";
        } else {
            startReadingBtn.textContent = "▶ Iniciar Lectura";
            startReadingBtn.className = "btn btn-primary mt-3";
        }
    }
}

// Control de velocidad de lectura (si existe el elemento)
const speedControl = document.getElementById("speedControl");
speedControl?.addEventListener("change", function() {
    const selectedSpeed = this.value;
    currentSpeed = readingSpeeds[selectedSpeed] || readingSpeeds.normal;

    // Si está leyendo, reiniciar con nueva velocidad
    if (isReading) {
        stopReading();
        setTimeout(startReading, 100);
    }
});

// Agregar estilos dinámicos para la lectura
if (typeof document !== 'undefined') {
    const style = document.createElement('style');
    style.textContent = `
        .current-word {
            background-color: #ffeb3b;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 1.2em;
        }
        
        .context-before, .context-after {
            opacity: 0.6;
            font-size: 0.9em;
        }
        
        .vocal-display {
            animation: fadeIn 0.5s ease-in-out;
        }
        
        .vocal-letter {
            font-size: 2rem;
            color: #007bff;
            font-weight: bold;
        }
        
        .vocal-count {
            background-color: #e9ecef;
            padding: 4px 8px;
            border-radius: 15px;
            font-size: 0.9rem;
            margin: 2px;
            display: inline-block;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .spinner-border {
            width: 2rem;
            height: 2rem;
        }
    `;
    document.head.appendChild(style);
}