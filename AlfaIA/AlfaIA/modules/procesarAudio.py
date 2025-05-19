import math
import subprocess
import cmath
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def webm_to_wav(input_file):
    """Convierte archivo WEBM a WAV con manejo mejorado de errores"""
    output_file = input_file.replace(".webm", ".wav")
    try:
        # Verificar que ffmpeg esté disponible
        result = subprocess.run(['ffmpeg', '-version'],
                                capture_output=True, text=True)
        if result.returncode != 0:
            raise FileNotFoundError("FFmpeg no está instalado")

        subprocess.run([
            'ffmpeg', '-i', input_file,
            '-ac', '2',  # 2 canales (estéreo)
            '-ar', '44100',  # Tasa de muestreo de 44.1 kHz
            '-acodec', 'pcm_s16le',  # Códec PCM de 16 bits
            '-y',  # Sobrescribir archivo si existe
            output_file
        ], check=True, capture_output=True)

        logger.info(f"Conversión exitosa: {output_file}")
        return output_file
    except subprocess.CalledProcessError as e:
        logger.error(f"Error al convertir el archivo: {e}")
        return None
    except FileNotFoundError as e:
        logger.error(f"FFmpeg no encontrado: {e}")
        return None


def leer_wav(archivo):
    """Lee archivo WAV con validación mejorada"""
    try:
        with open(archivo, "rb") as f:
            header = f.read(44)

            # Verificar que el archivo sea un WAV válido
            if len(header) < 44:
                raise ValueError("Archivo WAV incompleto o corrupto")

            if header[:4] != b'RIFF' or header[8:12] != b'WAVE':
                raise ValueError("El archivo no es un WAV válido.")

            # Leer parámetros del encabezado
            num_canales = int.from_bytes(header[22:24], byteorder="little")
            tasa_muestreo = int.from_bytes(header[24:28], byteorder="little")
            profundidad_bits = int.from_bytes(header[34:36], byteorder="little")
            tamano_datos = int.from_bytes(header[40:44], byteorder="little")

            # Verificar que los valores sean válidos
            if tasa_muestreo == 0 or num_canales == 0 or profundidad_bits == 0:
                raise ValueError("Parámetros inválidos en el encabezado WAV.")
            if tamano_datos == 0:
                raise ValueError("El tamaño de los datos en el archivo WAV es 0.")

            # Calcular la duración
            duracion = tamano_datos / (tasa_muestreo * num_canales * (profundidad_bits // 8))

            logger.info(f"Archivo: {archivo}")
            logger.info(f"Canales: {num_canales}, Tasa: {tasa_muestreo} Hz")
            logger.info(f"Duración: {duracion:.2f} segundos")

            # Leer los datos de audio
            datos = f.read(tamano_datos)  # Solo leer la cantidad especificada
            muestras = []
            paso = profundidad_bits // 8

            # Procesar solo un canal si es estéreo (simplificar)
            if num_canales == 2:
                paso *= 2  # Saltar el segundo canal

            for i in range(0, len(datos), paso * num_canales):
                if i + paso <= len(datos):
                    muestra = int.from_bytes(datos[i:i + paso], byteorder="little", signed=True)
                    muestras.append(muestra)

            return muestras, num_canales, tasa_muestreo
    except Exception as e:
        logger.error(f"Error al leer WAV: {e}")
        raise


def fft_transform(signal):
    """FFT con optimización para señales reales"""
    N = len(signal)
    if N <= 1:
        return signal

    # Ajustar la longitud de la señal a una potencia de 2
    next_power_of_two = 2 ** math.ceil(math.log2(N))
    if N != next_power_of_two:
        signal += [0] * (next_power_of_two - N)
        N = len(signal)

    # Caso base
    if N == 1:
        return signal

    # Dividir la señal en partes pares e impares
    even = fft_transform(signal[0::2])
    odd = fft_transform(signal[1::2])

    # Calcular los factores de giro (twiddle factors)
    T = [cmath.exp(-2j * math.pi * k / N) * odd[k] for k in range(N // 2)]

    # Combinar los resultados
    return [even[k] + T[k] for k in range(N // 2)] + [even[k] - T[k] for k in range(N // 2)]


def detectar_vocal(frecuencia):
    """Detección de vocales con rangos mejorados"""
    # Rangos más específicos basados en formantes típicos
    vocal_ranges = {
        'A': (700, 1100),
        'E': (400, 700),
        'I': (200, 400),
        'O': (300, 600),
        'U': (200, 400)
    }

    for vocal, (min_freq, max_freq) in vocal_ranges.items():
        if min_freq <= frecuencia < max_freq:
            return vocal

    return 'Desconocido'


def aplicar_ventana_hamming(signal):
    """Aplica ventana de Hamming para reducir efectos de borde en FFT"""
    N = len(signal)
    ventana = [0.54 - 0.46 * math.cos(2 * math.pi * n / (N - 1)) for n in range(N)]
    return [signal[i] * ventana[i] for i in range(N)]


def procesarAudio(file_path):
    """Función principal mejorada para procesar audio"""
    try:
        # Convertir si es necesario
        if file_path.endswith(".webm"):
            file_path = webm_to_wav(file_path)
            if file_path is None:
                return None

        # Leer archivo WAV
        muestras, canales, tasa = leer_wav(file_path)
        longitud_total = len(muestras)
        tamano_segmento = 2048  # Aumentar para mejor resolución frecuencial
        overlap = tamano_segmento // 2  # Solapamiento del 50%
        resultados = []

        # Procesar cada segmento con solapamiento
        for inicio in range(0, longitud_total - tamano_segmento, overlap):
            segmento = muestras[inicio:inicio + tamano_segmento]

            # Aplicar ventana de Hamming
            segmento_ventana = aplicar_ventana_hamming(segmento)

            # Aplicar FFT
            transformada = fft_transform(segmento_ventana)

            # Calcular magnitudes (solo mitad positiva del espectro)
            magnitudes = [abs(f) for f in transformada[:tamano_segmento // 2]]

            # Encontrar frecuencia dominante
            max_idx = magnitudes.index(max(magnitudes))
            frecuencia_dominante = max_idx * (tasa / tamano_segmento)

            # Solo procesar si la frecuencia está en rango de voz humana
            if 80 <= frecuencia_dominante <= 2000:
                vocal = detectar_vocal(frecuencia_dominante)

                resultados.append({
                    "inicio": inicio / tasa,
                    "frecuencia_dominante": frecuencia_dominante,
                    "vocal": vocal,
                    "confianza": max(magnitudes) / sum(magnitudes)  # Métrica de confianza
                })

        # Filtrar resultados por confianza
        resultados_filtrados = [r for r in resultados if r["confianza"] > 0.1]

        logger.info(f"Procesamiento completo: {len(resultados_filtrados)} segmentos válidos")
        return resultados_filtrados

    except Exception as e:
        logger.error(f"Error al procesar el archivo: {e}")
        return None