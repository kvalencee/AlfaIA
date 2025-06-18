# modules/generador_ejercicios.py
import random
import json
import os


class GeneradorEjercicios:
    def __init__(self):
        self.cargar_contenido()

    def cargar_contenido(self):
        """Cargar contenido para ejercicios desde archivos o definido aquí"""
        # Base de datos de palabras por dificultad
        self.palabras_por_nivel = {
            1: ["casa", "niño", "gato", "sol", "mar", "luz", "paz"],
            2: ["escuela", "jardín", "ventana", "música", "familia"],
            3: ["navegación", "comprensión", "extraordinario", "refrigerador"],
            4: ["extraordinariamente", "incomprensiblemente", "anticonstitucional"]
        }

        # Patrones de palabras incompletas
        self.patrones_palabras = [
            ("c_sa", "casa"),
            ("n_ño", "niño"),
            ("g_to", "gato"),
            ("s_l", "sol"),
            ("m_r", "mar"),
            ("l_z", "luz"),
            ("p_z", "paz"),
            ("esc_ela", "escuela"),
            ("jard_n", "jardín"),
            ("vent_na", "ventana"),
            ("mús_ca", "música"),
            ("fam_lia", "familia"),
            ("naveg_ción", "navegación"),
            ("compr_nsión", "comprensión"),
            ("extr_ordinario", "extraordinario"),
            ("refrig_rador", "refrigerador")
        ]

        # Frases por nivel de dificultad
        self.frases_por_nivel = {
            1: [
                "El gato come pescado",
                "La niña juega sola",
                "El sol brilla hoy",
                "Mamá cocina rico",
                "Papá lee el libro"
            ],
            2: [
                "Los niños juegan en el parque",
                "Mi familia va a la playa",
                "El profesor enseña matemáticas",
                "La música suena muy bonita",
                "Vamos a visitar a los abuelos"
            ],
            3: [
                "La investigación científica requiere mucha paciencia",
                "El desarrollo tecnológico avanza rápidamente",
                "Los estudiantes universitarios estudian constantemente",
                "La comunicación efectiva es fundamental en cualquier relación"
            ]
        }

        # Trabalenguas por dificultad
        self.trabalenguas = {
            1: [
                "Tres tristes tigres",
                "Pepe Pecas pica papas",
                "Paco poco paga"
            ],
            2: [
                "Tres tristes tigres tragaban trigo en un trigal",
                "Pepe Pecas pica papas con un pico",
                "El perro de San Roque no tiene rabo"
            ],
            3: [
                "Parangaricutirimícuaro se va a desparangaricutirimicuarizar",
                "Tres tristes tigres tragaban trigo en un trigal en tres tristes trastos",
                "Cuando cuentes cuentos cuenta cuantos cuentos cuentas"
            ]
        }

        # Ejercicios de pronunciación específicos
        self.ejercicios_pronunciacion = {
            "vocales": [
                {"texto": "A E I O U", "tipo": "vocales_secuencia"},
                {"texto": "aeiou aeiou aeiou", "tipo": "vocales_repeticion"},
                {"texto": "la le li lo lu", "tipo": "vocales_consonante"}
            ],
            "consonantes": [
                {"texto": "pa pe pi po pu", "tipo": "consonante_p"},
                {"texto": "ma me mi mo mu", "tipo": "consonante_m"},
                {"texto": "ta te ti to tu", "tipo": "consonante_t"},
                {"texto": "ra re ri ro ru", "tipo": "consonante_r"},
                {"texto": "sa se si so su", "tipo": "consonante_s"}
            ],
            "silabas": [
                {"texto": "ca co cu que qui", "tipo": "silabas_c"},
                {"texto": "ga go gu gue gui", "tipo": "silabas_g"},
                {"texto": "ña ñe ñi ño ñu", "tipo": "silabas_ñ"}
            ]
        }

    def generar_ordena_frase(self, nivel=1):
        """Generar ejercicio de ordenar frases"""
        nivel = max(1, min(nivel, 3))  # Asegurar nivel válido
        frases = self.frases_por_nivel[nivel]
        frase_elegida = random.choice(frases)

        palabras = frase_elegida.split()
        palabras_desordenadas = palabras.copy()
        random.shuffle(palabras_desordenadas)

        # Asegurar que esté realmente desordenada
        intentos = 0
        while palabras_desordenadas == palabras and intentos < 10:
            random.shuffle(palabras_desordenadas)
            intentos += 1

        return {
            "frase_correcta": frase_elegida,
            "palabras_desordenadas": palabras_desordenadas,
            "nivel": nivel,
            "puntos": nivel * 10
        }

    def generar_completa_palabra(self, nivel=1):
        """Generar ejercicio de completar palabras"""
        nivel = max(1, min(nivel, 4))  # Asegurar nivel válido

        # Filtrar patrones por nivel
        patrones_nivel = []
        for incompleta, completa in self.patrones_palabras:
            if len(completa) <= 4 + nivel:  # Ajustar dificultad por longitud
                patrones_nivel.append((incompleta, completa))

        if not patrones_nivel:
            patrones_nivel = self.patrones_palabras[:5]  # Fallback

        incompleta, completa = random.choice(patrones_nivel)

        return {
            "palabra_incompleta": incompleta,
            "palabra_completa": completa,
            "nivel": nivel,
            "puntos": len(completa) * 2,
            "pista": self.generar_pista(completa)
        }

    def generar_pista(self, palabra):
        """Generar una pista para la palabra"""
        pistas = {
            "casa": "Lugar donde vives",
            "niño": "Persona pequeña",
            "gato": "Animal que dice miau",
            "sol": "Estrella que nos da luz",
            "escuela": "Lugar donde aprendes",
            "jardín": "Lugar con plantas y flores",
            "música": "Arte de los sonidos",
            "familia": "Papá, mamá e hijos"
        }
        return pistas.get(palabra, f"Palabra de {len(palabra)} letras")

    def generar_ejercicio_pronunciacion(self, tipo="vocales", nivel=1):
        """Generar ejercicio de pronunciación"""
        if tipo not in self.ejercicios_pronunciacion:
            tipo = "vocales"

        ejercicios = self.ejercicios_pronunciacion[tipo]
        ejercicio = random.choice(ejercicios)

        return {
            "texto": ejercicio["texto"],
            "tipo": ejercicio["tipo"],
            "categoria": tipo,
            "nivel": nivel,
            "puntos": 15,
            "instrucciones": self.generar_instrucciones_pronunciacion(tipo)
        }

    def generar_instrucciones_pronunciacion(self, tipo):
        """Generar instrucciones específicas para cada tipo de ejercicio"""
        instrucciones = {
            "vocales": "Pronuncia claramente cada vocal. Abre bien la boca.",
            "consonantes": "Articula bien cada consonante con su vocal correspondiente.",
            "silabas": "Pronuncia cada sílaba de forma separada y clara."
        }
        return instrucciones.get(tipo, "Pronuncia el texto claramente.")

    def generar_trabalenguas(self, nivel=1):
        """Generar ejercicio de trabalenguas"""
        nivel = max(1, min(nivel, 3))
        trabalenguas = self.trabalenguas[nivel]
        elegido = random.choice(trabalenguas)

        return {
            "texto": elegido,
            "nivel": nivel,
            "puntos": nivel * 20,
            "instrucciones": "Repite el trabalenguas lo más rápido que puedas sin equivocarte"
        }

    def generar_lectura_guiada(self, nivel=1, tema="general"):
        """Generar texto para lectura guiada"""
        textos_por_tema = {
            "general": [
                "La lectura es una aventura maravillosa que nos transporta a mundos fantásticos.",
                "Cada libro que leemos nos enseña algo nuevo y nos hace crecer como personas.",
                "Los cuentos de hadas han encantado a niños y adultos durante generaciones enteras."
            ],
            "ciencia": [
                "Los científicos estudian el universo para entender mejor nuestro mundo.",
                "La tecnología avanza cada día y cambia nuestra forma de vivir.",
                "Los experimentos nos ayudan a descubrir nuevos conocimientos."
            ],
            "aventura": [
                "Los exploradores viajan a lugares desconocidos en busca de aventuras.",
                "En el océano profundo viven criaturas misteriosas y fascinantes.",
                "Las montañas altas son un desafío para los escaladores más valientes."
            ]
        }

        if tema not in textos_por_tema:
            tema = "general"

        texto = random.choice(textos_por_tema[tema])

        # Ajustar velocidad según nivel
        velocidades = {1: 800, 2: 500, 3: 300, 4: 200}
        velocidad = velocidades.get(nivel, 500)

        return {
            "texto": texto,
            "velocidad_ms": velocidad,
            "nivel": nivel,
            "tema": tema,
            "puntos": len(texto.split()) // 2
        }

    def obtener_estadisticas_ejercicio(self, respuesta_usuario, respuesta_correcta):
        """Calcular estadísticas de precisión del ejercicio"""
        if not respuesta_usuario or not respuesta_correcta:
            return {"precision": 0, "errores": [], "aciertos": []}

        palabras_usuario = respuesta_usuario.lower().strip().split()
        palabras_correctas = respuesta_correcta.lower().strip().split()

        # Comparar palabra por palabra
        errores = []
        aciertos = []

        max_len = max(len(palabras_usuario), len(palabras_correctas))
        coincidencias = 0

        for i in range(max_len):
            palabra_usuario = palabras_usuario[i] if i < len(palabras_usuario) else ""
            palabra_correcta = palabras_correctas[i] if i < len(palabras_correctas) else ""

            if palabra_usuario == palabra_correcta:
                coincidencias += 1
                aciertos.append(palabra_correcta)
            else:
                errores.append({
                    "posicion": i,
                    "esperada": palabra_correcta,
                    "recibida": palabra_usuario
                })

        precision = (coincidencias / max_len) * 100 if max_len > 0 else 0

        return {
            "precision": round(precision, 1),
            "errores": errores,
            "aciertos": aciertos,
            "palabras_totales": max_len,
            "palabras_correctas": coincidencias
        }
