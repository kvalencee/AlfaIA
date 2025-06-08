# modules/procesarAudio_mejorado.py
import math
import subprocess
import cmath
import logging
import numpy as np
import librosa
import scipy.signal
from scipy.fft import fft, fftfreq
import tempfile
import os
from typing import List, Dict, Optional, Tuple
import json

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioProcessor:
    def __init__(self):
        """Inicializar el procesador de audio con configuraciones optimizadas"""

        # Configuraciones de audio
        self.sample_rate = 44100
        self.frame_size = 2048
        self.hop_length = 512
        self.n_mfcc = 13

        # Rangos de frecuencias para vocales en español (Hz)
        # Basado en formantes F1 y F2
        self.vocal_formants = {
            'A': {'f1': (700, 900), 'f2': (1200, 1400)},
            'E': {'f1': (400, 600), 'f2': (2000, 2400)},
            'I': {'f1': (250, 350), 'f2': (2200, 2600)},
            'O': {'f1': (450, 650), 'f2': (800, 1200)},
            'U': {'f1': (250, 350), 'f2': (600, 900)}
        }

        # Configuraciones de detección
        self.min_duration = 0.1  # Mínima duración de una vocal (segundos)
        self.energy_threshold = 0.01  # Umbral de energía para detectar habla
        self.confidence_threshold = 0.6  # Umbral de confianza para clasificación

        # Filtros de frecuencia para voz humana
        self.voice_freq_min = 80  # Hz
        self.voice_freq_max = 3000  # Hz

    def webm_to_wav_librosa(self, input_file: str) -> Optional[str]:
        """Convertir WEBM a WAV usando FFmpeg y cargar con librosa"""
        try:
            # Crear archivo temporal para WAV
            temp_wav = tempfile.mktemp(suffix='.wav')

            # Usar FFmpeg para conversión
            cmd = [
                'ffmpeg', '-i', input_file,
                '-ac', '1',  # Mono
                '-ar', str(self.sample_rate),  # Sample rate
                '-acodec', 'pcm_s16le',
                '-y',  # Sobrescribir
                temp_wav
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"Conversión exitosa: {temp_wav}")
                return temp_wav
            else:
                logger.error(f"Error en FFmpeg: {result.stderr}")
                return None

        except Exception as e:
            logger.error(f"Error en conversión: {e}")
            return None

    def load_audio(self, file_path: str) -> Optional[Tuple[np.ndarray, int]]:
        """Cargar archivo de audio con librosa"""
        try:
            # Si es WEBM, convertir primero
            if file_path.endswith('.webm'):
                wav_path = self.webm_to_wav_librosa(file_path)
                if not wav_path:
                    return None
                file_path = wav_path

            # Cargar con librosa
            audio, sr = librosa.load(file_path, sr=self.sample_rate, mono=True)

            # Limpiar archivo temporal si se creó
            if file_path.endswith('.wav') and 'tmp' in file_path:
                try:
                    os.remove(file_path)
                except:
                    pass

            logger.info(f"Audio cargado: {len(audio)} muestras, {sr} Hz")
            return audio, sr

        except Exception as e:
            logger.error(f"Error cargando audio: {e}")
            return None

    def preprocess_audio(self, audio: np.ndarray) -> np.ndarray:
        """Preprocesar audio para mejorar la detección"""
        try:
            # Normalizar
            audio = librosa.util.normalize(audio)

            # Filtro pasa-banda para voz humana
            nyquist = self.sample_rate / 2
            low = self.voice_freq_min / nyquist
            high = self.voice_freq_max / nyquist

            b, a = scipy.signal.butter(4, [low, high], btype='band')
            audio = scipy.signal.filtfilt(b, a, audio)

            # Reducir ruido usando filtro de Wiener simplificado
            audio = self.reduce_noise(audio)

            return audio

        except Exception as e:
            logger.error(f"Error en preprocesamiento: {e}")
            return audio

    def reduce_noise(self, audio: np.ndarray, noise_factor: float = 0.1) -> np.ndarray:
        """Reducción simple de ruido"""
        try:
            # Estimar ruido del inicio del audio (primeros 0.5 segundos)
            noise_sample_size = int(0.5 * self.sample_rate)
            if len(audio) > noise_sample_size:
                noise_profile = np.mean(np.abs(audio[:noise_sample_size]))

                # Aplicar gate de ruido simple
                threshold = noise_profile * (1 + noise_factor)
                audio = np.where(np.abs(audio) > threshold, audio, audio * 0.1)

            return audio

        except Exception as e:
            logger.error(f"Error en reducción de ruido: {e}")
            return audio

    def detect_speech_segments(self, audio: np.ndarray) -> List[Tuple[float, float]]:
        """Detectar segmentos de habla usando energía y ZCR"""
        try:
            # Calcular energía por frame
            frame_length = self.frame_size
            hop_length = self.hop_length

            energy = []
            zcr = []  # Zero Crossing Rate

            for i in range(0, len(audio) - frame_length, hop_length):
                frame = audio[i:i + frame_length]

                # Energía RMS
                frame_energy = np.sqrt(np.mean(frame ** 2))
                energy.append(frame_energy)

                # Zero Crossing Rate
                zero_crossings = np.sum(np.abs(np.diff(np.sign(frame))))
                zcr.append(zero_crossings / len(frame))

            energy = np.array(energy)
            zcr = np.array(zcr)

            # Umbral adaptativo para energía
            energy_threshold = np.percentile(energy, 60)  # Percentil 60
            energy_threshold = max(energy_threshold, self.energy_threshold)

            # Detectar frames de habla
            speech_frames = (energy > energy_threshold) & (zcr < 0.3)

            # Convertir frames a tiempos
            segments = []
            in_speech = False
            start_time = 0

            for i, is_speech in enumerate(speech_frames):
                time = i * hop_length / self.sample_rate

                if is_speech and not in_speech:
                    start_time = time
                    in_speech = True
                elif not is_speech and in_speech:
                    if time - start_time >= self.min_duration:
                        segments.append((start_time, time))
                    in_speech = False

            # Cerrar último segmento si es necesario
            if in_speech:
                end_time = len(audio) / self.sample_rate
                if end_time - start_time >= self.min_duration:
                    segments.append((start_time, end_time))

            logger.info(f"Detectados {len(segments)} segmentos de habla")
            return segments

        except Exception as e:
            logger.error(f"Error en detección de habla: {e}")
            return [(0, len(audio) / self.sample_rate)]

    def extract_formants(self, audio_segment: np.ndarray) -> Dict[str, float]:
        """Extraer formantes usando LPC (Linear Predictive Coding)"""
        try:
            # Aplicar ventana Hamming
            windowed = audio_segment * np.hamming(len(audio_segment))

            # Análisis LPC
            order = 12  # Orden del filtro LPC
            a = librosa.lpc(windowed, order=order)

            # Encontrar raíces del polinomio LPC
            roots = np.roots(a)

            # Filtrar raíces complejas dentro del círculo unitario
            roots = roots[np.abs(roots) < 1]

            # Convertir a frecuencias
            angles = np.angle(roots)
            frequencies = np.abs(angles) * self.sample_rate / (2 * np.pi)

            # Filtrar frecuencias en rango de voz
            voice_freqs = frequencies[
                (frequencies >= self.voice_freq_min) &
                (frequencies <= self.voice_freq_max)
                ]

            if len(voice_freqs) >= 2:
                # Ordenar y tomar los primeros dos formantes
                voice_freqs = np.sort(voice_freqs)
                return {
                    'f1': voice_freqs[0],
                    'f2': voice_freqs[1] if len(voice_freqs) > 1 else voice_freqs[0]
                }
            else:
                # Fallback usando FFT
                return self.extract_formants_fft(audio_segment)

        except Exception as e:
            logger.error(f"Error extrayendo formantes LPC: {e}")
            return self.extract_formants_fft(audio_segment)

    def extract_formants_fft(self, audio_segment: np.ndarray) -> Dict[str, float]:
        """Extraer formantes usando FFT como fallback"""
        try:
            # FFT
            fft_vals = np.abs(fft(audio_segment * np.hamming(len(audio_segment))))
            freqs = fftfreq(len(audio_segment), 1 / self.sample_rate)

            # Solo frecuencias positivas
            positive_freqs = freqs[:len(freqs) // 2]
            positive_fft = fft_vals[:len(fft_vals) // 2]

            # Filtrar rango de voz
            voice_mask = (positive_freqs >= self.voice_freq_min) & (positive_freqs <= self.voice_freq_max)
            voice_freqs = positive_freqs[voice_mask]
            voice_fft = positive_fft[voice_mask]

            if len(voice_fft) > 0:
                # Encontrar picos
                peaks, _ = scipy.signal.find_peaks(voice_fft, height=np.max(voice_fft) * 0.1)

                if len(peaks) >= 2:
                    # Tomar los dos picos más prominentes
                    peak_heights = voice_fft[peaks]
                    sorted_indices = np.argsort(peak_heights)[::-1]

                    f1_idx = peaks[sorted_indices[0]]
                    f2_idx = peaks[sorted_indices[1]]

                    f1 = voice_freqs[f1_idx]
                    f2 = voice_freqs[f2_idx]

                    # Asegurar que F1 < F2
                    if f1 > f2:
                        f1, f2 = f2, f1

                    return {'f1': f1, 'f2': f2}

            # Si no se encuentran picos, usar frecuencia dominante
            max_idx = np.argmax(voice_fft)
            dominant_freq = voice_freqs[max_idx]
            return {'f1': dominant_freq, 'f2': dominant_freq * 1.5}

        except Exception as e:
            logger.error(f"Error en extracción FFT: {e}")
            return {'f1': 500, 'f2': 1500}  # Valores por defecto

    def classify_vowel(self, formants: Dict[str, float]) -> Tuple[str, float]:
        """Clasificar vocal basado en formantes con confianza"""
        try:
            f1 = formants['f1']
            f2 = formants['f2']

            best_vowel = 'Desconocido'
            best_confidence = 0.0

            for vowel, ranges in self.vocal_formants.items():
                # Calcular distancia normalizada a los rangos de formantes
                f1_center = (ranges['f1'][0] + ranges['f1'][1]) / 2
                f2_center = (ranges['f2'][0] + ranges['f2'][1]) / 2

                f1_width = ranges['f1'][1] - ranges['f1'][0]
                f2_width = ranges['f2'][1] - ranges['f2'][0]

                # Distancia normalizada
                f1_dist = abs(f1 - f1_center) / f1_width
                f2_dist = abs(f2 - f2_center) / f2_width

                # Confianza basada en proximidad (función gaussiana)
                confidence = math.exp(-(f1_dist ** 2 + f2_dist ** 2) / 2)

                if confidence > best_confidence:
                    best_confidence = confidence
                    best_vowel = vowel

            # Solo retornar si la confianza es suficiente
            if best_confidence >= self.confidence_threshold:
                return best_vowel, best_confidence
            else:
                return 'Desconocido', best_confidence

        except Exception as e:
            logger.error(f"Error clasificando vocal: {e}")
            return 'Desconocido', 0.0

    def extract_additional_features(self, audio_segment: np.ndarray) -> Dict:
        """Extraer características adicionales del audio"""
        try:
            features = {}

            # MFCCs
            mfccs = librosa.feature.mfcc(
                y=audio_segment,
                sr=self.sample_rate,
                n_mfcc=self.n_mfcc
            )
            features['mfcc_mean'] = np.mean(mfccs, axis=1).tolist()

            # Espectrograma mel
            mel_spectrogram = librosa.feature.melspectrogram(
                y=audio_segment,
                sr=self.sample_rate
            )
            features['mel_mean'] = np.mean(mel_spectrogram, axis=1).tolist()

            # Características temporales
            features['duration'] = len(audio_segment) / self.sample_rate
            features['energy'] = float(np.mean(audio_segment ** 2))
            features['zcr'] = float(np.mean(librosa.feature.zero_crossing_rate(audio_segment)))

            # Características espectrales
            spectral_centroids = librosa.feature.spectral_centroid(y=audio_segment, sr=self.sample_rate)
            features['spectral_centroid'] = float(np.mean(spectral_centroids))

            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio_segment, sr=self.sample_rate)
            features['spectral_rolloff'] = float(np.mean(spectral_rolloff))

            return features

        except Exception as e:
            logger.error(f"Error extrayendo características: {e}")
            return {}

    def process_audio_advanced(self, file_path: str) -> Optional[List[Dict]]:
        """Procesamiento avanzado de audio con todas las mejoras"""
        try:
            # Cargar audio
            audio_data = self.load_audio(file_path)
            if audio_data is None:
                return None

            audio, sr = audio_data

            # Preprocesar
            audio = self.preprocess_audio(audio)

            # Detectar segmentos de habla
            speech_segments = self.detect_speech_segments(audio)

            if not speech_segments:
                logger.warning("No se detectaron segmentos de habla")
                return []

            results = []

            for start_time, end_time in speech_segments:
                # Extraer segmento
                start_sample = int(start_time * sr)
                end_sample = int(end_time * sr)
                segment = audio[start_sample:end_sample]

                if len(segment) < self.frame_size:
                    continue

                # Extraer formantes
                formants = self.extract_formants(segment)

                # Clasificar vocal
                vowel, confidence = self.classify_vowel(formants)

                # Extraer características adicionales
                additional_features = self.extract_additional_features(segment)

                # Almacenar resultado
                result = {
                    'inicio': start_time,
                    'fin': end_time,
                    'duracion': end_time - start_time,
                    'vocal': vowel,
                    'confianza': confidence,
                    'formantes': formants,
                    'frecuencia_dominante': formants.get('f1', 0),
                    'caracteristicas': additional_features
                }

                results.append(result)

                logger.info(f"Vocal detectada: {vowel} (confianza: {confidence:.2f}) en {start_time:.2f}s")

            return results

        except Exception as e:
            logger.error(f"Error en procesamiento avanzado: {e}")
            return None

    def generate_analysis_report(self, results: List[Dict]) -> Dict:
        """Generar reporte de análisis del audio"""
        try:
            if not results:
                return {
                    'total_vocales': 0,
                    'duracion_total': 0,
                    'confianza_promedio': 0,
                    'distribucion_vocales': {},
                    'calidad_audio': 'Baja'
                }

            # Estadísticas básicas
            total_vocales = len(results)
            duracion_total = sum(r['duracion'] for r in results)
            confianza_promedio = np.mean([r['confianza'] for r in results])

            # Distribución de vocales
            distribucion = {}
            for result in results:
                vocal = result['vocal']
                if vocal != 'Desconocido':
                    distribucion[vocal] = distribucion.get(vocal, 0) + 1

            # Evaluar calidad del audio
            confianzas = [r['confianza'] for r in results]
            if np.mean(confianzas) > 0.8:
                calidad = 'Excelente'
            elif np.mean(confianzas) > 0.6:
                calidad = 'Buena'
            elif np.mean(confianzas) > 0.4:
                calidad = 'Regular'
            else:
                calidad = 'Baja'

            return {
                'total_vocales': total_vocales,
                'duracion_total': duracion_total,
                'confianza_promedio': confianza_promedio,
                'distribucion_vocales': distribucion,
                'calidad_audio': calidad,
                'vocales_detectadas': [r['vocal'] for r in results if r['vocal'] != 'Desconocido'],
                'recomendaciones': self.generate_recommendations(results)
            }

        except Exception as e:
            logger.error(f"Error generando reporte: {e}")
            return {}

    def generate_recommendations(self, results: List[Dict]) -> List[str]:
        """Generar recomendaciones basadas en el análisis"""
        recommendations = []

        try:
            if not results:
                return ['Intenta hablar más cerca del micrófono', 'Asegúrate de que no haya ruido de fondo']

            confianzas = [r['confianza'] for r in results]
            confianza_promedio = np.mean(confianzas)

            # Recomendaciones basadas en confianza
            if confianza_promedio < 0.5:
                recommendations.extend([
                    'Habla más claramente y despacio',
                    'Reduce el ruido de fondo',
                    'Acércate más al micrófono'
                ])
            elif confianza_promedio < 0.7:
                recommendations.extend([
                    'Exagera un poco más la pronunciación',
                    'Mantén un volumen constante'
                ])
            else:
                recommendations.append('¡Excelente pronunciación! Sigue así')

            # Analizar distribución de vocales
            distribucion = {}
            for result in results:
                vocal = result['vocal']
                if vocal != 'Desconocido':
                    distribucion[vocal] = distribucion.get(vocal, 0) + 1

            vocales_esperadas = set(['A', 'E', 'I', 'O', 'U'])
            vocales_detectadas = set(distribucion.keys())
            vocales_faltantes = vocales_esperadas - vocales_detectadas

            if vocales_faltantes:
                recommendations.append(f"Intenta pronunciar las vocales: {', '.join(sorted(vocales_faltantes))}")

            # Recomendaciones específicas por vocal
            for vocal, count in distribucion.items():
                if count == 1:
                    recommendations.append(f"Practica más la vocal '{vocal}'")

            # Análisis de duración
            duraciones = [r['duracion'] for r in results]
            if np.mean(duraciones) < 0.2:
                recommendations.append('Intenta sostener las vocales un poco más tiempo')

            return recommendations[:5]  # Máximo 5 recomendaciones

        except Exception as e:
            logger.error(f"Error generando recomendaciones: {e}")
            return ['Sigue practicando para mejorar tu pronunciación']


# Función principal compatible con el sistema existente
def procesarAudio(file_path: str) -> Optional[List[Dict]]:
    """
    Función principal para procesar audio - compatible con el sistema existente
    pero con todas las mejoras implementadas
    """
    try:
        processor = AudioProcessor()

        # Procesar con el sistema avanzado
        results = processor.process_audio_advanced(file_path)

        if not results:
            logger.warning("No se obtuvieron resultados del procesamiento avanzado")
            return None

        # Convertir a formato compatible con el sistema existente
        compatible_results = []
        for result in results:
            compatible_result = {
                'inicio': result['inicio'],
                'fin': result.get('fin', result['inicio'] + result.get('duracion', 1.0)),
                'frecuencia_dominante': result['frecuencia_dominante'],
                'vocal': result['vocal'],
                'confianza': result['confianza'],
                'formantes': result.get('formantes', {}),
                'duracion': result.get('duracion', 1.0)
            }
            compatible_results.append(compatible_result)

        logger.info(f"Procesamiento completado: {len(compatible_results)} resultados")
        return compatible_results

    except Exception as e:
        logger.error(f"Error en procesarAudio: {e}")
        return None


# Función avanzada para análisis completo
def procesarAudioAvanzado(file_path: str) -> Optional[Dict]:
    """
    Función avanzada que retorna análisis completo del audio
    """
    try:
        processor = AudioProcessor()

        # Procesar audio
        results = processor.process_audio_advanced(file_path)

        if not results:
            return None

        # Generar reporte completo
        analysis_report = processor.generate_analysis_report(results)

        return {
            'resultados_detallados': results,
            'reporte_analisis': analysis_report,
            'processor_config': {
                'sample_rate': processor.sample_rate,
                'confidence_threshold': processor.confidence_threshold,
                'vocal_formants': processor.vocal_formants
            }
        }

    except Exception as e:
        logger.error(f"Error en procesamiento avanzado: {e}")
        return None


# Clase para entrenar/calibrar el sistema (futuro)
class AudioTrainer:
    """Clase para entrenar y calibrar el sistema de reconocimiento"""

    def __init__(self):
        self.training_data = []
        self.processor = AudioProcessor()

    def add_training_sample(self, file_path: str, expected_vowel: str, user_id: str = None):
        """Agregar muestra de entrenamiento"""
        try:
            results = self.processor.process_audio_advanced(file_path)
            if results:
                training_sample = {
                    'file_path': file_path,
                    'expected_vowel': expected_vowel,
                    'user_id': user_id,
                    'results': results,
                    'timestamp': time.time()
                }
                self.training_data.append(training_sample)
                logger.info(f"Muestra de entrenamiento agregada: {expected_vowel}")
                return True
        except Exception as e:
            logger.error(f"Error agregando muestra de entrenamiento: {e}")
        return False

    def calibrate_for_user(self, user_id: str) -> Dict:
        """Calibrar el sistema para un usuario específico"""
        try:
            user_samples = [s for s in self.training_data if s.get('user_id') == user_id]

            if len(user_samples) < 10:
                return {'success': False, 'message': 'Necesitas al menos 10 muestras para calibrar'}

            # Analizar patrones del usuario
            user_formants = {}
            for sample in user_samples:
                expected = sample['expected_vowel']
                if expected not in user_formants:
                    user_formants[expected] = {'f1': [], 'f2': []}

                for result in sample['results']:
                    if result['vocal'] == expected and result['confianza'] > 0.5:
                        formants = result['formantes']
                        user_formants[expected]['f1'].append(formants['f1'])
                        user_formants[expected]['f2'].append(formants['f2'])

            # Calcular rangos personalizados
            personalized_ranges = {}
            for vowel, formant_data in user_formants.items():
                if len(formant_data['f1']) >= 3:  # Mínimo 3 muestras
                    f1_mean = np.mean(formant_data['f1'])
                    f1_std = np.std(formant_data['f1'])
                    f2_mean = np.mean(formant_data['f2'])
                    f2_std = np.std(formant_data['f2'])

                    personalized_ranges[vowel] = {
                        'f1': (f1_mean - f1_std, f1_mean + f1_std),
                        'f2': (f2_mean - f2_std, f2_mean + f2_std)
                    }

            logger.info(f"Calibración completada para usuario {user_id}")
            return {
                'success': True,
                'personalized_ranges': personalized_ranges,
                'samples_used': len(user_samples)
            }

        except Exception as e:
            logger.error(f"Error en calibración: {e}")
            return {'success': False, 'message': 'Error en calibración'}


# Sistema de métricas y evaluación
class AudioMetrics:
    """Clase para calcular métricas de rendimiento del sistema"""

    @staticmethod
    def calculate_accuracy(true_labels: List[str], predicted_labels: List[str]) -> Dict:
        """Calcular precisión del sistema"""
        try:
            if len(true_labels) != len(predicted_labels):
                return {'error': 'Las listas deben tener la misma longitud'}

            total = len(true_labels)
            correct = sum(1 for t, p in zip(true_labels, predicted_labels) if t == p)

            accuracy = correct / total if total > 0 else 0

            # Matriz de confusión
            from collections import defaultdict
            confusion_matrix = defaultdict(lambda: defaultdict(int))

            for true_label, pred_label in zip(true_labels, predicted_labels):
                confusion_matrix[true_label][pred_label] += 1

            # Métricas por clase
            vowels = set(true_labels + predicted_labels)
            class_metrics = {}

            for vowel in vowels:
                tp = confusion_matrix[vowel][vowel]
                fp = sum(confusion_matrix[other][vowel] for other in vowels if other != vowel)
                fn = sum(confusion_matrix[vowel][other] for other in vowels if other != vowel)

                precision = tp / (tp + fp) if (tp + fp) > 0 else 0
                recall = tp / (tp + fn) if (tp + fn) > 0 else 0
                f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

                class_metrics[vowel] = {
                    'precision': precision,
                    'recall': recall,
                    'f1_score': f1_score
                }

            return {
                'accuracy': accuracy,
                'total_samples': total,
                'correct_predictions': correct,
                'class_metrics': class_metrics,
                'confusion_matrix': dict(confusion_matrix)
            }

        except Exception as e:
            logger.error(f"Error calculando métricas: {e}")
            return {'error': str(e)}


# Utilidades adicionales
def validate_audio_file(file_path: str) -> Dict:
    """Validar archivo de audio antes del procesamiento"""
    try:
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            return {'valid': False, 'error': 'Archivo no encontrado'}

        # Verificar tamaño del archivo
        file_size = os.path.getsize(file_path)
        if file_size > 50 * 1024 * 1024:  # 50MB máximo
            return {'valid': False, 'error': 'Archivo demasiado grande (máximo 50MB)'}

        if file_size < 1024:  # 1KB mínimo
            return {'valid': False, 'error': 'Archivo demasiado pequeño'}

        # Verificar extensión
        valid_extensions = ['.webm', '.wav', '.mp3', '.m4a', '.flac']
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension not in valid_extensions:
            return {'valid': False, 'error': f'Extensión no soportada: {file_extension}'}

        return {
            'valid': True,
            'file_size': file_size,
            'extension': file_extension
        }

    except Exception as e:
        return {'valid': False, 'error': str(e)}


def benchmark_system(test_files: List[Tuple[str, str]]) -> Dict:
    """
    Hacer benchmark del sistema de reconocimiento
    test_files: Lista de tuplas (ruta_archivo, vocal_esperada)
    """
    try:
        processor = AudioProcessor()
        results = []

        for file_path, expected_vowel in test_files:
            # Validar archivo
            validation = validate_audio_file(file_path)
            if not validation['valid']:
                continue

            # Procesar archivo
            audio_results = processor.process_audio_advanced(file_path)

            if audio_results:
                # Tomar la vocal con mayor confianza
                best_result = max(audio_results, key=lambda x: x['confianza'])
                predicted_vowel = best_result['vocal']
            else:
                predicted_vowel = 'Desconocido'

            results.append({
                'file': file_path,
                'expected': expected_vowel,
                'predicted': predicted_vowel,
                'confidence': best_result.get('confianza', 0) if audio_results else 0
            })

        # Calcular métricas
        true_labels = [r['expected'] for r in results]
        pred_labels = [r['predicted'] for r in results]

        metrics = AudioMetrics.calculate_accuracy(true_labels, pred_labels)

        return {
            'results': results,
            'metrics': metrics,
            'total_files_processed': len(results)
        }

    except Exception as e:
        logger.error(f"Error en benchmark: {e}")
        return {'error': str(e)}


# Reemplazar el archivo modules/procesarAudio.py existente con este contenido mejorado
# También podemos mantener compatibilidad con el sistema anterior

# === COMPATIBILIDAD CON SISTEMA ANTERIOR ===

def webm_to_wav(input_file):
    """Función de compatibilidad - usar la nueva implementación"""
    try:
        processor = AudioProcessor()
        return processor.webm_to_wav_librosa(input_file)
    except Exception as e:
        logger.error(f"Error en compatibilidad webm_to_wav: {e}")
        return None


def detectar_vocal(frecuencia):
    """Función de compatibilidad - mantener interfaz antigua"""
    # Rangos simplificados para compatibilidad
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


# === FUNCIONES DE CONFIGURACIÓN ===

def configure_audio_processor(config: Dict):
    """Configurar el procesador de audio global"""
    global audio_processor

    try:
        if 'sample_rate' in config:
            audio_processor.sample_rate = config['sample_rate']

        if 'confidence_threshold' in config:
            audio_processor.confidence_threshold = config['confidence_threshold']

        if 'energy_threshold' in config:
            audio_processor.energy_threshold = config['energy_threshold']

        if 'vocal_formants' in config:
            audio_processor.vocal_formants.update(config['vocal_formants'])

        logger.info("Configuración del procesador de audio actualizada")
        return True

    except Exception as e:
        logger.error(f"Error configurando procesador: {e}")
        return False


def get_processor_config():
    """Obtener configuración actual del procesador"""
    global audio_processor

    return {
        'sample_rate': audio_processor.sample_rate,
        'confidence_threshold': audio_processor.confidence_threshold,
        'energy_threshold': audio_processor.energy_threshold,
        'vocal_formants': audio_processor.vocal_formants,
        'frame_size': audio_processor.frame_size,
        'hop_length': audio_processor.hop_length
    }


# === FUNCIONES DE ANÁLISIS ESTADÍSTICO ===

def analyze_user_voice_pattern(user_audio_files: List[Tuple[str, str]]) -> Dict:
    """
    Analizar patrones de voz de un usuario específico
    user_audio_files: Lista de tuplas (archivo, vocal_esperada)
    """
    try:
        processor = AudioProcessor()
        user_patterns = {
            'A': {'f1': [], 'f2': [], 'confidence': []},
            'E': {'f1': [], 'f2': [], 'confidence': []},
            'I': {'f1': [], 'f2': [], 'confidence': []},
            'O': {'f1': [], 'f2': [], 'confidence': []},
            'U': {'f1': [], 'f2': [], 'confidence': []}
        }

        total_processed = 0
        successful_detections = 0

        for file_path, expected_vowel in user_audio_files:
            results = processor.process_audio_advanced(file_path)

            if not results:
                continue

            total_processed += 1

            # Encontrar la mejor detección para la vocal esperada
            best_match = None
            best_confidence = 0

            for result in results:
                if result['vocal'] == expected_vowel and result['confianza'] > best_confidence:
                    best_match = result
                    best_confidence = result['confianza']

            if best_match and expected_vowel in user_patterns:
                formants = best_match['formantes']
                user_patterns[expected_vowel]['f1'].append(formants['f1'])
                user_patterns[expected_vowel]['f2'].append(formants['f2'])
                user_patterns[expected_vowel]['confidence'].append(best_match['confianza'])
                successful_detections += 1

        # Calcular estadísticas por vocal
        voice_profile = {}
        for vowel, data in user_patterns.items():
            if len(data['f1']) > 0:
                voice_profile[vowel] = {
                    'f1_mean': np.mean(data['f1']),
                    'f1_std': np.std(data['f1']),
                    'f2_mean': np.mean(data['f2']),
                    'f2_std': np.std(data['f2']),
                    'avg_confidence': np.mean(data['confidence']),
                    'sample_count': len(data['f1'])
                }

        return {
            'voice_profile': voice_profile,
            'total_files_processed': total_processed,
            'successful_detections': successful_detections,
            'success_rate': successful_detections / total_processed if total_processed > 0 else 0,
            'overall_confidence': np.mean([
                np.mean(data['confidence']) for data in user_patterns.values()
                if len(data['confidence']) > 0
            ]) if any(len(data['confidence']) > 0 for data in user_patterns.values()) else 0
        }

    except Exception as e:
        logger.error(f"Error analizando patrones de voz: {e}")
        return {'error': str(e)}


def create_personalized_model(voice_profile: Dict) -> Dict:
    """Crear modelo personalizado basado en el perfil de voz del usuario"""
    try:
        if 'voice_profile' not in voice_profile:
            return {'error': 'Perfil de voz inválido'}

        profile = voice_profile['voice_profile']
        personalized_formants = {}

        for vowel, stats in profile.items():
            if stats['sample_count'] >= 3:  # Mínimo 3 muestras para ser confiable
                # Crear rangos personalizados basados en media ± 1.5 * desviación estándar
                f1_range = (
                    max(50, stats['f1_mean'] - 1.5 * stats['f1_std']),
                    min(2000, stats['f1_mean'] + 1.5 * stats['f1_std'])
                )
                f2_range = (
                    max(500, stats['f2_mean'] - 1.5 * stats['f2_std']),
                    min(4000, stats['f2_mean'] + 1.5 * stats['f2_std'])
                )

                personalized_formants[vowel] = {
                    'f1': f1_range,
                    'f2': f2_range
                }

        return {
            'success': True,
            'personalized_formants': personalized_formants,
            'confidence_threshold': max(0.4, voice_profile.get('overall_confidence', 0.6) - 0.1),
            'model_quality': 'Excelente' if len(personalized_formants) >= 4 else 'Buena' if len(
                personalized_formants) >= 2 else 'Básica'
        }

    except Exception as e:
        logger.error(f"Error creando modelo personalizado: {e}")
        return {'error': str(e)}


# === FUNCIONES DE DEPURACIÓN Y DIAGNÓSTICO ===

def diagnose_audio_quality(file_path: str) -> Dict:
    """Diagnosticar calidad del audio y problemas potenciales"""
    try:
        processor = AudioProcessor()

        # Cargar audio
        audio_data = processor.load_audio(file_path)
        if not audio_data:
            return {'error': 'No se pudo cargar el archivo de audio'}

        audio, sr = audio_data

        # Análisis de calidad
        diagnostics = {
            'file_path': file_path,
            'duration': len(audio) / sr,
            'sample_rate': sr,
            'audio_length': len(audio)
        }

        # Análisis de energía
        energy = np.mean(audio ** 2)
        diagnostics['energy_level'] = energy

        if energy < 0.001:
            diagnostics['energy_status'] = 'Muy bajo - Aumenta el volumen'
        elif energy < 0.01:
            diagnostics['energy_status'] = 'Bajo - Habla más fuerte'
        elif energy > 0.5:
            diagnostics['energy_status'] = 'Muy alto - Reduce el volumen o aléjate del micrófono'
        else:
            diagnostics['energy_status'] = 'Óptimo'

        # Análisis de ruido
        noise_level = np.std(audio[:int(0.5 * sr)]) if len(audio) > sr else np.std(audio)
        diagnostics['noise_level'] = noise_level

        if noise_level > 0.1:
            diagnostics['noise_status'] = 'Alto - Reduce el ruido de fondo'
        elif noise_level > 0.05:
            diagnostics['noise_status'] = 'Moderado - Considera reducir el ruido'
        else:
            diagnostics['noise_status'] = 'Bajo - Excelente'

        # Análisis espectral
        fft_vals = np.abs(np.fft.fft(audio))
        freqs = np.fft.fftfreq(len(audio), 1 / sr)

        # Energía en rango de voz (80-3000 Hz)
        voice_mask = (freqs >= 80) & (freqs <= 3000)
        voice_energy = np.sum(fft_vals[voice_mask])
        total_energy = np.sum(fft_vals)

        voice_ratio = voice_energy / total_energy if total_energy > 0 else 0
        diagnostics['voice_energy_ratio'] = voice_ratio

        if voice_ratio > 0.7:
            diagnostics['spectral_status'] = 'Excelente - Audio claro de voz'
        elif voice_ratio > 0.5:
            diagnostics['spectral_status'] = 'Bueno - Mayoría energía en rango de voz'
        else:
            diagnostics['spectral_status'] = 'Pobre - Mucho ruido o audio no vocal'

        # Recomendaciones generales
        recommendations = []

        if diagnostics['energy_status'] != 'Óptimo':
            recommendations.append(f"Energía: {diagnostics['energy_status']}")

        if diagnostics['noise_status'] != 'Bajo - Excelente':
            recommendations.append(f"Ruido: {diagnostics['noise_status']}")

        if diagnostics['spectral_status'] == 'Pobre - Mucho ruido o audio no vocal':
            recommendations.append('Asegúrate de que el audio contenga principalmente voz')

        if diagnostics['duration'] < 0.5:
            recommendations.append('Audio muy corto - Intenta grabar por más tiempo')
        elif diagnostics['duration'] > 10:
            recommendations.append('Audio muy largo - Considera usar segmentos más cortos')

        diagnostics['recommendations'] = recommendations
        diagnostics['overall_quality'] = 'Excelente' if len(recommendations) == 0 else 'Buena' if len(
            recommendations) <= 2 else 'Necesita mejoras'

        return diagnostics

    except Exception as e:
        logger.error(f"Error en diagnóstico de audio: {e}")
        return {'error': str(e)}


def test_microphone_setup() -> Dict:
    """Probar configuración del micrófono del sistema"""
    try:
        import subprocess
        import platform

        results = {
            'system': platform.system(),
            'python_version': platform.python_version()
        }

        # Verificar FFmpeg
        try:
            ffmpeg_result = subprocess.run(['ffmpeg', '-version'],
                                           capture_output=True, text=True, timeout=10)
            results['ffmpeg_available'] = ffmpeg_result.returncode == 0
            if results['ffmpeg_available']:
                # Extraer versión de FFmpeg
                version_line = ffmpeg_result.stdout.split('\n')[0]
                results['ffmpeg_version'] = version_line
        except:
            results['ffmpeg_available'] = False
            results['ffmpeg_error'] = 'FFmpeg no encontrado o no responde'

        # Verificar librerías de audio Python
        try:
            import librosa
            results['librosa_version'] = librosa.__version__
        except ImportError:
            results['librosa_error'] = 'Librosa no instalada'

        try:
            import scipy
            results['scipy_version'] = scipy.__version__
        except ImportError:
            results['scipy_error'] = 'SciPy no instalada'

        try:
            import numpy
            results['numpy_version'] = numpy.__version__
        except ImportError:
            results['numpy_error'] = 'NumPy no instalada'

        # Evaluar estado general
        critical_components = ['ffmpeg_available', 'librosa_version', 'scipy_version', 'numpy_version']
        missing_components = [comp for comp in critical_components if comp not in results]

        if not missing_components:
            results['setup_status'] = 'Completo - Todo configurado correctamente'
            results['ready_for_processing'] = True
        else:
            results['setup_status'] = f'Incompleto - Faltan: {", ".join(missing_components)}'
            results['ready_for_processing'] = False

        return results

    except Exception as e:
        logger.error(f"Error probando configuración: {e}")
        return {'error': str(e), 'ready_for_processing': False}


if __name__ == "__main__":
    # Ejemplo de uso y pruebas
    print("=== SISTEMA DE RECONOCIMIENTO DE VOZ ALFAIA ===")

    # Probar configuración
    setup_test = test_microphone_setup()
    print(f"Estado del sistema: {setup_test.get('setup_status', 'Error')}")

    if setup_test.get('ready_for_processing'):
        print("✓ Sistema listo para procesar audio")

        # Ejemplo de configuración personalizada
        custom_config = {
            'confidence_threshold': 0.7,
            'energy_threshold': 0.02
        }
        configure_audio_processor(custom_config)
        print("✓ Configuración personalizada aplicada")

    else:
        print("✗ Sistema no está completamente configurado")
        print("Instala las dependencias faltantes y verifica la instalación de FFmpeg")