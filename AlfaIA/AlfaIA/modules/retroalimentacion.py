# modules/retroalimentacion.py
import random
from datetime import datetime


class SistemaRetroalimentacion:
    def __init__(self):
        self.mensajes_motivacion = {
            "excelente": [
                "¡Perfecto! 🌟",
                "¡Increíble trabajo! 🎉",
                "¡Eres fantástico! ⭐",
                "¡Sobresaliente! 👏",
                "¡Magnífico! 🏆"
            ],
            "muy_bien": [
                "¡Muy bien! 👍",
                "¡Genial! 😊",
                "¡Estupendo! 🎯",
                "¡Bien hecho! ✨",
                "¡Excelente progreso! 📈"
            ],
            "bien": [
                "¡Buen trabajo! 😊",
                "¡Vas por buen camino! 👍",
                "¡Sigue así! 💪",
                "¡Bien! 🙂",
                "¡No está mal! 👌"
            ],
            "necesita_mejora": [
                "¡Puedes hacerlo mejor! 💪",
                "¡Sigue practicando! 📚",
                "¡No te rindas! 🌈",
                "¡La práctica hace al maestro! 🎯",
                "¡Inténtalo de nuevo! 🔄"
            ],
            "animo": [
                "¡No te preocupes! 😊",
                "¡Todos aprendemos paso a paso! 👣",
                "¡Lo importante es seguir intentando! 🌟",
                "¡Cada error es una oportunidad de aprender! 💡",
                "¡Tú puedes! 💪"
            ]
        }

        self.consejos_por_tipo = {
            "pronunciacion": [
                "Intenta hablar más despacio y articular bien cada sonido",
                "Practica frente a un espejo para ver cómo mueves la boca",
                "Escucha atentamente cómo suenan las palabras",
                "Respira profundo antes de hablar",
                "No tengas miedo de exagerar los movimientos de la boca"
            ],
            "lectura": [
                "Lee en voz alta para practicar la fluidez",
                "Tómate tu tiempo, no hay prisa",
                "Señala con el dedo cada palabra que lees",
                "Si no entiendes una palabra, pregunta su significado",
                "Lee un poco cada día para mejorar"
            ],
            "ejercicios": [
                "Revisa tu respuesta antes de enviarla",
                "Piensa en el significado de las palabras",
                "No tengas miedo de cometer errores",
                "Practica un poco cada día",
                "Pide ayuda cuando la necesites"
            ]
        }

        self.logros_personalizados = {
            "primera_vez": "¡Es tu primera vez haciendo este ejercicio! 🌟",
            "racha_ejercicios": "¡Has completado {count} ejercicios seguidos! 🔥",
            "mejora_precision": "¡Tu precisión ha mejorado {mejora}%! 📈",
            "nuevo_nivel": "¡Has subido al nivel {nivel}! 🏆",
            "perfeccionista": "¡Respuesta perfecta! 💯",
            "persistencia": "¡No te rindes fácilmente! 💪"
        }

    def generar_retroalimentacion(self, precision, tipo_ejercicio, es_primera_vez=False, mejora_anterior=0):
        """Generar retroalimentación basada en el rendimiento"""
        # Determinar nivel de rendimiento
        if precision >= 95:
            nivel = "excelente"
            color = "success"
        elif precision >= 80:
            nivel = "muy_bien"
            color = "success"
        elif precision >= 60:
            nivel = "bien"
            color = "info"
        elif precision >= 40:
            nivel = "necesita_mejora"
            color = "warning"
        else:
            nivel = "animo"
            color = "danger"

        # Mensaje principal
        mensaje_principal = random.choice(self.mensajes_motivacion[nivel])

        # Agregar detalles específicos
        detalles = []

        if precision == 100:
            detalles.append("¡Respuesta perfecta! Sin errores.")
        elif precision >= 80:
            detalles.append(f"Precisión del {precision}%. ¡Muy bien!")
        else:
            detalles.append(f"Precisión del {precision}%. Puedes mejorar.")

        # Agregar consejo específico
        if precision < 80:
            consejo = random.choice(self.consejos_por_tipo.get(tipo_ejercicio, []))
            if consejo:
                detalles.append(f"💡 Consejo: {consejo}")

        # Verificar logros especiales
        logros = []
        if es_primera_vez:
            logros.append(self.logros_personalizados["primera_vez"])

        if precision == 100:
            logros.append(self.logros_personalizados["perfeccionista"])

        if mejora_anterior > 0 and precision > mejora_anterior + 10:
            mejora = precision - mejora_anterior
            logros.append(self.logros_personalizados["mejora_precision"].format(mejora=mejora))

        return {
            "mensaje_principal": mensaje_principal,
            "detalles": detalles,
            "logros": logros,
            "precision": precision,
            "color": color,
            "nivel_rendimiento": nivel
        }

    def generar_retroalimentacion_pronunciacion(self, vocales_detectadas, vocales_esperadas=None):
        """Retroalimentación específica para ejercicios de pronunciación"""
        total_detectadas = len(vocales_detectadas)

        if total_detectadas == 0:
            return {
                "mensaje": "No se detectaron vocales claramente. 🎤",
                "consejos": [
                    "Asegúrate de que el micrófono funcione correctamente",
                    "Habla más cerca del micrófono",
                    "Pronuncia más fuerte y claro",
                    "Reduce el ruido de fondo"
                ],
                "color": "warning"
            }

        # Analizar distribución de vocales
        conteo_vocales = {}
        for vocal in vocales_detectadas:
            if vocal != "Desconocido":
                conteo_vocales[vocal] = conteo_vocales.get(vocal, 0) + 1

        # Generar mensaje basado en variedad de vocales
        vocales_diferentes = len(conteo_vocales)

        if vocales_diferentes >= 4:
            mensaje = "¡Excelente! Detectamos una gran variedad de vocales. 🌟"
            color = "success"
        elif vocales_diferentes >= 2:
            mensaje = "¡Bien! Se detectaron varias vocales diferentes. 👍"
            color = "info"
        else:
            mensaje = "Se detectaron pocas vocales. Intenta variar más tu pronunciación. 🎯"
            color = "warning"

        # Consejos específicos por vocal
        consejos = []
        for vocal, cantidad in conteo_vocales.items():
            if cantidad >= 3:
                consejos.append(f"Excelente pronunciación de la vocal '{vocal}' ({cantidad} veces)")

        # Consejos generales de pronunciación
        if vocales_diferentes < 3:
            consejos.extend([
                "Intenta pronunciar todas las vocales: A, E, I, O, U",
                "Abre bien la boca para las vocales A y O",
                "Sonríe ligeramente para las vocales E e I",
                "Redondea los labios para la vocal U"
            ])

        return {
            "mensaje": mensaje,
            "conteo_vocales": conteo_vocales,
            "total_vocales": total_detectadas,
            "consejos": consejos[:3],  # Máximo 3 consejos
            "color": color
        }

    def generar_reporte_progreso(self, estadisticas_usuario):
        """Generar un reporte de progreso del usuario"""
        ejercicios = estadisticas_usuario.get("ejercicios_completados", 0)
        precision = estadisticas_usuario.get("precision_promedio", 0)
        racha = estadisticas_usuario.get("racha_dias", 0)

        # Mensaje principal basado en el progreso
        if ejercicios >= 50:
            mensaje_main = "¡Eres un estudiante dedicado! 🏆"
        elif ejercicios >= 20:
            mensaje_main = "¡Excelente progreso! 📈"
        elif ejercicios >= 5:
            mensaje_main = "¡Vas por buen camino! 🌟"
        else:
            mensaje_main = "¡Seguimos aprendiendo juntos! 🌱"

        # Generar insights
        insights = []

        if precision >= 90:
            insights.append("Tu precisión es excepcional")
        elif precision >= 70:
            insights.append("Mantienes una buena precisión")
        else:
            insights.append("Hay oportunidad de mejorar la precisión")

        if racha >= 7:
            insights.append(f"¡{racha} días de práctica consecutiva!")
        elif racha >= 3:
            insights.append(f"Llevas {racha} días practicando")
        else:
            insights.append("Intenta practicar más regularmente")

        # Recomendaciones personalizadas
        recomendaciones = []

        if precision < 70:
            recomendaciones.append("Dedica más tiempo a cada ejercicio")
            recomendaciones.append("Revisa tus respuestas antes de enviarlas")

        if racha < 3:
            recomendaciones.append("Intenta practicar un poco cada día")
            recomendaciones.append("Establece recordatorios para practicar")

        if ejercicios < 10:
            recomendaciones.append("Explora diferentes tipos de ejercicios")
            recomendaciones.append("No tengas miedo de cometer errores")

        return {
            "mensaje_principal": mensaje_main,
            "estadisticas": {
                "ejercicios": ejercicios,
                "precision": f"{precision:.1f}%",
                "racha": f"{racha} días"
            },
            "insights": insights,
            "recomendaciones": recomendaciones[:3],  # Máximo 3 recomendaciones
            "fecha": datetime.now().strftime("%d/%m/%Y")
        }

    def calcular_puntos_bonus(self, precision, tiempo_respuesta=None, es_racha=False):
        """Calcular puntos bonus basados en rendimiento"""
        puntos_base = 10
        bonus = 0

        # Bonus por precisión
        if precision == 100:
            bonus += 10  # Perfecto
        elif precision >= 90:
            bonus += 5  # Excelente
        elif precision >= 80:
            bonus += 3  # Muy bien

        # Bonus por velocidad (si se proporciona tiempo de respuesta)
        if tiempo_respuesta and tiempo_respuesta < 30:  # Menos de 30 segundos
            bonus += 2

        # Bonus por racha
        if es_racha:
            bonus += 5

        return puntos_base + bonus