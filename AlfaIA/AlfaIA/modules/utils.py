# modules/utils.py - Utilidades Comunes para AlfaIA
# Ubicación: AlfaIA/AlfaIA/modules/utils.py

import os
import re
import json
import hashlib
import secrets
import unicodedata
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union, Tuple
from functools import wraps
import logging

logger = logging.getLogger(__name__)


# === UTILIDADES DE TEXTO ===

def limpiar_texto(texto: str) -> str:
    """Limpiar y normalizar texto"""
    if not texto:
        return ""

    # Remover espacios extra
    texto = re.sub(r'\s+', ' ', texto.strip())

    # Normalizar unicode
    texto = unicodedata.normalize('NFKD', texto)

    return texto


def extraer_palabras(texto: str) -> List[str]:
    """Extraer palabras de un texto, removiendo puntuación"""
    if not texto:
        return []

    # Remover puntuación y convertir a minúsculas
    texto_limpio = re.sub(r'[^\w\s]', ' ', texto.lower())

    # Extraer palabras
    palabras = re.findall(r'\b\w+\b', texto_limpio)

    return [palabra for palabra in palabras if len(palabra) > 1]


def normalizar_respuesta(respuesta: str) -> str:
    """Normalizar respuesta del usuario para comparación"""
    if not respuesta:
        return ""

    # Convertir a minúsculas y remover acentos
    respuesta = respuesta.lower().strip()

    # Remover acentos
    respuesta = unicodedata.normalize('NFD', respuesta)
    respuesta = ''.join(c for c in respuesta if unicodedata.category(c) != 'Mn')

    # Remover espacios extra
    respuesta = re.sub(r'\s+', ' ', respuesta)

    return respuesta


def calcular_similitud_texto(texto1: str, texto2: str) -> float:
    """Calcular similitud entre dos textos (0.0 a 1.0)"""
    texto1_norm = normalizar_respuesta(texto1)
    texto2_norm = normalizar_respuesta(texto2)

    if not texto1_norm or not texto2_norm:
        return 0.0

    if texto1_norm == texto2_norm:
        return 1.0

    # Calcular similitud usando distancia de Levenshtein simplificada
    palabras1 = set(extraer_palabras(texto1_norm))
    palabras2 = set(extraer_palabras(texto2_norm))

    if not palabras1 or not palabras2:
        return 0.0

    interseccion = len(palabras1.intersection(palabras2))
    union = len(palabras1.union(palabras2))

    return interseccion / union if union > 0 else 0.0


def generar_slug(texto: str) -> str:
    """Generar slug URL-friendly desde texto"""
    if not texto:
        return ""

    # Normalizar y limpiar
    slug = normalizar_respuesta(texto)

    # Reemplazar espacios y caracteres especiales con guiones
    slug = re.sub(r'[^a-z0-9]+', '-', slug)

    # Remover guiones al inicio y final
    slug = slug.strip('-')

    return slug


# === UTILIDADES DE VALIDACIÓN ===

def validar_email(email: str) -> bool:
    """Validar formato de email"""
    if not email:
        return False

    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(patron, email))


def validar_username(username: str) -> Dict[str, Union[bool, str]]:
    """Validar nombre de usuario"""
    result = {'valid': False, 'message': ''}

    if not username:
        result['message'] = 'El nombre de usuario es requerido'
        return result

    if len(username) < 3:
        result['message'] = 'El nombre de usuario debe tener al menos 3 caracteres'
        return result

    if len(username) > 20:
        result['message'] = 'El nombre de usuario no puede tener más de 20 caracteres'
        return result

    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        result['message'] = 'El nombre de usuario solo puede contener letras, números y guiones bajos'
        return result

    result['valid'] = True
    result['message'] = 'Nombre de usuario válido'
    return result


def validar_password(password: str) -> Dict[str, Union[bool, str, List[str]]]:
    """Validar contraseña"""
    result = {
        'valid': False,
        'message': '',
        'requirements_met': [],
        'requirements_failed': []
    }

    if not password:
        result['message'] = 'La contraseña es requerida'
        return result

    requirements = [
        ('length', len(password) >= 8, 'Al menos 8 caracteres'),
        ('uppercase', any(c.isupper() for c in password), 'Al menos una mayúscula'),
        ('lowercase', any(c.islower() for c in password), 'Al menos una minúscula'),
        ('number', any(c.isdigit() for c in password), 'Al menos un número')
    ]

    for req_name, passed, description in requirements:
        if passed:
            result['requirements_met'].append(description)
        else:
            result['requirements_failed'].append(description)

    result['valid'] = len(result['requirements_failed']) == 0

    if result['valid']:
        result['message'] = 'Contraseña válida'
    else:
        result['message'] = f"Faltan: {', '.join(result['requirements_failed'])}"

    return result


def validar_fecha_nacimiento(fecha_str: str) -> Dict[str, Union[bool, str, datetime]]:
    """Validar fecha de nacimiento"""
    result = {'valid': False, 'message': '', 'fecha': None}

    if not fecha_str:
        result['message'] = 'La fecha de nacimiento es requerida'
        return result

    try:
        # Intentar parsear la fecha
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d')

        # Verificar que no sea en el futuro
        if fecha > datetime.now():
            result['message'] = 'La fecha de nacimiento no puede ser en el futuro'
            return result

        # Verificar edad mínima (3 años) y máxima (120 años)
        hoy = datetime.now()
        edad = (hoy - fecha).days / 365.25

        if edad < 3:
            result['message'] = 'Edad mínima: 3 años'
            return result

        if edad > 120:
            result['message'] = 'Fecha de nacimiento no válida'
            return result

        result['valid'] = True
        result['fecha'] = fecha
        result['message'] = 'Fecha válida'

    except ValueError:
        result['message'] = 'Formato de fecha inválido (usar YYYY-MM-DD)'

    return result


# === UTILIDADES DE ARCHIVOS ===

def obtener_extension_archivo(filename: str) -> str:
    """Obtener extensión de archivo"""
    if not filename or '.' not in filename:
        return ""
    return filename.rsplit('.', 1)[1].lower()


def validar_archivo_subido(file, allowed_extensions: List[str], max_size_mb: int = 10) -> Dict[str, Union[bool, str]]:
    """Validar archivo subido"""
    result = {'valid': False, 'message': ''}

    if not file or not file.filename:
        result['message'] = 'No se seleccionó ningún archivo'
        return result

    # Validar extensión
    extension = obtener_extension_archivo(file.filename)
    if extension not in allowed_extensions:
        result['message'] = f'Extensión no permitida. Permitidas: {", ".join(allowed_extensions)}'
        return result

    # Validar tamaño (aproximado)
    if hasattr(file, 'content_length') and file.content_length:
        size_mb = file.content_length / (1024 * 1024)
        if size_mb > max_size_mb:
            result['message'] = f'Archivo muy grande. Máximo: {max_size_mb}MB'
            return result

    result['valid'] = True
    result['message'] = 'Archivo válido'
    return result


def generar_nombre_archivo_seguro(filename: str, user_id: int = None) -> str:
    """Generar nombre de archivo seguro para guardar"""
    if not filename:
        return f"archivo_{datetime.now().timestamp()}"

    # Obtener extensión
    extension = obtener_extension_archivo(filename)

    # Limpiar nombre
    nombre_base = os.path.splitext(filename)[0]
    nombre_limpio = re.sub(r'[^\w\-_.]', '_', nombre_base)

    # Añadir timestamp y user_id para evitar colisiones
    timestamp = int(datetime.now().timestamp())
    user_part = f"_{user_id}" if user_id else ""

    return f"{nombre_limpio}{user_part}_{timestamp}.{extension}"


def limpiar_archivos_temporales(temp_folder: str, max_age_hours: int = 24):
    """Limpiar archivos temporales antiguos"""
    if not os.path.exists(temp_folder):
        return

    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
    archivos_eliminados = 0

    try:
        for filename in os.listdir(temp_folder):
            filepath = os.path.join(temp_folder, filename)

            if os.path.isfile(filepath):
                # Verificar edad del archivo
                modified_time = datetime.fromtimestamp(os.path.getmtime(filepath))

                if modified_time < cutoff_time:
                    os.remove(filepath)
                    archivos_eliminados += 1

        if archivos_eliminados > 0:
            logger.info(f"🗑️ Limpieza temporal: {archivos_eliminados} archivos eliminados")

    except Exception as e:
        logger.error(f"Error limpiando archivos temporales: {e}")


# === UTILIDADES DE FECHAS ===

def formatear_fecha(fecha: datetime, formato: str = 'humano') -> str:
    """Formatear fecha en diferentes formatos"""
    if not fecha:
        return ""

    if formato == 'humano':
        ahora = datetime.now()
        diferencia = ahora - fecha

        if diferencia.days == 0:
            if diferencia.seconds < 3600:  # Menos de 1 hora
                minutos = diferencia.seconds // 60
                return f"hace {minutos} minuto{'s' if minutos != 1 else ''}"
            else:  # Menos de 24 horas
                horas = diferencia.seconds // 3600
                return f"hace {horas} hora{'s' if horas != 1 else ''}"
        elif diferencia.days == 1:
            return "ayer"
        elif diferencia.days < 7:
            return f"hace {diferencia.days} días"
        elif diferencia.days < 30:
            semanas = diferencia.days // 7
            return f"hace {semanas} semana{'s' if semanas != 1 else ''}"
        else:
            return fecha.strftime("%d/%m/%Y")

    elif formato == 'corto':
        return fecha.strftime("%d/%m/%Y")

    elif formato == 'largo':
        return fecha.strftime("%d de %B de %Y")

    elif formato == 'iso':
        return fecha.isoformat()

    else:
        return fecha.strftime(formato)


def calcular_edad(fecha_nacimiento: datetime) -> int:
    """Calcular edad desde fecha de nacimiento"""
    if not fecha_nacimiento:
        return 0

    hoy = datetime.now()
    edad = hoy.year - fecha_nacimiento.year

    # Ajustar si aún no ha pasado el cumpleaños este año
    if (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
        edad -= 1

    return max(0, edad)


def obtener_rango_fechas(periodo: str) -> Tuple[datetime, datetime]:
    """Obtener rango de fechas para un período específico"""
    hoy = datetime.now()

    if periodo == 'hoy':
        inicio = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
        fin = inicio + timedelta(days=1) - timedelta(microseconds=1)

    elif periodo == 'semana':
        # Inicio de la semana (lunes)
        dias_desde_lunes = hoy.weekday()
        inicio = (hoy - timedelta(days=dias_desde_lunes)).replace(hour=0, minute=0, second=0, microsecond=0)
        fin = inicio + timedelta(days=7) - timedelta(microseconds=1)

    elif periodo == 'mes':
        inicio = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if hoy.month == 12:
            fin = datetime(hoy.year + 1, 1, 1) - timedelta(microseconds=1)
        else:
            fin = datetime(hoy.year, hoy.month + 1, 1) - timedelta(microseconds=1)

    elif periodo == 'año':
        inicio = datetime(hoy.year, 1, 1)
        fin = datetime(hoy.year + 1, 1, 1) - timedelta(microseconds=1)

    elif periodo == 'ultimo_7_dias':
        fin = hoy
        inicio = hoy - timedelta(days=7)

    elif periodo == 'ultimo_30_dias':
        fin = hoy
        inicio = hoy - timedelta(days=30)

    else:
        # Por defecto, hoy
        inicio = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
        fin = inicio + timedelta(days=1) - timedelta(microseconds=1)

    return inicio, fin


# === UTILIDADES DE SEGURIDAD ===

def generar_token_seguro(length: int = 32) -> str:
    """Generar token seguro aleatorio"""
    return secrets.token_urlsafe(length)


def generar_hash_archivo(filepath: str) -> str:
    """Generar hash MD5 de un archivo"""
    if not os.path.exists(filepath):
        return ""

    hash_md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"Error generando hash de archivo: {e}")
        return ""


def sanitizar_input_html(texto: str) -> str:
    """Sanitizar input para prevenir XSS básico"""
    if not texto:
        return ""

    # Reemplazar caracteres peligrosos
    texto = texto.replace('<', '&lt;')
    texto = texto.replace('>', '&gt;')
    texto = texto.replace('"', '&quot;')
    texto = texto.replace("'", '&#x27;')
    texto = texto.replace('&', '&amp;')

    return texto


# === UTILIDADES DE NÚMEROS ===

def formatear_numero(numero: Union[int, float], decimales: int = 2) -> str:
    """Formatear número con separadores de miles"""
    if numero is None:
        return "0"

    if isinstance(numero, float):
        return f"{numero:,.{decimales}f}".replace(',', ' ')
    else:
        return f"{numero:,}".replace(',', ' ')


def calcular_porcentaje(parte: Union[int, float], total: Union[int, float]) -> float:
    """Calcular porcentaje con validación de división por cero"""
    if not total or total == 0:
        return 0.0

    return min(100.0, max(0.0, (parte / total) * 100))


def redondear_inteligente(numero: float, precision: int = 2) -> Union[int, float]:
    """Redondear número de forma inteligente (devolver int si es entero)"""
    if numero is None:
        return 0

    redondeado = round(numero, precision)

    # Si el número es efectivamente entero, devolver int
    if redondeado == int(redondeado):
        return int(redondeado)

    return redondeado


# === UTILIDADES DE LISTAS Y DICCIONARIOS ===

def dividir_lista(lista: List[Any], tamaño_chunk: int) -> List[List[Any]]:
    """Dividir lista en chunks de tamaño específico"""
    if not lista or tamaño_chunk <= 0:
        return []

    return [lista[i:i + tamaño_chunk] for i in range(0, len(lista), tamaño_chunk)]


def filtrar_diccionario(diccionario: Dict[str, Any], claves_permitidas: List[str]) -> Dict[str, Any]:
    """Filtrar diccionario manteniendo solo claves permitidas"""
    return {k: v for k, v in diccionario.items() if k in claves_permitidas}


def combinar_diccionarios(*diccionarios: Dict[str, Any]) -> Dict[str, Any]:
    """Combinar múltiples diccionarios (el último tiene prioridad)"""
    resultado = {}
    for diccionario in diccionarios:
        if diccionario:
            resultado.update(diccionario)
    return resultado


def obtener_valor_anidado(diccionario: Dict[str, Any], ruta: str, default: Any = None) -> Any:
    """Obtener valor de diccionario anidado usando notación de puntos"""
    try:
        keys = ruta.split('.')
        current = diccionario

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default

        return current
    except Exception:
        return default


# === UTILIDADES DE LOGGING ===

def log_execution_time(func):
    """Decorador para medir tiempo de ejecución de funciones"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        try:
            result = func(*args, **kwargs)
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.debug(f"⏱️ {func.__name__} ejecutado en {execution_time:.3f} segundos")
            return result
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ {func.__name__} falló después de {execution_time:.3f} segundos: {e}")
            raise

    return wrapper


def log_function_call(func):
    """Decorador para loggear llamadas a funciones"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Preparar argumentos para logging (sin datos sensibles)
        args_str = ', '.join([str(arg)[:50] + '...' if len(str(arg)) > 50 else str(arg) for arg in args[:3]])
        if len(args) > 3:
            args_str += f', ... y {len(args) - 3} más'

        logger.debug(f"🔧 Llamando {func.__name__}({args_str})")

        try:
            result = func(*args, **kwargs)
            logger.debug(f"✅ {func.__name__} completado exitosamente")
            return result
        except Exception as e:
            logger.error(f"❌ {func.__name__} falló: {e}")
            raise

    return wrapper


# === UTILIDADES DE EJERCICIOS ===

def generar_id_ejercicio(tipo: str, nivel: int, timestamp: datetime = None) -> str:
    """Generar ID único para ejercicio"""
    if not timestamp:
        timestamp = datetime.now()

    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
    random_part = secrets.token_hex(4)

    return f"{tipo}_{nivel}_{timestamp_str}_{random_part}"


def calcular_puntos_ejercicio(
        tipo_ejercicio: str,
        nivel: int,
        precision: float,
        tiempo_segundos: int,
        bonus_factors: Dict[str, float] = None
) -> int:
    """Calcular puntos para un ejercicio completado"""

    # Puntos base por tipo de ejercicio
    puntos_base = {
        'lectura': 10,
        'ejercicios': 15,
        'pronunciacion': 20,
        'memoria': 25,
        'ahorcado': 20,
        'trivia': 15,
        'completar_palabra': 12,
        'ordenar_frase': 18
    }

    base = puntos_base.get(tipo_ejercicio, 10)

    # Multiplicador por nivel
    multiplicador_nivel = 1 + (nivel - 1) * 0.2

    # Multiplicador por precisión
    multiplicador_precision = precision / 100.0

    # Bonus por velocidad (si completó rápido)
    bonus_velocidad = 1.0
    if tiempo_segundos < 30:  # Menos de 30 segundos
        bonus_velocidad = 1.2
    elif tiempo_segundos < 60:  # Menos de 1 minuto
        bonus_velocidad = 1.1

    # Aplicar factors de bonus adicionales
    if bonus_factors:
        for factor_name, factor_value in bonus_factors.items():
            if factor_name == 'racha' and factor_value:
                bonus_velocidad *= 1.1
            elif factor_name == 'perfecto' and precision == 100:
                bonus_velocidad *= 1.3

    # Calcular puntos finales
    puntos = int(base * multiplicador_nivel * multiplicador_precision * bonus_velocidad)

    return max(1, puntos)  # Mínimo 1 punto


def evaluar_respuesta_texto(respuesta_usuario: str, respuesta_correcta: str, tolerancia: float = 0.8) -> Dict[str, Any]:
    """Evaluar respuesta de texto del usuario"""
    similitud = calcular_similitud_texto(respuesta_usuario, respuesta_correcta)

    es_correcta = similitud >= tolerancia

    # Generar feedback específico
    if similitud == 1.0:
        feedback = "¡Perfecto! Respuesta exacta."
    elif similitud >= 0.9:
        feedback = "¡Excelente! Muy cerca de la respuesta correcta."
    elif similitud >= 0.7:
        feedback = "Bien, pero hay pequeños errores."
    elif similitud >= 0.5:
        feedback = "La respuesta tiene algunos elementos correctos."
    else:
        feedback = "La respuesta no es correcta. Intenta de nuevo."

    return {
        'correcta': es_correcta,
        'similitud': similitud,
        'feedback': feedback,
        'respuesta_usuario': respuesta_usuario,
        'respuesta_correcta': respuesta_correcta
    }


# === UTILIDADES DE ESTADÍSTICAS ===

def calcular_estadisticas_basicas(valores: List[Union[int, float]]) -> Dict[str, float]:
    """Calcular estadísticas básicas de una lista de valores"""
    if not valores:
        return {
            'count': 0,
            'sum': 0,
            'mean': 0,
            'min': 0,
            'max': 0,
            'median': 0
        }

    valores_ordenados = sorted(valores)
    n = len(valores)

    # Mediana
    if n % 2 == 0:
        median = (valores_ordenados[n // 2 - 1] + valores_ordenados[n // 2]) / 2
    else:
        median = valores_ordenados[n // 2]

    return {
        'count': n,
        'sum': sum(valores),
        'mean': sum(valores) / n,
        'min': min(valores),
        'max': max(valores),
        'median': median
    }


def generar_reporte_progreso(datos_ejercicios: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generar reporte de progreso basado en datos de ejercicios"""
    if not datos_ejercicios:
        return {
            'total_ejercicios': 0,
            'precision_promedio': 0,
            'tiempo_total': 0,
            'tipos_ejercicios': {},
            'progreso_semanal': [],
            'tendencia': 'Sin datos'
        }

    # Estadísticas generales
    total = len(datos_ejercicios)
    precisiones = [e.get('precision_porcentaje', 0) for e in datos_ejercicios]
    tiempos = [e.get('tiempo_empleado_segundos', 0) for e in datos_ejercicios]

    # Ejercicios por tipo
    tipos = {}
    for ejercicio in datos_ejercicios:
        tipo = ejercicio.get('tipo_ejercicio', 'unknown')
        if tipo not in tipos:
            tipos[tipo] = {'count': 0, 'precision_promedio': 0}
        tipos[tipo]['count'] += 1

    # Calcular precisión promedio por tipo
    for tipo in tipos:
        ejercicios_tipo = [e for e in datos_ejercicios if e.get('tipo_ejercicio') == tipo]
        precisiones_tipo = [e.get('precision_porcentaje', 0) for e in ejercicios_tipo]
        tipos[tipo]['precision_promedio'] = sum(precisiones_tipo) / len(precisiones_tipo) if precisiones_tipo else 0

    # Tendencia simple (comparar última semana con anterior)
    ahora = datetime.now()
    ejercicios_semana_pasada = [
        e for e in datos_ejercicios
        if 'fecha_completado' in e and
           (ahora - timedelta(days=7)) <= datetime.fromisoformat(
            str(e['fecha_completado']).replace('Z', '+00:00').replace('+00:00', '')) <= ahora
    ]
    ejercicios_semana_anterior = [
        e for e in datos_ejercicios
        if 'fecha_completado' in e and
           (ahora - timedelta(days=14)) <= datetime.fromisoformat(
            str(e['fecha_completado']).replace('Z', '+00:00').replace('+00:00', '')) <= (ahora - timedelta(days=7))
    ]

    if len(ejercicios_semana_pasada) > len(ejercicios_semana_anterior):
        tendencia = 'Mejorando'
    elif len(ejercicios_semana_pasada) < len(ejercicios_semana_anterior):
        tendencia = 'Disminuyendo'
    else:
        tendencia = 'Estable'

    return {
        'total_ejercicios': total,
        'precision_promedio': sum(precisiones) / len(precisiones) if precisiones else 0,
        'tiempo_total': sum(tiempos),
        'tipos_ejercicios': tipos,
        'tendencia': tendencia,
        'ejercicios_ultima_semana': len(ejercicios_semana_pasada)
    }


# === UTILIDADES DE EXPORT/IMPORT ===

def exportar_datos_json(datos: Any, filepath: str) -> bool:
    """Exportar datos a archivo JSON"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"✅ Datos exportados a {filepath}")
        return True
    except Exception as e:
        logger.error(f"❌ Error exportando datos: {e}")
        return False


def importar_datos_json(filepath: str) -> Optional[Any]:
    """Importar datos desde archivo JSON"""
    try:
        if not os.path.exists(filepath):
            logger.warning(f"⚠️ Archivo no encontrado: {filepath}")
            return None

        with open(filepath, 'r', encoding='utf-8') as f:
            datos = json.load(f)

        logger.info(f"✅ Datos importados desde {filepath}")
        return datos
    except Exception as e:
        logger.error(f"❌ Error importando datos: {e}")
        return None


# === CONSTANTES ÚTILES ===

VOCALES = ['A', 'E', 'I', 'O', 'U']
CONSONANTES = ['B', 'C', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'Ñ', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'X', 'Y',
               'Z']

NIVELES_DIFICULTAD = {
    1: 'Principiante',
    2: 'Básico',
    3: 'Intermedio',
    4: 'Avanzado',
    5: 'Experto'
}

TIPOS_EJERCICIOS = [
    'lectura',
    'ejercicios',
    'pronunciacion',
    'memoria',
    'ahorcado',
    'trivia',
    'completar_palabra',
    'ordenar_frase'
]

MENSAJES_MOTIVACIONALES = [
    "¡Excelente trabajo!",
    "¡Sigue así!",
    "¡Cada día mejoras más!",
    "¡Eres increíble!",
    "¡No te rindas!",
    "¡Vas por buen camino!",
    "¡Tú puedes!",
    "¡Sigue practicando!",
    "¡Lo estás haciendo genial!",
    "¡Cada error es un aprendizaje!"
]


# === FUNCIONES DE TESTING Y DEBUG ===

def ejecutar_pruebas_utilidades():
    """Ejecutar pruebas básicas de las utilidades"""
    print("=== PRUEBAS DE UTILIDADES ALFAIA ===")

    # Probar validaciones
    print(f"Email válido: {validar_email('test@example.com')}")
    print(f"Username válido: {validar_username('usuario123')}")

    # Probar texto
    texto1 = "Hola mundo"
    texto2 = "hola mundo"
    print(f"Similitud texto: {calcular_similitud_texto(texto1, texto2)}")

    # Probar fechas
    fecha = datetime.now() - timedelta(hours=2)
    print(f"Fecha formateada: {formatear_fecha(fecha)}")

    # Probar números
    print(f"Número formateado: {formatear_numero(1234.567)}")
    print(f"Porcentaje: {calcular_porcentaje(75, 100)}%")

    # Probar estadísticas
    valores = [10, 20, 30, 40, 50]
    stats = calcular_estadisticas_basicas(valores)
    print(f"Estadísticas: {stats}")

    print("✅ Pruebas completadas")


if __name__ == "__main__":
    ejecutar_pruebas_utilidades()
