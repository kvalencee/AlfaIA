import math
import subprocess
import cmath

def webm_to_wav(input_file):
    output_file = input_file.replace(".webm", ".wav")
    try:
        subprocess.run([
            'ffmpeg', '-i', input_file,
            '-ac', '2',          # 2 canales (estéreo)
            '-ar', '44100',      # Tasa de muestreo de 44.1 kHz
            '-acodec', 'pcm_s16le',  # Códec PCM de 16 bits
            output_file
        ], check=True)
        print(f"Conversión exitosa: {output_file}")
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"Error al convertir el archivo: {e}")
        return None

def leer_wav(archivo):
    with open(archivo, "rb") as f:
        header = f.read(44)
        
        # Verificar que el archivo sea un WAV válido
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
        
        print(f"Información del archivo {archivo}:")
        print(f"Canales: {num_canales}")
        print(f"Tasa de muestreo: {tasa_muestreo} Hz")
        print(f"Tamaño de datos: {tamano_datos} bytes")
        print(f"Profundidad de bits: {profundidad_bits} bits")
        print(f"Duración: {duracion:.2f} segundos")
        
        # Leer los datos de audio
        datos = f.read()
        muestras = []
        paso = profundidad_bits // 8
        for i in range(0, len(datos), paso):
            muestra = int.from_bytes(datos[i:i+paso], byteorder="little", signed=True)
            muestras.append(muestra)
        
        return muestras, num_canales, tasa_muestreo

def fft_transform(signal):
    N = len(signal)
    if N <= 1:
        return signal
    
    # Ajustar la longitud de la señal a una potencia de 2
    if N % 2 != 0:
        next_power_of_two = 2**math.ceil(math.log2(N))
        signal += [0] * (next_power_of_two - N)
        N = len(signal)
    
    # Dividir la señal en partes pares e impares
    even = fft_transform(signal[0::2])
    odd = fft_transform(signal[1::2])
    
    # Calcular los factores de giro (twiddle factors)
    T = [cmath.exp(-2j * math.pi * k / N) * odd[k] for k in range(N // 2)]
    
    # Combinar los resultados
    return [even[k] + T[k] for k in range(N // 2)] + [even[k] - T[k] for k in range(N // 2)]

def detectar_vocal(frecuencia):
    if 200 <= frecuencia < 400:  # Rangos para 'I' y 'U'
        # 'I' y 'U' tienen rangos similares, por lo que no se pueden distinguir solo por frecuencia
        return 'I/U'
    elif 400 <= frecuencia < 700:  # Rango para 'E'
        return 'E'
    elif 700 <= frecuencia < 1100:  # Rango para 'A'
        return 'A'
    elif 1100 <= frecuencia < 1500:  # Rango para 'O'
        return 'O'
    else:
        return 'Desconocido'

def procesarAudio(file_path):
    if file_path.endswith(".webm"):
        file_path = webm_to_wav(file_path)
        if file_path is None:
            return None  # Si la conversión falla, salir
    
    try:
        muestras, canales, tasa = leer_wav(file_path)
        longitud_total = len(muestras)
        tamano_segmento = 1024  # Tamaño de cada segmento
        resultados = []

        # Procesar cada segmento
        for inicio in range(0, longitud_total, tamano_segmento):
            segmento = muestras[inicio:inicio + tamano_segmento]
            if len(segmento) < tamano_segmento:
                break  # Ignorar el último segmento si es más pequeño
            
            transformada = fft_transform(segmento)
            magnitudes = [abs(f) for f in transformada]
            frecuencia_dominante = magnitudes.index(max(magnitudes)) * (tasa / tamano_segmento)
            vocal = detectar_vocal(frecuencia_dominante)
            
            resultados.append({
                "inicio": inicio / tasa,  # Tiempo de inicio del segmento en segundos
                "frecuencia_dominante": frecuencia_dominante,
                "vocal": vocal
            })
        
        # Devolver todos los resultados
        return resultados
    except Exception as e:
        print(f"Error al procesar el archivo: {e}")
        return None