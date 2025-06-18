# setup_database.py - Script Final Corregido para configurar la base de datos de AlfaIA
# Ubicación: AlfaIA/AlfaIA/setup_database.py

import mysql.connector
from mysql.connector import Error
import bcrypt
import os
import sys


def setup_database(reset_if_exists=False):
    """Configurar la base de datos AlfaIA"""
    print("🔧 CONFIGURANDO BASE DE DATOS ALFAIA")
    print("=" * 50)

    # Configuraciones de conexión a probar
    configs = [
        {
            'host': 'localhost',
            'user': 'root',
            'password': 'tired2019',
            'charset': 'utf8mb4'
        },
        {
            'host': 'localhost',
            'user': 'alfaia_user',
            'password': 'alfaia2024',
            'charset': 'utf8mb4'
        }
    ]

    connection = None

    # Intentar conectar
    for config in configs:
        try:
            print(f"🔍 Intentando conectar con usuario: {config['user']}")
            connection = mysql.connector.connect(**config)
            print(f"✅ Conexión exitosa con {config['user']}")
            break
        except Error as e:
            print(f"❌ Error con {config['user']}: {e}")
            continue

    if not connection:
        print("\n❌ No se pudo conectar a MySQL")
        print("💡 Verifica que MySQL esté ejecutándose y las credenciales sean correctas")
        return False

    try:
        cursor = connection.cursor()

        # 1. Manejar base de datos existente
        if reset_if_exists:
            print("\n🔥 Eliminando base de datos existente...")
            cursor.execute("DROP DATABASE IF EXISTS alfaia")
            print("✅ Base de datos anterior eliminada")

        # 2. Crear base de datos
        print("\n📂 Creando base de datos...")
        cursor.execute("CREATE DATABASE IF NOT EXISTS alfaia CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute("USE alfaia")
        print("✅ Base de datos 'alfaia' creada/verificada")

        # 3. Verificar si las tablas ya existen y tienen datos
        cursor.execute("SHOW TABLES LIKE 'usuarios'")
        table_exists = cursor.fetchone()

        if table_exists:
            print("⚠️ Las tablas ya existen. Verificando estructura...")
            if not verify_table_structure(cursor):
                print("⚠️ Estructura de tablas incompatible. Recreando...")
                drop_all_tables(cursor)
                create_tables(cursor)
            else:
                print("✅ Estructura de tablas correcta")
        else:
            # 4. Crear tablas
            print("\n📋 Creando tablas...")
            create_tables(cursor)

        # 5. Crear procedimientos almacenados
        create_stored_procedures(cursor)

        # 6. Crear usuario demo
        print("\n👤 Creando usuario demo...")
        create_demo_user(cursor)

        # 7. Insertar datos de prueba
        print("\n📊 Insertando datos de prueba...")
        insert_sample_data(cursor)

        connection.commit()
        print("\n✅ ¡Base de datos configurada exitosamente!")
        print("\n🔑 Credenciales de prueba:")
        print("   Usuario: demo_user")
        print("   Contraseña: demo123")

        return True

    except Error as e:
        print(f"\n❌ Error configurando base de datos: {e}")
        if connection:
            connection.rollback()
        return False

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


def verify_table_structure(cursor):
    """Verificar si la estructura de las tablas es correcta"""
    try:
        # Verificar que la tabla usuarios tenga las columnas necesarias
        cursor.execute("DESCRIBE usuarios")
        columns = [row[0] for row in cursor.fetchall()]

        required_columns = ['id', 'username', 'email', 'password_hash', 'nombre', 'apellido']

        for col in required_columns:
            if col not in columns:
                print(f"   ❌ Falta columna '{col}' en tabla usuarios")
                return False

        print("   ✅ Estructura de tabla usuarios correcta")
        return True

    except Error as e:
        print(f"   ❌ Error verificando estructura: {e}")
        return False


def drop_all_tables(cursor):
    """Eliminar todas las tablas para recrearlas"""
    try:
        print("   🔥 Eliminando tablas existentes...")

        # Desactivar verificación de claves foráneas temporalmente
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

        tables_to_drop = [
            'vocales_detectadas',
            'logros',
            'estadisticas_diarias',
            'ejercicios_realizados',
            'configuraciones_usuario',
            'progreso_usuario',
            'usuarios'
        ]

        for table in tables_to_drop:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"      ✅ Tabla '{table}' eliminada")

        # Reactivar verificación de claves foráneas
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

    except Error as e:
        print(f"   ❌ Error eliminando tablas: {e}")
        raise


def create_tables(cursor):
    """Crear todas las tablas necesarias"""

    # Desactivar verificación de claves foráneas temporalmente
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

    tables = {
        'usuarios': """
                    CREATE TABLE usuarios
                    (
                        id               INT AUTO_INCREMENT PRIMARY KEY,
                        username         VARCHAR(50) UNIQUE  NOT NULL,
                        email            VARCHAR(100) UNIQUE NOT NULL,
                        password_hash    VARCHAR(255)        NOT NULL,
                        nombre           VARCHAR(100)        NOT NULL,
                        apellido         VARCHAR(100)        NOT NULL,
                        fecha_nacimiento DATE,
                        nivel_actual     INT       DEFAULT 1,
                        fecha_registro   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        ultimo_acceso    TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        activo           BOOLEAN   DEFAULT TRUE,
                        is_admin         BOOLEAN   DEFAULT FALSE,
                        INDEX idx_username (username),
                        INDEX idx_email (email),
                        INDEX idx_activo (activo)
                    ) ENGINE = InnoDB
                      DEFAULT CHARSET = utf8mb4
                      COLLATE = utf8mb4_unicode_ci
                    """,

        'progreso_usuario': """
                            CREATE TABLE progreso_usuario
                            (
                                id                     INT AUTO_INCREMENT PRIMARY KEY,
                                usuario_id             INT NOT NULL,
                                ejercicios_completados INT           DEFAULT 0,
                                tiempo_total_minutos   INT           DEFAULT 0,
                                precision_promedio     DECIMAL(5, 2) DEFAULT 0.00,
                                racha_dias             INT           DEFAULT 0,
                                puntos_totales         INT           DEFAULT 0,
                                nivel_lectura          INT           DEFAULT 1,
                                nivel_ejercicios       INT           DEFAULT 1,
                                nivel_pronunciacion    INT           DEFAULT 1,
                                fecha_actualizacion    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                                                              INDEX idx_usuario (usuario_id)
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                            """,

        'ejercicios_realizados': """
                                 CREATE TABLE ejercicios_realizados (
                                                                        id INT AUTO_INCREMENT PRIMARY KEY,
                                                                        usuario_id INT NOT NULL,
                                                                        tipo_ejercicio ENUM('lectura', 'ejercicios', 'pronunciacion', 'memoria', 'ahorcado', 'trivia', 'crucigrama') NOT NULL,
                                                                        nombre_ejercicio VARCHAR(100) NOT NULL,
                                                                        puntos_obtenidos INT DEFAULT 0,
                                                                        precision_porcentaje DECIMAL(5,2) DEFAULT 0.00,
                                                                        tiempo_empleado_segundos INT DEFAULT 0,
                                                                        fecha_completado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                                        datos_adicionales JSON,
                                                                        INDEX idx_usuario_fecha (usuario_id, fecha_completado),
                                                                        INDEX idx_tipo (tipo_ejercicio)
                                 ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                                 """,

        'estadisticas_diarias': """
                                CREATE TABLE estadisticas_diarias (
                                                                      id INT AUTO_INCREMENT PRIMARY KEY,
                                                                      usuario_id INT NOT NULL,
                                                                      fecha DATE NOT NULL,
                                                                      ejercicios_completados INT DEFAULT 0,
                                                                      tiempo_estudiado_minutos INT DEFAULT 0,
                                                                      puntos_obtenidos INT DEFAULT 0,
                                                                      precision_promedio DECIMAL(5,2) DEFAULT 0.00,
                                                                      UNIQUE KEY unique_user_date (usuario_id, fecha),
                                                                      INDEX idx_usuario_fecha (usuario_id, fecha)
                                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                                """,

        'logros': """
                  CREATE TABLE logros (
                                          id INT AUTO_INCREMENT PRIMARY KEY,
                                          usuario_id INT NOT NULL,
                                          nombre_logro VARCHAR(100) NOT NULL,
                                          descripcion TEXT,
                                          icono VARCHAR(50) DEFAULT '🏆',
                                          categoria ENUM('ejercicios', 'pronunciacion', 'racha', 'precision', 'especial') DEFAULT 'ejercicios',
                                          fecha_obtenido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                          UNIQUE KEY unique_user_logro (usuario_id, nombre_logro),
                                          INDEX idx_usuario (usuario_id),
                                          INDEX idx_categoria (categoria)
                  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                  """,

        'vocales_detectadas': """
                              CREATE TABLE vocales_detectadas (
                                                                  id INT AUTO_INCREMENT PRIMARY KEY,
                                                                  usuario_id INT NOT NULL,
                                                                  ejercicio_id INT,
                                                                  vocal CHAR(1) NOT NULL,
                                                                  frecuencia DECIMAL(8,2),
                                                                  tiempo_deteccion DECIMAL(5,2),
                                                                  confianza DECIMAL(5,2),
                                                                  fecha_deteccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                                  INDEX idx_usuario (usuario_id),
                                                                  INDEX idx_vocal (vocal),
                                                                  INDEX idx_fecha (fecha_deteccion)
                              ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                              """,

        'configuraciones_usuario': """
                                   CREATE TABLE configuraciones_usuario (
                                                                            id INT AUTO_INCREMENT PRIMARY KEY,
                                                                            usuario_id INT NOT NULL,
                                                                            velocidad_lectura INT DEFAULT 500,
                                                                            dificultad_preferida ENUM('facil', 'medio', 'dificil') DEFAULT 'medio',
                                                                            tema_preferido VARCHAR(50) DEFAULT 'brown',
                                                                            notificaciones_activas BOOLEAN DEFAULT TRUE,
                                                                            sonidos_activos BOOLEAN DEFAULT TRUE,
                                                                            configuracion_json JSON,
                                                                            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                                                                            UNIQUE KEY unique_user_config (usuario_id)
                                   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                                   """
    }

    # Crear tablas en orden
    for table_name, create_sql in tables.items():
        try:
            cursor.execute(create_sql)
            print(f"   ✅ Tabla '{table_name}' creada")
        except Error as e:
            print(f"   ❌ Error creando tabla '{table_name}': {e}")
            raise

    # Reactivar verificación de claves foráneas
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

def create_demo_user(cursor):
    """Crear usuario de demostración"""
    try:
        # Verificar si ya existe
        cursor.execute("SELECT id FROM usuarios WHERE username = %s", ('demo_user',))
        existing_user = cursor.fetchone()

        if existing_user:
            print("   ✅ Usuario demo ya existe")
            user_id = existing_user[0]
        else:
            # Crear hash de contraseña
            password_hash = bcrypt.hashpw('demo123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            # Insertar usuario
            cursor.execute("""
                           INSERT INTO usuarios (username, email, password_hash, nombre, apellido, fecha_nacimiento)
                           VALUES (%s, %s, %s, %s, %s, %s)
                           """, ('demo_user', 'demo@alfaia.com', password_hash, 'Usuario', 'Demo', '1990-01-01'))

            user_id = cursor.lastrowid
            print("   ✅ Usuario demo creado exitosamente")

        # Verificar progreso inicial
        cursor.execute("SELECT id FROM progreso_usuario WHERE usuario_id = %s", (user_id,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO progreso_usuario (usuario_id) VALUES (%s)", (user_id,))
            print("   ✅ Progreso inicial creado")

        # Verificar configuración inicial
        cursor.execute("SELECT id FROM configuraciones_usuario WHERE usuario_id = %s", (user_id,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO configuraciones_usuario (usuario_id) VALUES (%s)", (user_id,))
            print("   ✅ Configuración inicial creada")

    except Error as e:
        print(f"   ❌ Error creando usuario demo: {e}")
        raise

def insert_sample_data(cursor):
    """Insertar datos de prueba"""
    try:
        # Obtener ID del usuario demo
        cursor.execute("SELECT id FROM usuarios WHERE username = %s", ('demo_user',))
        result = cursor.fetchone()
        if not result:
            print("   ❌ Usuario demo no encontrado")
            return

        user_id = result[0]

        # Verificar si ya hay ejercicios
        cursor.execute("SELECT COUNT(*) FROM ejercicios_realizados WHERE usuario_id = %s", (user_id,))
        existing_exercises = cursor.fetchone()[0]

        if existing_exercises > 0:
            print("   ✅ Datos de prueba ya existen")
            return

        # Insertar algunos ejercicios de ejemplo
        ejercicios_ejemplo = [
            (user_id, 'lectura', 'Lectura Guiada - El Parque', 25, 85.5, 120),
            (user_id, 'ejercicios', 'Ordenar Frases', 30, 92.0, 95),
            (user_id, 'pronunciacion', 'Detección de Vocales', 20, 78.0, 60),
            (user_id, 'memoria', 'Juego de Memoria', 35, 88.0, 180),
            (user_id, 'trivia', 'Pregunta del Día', 15, 75.0, 45)
        ]

        for ejercicio in ejercicios_ejemplo:
            cursor.execute("""
                           INSERT INTO ejercicios_realizados
                           (usuario_id, tipo_ejercicio, nombre_ejercicio, puntos_obtenidos, precision_porcentaje, tiempo_empleado_segundos)
                           VALUES (%s, %s, %s, %s, %s, %s)
                           """, ejercicio)

        # Actualizar progreso
        cursor.execute("""
                       UPDATE progreso_usuario
                       SET ejercicios_completados = 5,
                           tiempo_total_minutos = 8,
                           precision_promedio = 83.70,
                           racha_dias = 3,
                           puntos_totales = 125
                       WHERE usuario_id = %s
                       """, (user_id,))

        # Insertar estadísticas diarias
        cursor.execute("""
                       INSERT IGNORE INTO estadisticas_diarias
                       (usuario_id, fecha, ejercicios_completados, tiempo_estudiado_minutos, puntos_obtenidos, precision_promedio)
                       VALUES
                           (%s, CURDATE(), 2, 5, 45, 85.0),
                           (%s, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 3, 8, 80, 82.5)
                       """, (user_id, user_id))

        # Insertar algunos logros
        logros_ejemplo = [
            (user_id, 'Primer Ejercicio', 'Completaste tu primer ejercicio en AlfaIA', '🎯', 'ejercicios'),
            (user_id, 'Racha de 3 días', 'Mantuviste una racha de 3 días consecutivos', '🔥', 'racha'),
            (user_id, 'Buen Estudiante', 'Completaste 5 ejercicios', '📚', 'ejercicios')
        ]

        for logro in logros_ejemplo:
            cursor.execute("""
                           INSERT IGNORE INTO logros
                               (usuario_id, nombre_logro, descripcion, icono, categoria)
                           VALUES (%s, %s, %s, %s, %s)
                           """, logro)

        print("   ✅ Datos de prueba insertados")

    except Error as e:
        print(f"   ❌ Error insertando datos de prueba: {e}")
        raise

def create_stored_procedures(cursor):
    """Crear procedimientos almacenados"""
    try:
        print("\n⚙️ Creando procedimientos almacenados...")

        # Procedimiento para actualizar estadísticas
        cursor.execute("DROP PROCEDURE IF EXISTS ActualizarEstadisticasUsuario")

        procedure_sql = """
                        CREATE PROCEDURE ActualizarEstadisticasUsuario(
                            IN p_usuario_id INT,
                            IN p_puntos INT,
                            IN p_precision DECIMAL(5,2),
                            IN p_tiempo_segundos INT
                        )
                        BEGIN
                            DECLARE EXIT HANDLER FOR SQLEXCEPTION
                                BEGIN
                                    ROLLBACK;
                                    RESIGNAL;
                                END;

                            START TRANSACTION;

                            UPDATE progreso_usuario
                            SET
                                ejercicios_completados = ejercicios_completados + 1,
                                tiempo_total_minutos = tiempo_total_minutos + CEIL(p_tiempo_segundos / 60),
                                puntos_totales = puntos_totales + p_puntos,
                                fecha_actualizacion = CURRENT_TIMESTAMP
                            WHERE usuario_id = p_usuario_id;

                            UPDATE progreso_usuario p
                            SET precision_promedio = (
                                SELECT AVG(precision_porcentaje)
                                FROM ejercicios_realizados
                                WHERE usuario_id = p_usuario_id
                            )
                            WHERE p.usuario_id = p_usuario_id;

                            INSERT INTO estadisticas_diarias
                            (usuario_id, fecha, ejercicios_completados, tiempo_estudiado_minutos, puntos_obtenidos, precision_promedio)
                            VALUES
                                (p_usuario_id, CURDATE(), 1, CEIL(p_tiempo_segundos / 60), p_puntos, p_precision)
                            ON DUPLICATE KEY UPDATE
                                                 ejercicios_completados = ejercicios_completados + 1,
                                                 tiempo_estudiado_minutos = tiempo_estudiado_minutos + CEIL(p_tiempo_segundos / 60),
                                                 puntos_obtenidos = puntos_obtenidos + p_puntos,
                                                 precision_promedio = (precision_promedio + p_precision) / 2;

                            COMMIT;
                        END \
                        """

        cursor.execute(procedure_sql)
        print("   ✅ Procedimiento 'ActualizarEstadisticasUsuario' creado")

    except Error as e:
        print(f"   ❌ Error creando procedimientos: {e}")
        # No es crítico, continuar sin procedimientos
        pass

def reset_database():
    """Resetear completamente la base de datos"""
    print("⚠️ RESETEAR BASE DE DATOS")
    print("=" * 50)
    print()
    print("🚨 ADVERTENCIA: Esta acción eliminará TODOS los datos")
    print()

    respuesta = input("¿Estás seguro? Escribe 'RESETEAR' para continuar: ").strip()
    if respuesta != 'RESETEAR':
        print("❌ Reseteo cancelado")
        return False

    return setup_database(reset_if_exists=True)

def main():
    """Función principal"""
    print("🚀 CONFIGURADOR DE BASE DE DATOS ALFAIA")
    print("=" * 50)
    print()

    # Verificar dependencias
    try:
        import mysql.connector
        print("✅ MySQL Connector disponible")
    except ImportError:
        print("❌ MySQL Connector no está instalado")
        print("💡 Instala con: pip install mysql-connector-python")
        return False

    try:
        import bcrypt
        print("✅ bcrypt disponible")
    except ImportError:
        print("❌ bcrypt no está instalado")
        print("💡 Instala con: pip install bcrypt")
        return False

    print()
    print("📋 INFORMACIÓN:")
    print("   - Este script configurará la base de datos 'alfaia'")
    print("   - Creará todas las tablas necesarias")
    print("   - Insertará un usuario de prueba: demo_user / demo123")
    print("   - Agregará datos de ejemplo para testing")
    print()

    # Mostrar opciones
    print("OPCIONES:")
    print("1. Configuración normal (mantener datos existentes)")
    print("2. Resetear y reconfigurar (ELIMINA todos los datos)")
    print("3. Cancelar")
    print()

    while True:
        opcion = input("Selecciona una opción (1-3): ").strip()
        if opcion == '1':
            success = setup_database(reset_if_exists=False)
            break
        elif opcion == '2':
            success = reset_database()
            break
        elif opcion == '3':
            print("❌ Configuración cancelada")
            return False
        else:
            print("Por favor selecciona 1, 2 o 3")

    if success:
        print("\n" + "=" * 50)
        print("🎉 ¡CONFIGURACIÓN COMPLETADA!")
        print("=" * 50)
        print()
        print("✅ Base de datos 'alfaia' configurada correctamente")
        print("✅ Usuario demo creado: demo_user / demo123")
        print("✅ Datos de prueba insertados")
        print()
        print("🚀 Ahora puedes ejecutar:")
        print("   python app.py")
        print()
        print("🌐 Y acceder a: http://localhost:5000")
        print("🔑 Usar credenciales: demo_user / demo123")
    else:
        print("\n" + "=" * 50)
        print("❌ CONFIGURACIÓN FALLÓ")
        print("=" * 50)

    return success

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--reset':
        reset_database()
    else:
        main()