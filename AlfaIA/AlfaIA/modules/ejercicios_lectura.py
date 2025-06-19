# modules/ejercicios_lectura.py
import random
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class PreguntaLectura:
    """Clase para representar una pregunta de comprensión lectora"""
    pregunta: str
    opciones: List[str]
    respuesta_correcta: int  # índice de la respuesta correcta
    tipo: str  # 'literal', 'inferencial', 'critica'
    puntos: int


@dataclass
class TextoLectura:
    """Clase para representar un texto de lectura"""
    titulo: str
    contenido: str
    nivel: int
    categoria: str
    palabras_clave: List[str]
    tiempo_estimado: int  # en segundos
    preguntas: List[PreguntaLectura]


class EjerciciosLectura:
    """
    Módulo completo de ejercicios de lectura con diferentes niveles y tipos de comprensión
    """

    def __init__(self):
        self.textos_por_nivel = self._cargar_textos()
        self.tipos_pregunta = ['literal', 'inferencial', 'critica', 'vocabulario']

    def _cargar_textos(self) -> Dict[int, List[TextoLectura]]:
        """Cargar textos de lectura organizados por nivel"""
        return {
            1: self._textos_nivel_1(),
            2: self._textos_nivel_2(),
            3: self._textos_nivel_3(),
            4: self._textos_nivel_4(),
            5: self._textos_nivel_5()
        }

    def _textos_nivel_1(self) -> List[TextoLectura]:
        """Textos básicos para principiantes"""
        textos = []

        # Texto 1: La familia
        preguntas_familia = [
            PreguntaLectura(
                "¿Cuántas personas viven en la casa?",
                ["Tres", "Cuatro", "Cinco", "Seis"],
                1,  # Cuatro
                "literal",
                10
            ),
            PreguntaLectura(
                "¿Qué hace mamá en la cocina?",
                ["Come", "Cocina", "Limpia", "Duerme"],
                1,  # Cocina
                "literal",
                10
            ),
            PreguntaLectura(
                "¿Cómo se siente la familia?",
                ["Triste", "Enojada", "Feliz", "Cansada"],
                2,  # Feliz
                "inferencial",
                15
            )
        ]

        textos.append(TextoLectura(
            titulo="Mi Familia",
            contenido="""En mi casa viven cuatro personas: papá, mamá, mi hermana y yo. 
            Papá trabaja en una oficina. Mamá cocina muy rico en la cocina. 
            Mi hermana juega conmigo todos los días. Somos una familia muy feliz.""",
            nivel=1,
            categoria="familia",
            palabras_clave=["familia", "casa", "papá", "mamá", "hermana"],
            tiempo_estimado=60,
            preguntas=preguntas_familia
        ))

        # Texto 2: El parque
        preguntas_parque = [
            PreguntaLectura(
                "¿Dónde juegan los niños?",
                ["En casa", "En la escuela", "En el parque", "En la calle"],
                2,  # En el parque
                "literal",
                10
            ),
            PreguntaLectura(
                "¿Qué hacen en los columpios?",
                ["Corren", "Se mecen", "Comen", "Estudian"],
                1,  # Se mecen
                "literal",
                10
            ),
            PreguntaLectura(
                "¿Por qué les gusta el parque?",
                ["Es grande", "Es divertido", "Está cerca", "Es nuevo"],
                1,  # Es divertido
                "inferencial",
                15
            )
        ]

        textos.append(TextoLectura(
            titulo="El Parque Divertido",
            contenido="""El parque es un lugar muy divertido. Los niños corren en el pasto verde. 
            Algunos se mecen en los columpios. Otros juegan en el tobogán. 
            Todos los niños ríen y se divierten mucho en el parque.""",
            nivel=1,
            categoria="recreacion",
            palabras_clave=["parque", "niños", "columpios", "tobogán", "divertido"],
            tiempo_estimado=60,
            preguntas=preguntas_parque
        ))

        # Texto 3: Los animales
        preguntas_animales = [
            PreguntaLectura(
                "¿Qué animal dice 'miau'?",
                ["El perro", "El gato", "El pájaro", "El pez"],
                1,  # El gato
                "literal",
                10
            ),
            PreguntaLectura(
                "¿Dónde vive el pez?",
                ["En el cielo", "En el agua", "En un árbol", "En una casa"],
                1,  # En el agua
                "literal",
                10
            ),
            PreguntaLectura(
                "¿Cuál es el tema principal del texto?",
                ["La comida", "Los colores", "Los animales", "Los juegos"],
                2,  # Los animales
                "inferencial",
                15
            )
        ]

        textos.append(TextoLectura(
            titulo="Animales Amigos",
            contenido="""Los animales son muy diferentes. El gato dice 'miau' y le gusta dormir. 
            El perro dice 'guau' y mueve la cola cuando está contento. 
            El pájaro canta bonito y vuela en el cielo. El pez nada en el agua todo el día.""",
            nivel=1,
            categoria="animales",
            palabras_clave=["animales", "gato", "perro", "pájaro", "pez"],
            tiempo_estimado=60,
            preguntas=preguntas_animales
        ))

        return textos

    def _textos_nivel_2(self) -> List[TextoLectura]:
        """Textos básicos con mayor complejidad"""
        textos = []

        # Texto 1: La escuela
        preguntas_escuela = [
            PreguntaLectura(
                "¿A qué hora empieza la escuela?",
                ["A las 7:00", "A las 8:00", "A las 9:00", "A las 10:00"],
                1,  # A las 8:00
                "literal",
                12
            ),
            PreguntaLectura(
                "¿Cuál es la materia favorita de María?",
                ["Matemáticas", "Historia", "Ciencias", "Arte"],
                0,  # Matemáticas
                "literal",
                12
            ),
            PreguntaLectura(
                "¿Por qué a María le gusta tanto la escuela?",
                ["Porque es fácil", "Porque aprende cosas nuevas", "Porque está cerca", "Porque tiene amigos"],
                1,  # Porque aprende cosas nuevas
                "inferencial",
                18
            ),
            PreguntaLectura(
                "¿Qué significa 'conocimiento' en el texto?",
                ["Amigos", "Libros", "Lo que se aprende", "Juegos"],
                2,  # Lo que se aprende
                "vocabulario",
                20
            )
        ]

        textos.append(TextoLectura(
            titulo="Un Día en la Escuela",
            contenido="""María va a la escuela todos los días. La escuela empieza a las 8:00 de la mañana. 
            Su materia favorita es matemáticas porque le gusta resolver problemas. 
            También tiene clases de historia, ciencias y arte. En el recreo juega con sus amigas. 
            María piensa que la escuela es importante porque aprende cosas nuevas cada día. 
            El conocimiento la ayuda a entender mejor el mundo.""",
            nivel=2,
            categoria="educacion",
            palabras_clave=["escuela", "matemáticas", "conocimiento", "aprender", "materias"],
            tiempo_estimado=90,
            preguntas=preguntas_escuela
        ))

        # Texto 2: Las estaciones
        preguntas_estaciones = [
            PreguntaLectura(
                "¿En qué estación florecen las plantas?",
                ["Invierno", "Primavera", "Verano", "Otoño"],
                1,  # Primavera
                "literal",
                12
            ),
            PreguntaLectura(
                "¿Qué pasa con las hojas en otoño?",
                ["Crecen", "Se vuelven verdes", "Cambian de color", "Desaparecen"],
                2,  # Cambian de color
                "literal",
                12
            ),
            PreguntaLectura(
                "¿Por qué cada estación es especial?",
                ["Porque duran poco", "Porque tienen características únicas", "Porque llueve", "Porque hace calor"],
                1,  # Porque tienen características únicas
                "inferencial",
                18
            )
        ]

        textos.append(TextoLectura(
            titulo="Las Cuatro Estaciones",
            contenido="""Durante el año hay cuatro estaciones diferentes. En primavera, las plantas florecen 
            y todo se vuelve verde. El verano es caluroso y perfecto para ir a la playa. 
            En otoño, las hojas de los árboles cambian de color y caen al suelo. 
            El invierno es frío y a veces nieva. Cada estación tiene su propia belleza y características especiales.""",
            nivel=2,
            categoria="naturaleza",
            palabras_clave=["estaciones", "primavera", "verano", "otoño", "invierno"],
            tiempo_estimado=90,
            preguntas=preguntas_estaciones
        ))

        return textos

    def _textos_nivel_3(self) -> List[TextoLectura]:
        """Textos intermedios con mayor complejidad narrativa"""
        textos = []

        # Texto 1: La amistad
        preguntas_amistad = [
            PreguntaLectura(
                "¿Cómo se conocieron Ana y Luis?",
                ["En la escuela", "En el parque", "En una biblioteca", "En casa de un amigo"],
                2,  # En una biblioteca
                "literal",
                15
            ),
            PreguntaLectura(
                "¿Qué les gusta hacer juntos principalmente?",
                ["Jugar deportes", "Ver televisión", "Leer y estudiar", "Escuchar música"],
                2,  # Leer y estudiar
                "literal",
                15
            ),
            PreguntaLectura(
                "¿Qué cualidad valoran más en su amistad?",
                ["La diversión", "La confianza", "Los juegos", "Los regalos"],
                1,  # La confianza
                "inferencial",
                20
            ),
            PreguntaLectura(
                "¿Cuál es el mensaje principal del texto?",
                ["Los amigos deben ser iguales", "La amistad verdadera supera las diferencias",
                 "Solo los niños pueden ser amigos", "Es mejor tener muchos amigos"],
                1,  # La amistad verdadera supera las diferencias
                "critica",
                25
            )
        ]

        textos.append(TextoLectura(
            titulo="Una Amistad Especial",
            contenido="""Ana y Luis se conocieron en la biblioteca del barrio. Aunque Ana era muy estudiosa 
            y Luis más aventurero, pronto descubrieron que compartían el amor por los libros de aventuras. 
            Cada tarde se reunían para leer juntos y contarse historias increíbles. 
            A pesar de sus diferencias, su amistad se hizo muy fuerte porque se respetaban mutuamente. 
            Ana aprendió a ser más espontánea con Luis, y él aprendió a valorar los estudios. 
            Su amistad les enseñó que las diferencias pueden enriquecer una relación cuando hay confianza y respeto.""",
            nivel=3,
            categoria="valores",
            palabras_clave=["amistad", "respeto", "diferencias", "confianza", "bibliotca"],
            tiempo_estimado=120,
            preguntas=preguntas_amistad
        ))

        return textos

    def _textos_nivel_4(self) -> List[TextoLectura]:
        """Textos avanzados con temas más complejos"""
        textos = []

        # Texto 1: La tecnología y la comunicación
        preguntas_tecnologia = [
            PreguntaLectura(
                "Según el texto, ¿cuál fue el primer medio de comunicación a distancia?",
                ["El teléfono", "El telégrafo", "La radio", "Internet"],
                1,  # El telégrafo
                "literal",
                18
            ),
            PreguntaLectura(
                "¿Qué ventaja principal menciona el texto sobre la comunicación digital?",
                ["Es más barata", "Es instantánea", "Es más segura", "Es más divertida"],
                1,  # Es instantánea
                "literal",
                18
            ),
            PreguntaLectura(
                "¿Qué preocupación expresa el autor sobre las redes sociales?",
                ["Son muy caras", "Pueden reducir la comunicación cara a cara", "Son difíciles de usar",
                 "No son seguras"],
                1,  # Pueden reducir la comunicación cara a cara
                "inferencial",
                22
            ),
            PreguntaLectura(
                "¿Cuál es la posición del autor sobre el uso equilibrado de la tecnología?",
                ["Está en contra", "Está a favor", "Es neutral", "No se puede determinar"],
                1,  # Está a favor
                "critica",
                28
            )
        ]

        textos.append(TextoLectura(
            titulo="La Evolución de la Comunicación",
            contenido="""La comunicación humana ha evolucionado dramáticamente en las últimas décadas. 
            Desde el telégrafo hasta las redes sociales, cada avance tecnológico ha transformado 
            la forma en que nos relacionamos. Hoy podemos comunicarnos instantáneamente con personas 
            al otro lado del mundo a través de mensajes, videollamadas y plataformas digitales.

            Sin embargo, esta revolución digital también presenta desafíos. Algunos expertos 
            advierten que la comunicación virtual puede reducir nuestra capacidad para mantener 
            conversaciones cara a cara significativas. La clave está en encontrar un equilibrio 
            que nos permita aprovechar las ventajas de la tecnología sin perder la riqueza 
            de la interacción humana directa.""",
            nivel=4,
            categoria="tecnologia",
            palabras_clave=["comunicación", "tecnología", "digital", "evolución", "equilibrio"],
            tiempo_estimado=150,
            preguntas=preguntas_tecnologia
        ))

        return textos

    def _textos_nivel_5(self) -> List[TextoLectura]:
        """Textos expertos con análisis crítico complejo"""
        textos = []

        # Texto 1: El cambio climático
        preguntas_clima = [
            PreguntaLectura(
                "¿Cuál es la principal causa del cambio climático según el texto?",
                ["Las erupciones volcánicas", "Las emisiones de gases de efecto invernadero", "Los cambios naturales",
                 "La deforestación"],
                1,  # Las emisiones de gases de efecto invernadero
                "literal",
                20
            ),
            PreguntaLectura(
                "¿Qué evidencia científica se menciona del calentamiento global?",
                ["Aumento de terremotos", "Derretimiento de glaciares", "Más volcanes activos", "Cambios en la luna"],
                1,  # Derretimiento de glaciares
                "literal",
                20
            ),
            PreguntaLectura(
                "¿Por qué el autor considera urgente actuar ahora?",
                ["Porque es barato", "Porque los efectos pueden ser irreversibles", "Porque lo dice la ley",
                 "Porque está de moda"],
                1,  # Porque los efectos pueden ser irreversibles
                "inferencial",
                25
            ),
            PreguntaLectura(
                "¿Cuál es el tono del autor hacia este tema?",
                ["Indiferente", "Optimista", "Preocupado pero esperanzado", "Pesimista"],
                2,  # Preocupado pero esperanzado
                "critica",
                30
            ),
            PreguntaLectura(
                "¿Qué implica la frase 'responsabilidad compartida'?",
                ["Solo los gobiernos deben actuar", "Todos tenemos un papel que desempeñar",
                 "Solo los científicos pueden ayudar", "No podemos hacer nada"],
                1,  # Todos tenemos un papel que desempeñar
                "vocabulario",
                25
            )
        ]

        textos.append(TextoLectura(
            titulo="El Desafío del Cambio Climático",
            contenido="""El cambio climático representa uno de los desafíos más complejos de nuestro tiempo. 
            Las evidencias científicas son contundentes: las emisiones de gases de efecto invernadero 
            generadas por actividades humanas han elevado las temperaturas globales de manera sin precedentes. 

            Los efectos son visibles en el derretimiento acelerado de glaciares, el aumento del nivel del mar, 
            y la intensificación de eventos climáticos extremos. Estas transformaciones no solo afectan 
            los ecosistemas naturales, sino que también amenaza la seguridad alimentaria, la salud pública 
            y la estabilidad económica de millones de personas.

            Sin embargo, aún existe esperanza si actuamos con determinación. La transición hacia energías 
            renovables, la implementación de políticas ambientales efectivas, y los cambios en nuestros 
            hábitos de consumo pueden marcar la diferencia. Este es un desafío que requiere una respuesta 
            coordinada y una responsabilidad compartida entre gobiernos, empresas y ciudadanos.""",
            nivel=5,
            categoria="ciencia",
            palabras_clave=["cambio climático", "emisiones", "sostenibilidad", "responsabilidad", "evidencias"],
            tiempo_estimado=200,
            preguntas=preguntas_clima
        ))

        return textos

    def generar_ejercicio_lectura(self, nivel: int = 1, categoria: str = None) -> Dict[str, Any]:
        """
        Generar un ejercicio completo de lectura

        Args:
            nivel: Nivel de dificultad (1-5)
            categoria: Categoría específica (opcional)

        Returns:
            Dict con el ejercicio completo
        """
        nivel = max(1, min(nivel, 5))  # Asegurar nivel válido

        # Filtrar textos por nivel y categoría si se especifica
        textos_disponibles = self.textos_por_nivel.get(nivel, [])

        if categoria:
            textos_disponibles = [t for t in textos_disponibles if t.categoria == categoria]

        if not textos_disponibles:
            # Fallback al nivel 1 si no hay textos disponibles
            textos_disponibles = self.textos_por_nivel[1]

        # Seleccionar texto aleatorio
        texto_seleccionado = random.choice(textos_disponibles)

        # Seleccionar preguntas (todas o una muestra aleatoria)
        num_preguntas = min(len(texto_seleccionado.preguntas), 5)  # Máximo 5 preguntas
        preguntas_seleccionadas = random.sample(texto_seleccionado.preguntas, num_preguntas)

        # Calcular puntos totales
        puntos_totales = sum(p.puntos for p in preguntas_seleccionadas)

        return {
            "id": f"lectura_{nivel}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "tipo_ejercicio": "lectura",
            "nivel": nivel,
            "texto": {
                "titulo": texto_seleccionado.titulo,
                "contenido": texto_seleccionado.contenido,
                "palabras_clave": texto_seleccionado.palabras_clave,
                "tiempo_estimado": texto_seleccionado.tiempo_estimado,
                "categoria": texto_seleccionado.categoria
            },
            "preguntas": [
                {
                    "id": i,
                    "pregunta": p.pregunta,
                    "opciones": p.opciones,
                    "respuesta_correcta": p.respuesta_correcta,
                    "tipo": p.tipo,
                    "puntos": p.puntos
                }
                for i, p in enumerate(preguntas_seleccionadas)
            ],
            "puntos_totales": puntos_totales,
            "instrucciones": self._generar_instrucciones(nivel),
            "tiempo_limite": texto_seleccionado.tiempo_estimado + (num_preguntas * 30),  # 30 seg por pregunta
            "fecha_creacion": datetime.now().isoformat()
        }

    def _generar_instrucciones(self, nivel: int) -> str:
        """Generar instrucciones específicas por nivel"""
        instrucciones = {
            1: "Lee el texto con atención y responde las preguntas. Tómate tu tiempo.",
            2: "Lee cuidadosamente el texto y responde las preguntas sobre lo que leíste.",
            3: "Analiza el texto y responde las preguntas. Algunas requieren inferencia.",
            4: "Lee críticamente el texto y responde. Analiza tanto lo literal como lo implícito.",
            5: "Realiza una lectura crítica profunda. Evalúa argumentos, evidencias y perspectivas."
        }
        return instrucciones.get(nivel, instrucciones[1])

    def evaluar_respuestas(self, ejercicio: Dict[str, Any], respuestas_usuario: List[int]) -> Dict[str, Any]:
        """
        Evaluar las respuestas del usuario

        Args:
            ejercicio: Ejercicio original
            respuestas_usuario: Lista de índices de respuestas seleccionadas

        Returns:
            Dict con resultados de evaluación
        """
        preguntas = ejercicio["preguntas"]
        total_preguntas = len(preguntas)
        respuestas_correctas = 0
        puntos_obtenidos = 0
        detalles_respuestas = []

        for i, respuesta_usuario in enumerate(respuestas_usuario):
            if i < len(preguntas):
                pregunta = preguntas[i]
                es_correcta = respuesta_usuario == pregunta["respuesta_correcta"]

                if es_correcta:
                    respuestas_correctas += 1
                    puntos_obtenidos += pregunta["puntos"]

                detalles_respuestas.append({
                    "pregunta_id": i,
                    "pregunta": pregunta["pregunta"],
                    "respuesta_usuario": respuesta_usuario,
                    "respuesta_correcta": pregunta["respuesta_correcta"],
                    "opciones": pregunta["opciones"],
                    "es_correcta": es_correcta,
                    "tipo_pregunta": pregunta["tipo"],
                    "puntos": pregunta["puntos"] if es_correcta else 0,
                    "explicacion": self._generar_explicacion(pregunta, es_correcta)
                })

        precision = (respuestas_correctas / total_preguntas) * 100 if total_preguntas > 0 else 0

        return {
            "precision_porcentaje": round(precision, 2),
            "respuestas_correctas": respuestas_correctas,
            "total_preguntas": total_preguntas,
            "puntos_obtenidos": puntos_obtenidos,
            "puntos_totales": ejercicio["puntos_totales"],
            "detalles_respuestas": detalles_respuestas,
            "nivel_ejercicio": ejercicio["nivel"],
            "feedback_general": self._generar_feedback_general(precision, ejercicio["nivel"]),
            "recomendaciones": self._generar_recomendaciones(precision, detalles_respuestas),
            "fecha_evaluacion": datetime.now().isoformat()
        }

    def _generar_explicacion(self, pregunta: Dict[str, Any], es_correcta: bool) -> str:
        """Generar explicación para la respuesta"""
        if es_correcta:
            explicaciones = [
                "¡Correcto! Has entendido bien el texto.",
                "¡Excelente! Tu comprensión es muy buena.",
                "¡Perfecto! Has identificado la respuesta correcta."
            ]
        else:
            explicaciones = [
                f"La respuesta correcta es: {pregunta['opciones'][pregunta['respuesta_correcta']]}",
                "Revisa el texto nuevamente para encontrar la información correcta.",
                "Esta pregunta requiere leer con más atención los detalles del texto."
            ]

        return random.choice(explicaciones)

    def _generar_feedback_general(self, precision: float, nivel: int) -> str:
        """Generar feedback general basado en la precisión"""
        if precision >= 90:
            return f"¡Excelente comprensión lectora! Dominas muy bien el nivel {nivel}."
        elif precision >= 75:
            return f"¡Muy bien! Tu comprensión del nivel {nivel} es buena."
        elif precision >= 60:
            return f"Comprensión aceptable del nivel {nivel}. Sigue practicando."
        elif precision >= 40:
            return f"Necesitas mejorar tu comprensión del nivel {nivel}. Te recomiendo leer más despacio."
        else:
            return f"Es importante que practiques más la lectura comprensiva del nivel {nivel}."

    def _generar_recomendaciones(self, precision: float, detalles_respuestas: List[Dict]) -> List[str]:
        """Generar recomendaciones personalizadas"""
        recomendaciones = []

        # Analizar tipos de preguntas falladas
        tipos_fallados = [d["tipo_pregunta"] for d in detalles_respuestas if not d["es_correcta"]]

        if "literal" in tipos_fallados:
            recomendaciones.append("Practica identificar información explícita en el texto")

        if "inferencial" in tipos_fallados:
            recomendaciones.append("Trabaja en hacer conexiones e inferencias a partir del texto")

        if "critica" in tipos_fallados:
            recomendaciones.append("Desarrolla tu capacidad de análisis crítico y evaluación")

        if "vocabulario" in tipos_fallados:
            recomendaciones.append("Amplía tu vocabulario y contexto de palabras")

        if precision < 60:
            recomendaciones.append("Lee el texto completo antes de responder las preguntas")
            recomendaciones.append("Tómate más tiempo para comprender cada párrafo")

        if not recomendaciones:
            recomendaciones.append("¡Continúa con tu excelente trabajo de comprensión!")

        return recomendaciones

    def obtener_estadisticas_nivel(self, nivel: int) -> Dict[str, Any]:
        """Obtener estadísticas de un nivel específico"""
        textos = self.textos_por_nivel.get(nivel, [])

        if not textos:
            return {"error": "Nivel no disponible"}

        total_textos = len(textos)
        categorias = list(set(t.categoria for t in textos))
        total_preguntas = sum(len(t.preguntas) for t in textos)
        tiempo_total = sum(t.tiempo_estimado for t in textos)

        return {
            "nivel": nivel,
            "total_textos": total_textos,
            "categorias_disponibles": categorias,
            "total_preguntas": total_preguntas,
            "tiempo_estimado_total": tiempo_total,
            "promedio_preguntas_por_texto": total_preguntas / total_textos if total_textos > 0 else 0
        }

    def generar_ejercicio_personalizado(self, historial_usuario: List[Dict], nivel_actual: int) -> Dict[str, Any]:
        """
        Generar ejercicio personalizado basado en el historial del usuario

        Args:
            historial_usuario: Lista de ejercicios anteriores del usuario
            nivel_actual: Nivel actual del usuario

        Returns:
            Dict con ejercicio personalizado
        """
        # Analizar fortalezas y debilidades
        tipos_dificultad = self._analizar_tipos_dificultad(historial_usuario)
        categorias_debiles = self._identificar_categorias_debiles(historial_usuario)

        # Determinar nivel apropiado
        nivel_recomendado = self._calcular_nivel_recomendado(historial_usuario, nivel_actual)

        # Seleccionar categoría que necesita refuerzo
        categoria_objetivo = categorias_debiles[0] if categorias_debiles else None

        # Generar ejercicio dirigido
        ejercicio = self.generar_ejercicio_lectura(nivel_recomendado, categoria_objetivo)

        # Agregar información de personalización
        ejercicio["personalizacion"] = {
            "tipos_reforzar": tipos_dificultad,
            "categoria_objetivo": categoria_objetivo,
            "nivel_recomendado": nivel_recomendado,
            "razon_seleccion": self._explicar_seleccion(tipos_dificultad, categoria_objetivo)
        }

        return ejercicio

    def _analizar_tipos_dificultad(self, historial: List[Dict]) -> List[str]:
        """Analizar qué tipos de preguntas causan más dificultad"""
        tipos_fallados = {}

        for ejercicio in historial:
            if "detalles_respuestas" in ejercicio:
                for respuesta in ejercicio["detalles_respuestas"]:
                    if not respuesta.get("es_correcta", True):
                        tipo = respuesta.get("tipo_pregunta", "literal")
                        tipos_fallados[tipo] = tipos_fallados.get(tipo, 0) + 1

        # Ordenar por frecuencia de error
        return sorted(tipos_fallados.keys(), key=lambda x: tipos_fallados[x], reverse=True)

    def _identificar_categorias_debiles(self, historial: List[Dict]) -> List[str]:
        """Identificar categorías que necesitan refuerzo"""
        precision_por_categoria = {}

        for ejercicio in historial:
            categoria = ejercicio.get("texto", {}).get("categoria", "general")
            precision = ejercicio.get("precision_porcentaje", 0)

            if categoria not in precision_por_categoria:
                precision_por_categoria[categoria] = []
            precision_por_categoria[categoria].append(precision)

        # Calcular promedio por categoría y identificar las más débiles
        promedios = {}
        for cat, precisiones in precision_por_categoria.items():
            promedios[cat] = sum(precisiones) / len(precisiones)

        # Retornar categorías con precisión menor a 70%
        return [cat for cat, prom in promedios.items() if prom < 70.0]

    def _calcular_nivel_recomendado(self, historial: List[Dict], nivel_actual: int) -> int:
        """Calcular nivel recomendado basado en rendimiento"""
        if not historial:
            return nivel_actual

        # Obtener precisiones recientes (últimos 5 ejercicios)
        precisiones_recientes = [
            ej.get("precision_porcentaje", 0)
            for ej in historial[-5:]
            if ej.get("nivel_ejercicio") == nivel_actual
        ]

        if not precisiones_recientes:
            return nivel_actual

        promedio_reciente = sum(precisiones_recientes) / len(precisiones_recientes)

        # Lógica de recomendación
        if promedio_reciente >= 85 and len(precisiones_recientes) >= 3:
            return min(nivel_actual + 1, 5)  # Subir nivel
        elif promedio_reciente < 60:
            return max(nivel_actual - 1, 1)  # Bajar nivel
        else:
            return nivel_actual  # Mantener nivel

    def _explicar_seleccion(self, tipos_dificultad: List[str], categoria_objetivo: str) -> str:
        """Explicar por qué se seleccionó este ejercicio"""
        explicaciones = []

        if tipos_dificultad:
            tipo_principal = tipos_dificultad[0]
            explicaciones.append(f"Incluye preguntas {tipo_principal} para reforzar esta habilidad")

        if categoria_objetivo:
            explicaciones.append(f"Enfoque en {categoria_objetivo} para mejorar comprensión en esta área")

        if not explicaciones:
            explicaciones.append("Ejercicio variado para mantener todas las habilidades")

        return ". ".join(explicaciones)

    def generar_reporte_progreso_lectura(self, historial_usuario: List[Dict]) -> Dict[str, Any]:
        """
        Generar reporte detallado del progreso en lectura

        Args:
            historial_usuario: Historial completo de ejercicios de lectura

        Returns:
            Dict con reporte completo de progreso
        """
        if not historial_usuario:
            return {"error": "No hay historial disponible"}

        # Estadísticas generales
        total_ejercicios = len(historial_usuario)
        precision_promedio = sum(ej.get("precision_porcentaje", 0) for ej in historial_usuario) / total_ejercicios

        # Progreso por nivel
        progreso_niveles = {}
        for ejercicio in historial_usuario:
            nivel = ejercicio.get("nivel_ejercicio", 1)
            if nivel not in progreso_niveles:
                progreso_niveles[nivel] = []
            progreso_niveles[nivel].append(ejercicio.get("precision_porcentaje", 0))

        # Progreso por tipo de pregunta
        progreso_tipos = {}
        for ejercicio in historial_usuario:
            for respuesta in ejercicio.get("detalles_respuestas", []):
                tipo = respuesta.get("tipo_pregunta", "literal")
                if tipo not in progreso_tipos:
                    progreso_tipos[tipo] = {"correctas": 0, "total": 0}

                progreso_tipos[tipo]["total"] += 1
                if respuesta.get("es_correcta", False):
                    progreso_tipos[tipo]["correctas"] += 1

        # Progreso por categoría
        progreso_categorias = {}
        for ejercicio in historial_usuario:
            categoria = ejercicio.get("texto", {}).get("categoria", "general")
            if categoria not in progreso_categorias:
                progreso_categorias[categoria] = []
            progreso_categorias[categoria].append(ejercicio.get("precision_porcentaje", 0))

        # Análisis de tendencias (últimos 10 ejercicios)
        ejercicios_recientes = historial_usuario[-10:] if len(historial_usuario) >= 10 else historial_usuario
        precision_reciente = sum(ej.get("precision_porcentaje", 0) for ej in ejercicios_recientes) / len(
            ejercicios_recientes)

        # Determinar tendencia
        if len(historial_usuario) >= 10:
            precision_anterior = sum(ej.get("precision_porcentaje", 0) for ej in historial_usuario[-20:-10]) / 10
            if precision_reciente > precision_anterior + 5:
                tendencia = "mejorando"
            elif precision_reciente < precision_anterior - 5:
                tendencia = "empeorando"
            else:
                tendencia = "estable"
        else:
            tendencia = "insuficientes_datos"

        # Identificar fortalezas y áreas de mejora
        precision_por_tipo = {
            tipo: (datos["correctas"] / datos["total"]) * 100
            for tipo, datos in progreso_tipos.items()
        }

        fortalezas = [tipo for tipo, prec in precision_por_tipo.items() if prec >= 80]
        areas_mejora = [tipo for tipo, prec in precision_por_tipo.items() if prec < 60]

        # Recomendaciones personalizadas
        recomendaciones = self._generar_recomendaciones_progreso(
            precision_promedio, tendencia, areas_mejora, progreso_niveles
        )

        return {
            "resumen_general": {
                "total_ejercicios": total_ejercicios,
                "precision_promedio": round(precision_promedio, 2),
                "precision_reciente": round(precision_reciente, 2),
                "tendencia": tendencia
            },
            "progreso_por_nivel": {
                nivel: {
                    "ejercicios_completados": len(precisiones),
                    "precision_promedio": round(sum(precisiones) / len(precisiones), 2),
                    "mejor_resultado": max(precisiones),
                    "ultimo_resultado": precisiones[-1] if precisiones else 0
                }
                for nivel, precisiones in progreso_niveles.items()
            },
            "progreso_por_tipo": {
                tipo: {
                    "precision_porcentaje": round(precision, 2),
                    "total_preguntas": datos["total"],
                    "respuestas_correctas": datos["correctas"]
                }
                for tipo, datos in progreso_tipos.items()
                for precision in [precision_por_tipo[tipo]]
            },
            "progreso_por_categoria": {
                categoria: {
                    "ejercicios_completados": len(precisiones),
                    "precision_promedio": round(sum(precisiones) / len(precisiones), 2)
                }
                for categoria, precisiones in progreso_categorias.items()
            },
            "analisis_habilidades": {
                "fortalezas": fortalezas,
                "areas_de_mejora": areas_mejora,
                "tipo_dominante": max(precision_por_tipo.keys(),
                                      key=lambda x: precision_por_tipo[x]) if precision_por_tipo else None
            },
            "recomendaciones": recomendaciones,
            "fecha_reporte": datetime.now().isoformat()
        }

    def _generar_recomendaciones_progreso(self, precision_promedio: float, tendencia: str,
                                          areas_mejora: List[str], progreso_niveles: Dict) -> List[str]:
        """Generar recomendaciones basadas en el análisis de progreso"""
        recomendaciones = []

        # Recomendaciones basadas en precisión general
        if precision_promedio < 60:
            recomendaciones.append("Considera practicar con textos más cortos y simples")
            recomendaciones.append("Dedica más tiempo a leer cada párrafo antes de las preguntas")
        elif precision_promedio < 75:
            recomendaciones.append("Mantén un ritmo constante de práctica")
            recomendaciones.append("Enfócate en las áreas específicas que necesitan mejora")
        else:
            recomendaciones.append("¡Excelente progreso! Considera intentar nivel superior")

        # Recomendaciones basadas en tendencia
        if tendencia == "empeorando":
            recomendaciones.append("Tómate descansos regulares para evitar fatiga mental")
            recomendaciones.append("Revisa las estrategias de lectura que usabas antes")
        elif tendencia == "mejorando":
            recomendaciones.append("¡Sigue con el buen trabajo! Tu esfuerzo está dando frutos")

        # Recomendaciones específicas por área de mejora
        if "literal" in areas_mejora:
            recomendaciones.append("Practica identificar información específica en los textos")
        if "inferencial" in areas_mejora:
            recomendaciones.append("Trabaja en conectar ideas implícitas del texto")
        if "critica" in areas_mejora:
            recomendaciones.append("Desarrolla tu pensamiento crítico leyendo textos argumentativos")
        if "vocabulario" in areas_mejora:
            recomendaciones.append("Amplía tu vocabulario con lecturas variadas")

        # Recomendaciones de nivel
        niveles_completados = list(progreso_niveles.keys())
        if niveles_completados:
            nivel_maximo = max(niveles_completados)
            if nivel_maximo < 5 and precision_promedio >= 80:
                recomendaciones.append(f"Está listo para intentar textos de nivel {nivel_maximo + 1}")

        return recomendaciones[:5]  # Máximo 5 recomendaciones

    def obtener_ejercicios_por_categoria(self, categoria: str) -> List[Dict[str, Any]]:
        """Obtener todos los ejercicios disponibles de una categoría específica"""
        ejercicios_categoria = []

        for nivel, textos in self.textos_por_nivel.items():
            for texto in textos:
                if texto.categoria == categoria:
                    ejercicios_categoria.append({
                        "nivel": nivel,
                        "titulo": texto.titulo,
                        "categoria": texto.categoria,
                        "tiempo_estimado": texto.tiempo_estimado,
                        "num_preguntas": len(texto.preguntas),
                        "palabras_clave": texto.palabras_clave
                    })

        return ejercicios_categoria

    def obtener_categorias_disponibles(self) -> Dict[str, List[int]]:
        """Obtener todas las categorías disponibles y en qué niveles"""
        categorias = {}

        for nivel, textos in self.textos_por_nivel.items():
            for texto in textos:
                if texto.categoria not in categorias:
                    categorias[texto.categoria] = []
                if nivel not in categorias[texto.categoria]:
                    categorias[texto.categoria].append(nivel)

        # Ordenar niveles
        for categoria in categorias:
            categorias[categoria].sort()

        return categorias