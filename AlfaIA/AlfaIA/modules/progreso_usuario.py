# modules/progreso_usuario.py
import json
import os
from datetime import datetime, timedelta


class ProgresoUsuario:
    def __init__(self, archivo_progreso="data/progreso.json"):
        self.archivo_progreso = archivo_progreso
        self.crear_directorio_si_no_existe()
        self.progreso = self.cargar_progreso()

    def crear_directorio_si_no_existe(self):
        """Crear directorio data si no existe"""
        os.makedirs(os.path.dirname(self.archivo_progreso), exist_ok=True)

    def cargar_progreso(self):
        """Cargar progreso desde archivo JSON"""
        try:
            if os.path.exists(self.archivo_progreso):
                with open(self.archivo_progreso, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return self.progreso_inicial()
        except Exception as e:
            print(f"Error al cargar progreso: {e}")
            return self.progreso_inicial()

    def progreso_inicial(self):
        """Estructura inicial del progreso"""
        return {
            "estadisticas": {
                "ejercicios_completados": 0,
                "tiempo_total_minutos": 0,
                "vocales_detectadas": {"A": 0, "E": 0, "I": 0, "O": 0, "U": 0},
                "precision_promedio": 0.0,
                "racha_dias": 0,
                "ultimo_acceso": None
            },
            "niveles": {
                "lectura": {"nivel": 1, "puntos": 0, "desbloqueado": True},
                "ejercicios": {"nivel": 1, "puntos": 0, "desbloqueado": True},
                "pronunciacion": {"nivel": 1, "puntos": 0, "desbloqueado": False}
            },
            "logros": [],
            "historial": []
        }

    def guardar_progreso(self):
        """Guardar progreso en archivo JSON"""
        try:
            with open(self.archivo_progreso, 'w', encoding='utf-8') as f:
                json.dump(self.progreso, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error al guardar progreso: {e}")
            return False

    def registrar_ejercicio_completado(self, tipo_ejercicio, puntos=10, precision=100):
        """Registrar un ejercicio completado"""
        self.progreso["estadisticas"]["ejercicios_completados"] += 1
        self.progreso["niveles"][tipo_ejercicio]["puntos"] += puntos

        # Actualizar precisión promedio
        stats = self.progreso["estadisticas"]
        if stats["precision_promedio"] == 0:
            stats["precision_promedio"] = precision
        else:
            total_ejercicios = stats["ejercicios_completados"]
            stats["precision_promedio"] = (
                    (stats["precision_promedio"] * (total_ejercicios - 1) + precision) / total_ejercicios
            )

        # Verificar nivel
        self.verificar_subida_nivel(tipo_ejercicio)

        # Registrar en historial
        self.progreso["historial"].append({
            "fecha": datetime.now().isoformat(),
            "tipo": tipo_ejercicio,
            "puntos": puntos,
            "precision": precision
        })

        # Actualizar racha
        self.actualizar_racha()

        # Verificar logros
        self.verificar_logros()

        self.guardar_progreso()

    def registrar_vocales_detectadas(self, vocales):
        """Registrar vocales detectadas en la pronunciación"""
        for vocal in vocales:
            if vocal in self.progreso["estadisticas"]["vocales_detectadas"]:
                self.progreso["estadisticas"]["vocales_detectadas"][vocal] += 1
        self.guardar_progreso()

    def verificar_subida_nivel(self, tipo_ejercicio):
        """Verificar si el usuario sube de nivel"""
        nivel_info = self.progreso["niveles"][tipo_ejercicio]
        puntos_necesarios = nivel_info["nivel"] * 50  # 50 puntos por nivel

        if nivel_info["puntos"] >= puntos_necesarios:
            nivel_info["nivel"] += 1
            nivel_info["puntos"] = 0  # Resetear puntos para siguiente nivel

            # Desbloquear módulo de pronunciación en nivel 3
            if tipo_ejercicio in ["lectura", "ejercicios"] and nivel_info["nivel"] >= 3:
                self.progreso["niveles"]["pronunciacion"]["desbloqueado"] = True

    def actualizar_racha(self):
        """Actualizar racha de días consecutivos"""
        hoy = datetime.now().date()
        ultimo_acceso = self.progreso["estadisticas"]["ultimo_acceso"]

        if ultimo_acceso:
            ultimo_fecha = datetime.fromisoformat(ultimo_acceso).date()
            if hoy == ultimo_fecha:
                # Mismo día, no cambiar racha
                return
            elif hoy == ultimo_fecha + timedelta(days=1):
                # Día consecutivo
                self.progreso["estadisticas"]["racha_dias"] += 1
            else:
                # Se rompió la racha
                self.progreso["estadisticas"]["racha_dias"] = 1
        else:
            # Primer acceso
            self.progreso["estadisticas"]["racha_dias"] = 1

        self.progreso["estadisticas"]["ultimo_acceso"] = hoy.isoformat()

    def verificar_logros(self):
        """Verificar y otorgar logros"""
        logros_disponibles = [
            {
                "id": "primer_ejercicio",
                "nombre": "¡Primer Paso!",
                "descripcion": "Completar tu primer ejercicio",
                "condicion": lambda p: p["estadisticas"]["ejercicios_completados"] >= 1
            },
            {
                "id": "racha_7_dias",
                "nombre": "Una Semana Completa",
                "descripcion": "Practicar 7 días seguidos",
                "condicion": lambda p: p["estadisticas"]["racha_dias"] >= 7
            },
            {
                "id": "maestro_vocales",
                "nombre": "Maestro de Vocales",
                "descripcion": "Detectar 100 vocales en total",
                "condicion": lambda p: sum(p["estadisticas"]["vocales_detectadas"].values()) >= 100
            },
            {
                "id": "perfeccionista",
                "nombre": "Perfeccionista",
                "descripcion": "Mantener 95% de precisión promedio",
                "condicion": lambda p: p["estadisticas"]["precision_promedio"] >= 95
            }
        ]

        logros_actuales = [logro["id"] for logro in self.progreso["logros"]]

        for logro in logros_disponibles:
            if logro["id"] not in logros_actuales and logro["condicion"](self.progreso):
                self.progreso["logros"].append({
                    "id": logro["id"],
                    "nombre": logro["nombre"],
                    "descripcion": logro["descripcion"],
                    "fecha_obtencion": datetime.now().isoformat()
                })

    def obtener_estadisticas(self):
        """Obtener resumen de estadísticas del usuario"""
        stats = self.progreso["estadisticas"]
        niveles = self.progreso["niveles"]

        return {
            "ejercicios_completados": stats["ejercicios_completados"],
            "precision_promedio": round(stats["precision_promedio"], 1),
            "racha_dias": stats["racha_dias"],
            "niveles": {
                nombre: {"nivel": info["nivel"], "puntos": info["puntos"]}
                for nombre, info in niveles.items()
            },
            "total_vocales": sum(stats["vocales_detectadas"].values()),
            "logros_count": len(self.progreso["logros"])
        }

    def obtener_progreso_nivel(self, tipo_ejercicio):
        """Obtener progreso hacia el siguiente nivel"""
        nivel_info = self.progreso["niveles"][tipo_ejercicio]
        puntos_necesarios = nivel_info["nivel"] * 50
        progreso_porcentaje = min(100, (nivel_info["puntos"] / puntos_necesarios) * 100)

        return {
            "nivel_actual": nivel_info["nivel"],
            "puntos_actuales": nivel_info["puntos"],
            "puntos_necesarios": puntos_necesarios,
            "progreso_porcentaje": round(progreso_porcentaje, 1)
        }