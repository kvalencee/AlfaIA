# modules/juegos_interactivos.py
import random
import json
from datetime import datetime


class JuegosInteractivos:
    def __init__(self):
        self.cargar_contenido_juegos()

    def cargar_contenido_juegos(self):
        """Cargar contenido para todos los juegos"""

        # Palabras para el juego de memoria (pares español-español: sinónimos)
        self.palabras_memoria = [
            ("Grande", "Enorme"), ("Pequeño", "Chico"), ("Bonito", "Hermoso"), ("Rápido", "Veloz"),
            ("Feliz", "Alegre"), ("Triste", "Melancólico"), ("Fuerte", "Robusto"), ("Débil", "Frágil"),
            ("Caliente", "Cálido"), ("Frío", "Helado"), ("Nuevo", "Moderno"), ("Viejo", "Antiguo"),
            ("Alto", "Elevado"), ("Bajo", "Pequeño"), ("Ancho", "Amplio"), ("Estrecho", "Angosto"),
            ("Claro", "Brillante"), ("Oscuro", "Tenebroso"), ("Dulce", "Sabroso"), ("Amargo", "Ácido"),
            ("Limpio", "Aseado"), ("Sucio", "Manchado"), ("Fácil", "Sencillo"), ("Difícil", "Complicado"),
            ("Rico", "Adinerado"), ("Pobre", "Humilde"), ("Gordo", "Rechoncho"), ("Flaco", "Delgado"),
            ("Lento", "Pausado"), ("Inteligente", "Listo"), ("Tonto", "Ingenuo"), ("Valiente", "Audaz"),
            ("Cobarde", "Miedoso"), ("Generoso", "Dadivoso"), ("Tacaño", "Avaro"), ("Trabajador", "Laborioso")
        ]

        # Palabras para ahorcado por dificultad
        self.palabras_ahorcado = {
            1: [
                {"palabra": "GATO", "pista": "Animal doméstico que dice miau"},
                {"palabra": "CASA", "pista": "Lugar donde vives"},
                {"palabra": "SOL", "pista": "Estrella que nos da luz"},
                {"palabra": "MAR", "pista": "Agua salada muy grande"},
                {"palabra": "PAN", "pista": "Alimento hecho con harina"},
                {"palabra": "LUZ", "pista": "Lo contrario de oscuridad"},
                {"palabra": "PAZ", "pista": "Lo contrario de guerra"},
                {"palabra": "OSO", "pista": "Animal grande y peludo"},
                {"palabra": "PEZ", "pista": "Animal que vive en el agua"},
                {"palabra": "REY", "pista": "Gobernante de un reino"}
            ],
            2: [
                {"palabra": "ESCUELA", "pista": "Lugar donde los niños aprenden"},
                {"palabra": "FAMILIA", "pista": "Papá, mamá e hijos"},
                {"palabra": "JARDIN", "pista": "Lugar con plantas y flores"},
                {"palabra": "MUSICA", "pista": "Arte de los sonidos"},
                {"palabra": "VENTANA", "pista": "Abertura en la pared para ver afuera"},
                {"palabra": "COCINA", "pista": "Lugar donde se prepara la comida"},
                {"palabra": "PAISAJE", "pista": "Vista de un lugar natural"},
                {"palabra": "MASCOTA", "pista": "Animal de compañía"},
                {"palabra": "AMISTAD", "pista": "Relación entre amigos"},
                {"palabra": "TRABAJO", "pista": "Actividad para ganar dinero"}
            ],
            3: [
                {"palabra": "UNIVERSIDAD", "pista": "Institución de educación superior"},
                {"palabra": "BIBLIOTECA", "pista": "Lugar lleno de libros"},
                {"palabra": "COMPUTADORA", "pista": "Máquina para procesar información"},
                {"palabra": "TELEFONO", "pista": "Dispositivo para comunicarse a distancia"},
                {"palabra": "REFRIGERADOR", "pista": "Electrodoméstico que enfría alimentos"},
                {"palabra": "ARQUITECTURA", "pista": "Arte de diseñar edificios"},
                {"palabra": "FOTOGRAFIA", "pista": "Arte de capturar imágenes"},
                {"palabra": "DEMOCRACIA", "pista": "Sistema de gobierno del pueblo"},
                {"palabra": "TECNOLOGIA", "pista": "Aplicación de conocimientos científicos"},
                {"palabra": "MATEMATICAS", "pista": "Ciencia de los números"}
            ]
        }

        # Preguntas de trivia por categorías
        self.preguntas_trivia = {
            "gramática": [
                {
                    "pregunta": "¿Cuál es el plural de 'lápiz'?",
                    "opciones": ["lápizs", "lápices", "lápizes", "lapices"],
                    "respuesta": 1,
                    "explicacion": "El plural de 'lápiz' es 'lápices', siguiendo la regla de palabras agudas terminadas en 'z'"
                },
                {
                    "pregunta": "¿Qué tipo de palabra es 'rápidamente'?",
                    "opciones": ["sustantivo", "adjetivo", "adverbio", "verbo"],
                    "respuesta": 2,
                    "explicacion": "'Rápidamente' es un adverbio de modo, indica cómo se realiza la acción"
                },
                {
                    "pregunta": "¿Cuál es el femenino de 'actor'?",
                    "opciones": ["actora", "actriz", "actresa", "actriz femenina"],
                    "respuesta": 1,
                    "explicacion": "El femenino de 'actor' es 'actriz', que es una forma irregular"
                },
                {
                    "pregunta": "¿Qué tiempo verbal es 'habíamos comido'?",
                    "opciones": ["presente", "pretérito perfecto", "pluscuamperfecto", "futuro"],
                    "respuesta": 2,
                    "explicacion": "'Habíamos comido' es pretérito pluscuamperfecto, indica una acción anterior a otra en el pasado"
                },
                {
                    "pregunta": "¿Cuál es el superlativo de 'bueno'?",
                    "opciones": ["muy bueno", "buenísimo", "más bueno", "óptimo"],
                    "respuesta": 3,
                    "explicacion": "'Óptimo' es el superlativo culto de 'bueno', aunque 'buenísimo' también es correcto"
                }
            ],
            "vocabulario": [
                {
                    "pregunta": "¿Qué significa 'ubérrimo'?",
                    "opciones": ["muy grande", "muy pequeño", "muy fértil", "muy seco"],
                    "respuesta": 2,
                    "explicacion": "'Ubérrimo' significa muy fértil, abundante o productivo"
                },
                {
                    "pregunta": "¿Cuál es un sinónimo de 'diáfano'?",
                    "opciones": ["opaco", "transparente", "colorido", "rugoso"],
                    "respuesta": 1,
                    "explicacion": "'Diáfano' significa transparente, claro o que se ve a través de él"
                },
                {
                    "pregunta": "¿Qué es un 'quelonio'?",
                    "opciones": ["un pez", "un ave", "una tortuga", "un insecto"],
                    "respuesta": 2,
                    "explicacion": "Un quelonio es cualquier reptil del orden de las tortugas"
                },
                {
                    "pregunta": "¿Qué significa 'perspicaz'?",
                    "opciones": ["confuso", "astuto", "lento", "obvio"],
                    "respuesta": 1,
                    "explicacion": "'Perspicaz' significa que tiene agudeza mental, astuto o sagaz"
                },
                {
                    "pregunta": "¿Cuál es el antónimo de 'efímero'?",
                    "opciones": ["permanente", "rápido", "pequeño", "visible"],
                    "respuesta": 0,
                    "explicacion": "'Efímero' significa que dura poco tiempo, su antónimo es 'permanente'"
                }
            ],
            "cultura": [
                {
                    "pregunta": "¿Quién escribió 'Don Quijote de la Mancha'?",
                    "opciones": ["Lope de Vega", "Miguel de Cervantes", "Federico García Lorca", "Pablo Neruda"],
                    "respuesta": 1,
                    "explicacion": "Miguel de Cervantes Saavedra escribió 'Don Quijote de la Mancha', considerada la primera novela moderna"
                },
                {
                    "pregunta": "¿En qué país está Machu Picchu?",
                    "opciones": ["Colombia", "Ecuador", "Perú", "Bolivia"],
                    "respuesta": 2,
                    "explicacion": "Machu Picchu está en Perú, es una antigua ciudad inca en los Andes"
                },
                {
                    "pregunta": "¿Cuál es la capital de Argentina?",
                    "opciones": ["Montevideo", "Buenos Aires", "Santiago", "Bogotá"],
                    "respuesta": 1,
                    "explicacion": "Buenos Aires es la capital y ciudad más poblada de Argentina"
                },
                {
                    "pregunta": "¿Qué pintor español pintó 'Guernica'?",
                    "opciones": ["Salvador Dalí", "Pablo Picasso", "Joan Miró", "Francisco Goya"],
                    "respuesta": 1,
                    "explicacion": "Pablo Picasso pintó 'Guernica' en 1937, obra maestra del arte moderno"
                },
                {
                    "pregunta": "¿Cuál es el río más largo de España?",
                    "opciones": ["Guadalquivir", "Ebro", "Tajo", "Duero"],
                    "respuesta": 2,
                    "explicacion": "El río Tajo es el más largo de España con 1007 km de longitud"
                }
            ],
            "historia": [
                {
                    "pregunta": "¿En qué año llegó Cristóbal Colón a América?",
                    "opciones": ["1490", "1491", "1492", "1493"],
                    "respuesta": 2,
                    "explicacion": "Cristóbal Colón llegó a América el 12 de octubre de 1492"
                },
                {
                    "pregunta": "¿Qué imperio conquistó Francisco Pizarro?",
                    "opciones": ["Azteca", "Maya", "Inca", "Olmeca"],
                    "respuesta": 2,
                    "explicacion": "Francisco Pizarro conquistó el Imperio Inca en el siglo XVI"
                },
                {
                    "pregunta": "¿Cuándo terminó la Guerra Civil Española?",
                    "opciones": ["1937", "1938", "1939", "1940"],
                    "respuesta": 2,
                    "explicacion": "La Guerra Civil Española terminó en 1939 con la victoria del bando nacional"
                }
            ]
        }

        # Crucigramas predefinidos
        self.crucigramas = [
            {
                "titulo": "Animales",
                "tamaño": 7,
                "palabras": [
                    {"palabra": "GATO", "pista": "Animal que dice miau", "fila": 0, "columna": 0,
                     "direccion": "horizontal"},
                    {"palabra": "TORO", "pista": "Animal de granja con cuernos", "fila": 1, "columna": 2,
                     "direccion": "vertical"},
                    {"palabra": "OSO", "pista": "Animal grande del bosque", "fila": 2, "columna": 1,
                     "direccion": "horizontal"},
                    {"palabra": "PEZ", "pista": "Animal que vive en el agua", "fila": 4, "columna": 3,
                     "direccion": "horizontal"},
                    {"palabra": "AVE", "pista": "Animal que vuela", "fila": 1, "columna": 5, "direccion": "vertical"}
                ]
            },
            {
                "titulo": "La Casa",
                "tamaño": 8,
                "palabras": [
                    {"palabra": "COCINA", "pista": "Lugar donde se cocina", "fila": 0, "columna": 0,
                     "direccion": "horizontal"},
                    {"palabra": "CAMA", "pista": "Donde duermes", "fila": 1, "columna": 2, "direccion": "vertical"},
                    {"palabra": "MESA", "pista": "Mueble para comer", "fila": 2, "columna": 0,
                     "direccion": "horizontal"},
                    {"palabra": "SOFA", "pista": "Mueble para sentarse", "fila": 4, "columna": 1,
                     "direccion": "horizontal"},
                    {"palabra": "PUERTA", "pista": "Se abre y se cierra", "fila": 1, "columna": 6,
                     "direccion": "vertical"}
                ]
            },
            {
                "titulo": "Colores",
                "tamaño": 6,
                "palabras": [
                    {"palabra": "ROJO", "pista": "Color del fuego", "fila": 0, "columna": 0, "direccion": "horizontal"},
                    {"palabra": "AZUL", "pista": "Color del cielo", "fila": 1, "columna": 1, "direccion": "horizontal"},
                    {"palabra": "VERDE", "pista": "Color de las plantas", "fila": 2, "columna": 0,
                     "direccion": "horizontal"},
                    {"palabra": "AMARILLO", "pista": "Color del sol", "fila": 0, "columna": 3, "direccion": "vertical"}
                ]
            },
            {
                "titulo": "Comida",
                "tamaño": 9,
                "palabras": [
                    {"palabra": "PIZZA", "pista": "Comida italiana redonda", "fila": 0, "columna": 0,
                     "direccion": "horizontal"},
                    {"palabra": "PASTA", "pista": "Comida italiana de trigo", "fila": 1, "columna": 2,
                     "direccion": "horizontal"},
                    {"palabra": "ARROZ", "pista": "Cereal muy común", "fila": 2, "columna": 1,
                     "direccion": "horizontal"},
                    {"palabra": "POLLO", "pista": "Carne de ave", "fila": 3, "columna": 3, "direccion": "horizontal"},
                    {"palabra": "PESCADO", "pista": "Comida del mar", "fila": 1, "columna": 5, "direccion": "vertical"}
                ]
            }
        ]

    def generar_juego_memoria(self, nivel=1):
        """Generar un juego de memoria basado en el nivel"""
        if nivel == 1:
            num_pares = 6
        elif nivel == 2:
            num_pares = 8
        elif nivel == 3:
            num_pares = 10
        else:
            num_pares = 12

        # Seleccionar pares aleatorios
        pares_seleccionados = random.sample(self.palabras_memoria, num_pares)

        # Crear lista de cartas
        cartas = []
        for i, (español, ingles) in enumerate(pares_seleccionados):
            cartas.append({"id": i * 2, "texto": español, "par": i, "mostrada": False, "encontrada": False})
            cartas.append({"id": i * 2 + 1, "texto": ingles, "par": i, "mostrada": False, "encontrada": False})

        # Mezclar las cartas
        random.shuffle(cartas)

        return {
            "cartas": cartas,
            "nivel": nivel,
            "puntos": num_pares * 10,
            "tiempo_limite": 60 + (num_pares * 5)
        }

    def generar_ahorcado(self, nivel=1):
        """Generar un juego de ahorcado"""
        nivel = max(1, min(nivel, 3))
        palabras_nivel = self.palabras_ahorcado[nivel]
        palabra_elegida = random.choice(palabras_nivel)

        return {
            "palabra": palabra_elegida["palabra"],
            "pista": palabra_elegida["pista"],
            "letras_adivinadas": [],
            "letras_incorrectas": [],
            "intentos_restantes": 6,
            "nivel": nivel,
            "puntos": len(palabra_elegida["palabra"]) * 5
        }

    def generar_trivia(self, categoria=None, nivel=1):
        """Generar una pregunta de trivia"""
        if categoria is None or categoria not in self.preguntas_trivia:
            categoria = random.choice(list(self.preguntas_trivia.keys()))

        preguntas = self.preguntas_trivia[categoria]
        pregunta = random.choice(preguntas)

        return {
            "pregunta": pregunta["pregunta"],
            "opciones": pregunta["opciones"],
            "respuesta_correcta": pregunta["respuesta"],
            "explicacion": pregunta["explicacion"],
            "categoria": categoria,
            "nivel": nivel,
            "puntos": 20 + (nivel * 5)
        }

    def generar_crucigrama(self, nivel=1):
        """Generar un crucigrama"""
        crucigrama = random.choice(self.crucigramas)

        # Crear grid vacío
        tamaño = crucigrama["tamaño"]
        grid = [["" for _ in range(tamaño)] for _ in range(tamaño)]

        # Colocar palabras en el grid
        for palabra_data in crucigrama["palabras"]:
            palabra = palabra_data["palabra"]
            fila = palabra_data["fila"]
            columna = palabra_data["columna"]
            direccion = palabra_data["direccion"]

            if direccion == "horizontal":
                for i, letra in enumerate(palabra):
                    if columna + i < tamaño:
                        grid[fila][columna + i] = letra
            else:  # vertical
                for i, letra in enumerate(palabra):
                    if fila + i < tamaño:
                        grid[fila + i][columna] = letra

        return {
            "titulo": crucigrama["titulo"],
            "grid": grid,
            "palabras": crucigrama["palabras"],
            "tamaño": tamaño,
            "nivel": nivel,
            "puntos": len(crucigrama["palabras"]) * 15
        }

    def verificar_respuesta_trivia(self, respuesta_usuario, respuesta_correcta):
        """Verificar respuesta de trivia"""
        return respuesta_usuario == respuesta_correcta

    def actualizar_ahorcado(self, juego_data, letra):
        """Actualizar estado del juego de ahorcado"""
        letra = letra.upper()
        palabra = juego_data["palabra"]

        if letra in juego_data["letras_adivinadas"] or letra in juego_data["letras_incorrectas"]:
            return {"ya_usada": True}

        if letra in palabra:
            juego_data["letras_adivinadas"].append(letra)

            # Verificar si la palabra está completa
            palabra_completa = all(letra in juego_data["letras_adivinadas"] for letra in palabra)

            return {
                "correcto": True,
                "palabra_completa": palabra_completa,
                "juego_terminado": palabra_completa
            }
        else:
            juego_data["letras_incorrectas"].append(letra)
            juego_data["intentos_restantes"] -= 1

            return {
                "correcto": False,
                "palabra_completa": False,
                "juego_terminado": juego_data["intentos_restantes"] <= 0
            }

    def generar_palabra_con_espacios(self, palabra, letras_adivinadas):
        """Generar palabra con espacios para letras no adivinadas"""
        return " ".join([letra if letra in letras_adivinadas else "_" for letra in palabra])

    def calcular_puntos_juego(self, tipo_juego, nivel, precision=100, tiempo_usado=0, tiempo_limite=60):
        """Calcular puntos basados en el tipo de juego y rendimiento"""
        puntos_base = {
            "memoria": 50,
            "ahorcado": 40,
            "trivia": 30,
            "crucigrama": 60
        }

        base = puntos_base.get(tipo_juego, 30)

        # Multiplicador por nivel
        multiplicador_nivel = 1 + (nivel - 1) * 0.5

        # Bonus por precisión
        bonus_precision = (precision / 100) * 0.5

        # Bonus por velocidad (solo si hay tiempo límite)
        bonus_velocidad = 0
        if tiempo_limite > 0 and tiempo_usado < tiempo_limite:
            porcentaje_tiempo = tiempo_usado / tiempo_limite
            if porcentaje_tiempo < 0.5:  # Completado en menos de la mitad del tiempo
                bonus_velocidad = 0.3
            elif porcentaje_tiempo < 0.75:  # Completado en menos de 3/4 del tiempo
                bonus_velocidad = 0.15

        # Calcular puntos finales
        puntos_finales = int(base * multiplicador_nivel * (1 + bonus_precision + bonus_velocidad))

        return puntos_finales

    def obtener_categorias_trivia(self):
        """Obtener lista de categorías disponibles para trivia"""
        return list(self.preguntas_trivia.keys())

    def obtener_estadisticas_juego(self, tipo_juego):
        """Obtener estadísticas generales de un tipo de juego"""
        if tipo_juego == "memoria":
            return {
                "total_pares": len(self.palabras_memoria),
                "niveles_disponibles": 4,
                "tiempo_promedio": "2-5 minutos"
            }
        elif tipo_juego == "ahorcado":
            total_palabras = sum(len(palabras) for palabras in self.palabras_ahorcado.values())
            return {
                "total_palabras": total_palabras,
                "niveles_disponibles": 3,
                "dificultad": "Fácil a Difícil"
            }
        elif tipo_juego == "trivia":
            total_preguntas = sum(len(preguntas) for preguntas in self.preguntas_trivia.values())
            return {
                "total_preguntas": total_preguntas,
                "categorias": len(self.preguntas_trivia),
                "temas": list(self.preguntas_trivia.keys())
            }
        elif tipo_juego == "crucigrama":
            return {
                "total_crucigramas": len(self.crucigramas),
                "temas_disponibles": [c["titulo"] for c in self.crucigramas],
                "dificultad": "Intermedio"
            }
        else:
            return {"error": "Tipo de juego no reconocido"}

    def generar_reporte_juego(self, tipo_juego, resultados_sesion):
        """Generar reporte de rendimiento en una sesión de juego"""
        if not resultados_sesion:
            return {"error": "No hay resultados para reportar"}

        total_juegos = len(resultados_sesion)
        puntos_totales = sum(r.get("puntos", 0) for r in resultados_sesion)
        precision_promedio = sum(r.get("precision", 0) for r in resultados_sesion) / total_juegos
        tiempo_total = sum(r.get("tiempo", 0) for r in resultados_sesion)

        return {
            "tipo_juego": tipo_juego,
            "juegos_completados": total_juegos,
            "puntos_totales": puntos_totales,
            "precision_promedio": round(precision_promedio, 1),
            "tiempo_total_minutos": round(tiempo_total / 60, 1),
            "puntos_por_juego": round(puntos_totales / total_juegos, 1),
            "mejor_resultado": max(resultados_sesion, key=lambda x: x.get("puntos", 0)),
            "recomendaciones": self._generar_recomendaciones(tipo_juego, precision_promedio, puntos_totales)
        }

    def _generar_recomendaciones(self, tipo_juego, precision, puntos):
        """Generar recomendaciones personalizadas basadas en el rendimiento"""
        recomendaciones = []

        if precision < 70:
            recomendaciones.append(f"Enfócate en mejorar la precisión en {tipo_juego}")
            recomendaciones.append("Tómate más tiempo para pensar las respuestas")

        if puntos < 100:
            recomendaciones.append("Intenta completar los ejercicios más rápido para obtener bonus")

        if tipo_juego == "memoria":
            recomendaciones.append("Practica técnicas de memorización para mejorar")
        elif tipo_juego == "ahorcado":
            recomendaciones.append("Familiarízate con palabras comunes en español")
        elif tipo_juego == "trivia":
            recomendaciones.append("Lee más sobre cultura e historia española")
        elif tipo_juego == "crucigrama":
            recomendaciones.append("Amplía tu vocabulario con sinónimos y definiciones")

        return recomendaciones[:3]  # Máximo 3 recomendaciones