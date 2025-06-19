# database_manager_patch.py - Parche para arreglar los métodos faltantes
import os
import re


def patch_database_manager():
    """Agregar métodos faltantes al DatabaseManager"""
    print("🔧 APLICANDO PARCHE AL DATABASE MANAGER")
    print("=" * 50)

    # Leer archivo actual
    with open('modules/database_manager.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Métodos faltantes para agregar
    missing_methods = '''
    # =====================================================
    # MÉTODOS FALTANTES - PARCHE DE COMPATIBILIDAD
    # =====================================================

    def get_user_progress_summary(self, user_id: int) -> Dict[str, Any]:
        """Obtener resumen de progreso del usuario"""
        try:
            query = """
                SELECT 
                    COUNT(CASE WHEN completado = TRUE THEN 1 END) as ejercicios_completados,
                    COALESCE(AVG(CASE WHEN completado = TRUE THEN precision_porcentaje END), 0) as precision_promedio,
                    COALESCE(SUM(CASE WHEN completado = TRUE THEN puntos_obtenidos + puntos_bonus END), 0) as puntos_totales,
                    COALESCE(SUM(CASE WHEN completado = TRUE THEN tiempo_empleado_segundos END), 0) as tiempo_total_segundos,
                    MAX(fecha_finalizacion) as ultima_actividad,
                    COUNT(DISTINCT DATE(fecha_inicio)) as dias_activos
                FROM resultados_ejercicios
                WHERE user_id = %s
                AND fecha_inicio >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            """

            result = self.execute_query(query, (user_id,), fetch='one')

            if result:
                # Convertir tiempo a minutos
                result['tiempo_total_minutos'] = round(result['tiempo_total_segundos'] / 60)
                # Calcular racha
                result['racha_dias_consecutivos'] = self._calculate_streak(user_id)
                return result
            else:
                return {
                    'ejercicios_completados': 0,
                    'precision_promedio': 0,
                    'puntos_totales': 0,
                    'tiempo_total_minutos': 0,
                    'racha_dias_consecutivos': 0,
                    'dias_activos': 0,
                    'ultima_actividad': None
                }

        except Exception as e:
            logger.error(f"❌ Error obteniendo resumen de progreso: {e}")
            return {
                'ejercicios_completados': 0,
                'precision_promedio': 0,
                'puntos_totales': 0,
                'tiempo_total_minutos': 0,
                'racha_dias_consecutivos': 0,
                'dias_activos': 0,
                'ultima_actividad': None
            }

    def get_exercise_progress_by_type(self, user_id: int) -> Dict[str, Dict[str, Any]]:
        """Obtener progreso por tipo de ejercicio"""
        try:
            query = """
                SELECT 
                    e.tipo_ejercicio,
                    COUNT(CASE WHEN r.completado = TRUE THEN 1 END) as completados,
                    COALESCE(AVG(CASE WHEN r.completado = TRUE THEN r.precision_porcentaje END), 0) as progreso,
                    COALESCE(SUM(CASE WHEN r.completado = TRUE THEN r.puntos_obtenidos + r.puntos_bonus END), 0) as puntos,
                    MAX(r.fecha_finalizacion) as ultimo_ejercicio
                FROM ejercicios e
                LEFT JOIN resultados_ejercicios r ON e.id = r.ejercicio_id AND r.user_id = %s
                GROUP BY e.tipo_ejercicio
            """

            results = self.execute_query(query, (user_id,), fetch='all')

            progress_by_type = {}
            for result in results:
                tipo = result['tipo_ejercicio']
                progress_by_type[tipo] = {
                    'completados': result['completados'] or 0,
                    'progreso': round(result['progreso'] or 0, 1),
                    'puntos': result['puntos'] or 0,
                    'ultimo_ejercicio': result['ultimo_ejercicio']
                }

            # Asegurar que todos los tipos tengan datos
            tipos_ejercicios = ['lectura', 'pronunciacion', 'memoria', 'ahorcado', 'trivia', 
                              'completar_palabra', 'ordenar_frase', 'ortografia']

            for tipo in tipos_ejercicios:
                if tipo not in progress_by_type:
                    progress_by_type[tipo] = {
                        'completados': 0,
                        'progreso': 0,
                        'puntos': 0,
                        'ultimo_ejercicio': None
                    }

            return progress_by_type

        except Exception as e:
            logger.error(f"❌ Error obteniendo progreso por tipo: {e}")
            # Retornar datos por defecto
            tipos_ejercicios = ['lectura', 'pronunciacion', 'memoria', 'ahorcado', 'trivia', 
                              'completar_palabra', 'ordenar_frase', 'ortografia']
            return {tipo: {'completados': 0, 'progreso': 0, 'puntos': 0, 'ultimo_ejercicio': None} 
                    for tipo in tipos_ejercicios}

    def create_exercise_session(self, user_id: int, exercise_type: str, 
                               exercise_id: int = None, config_data: Dict = None) -> str:
        """Crear nueva sesión de ejercicio"""
        try:
            session_id = self._generate_session_id()

            query = """
                INSERT INTO sesiones_ejercicios 
                (sesion_id, user_id, ejercicio_id, tipo_ejercicio, estado, 
                 configuracion, fecha_inicio, ip_address, dispositivo)
                VALUES (%s, %s, %s, %s, 'iniciado', %s, NOW(), %s, %s)
            """

            import json
            import flask

            # Obtener información de la request
            ip_address = flask.request.environ.get('REMOTE_ADDR', 'unknown')
            user_agent = flask.request.headers.get('User-Agent', 'unknown')

            self.execute_query(query, (
                session_id,
                user_id,
                exercise_id,
                exercise_type,
                json.dumps(config_data or {}),
                ip_address,
                user_agent[:255]  # Limitar longitud
            ))

            logger.info(f"✅ Sesión creada: {session_id} para usuario {user_id}")
            return session_id

        except Exception as e:
            logger.error(f"❌ Error creando sesión: {e}")
            # Retornar ID temporal si falla
            import time
            return f"temp_{user_id}_{int(time.time())}"

    def get_user_recent_activity(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtener actividad reciente del usuario"""
        try:
            query = """
                SELECT 
                    r.id,
                    e.nombre as ejercicio_nombre,
                    e.tipo_ejercicio,
                    r.precision_porcentaje,
                    r.puntos_obtenidos,
                    r.tiempo_empleado_segundos,
                    r.completado,
                    r.fecha_finalizacion,
                    c.nombre as categoria_nombre
                FROM resultados_ejercicios r
                JOIN ejercicios e ON r.ejercicio_id = e.id
                LEFT JOIN categorias c ON e.categoria_id = c.id
                WHERE r.user_id = %s
                AND r.completado = TRUE
                ORDER BY r.fecha_finalizacion DESC
                LIMIT %s
            """

            results = self.execute_query(query, (user_id, limit), fetch='all')

            # Formatear resultados
            activity = []
            for result in results:
                activity.append({
                    'id': result['id'],
                    'ejercicio': result['ejercicio_nombre'],
                    'tipo': result['tipo_ejercicio'],
                    'categoria': result['categoria_nombre'],
                    'precision': result['precision_porcentaje'],
                    'puntos': result['puntos_obtenidos'],
                    'tiempo': result['tiempo_empleado_segundos'],
                    'fecha': result['fecha_finalizacion']
                })

            return activity

        except Exception as e:
            logger.error(f"❌ Error obteniendo actividad reciente: {e}")
            return []

    def get_user_achievements(self, user_id: int, **kwargs) -> List[Dict[str, Any]]:
        """Obtener logros del usuario (con compatibilidad de parámetros)"""
        try:
            # Extraer limit si está en kwargs
            limit = kwargs.get('limit', 50)

            query = """
                SELECT 
                    l.id,
                    l.nombre,
                    l.descripcion,
                    l.icono,
                    l.puntos_recompensa,
                    ld.fecha_desbloqueado,
                    l.tipo_logro,
                    l.rareza
                FROM logros_desbloqueados ld
                JOIN logros l ON ld.logro_id = l.id
                WHERE ld.user_id = %s
                ORDER BY ld.fecha_desbloqueado DESC
                LIMIT %s
            """

            return self.execute_query(query, (user_id, limit), fetch='all') or []

        except Exception as e:
            logger.error(f"❌ Error obteniendo logros: {e}")
            return []

    def _generate_session_id(self) -> str:
        """Generar ID único para sesión"""
        import uuid
        return str(uuid.uuid4())

    def _calculate_streak(self, user_id: int) -> int:
        """Calcular racha de días consecutivos"""
        try:
            query = """
                SELECT DISTINCT DATE(fecha_finalizacion) as fecha
                FROM resultados_ejercicios
                WHERE user_id = %s
                AND completado = TRUE
                AND fecha_finalizacion >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                ORDER BY fecha DESC
            """

            dates = self.execute_query(query, (user_id,), fetch='all')

            if not dates:
                return 0

            from datetime import date, timedelta

            streak = 0
            current_date = date.today()

            for date_row in dates:
                exercise_date = date_row['fecha']

                if exercise_date == current_date or exercise_date == current_date - timedelta(days=1):
                    streak += 1
                    current_date = exercise_date - timedelta(days=1)
                else:
                    break

            return streak

        except Exception as e:
            logger.error(f"❌ Error calculando racha: {e}")
            return 0
'''

    # Buscar la última clase o método en el archivo
    # Agregar los métodos antes del final del archivo
    if 'class DatabaseManager' in content:
        # Encontrar el final de la clase (antes del último comentario o final del archivo)
        insertion_point = content.rfind('\n\n    def ')
        if insertion_point != -1:
            # Encontrar el final de ese método
            rest_of_content = content[insertion_point:]
            next_method_or_end = rest_of_content.find('\n\n', 10)
            if next_method_or_end != -1:
                insertion_point = insertion_point + next_method_or_end
            else:
                insertion_point = len(content) - 100  # Cerca del final
        else:
            insertion_point = len(content) - 100

        # Insertar los métodos
        content = content[:insertion_point] + missing_methods + '\n' + content[insertion_point:]
    else:
        # Si no encuentra la clase, agregar al final
        content += missing_methods

    # Asegurar que las importaciones estén presentes
    if 'from typing import Dict, List, Any, Optional, Union' not in content:
        import_line = 'from typing import Dict, List, Any, Optional, Union\n'
        content = import_line + content

    # Guardar archivo patcheado
    with open('modules/database_manager.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("✅ Parche aplicado al DatabaseManager")

    # También verificar que la tabla sesiones_ejercicios exista
    create_missing_table()


def create_missing_table():
    """Crear tabla faltante si no existe"""
    print("🔧 Verificando tabla sesiones_ejercicios...")

    sql_patch = '''
-- Crear tabla sesiones_ejercicios si no existe
CREATE TABLE IF NOT EXISTS sesiones_ejercicios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sesion_id VARCHAR(100) UNIQUE NOT NULL,
    user_id INT NOT NULL,
    ejercicio_id INT NULL,
    tipo_ejercicio VARCHAR(50) NOT NULL,
    estado ENUM('iniciado', 'en_progreso', 'completado', 'abandonado') DEFAULT 'iniciado',
    configuracion JSON NULL,
    fecha_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_finalizacion TIMESTAMP NULL,
    ip_address VARCHAR(45) NULL,
    dispositivo TEXT NULL,
    notas TEXT NULL,
    FOREIGN KEY (user_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (ejercicio_id) REFERENCES ejercicios(id) ON DELETE SET NULL,
    INDEX idx_user_sesiones (user_id),
    INDEX idx_sesion_id (sesion_id),
    INDEX idx_fecha_inicio (fecha_inicio)
);
'''

    # Guardar script SQL
    with open('temp_patch.sql', 'w', encoding='utf-8') as f:
        f.write(sql_patch)

    print("✅ Script SQL creado: temp_patch.sql")
    print("📝 Ejecuta este archivo en tu base de datos MySQL")


if __name__ == "__main__":
    patch_database_manager()
    print("\n🚀 PARCHE COMPLETADO")
    print("=" * 50)
    print("1. ✅ Métodos agregados al DatabaseManager")
    print("2. 📄 Script SQL creado (temp_patch.sql)")
    print("3. 🔄 Reinicia tu app.py para aplicar cambios")
    print("\nEjecuta temp_patch.sql en tu base de datos MySQL antes de reiniciar.")