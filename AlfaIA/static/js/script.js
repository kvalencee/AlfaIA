let mediaRecorder;
let audioChunks = [];

document.getElementById("start").addEventListener("click", async () => {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.start();

        document.getElementById("start").disabled = true;
        document.getElementById("stop").disabled = false;

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: "audio/webm" }); // Usa WebM en lugar de WAV
            const formData = new FormData();
            formData.append("audio", audioBlob, "grabacion.webm"); // Guarda como .webm
        
            const response = await fetch("/upload", { method: "POST", body: formData });
            const data = await response.json();

            if (data.resultados) {
                // Mostrar las vocales detectadas una por una
                mostrarVocalesUnaPorUna(data.resultados.map(r => r.vocal));
            } else {
                console.error("No se detectaron vocales");
            }

            const audioURL = URL.createObjectURL(audioBlob);
            document.getElementById("audio").src = audioURL;
        };
        
    } catch (error) {
        console.error("Error al acceder al micrófono:", error);
    }
});

document.getElementById("stop").addEventListener("click", () => {
    mediaRecorder.stop();
    document.getElementById("start").disabled = false;
    document.getElementById("stop").disabled = true;
});

const text = "Esta es una prueba de lectura guiada. El texto aparecerá palabra por palabra.";
const words = text.split(" ");
let index = 0;
let interval = null;

document.getElementById("startReading").addEventListener("click", function() {
    const textElement = document.getElementById("text");
    textElement.innerHTML = "";
    index = 0;
    clearInterval(interval);

    interval = setInterval(() => {
        if (index < words.length) {
            textElement.innerHTML += words[index] + " ";
            index++;
        } else {
            clearInterval(interval);
        }
    }, 500); // 🕒 Velocidad de aparición (500ms por palabra)
});

// Función para mostrar las vocales una a una
function mostrarVocalesUnaPorUna(vocales) {
    let index = 0;
    const vowelBox = document.getElementById("vowelBox");
    vowelBox.textContent = "Vocales detectadas: ";

    function mostrarSiguienteVocal() {
        if (index < vocales.length) {
            vowelBox.textContent = "Vocal detectada: " + vocales[index]; // Muestra una sola vocal
            index++;
            setTimeout(mostrarSiguienteVocal, 500); // Muestra la siguiente vocal después de 1 segundo
        }
    }

    mostrarSiguienteVocal();
}
