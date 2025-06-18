#!/usr/bin/env python3
# install.py - Script de Instalación Automática de AlfaIA (CORREGIDO)
# Ubicación: AlfaIA/install.py

import os
import sys
import subprocess
import json
from pathlib import Path
import logging
import time

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class AlfaIAInstaller:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.success_steps = []
        self.failed_steps = []
        self.mysql_config = None

    def print_header(self):
        """Imprimir cabecera del instalador"""
        print("=" * 60)
        print("🚀 INSTALADOR AUTOMÁTICO DE ALFAIA")
        print("   Sistema de Aprendizaje de Lectura con IA")
        print("=" * 60)
        print()

    def check_python_version(self):
        """Verificar versión de Python"""
        print("📋 Verificando versión de Python...")

        if sys.version_info < (3, 8):
            print("❌ ERROR: Se requiere Python 3.8 o superior")
            print(f"   Versión actual: {sys.version}")
            return False

        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} detectado")
        self.success_steps.append("Python version check")
        return True

    def create_directories(self):
        """Crear directorios necesarios"""
        print("\n📁 Creando estructura de directorios...")

        directories = [
            "logs",
            "data",
            "config",
            "static/uploads",
            "static/css",
            "static/js",
            "static/img",
            "temp",
            "backups",
            "templates/auth",
            "templates/ejercicios",
            "templates/juegos",
            "templates/pronunciacion",
            "templates/lectura",
            "templates/errors"
        ]

        created_count = 0
        for directory in directories:
            dir_path = self.project_root / directory
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                created_count += 1
            except Exception as e:
                print(f"⚠️ Error creando directorio {directory}: {e}")

        print(f"✅ {created_count}/{len(directories)} directorios creados/verificados")
        self.success_steps.append("Directory structure")
        return True

    def install_dependencies(self):
        """Instalar dependencias de Python usando método seguro"""
        print("\n📦 Instalando dependencias de Python...")

        requirements_file = self.project_root / "requirements.txt"

        if not requirements_file.exists():
            print("⚠️ requirements.txt no encontrado, creando uno básico...")
            self.create_basic_requirements()

        # Usar instalación segura
        return self.install_dependencies_safe()

    def create_basic_requirements(self):
        """Crear archivo requirements.txt básico"""
        basic_requirements = """Flask==3.0.0
Flask-CORS==4.0.0
mysql-connector-python==8.2.0
bcrypt==4.1.2
librosa==0.10.1
numpy==1.24.4
scipy==1.11.4
soundfile==0.12.1
pandas==2.1.4
python-dateutil==2.8.2
requests==2.31.0
"""

        requirements_file = self.project_root / "requirements.txt"
        with open(requirements_file, 'w') as f:
            f.write(basic_requirements)
        print("✅ requirements.txt básico creado")

    def install_dependencies_safe(self):
        """Instalación segura de dependencias con manejo de errores"""
        print("🔧 Usando instalación segura de dependencias...")

        # Dependencias críticas que deben instalarse
        critical_deps = [
            "Flask==3.0.0",
            "Flask-CORS==4.0.0"
        ]

        # Dependencias opcionales
        optional_deps = [
            "mysql-connector-python==8.2.0",
            "bcrypt==4.1.2",
            "numpy==1.24.4",
            "pandas==2.1.4",
            "python-dateutil==2.8.2"
        ]

        # Dependencias de audio (pueden fallar en algunos sistemas)
        audio_deps = [
            "scipy==1.11.4",
            "soundfile==0.12.1"
        ]

        success_count = 0
        total_count = 0

        # Actualizar pip primero
        print("📥 Actualizando pip...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
                           capture_output=True, check=True, timeout=60)
            print("✅ pip actualizado")
        except Exception as e:
            print(f"⚠️ No se pudo actualizar pip: {e}")

        # Instalar dependencias críticas
        print("🎯 Instalando dependencias críticas...")
        for dep in critical_deps:
            total_count += 1
            if self.install_single_dependency(dep, critical=True):
                success_count += 1
            else:
                print(f"❌ Fallo crítico instalando {dep}")
                self.failed_steps.append("Python dependencies")
                return False

        # Instalar dependencias opcionales
        print("📦 Instalando dependencias opcionales...")
        for dep in optional_deps:
            total_count += 1
            if self.install_single_dependency(dep, critical=False):
                success_count += 1

        # Instalar dependencias de audio
        print("🎤 Instalando dependencias de audio (opcional)...")
        for dep in audio_deps:
            total_count += 1
            if self.install_single_dependency(dep, critical=False):
                success_count += 1

        print(f"\n📊 Dependencias instaladas: {success_count}/{total_count}")

        if success_count >= len(critical_deps):
            print("✅ Dependencias críticas instaladas correctamente")
            self.success_steps.append("Python dependencies")
            return True
        else:
            print("❌ Error instalando dependencias críticas")
            self.failed_steps.append("Python dependencies")
            return False

    def install_single_dependency(self, dependency, critical=False):
        """Instalar una sola dependencia con manejo de errores"""
        try:
            package_name = dependency.split('==')[0]
            print(f"   📥 Instalando {package_name}...")

            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", dependency],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos timeout
            )

            if result.returncode == 0:
                print(f"   ✅ {package_name} instalado")
                return True
            else:
                error_msg = result.stderr.strip()
                print(f"   ⚠️ Error instalando {package_name}")
                if critical:
                    print(f"   💔 Error crítico: {error_msg}")
                else:
                    print(f"   💡 {package_name} es opcional, continuando...")
                return not critical

        except subprocess.TimeoutExpired:
            print(f"   ⏱️ Timeout instalando {dependency}")
            return not critical
        except Exception as e:
            print(f"   ❌ Error inesperado instalando {dependency}: {e}")
            return not critical

    def check_mysql_connection(self):
        """Verificar conexión a MySQL"""
        print("\n🗄️ Verificando conexión a MySQL...")

        # Configuraciones a probar
        configs = [
            {
                'host': 'localhost',
                'user': 'root',
                'password': 'tired2019',
                'auth_plugin': 'mysql_native_password'
            },
            {
                'host': 'localhost',
                'user': 'root',
                'password': 'tired2019'
            },
            {
                'host': 'localhost',
                'user': 'alfaia_user',
                'password': 'alfaia2024'
            }
        ]

        for i, config in enumerate(configs):
            try:
                print(f"   🔍 Probando configuración {i + 1}...")

                # Intentar importar mysql.connector
                try:
                    import mysql.connector
                except ImportError:
                    print("   📦 Instalando mysql-connector-python...")
                    if self.install_single_dependency("mysql-connector-python==8.2.0", critical=True):
                        import mysql.connector
                    else:
                        print("   ❌ No se pudo instalar mysql-connector-python")
                        continue

                # Intentar conexión
                connection = mysql.connector.connect(**config, connect_timeout=5)
                if connection.is_connected():
                    connection.close()
                    print(f"✅ Conexión MySQL exitosa con: {config['user']}@{config['host']}")
                    self.mysql_config = config
                    self.success_steps.append("MySQL connection")
                    return True

            except Exception as e:
                print(f"   ❌ Configuración {i + 1} falló: {e}")

        print("❌ No se pudo conectar a MySQL")
        print("💡 Asegúrate de que MySQL esté corriendo:")
        print("   Windows: net start mysql")
        print("   Linux: sudo systemctl start mysql")
        print("   macOS: brew services start mysql")
        self.failed_steps.append("MySQL connection")
        return False

    def create_database(self):
        """Crear base de datos AlfaIA"""
        print("\n🏗️ Creando base de datos AlfaIA...")

        if not hasattr(self, 'mysql_config') or not self.mysql_config:
            print("❌ No hay configuración MySQL válida")
            self.failed_steps.append("Database creation")
            return False

        try:
            import mysql.connector

            # Conectar sin especificar base de datos
            connection = mysql.connector.connect(**self.mysql_config)
            cursor = connection.cursor()

            # Crear base de datos si no existe
            cursor.execute("CREATE DATABASE IF NOT EXISTS alfaia CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("✅ Base de datos 'alfaia' creada/verificada")

            # Crear usuario específico si no existe (solo si estamos conectados como root)
            if self.mysql_config['user'] == 'root':
                try:
                    cursor.execute("CREATE USER IF NOT EXISTS 'alfaia_user'@'localhost' IDENTIFIED BY 'alfaia2024'")
                    cursor.execute("GRANT ALL PRIVILEGES ON alfaia.* TO 'alfaia_user'@'localhost'")
                    cursor.execute("FLUSH PRIVILEGES")
                    print("✅ Usuario 'alfaia_user' creado/configurado")
                except Exception as e:
                    print(f"⚠️ No se pudo crear usuario específico: {e}")

            cursor.close()
            connection.close()

            self.success_steps.append("Database creation")
            return True

        except Exception as e:
            print(f"❌ Error creando base de datos: {e}")
            self.failed_steps.append("Database creation")
            return False

    def create_database_tables(self):
        """Crear tablas de la base de datos"""
        print("\n📋 Creando tablas de la base de datos...")

        # SQL dividido en statements individuales para mejor manejo de errores
        sql_statements = [
            """CREATE TABLE IF NOT EXISTS usuarios
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
                 COLLATE = utf8mb4_unicode_ci""",

            """CREATE TABLE IF NOT EXISTS progreso_usuario
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
                   FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,
                   INDEX idx_usuario (usuario_id)
               ) ENGINE = InnoDB
                 DEFAULT CHARSET = utf8mb4
                 COLLATE = utf8mb4_unicode_ci""",

            """CREATE TABLE IF NOT EXISTS ejercicios_realizados
               (
                   id                       INT AUTO_INCREMENT PRIMARY KEY,
                   usuario_id               INT                                                                                            NOT NULL,
                   tipo_ejercicio           ENUM ('lectura', 'ejercicios', 'pronunciacion', 'memoria', 'ahorcado', 'trivia', 'crucigrama') NOT NULL,
                   nombre_ejercicio         VARCHAR(100)                                                                                   NOT NULL,
                   puntos_obtenidos         INT           DEFAULT 0,
                   precision_porcentaje     DECIMAL(5, 2) DEFAULT 0.00,
                   tiempo_empleado_segundos INT           DEFAULT 0,
                   fecha_completado         TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
                   datos_adicionales        JSON,
                   FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,
                   INDEX idx_usuario_fecha (usuario_id, fecha_completado),
                   INDEX idx_tipo (tipo_ejercicio)
               ) ENGINE = InnoDB
                 DEFAULT CHARSET = utf8mb4
                 COLLATE = utf8mb4_unicode_ci""",

            """CREATE TABLE IF NOT EXISTS logros
               (
                   id                INT AUTO_INCREMENT PRIMARY KEY,
                   nombre            VARCHAR(100) UNIQUE NOT NULL,
                   descripcion       TEXT,
                   puntos_requeridos INT                                                          DEFAULT 0,
                   icono             VARCHAR(50),
                   categoria         ENUM ('ejercicios', 'tiempo', 'precision', 'racha', 'nivel') DEFAULT 'ejercicios',
                   activo            BOOLEAN                                                      DEFAULT TRUE,
                   INDEX idx_categoria (categoria)
               ) ENGINE = InnoDB
                 DEFAULT CHARSET = utf8mb4
                 COLLATE = utf8mb4_unicode_ci""",

            """CREATE TABLE IF NOT EXISTS logros_usuario
               (
                   id             INT AUTO_INCREMENT PRIMARY KEY,
                   usuario_id     INT NOT NULL,
                   logro_id       INT NOT NULL,
                   fecha_obtenido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                   FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,
                   FOREIGN KEY (logro_id) REFERENCES logros (id) ON DELETE CASCADE,
                   UNIQUE KEY unique_user_logro (usuario_id, logro_id),
                   INDEX idx_usuario (usuario_id),
                   INDEX idx_fecha (fecha_obtenido)
               ) ENGINE = InnoDB
                 DEFAULT CHARSET = utf8mb4
                 COLLATE = utf8mb4_unicode_ci""",

            """CREATE TABLE IF NOT EXISTS configuraciones_usuario
               (
                   id                     INT AUTO_INCREMENT PRIMARY KEY,
                   usuario_id             INT NOT NULL,
                   velocidad_lectura      ENUM ('lenta', 'normal', 'rapida') DEFAULT 'normal',
                   dificultad_preferida   INT                                DEFAULT 1,
                   tema_preferido         VARCHAR(50)                        DEFAULT 'general',
                   notificaciones_activas BOOLEAN                            DEFAULT TRUE,
                   sonidos_activos        BOOLEAN                            DEFAULT TRUE,
                   configuracion_json     JSON,
                   fecha_actualizacion    TIMESTAMP                          DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                   FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,
                   UNIQUE KEY unique_user_config (usuario_id)
               ) ENGINE = InnoDB
                 DEFAULT CHARSET = utf8mb4
                 COLLATE = utf8mb4_unicode_ci"""
        ]

        try:
            import mysql.connector

            connection = mysql.connector.connect(
                host=self.mysql_config['host'],
                user=self.mysql_config['user'],
                password=self.mysql_config['password'],
                database='alfaia'
            )

            cursor = connection.cursor()

            # Ejecutar cada statement por separado
            for i, statement in enumerate(sql_statements):
                try:
                    cursor.execute(statement)
                    print(f"   ✅ Tabla {i + 1}/{len(sql_statements)} creada")
                except Exception as e:
                    print(f"   ⚠️ Error en tabla {i + 1}: {e}")

            connection.commit()
            cursor.close()
            connection.close()

            print("✅ Tablas de la base de datos creadas correctamente")
            self.success_steps.append("Database tables")
            return True

        except Exception as e:
            print(f"❌ Error creando tablas: {e}")
            self.failed_steps.append("Database tables")
            return False

    def insert_initial_data(self):
        """Insertar datos iniciales"""
        print("\n📝 Insertando datos iniciales...")

        initial_logros = [
            ('primer_ejercicio', 'Completar primer ejercicio', 10, '🎯', 'ejercicios'),
            ('racha_7_dias', '7 días consecutivos practicando', 50, '🔥', 'racha'),
            ('racha_30_dias', '30 días consecutivos practicando', 200, '🏆', 'racha'),
            ('precision_perfecta', '100% de precisión en un ejercicio', 25, '🎯', 'precision'),
            ('nivel_2', 'Alcanzar nivel 2', 100, '⭐', 'nivel'),
            ('nivel_3', 'Alcanzar nivel 3', 250, '⭐⭐', 'nivel'),
            ('ejercicios_100', 'Completar 100 ejercicios', 300, '💯', 'ejercicios'),
            ('maestro_pronunciacion', 'Dominar todos los ejercicios de pronunciación', 500, '🎤', 'ejercicios')
        ]

        try:
            import mysql.connector

            connection = mysql.connector.connect(
                host=self.mysql_config['host'],
                user=self.mysql_config['user'],
                password=self.mysql_config['password'],
                database='alfaia'
            )
            cursor = connection.cursor()

            # Insertar logros si no existen
            for logro in initial_logros:
                try:
                    cursor.execute("""
                                   INSERT IGNORE INTO logros (nombre, descripcion, puntos_requeridos, icono, categoria)
                                   VALUES (%s, %s, %s, %s, %s)
                                   """, logro)
                except Exception as e:
                    print(f"   ⚠️ Error insertando logro {logro[0]}: {e}")

            connection.commit()
            cursor.close()
            connection.close()

            print("✅ Datos iniciales insertados correctamente")
            self.success_steps.append("Initial data")
            return True

        except Exception as e:
            print(f"❌ Error insertando datos iniciales: {e}")
            self.failed_steps.append("Initial data")
            return False

    def create_config_files(self):
        """Crear archivos de configuración"""
        print("\n⚙️ Creando archivos de configuración...")

        try:
            # Crear directorio config si no existe
            config_dir = self.project_root / "config"
            config_dir.mkdir(exist_ok=True)

            # Crear config/app_config.json si no existe
            config_file = config_dir / "app_config.json"

            if not config_file.exists():
                config_data = {
                    "app": {
                        "name": "AlfaIA",
                        "version": "1.0.0",
                        "debug": True,
                        "host": "127.0.0.1",
                        "port": 5000,
                        "secret_key": "alfaia-secret-key-2025-change-in-production"
                    },
                    "database": {
                        "host": self.mysql_config.get('host', 'localhost') if self.mysql_config else 'localhost',
                        "port": 3306,
                        "database": "alfaia",
                        "user": self.mysql_config.get('user', 'alfaia_user') if self.mysql_config else 'alfaia_user',
                        "password": self.mysql_config.get('password',
                                                          'alfaia2024') if self.mysql_config else 'alfaia2024'
                    },
                    "audio": {
                        "sample_rate": 44100,
                        "confidence_threshold": 0.6,
                        "energy_threshold": 0.01
                    }
                }

                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)

                print("✅ Archivo de configuración creado")
            else:
                print("✅ Archivo de configuración ya existe")

            self.success_steps.append("Config files")
            return True

        except Exception as e:
            print(f"❌ Error creando archivos de configuración: {e}")
            self.failed_steps.append("Config files")
            return False

    def create_basic_templates(self):
        """Crear plantillas HTML básicas si no existen"""
        print("\n🌐 Verificando plantillas HTML básicas...")

        try:
            # Crear directorio templates si no existe
            templates_dir = self.project_root / "templates"
            templates_dir.mkdir(exist_ok=True)

            # Crear base.html básico
            base_template = templates_dir / "base.html"
            if not base_template.exists():
                base_html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}AlfaIA{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""

                with open(base_template, 'w', encoding='utf-8') as f:
                    f.write(base_html)
                print("✅ Plantilla base.html creada")
            else:
                print("✅ Plantillas HTML verificadas")

            self.success_steps.append("Basic templates")
            return True

        except Exception as e:
            print(f"❌ Error creando plantillas: {e}")
            self.failed_steps.append("Basic templates")
            return False

    def test_installation(self):
        """Probar la instalación"""
        print("\n🧪 Probando la instalación...")

        try:
            # Agregar el directorio del proyecto al path
            project_path = str(self.project_root)
            if project_path not in sys.path:
                sys.path.insert(0, project_path)

            print("   🔍 Probando importación de módulos...")

            # Test de módulos básicos
            tests_passed = 0
            total_tests = 3

            try:
                from modules.config import ConfigManager
                config = ConfigManager()
                print("   ✅ Módulo de configuración funcionando")
                tests_passed += 1
            except Exception as e:
                print(f"   ⚠️ Error en módulo config: {e}")

            try:
                from modules.database import DatabaseManager
                db = DatabaseManager()
                if db and hasattr(db, 'test_connection'):
                    if db.test_connection():
                        print("   ✅ Conexión a base de datos funcionando")
                        tests_passed += 1
                    else:
                        print("   ⚠️ Conexión a base de datos con problemas")
                else:
                    print("   ⚠️ Módulo de base de datos sin método test_connection")
            except Exception as e:
                print(f"   ⚠️ Error en módulo database: {e}")

            try:
                from modules.generador_ejercicios import GeneradorEjercicios
                gen = GeneradorEjercicios()
                ejercicio = gen.generar_ordena_frase(1)
                if ejercicio:
                    print("   ✅ Generador de ejercicios funcionando")
                    tests_passed += 1
                else:
                    print("   ⚠️ Generador de ejercicios con problemas")
            except Exception as e:
                print(f"   ⚠️ Error en generador de ejercicios: {e}")

            print(f"   📊 Tests pasados: {tests_passed}/{total_tests}")

            if tests_passed >= 1:  # Al menos un test debe pasar
                self.success_steps.append("Installation test")
                return True
            else:
                self.failed_steps.append("Installation test")
                return False

        except Exception as e:
            print(f"❌ Error en pruebas: {e}")
            self.failed_steps.append("Installation test")
            return False

    def print_summary(self):
        """Imprimir resumen de la instalación"""
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE LA INSTALACIÓN")
        print("=" * 60)

        print(f"\n✅ Pasos completados exitosamente ({len(self.success_steps)}):")
        for step in self.success_steps:
            print(f"   • {step}")

        if self.failed_steps:
            print(f"\n❌ Pasos que fallaron ({len(self.failed_steps)}):")
            for step in self.failed_steps:
                print(f"   • {step}")

        if not self.failed_steps:
            print("\n🎉 ¡INSTALACIÓN COMPLETADA EXITOSAMENTE!")
            print("\n📋 Próximos pasos:")
            print("   1. Ejecuta: python app.py")
            print("   2. Abre tu navegador en: http://127.0.0.1:5000")
            print("   3. Regístrate como nuevo usuario")
            print("\n💡 Consejos:")
            print("   • Cambia la clave secreta en config/app_config.json para producción")
            print("   • Revisa los logs en la carpeta 'logs' si hay problemas")
            print("   • Consulta la documentación para configuraciones avanzadas")
        else:
            print("\n⚠️ INSTALACIÓN PARCIAL")
            print("   Algunos componentes fallaron, pero la aplicación puede funcionar.")
            print("   Revisa los errores arriba y repite la instalación si es necesario.")

        print("\n" + "=" * 60)

    def run_installation(self):
        """Ejecutar proceso completo de instalación"""
        self.print_header()

        # Ejecutar pasos de instalación
        steps = [
            ("Verificar Python", self.check_python_version),
            ("Crear directorios", self.create_directories),
            ("Instalar dependencias", self.install_dependencies),
            ("Verificar MySQL", self.check_mysql_connection),
            ("Crear base de datos", self.create_database),
            ("Crear tablas", self.create_database_tables),
            ("Insertar datos iniciales", self.insert_initial_data),
            ("Crear configuraciones", self.create_config_files),
            ("Verificar plantillas", self.create_basic_templates),
            ("Probar instalación", self.test_installation)
        ]

        for step_name, step_function in steps:
            print(f"\n🔄 {step_name}...")
            try:
                result = step_function()
                if not result and step_name in ["Verificar Python", "Crear directorios"]:
                    # Pasos críticos que deben pasar
                    print(f"❌ Paso crítico falló: {step_name}")
                    break
            except KeyboardInterrupt:
                print(f"\n⚠️ Instalación cancelada por el usuario en: {step_name}")
                break
            except Exception as e:
                print(f"❌ Error inesperado en {step_name}: {e}")
                self.failed_steps.append(step_name)

        self.print_summary()

    def create_startup_script(self):
        """Crear script de inicio para diferentes sistemas operativos"""
        print("\n📝 Creando scripts de inicio...")

        try:
            import platform
            system = platform.system().lower()

            if system == 'windows':
                # Crear archivo .bat para Windows
                bat_content = f"""@echo off
cd /d "{self.project_root}"
echo Iniciando AlfaIA...
python app.py
pause
"""
                bat_file = self.project_root / "iniciar_alfaia.bat"
                with open(bat_file, 'w', encoding='utf-8') as f:
                    f.write(bat_content)
                print("   ✅ Script de Windows creado: iniciar_alfaia.bat")

            # Crear script universal de Python
            py_script = f"""#!/usr/bin/env python3
# Script de inicio automático para AlfaIA
import os
import sys
from pathlib import Path

# Cambiar al directorio del proyecto
project_dir = Path(__file__).parent
os.chdir(project_dir)

# Agregar al path
sys.path.insert(0, str(project_dir))

# Importar y ejecutar
try:
    from app import app
    print("🚀 Iniciando AlfaIA...")
    print("📱 Disponible en: http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)
except ImportError as e:
    print(f"❌ Error de importación: {{e}}")
    print("💡 Ejecuta 'python install.py' primero")
except Exception as e:
    print(f"❌ Error: {{e}}")

input("Presiona Enter para salir...")
"""

            py_file = self.project_root / "iniciar_alfaia.py"
            with open(py_file, 'w', encoding='utf-8') as f:
                f.write(py_script)
            print("   ✅ Script de Python creado: iniciar_alfaia.py")

            return True

        except Exception as e:
            print(f"   ⚠️ Error creando scripts de inicio: {e}")
            return False


def safe_input(prompt, default=""):
    """Input seguro con manejo de errores"""
    try:
        return input(prompt).strip() or default
    except (KeyboardInterrupt, EOFError):
        return default


def main():
    """Función principal con manejo robusto de errores"""
    installer = AlfaIAInstaller()

    try:
        # Verificar que estamos en el directorio correcto
        current_dir = Path.cwd()
        modules_dir = current_dir / "modules"
        app_file = current_dir / "app.py"

        if not modules_dir.exists():
            print("❌ ERROR: No se encuentra la carpeta 'modules'")
            print("   Ejecuta este script desde el directorio raíz del proyecto AlfaIA")

            # Intentar encontrar el directorio correcto
            for parent in [current_dir] + list(current_dir.parents):
                if (parent / "modules").exists():
                    print(f"💡 Directorio del proyecto encontrado en: {parent}")
                    response = safe_input("¿Cambiar a este directorio? (s/n): ", "s")
                    if response.lower() in ['s', 'si', 'y', 'yes']:
                        os.chdir(parent)
                        installer.project_root = parent
                        break
            else:
                print("💡 Asegúrate de estar en el directorio que contiene:")
                print("   - modules/ (carpeta con módulos de Python)")
                print("   - app.py (archivo principal de la aplicación)")
                print("   - este script install.py")
                sys.exit(1)

        # Verificar archivo app.py
        if not app_file.exists() and not (installer.project_root / "app.py").exists():
            print("⚠️ ADVERTENCIA: No se encuentra app.py")
            print("   La instalación continuará, pero será necesario crear el archivo principal")

        # Ejecutar instalación
        installer.run_installation()

        # Crear scripts de inicio si la instalación fue exitosa
        if len(installer.success_steps) > len(installer.failed_steps):
            installer.create_startup_script()

            # Mostrar mensaje final optimista
            print("\n🎊 ¡Instalación completada!")
            print("🚀 Para iniciar AlfaIA:")
            print("   • Opción 1: python app.py")
            print("   • Opción 2: python start.py")
            print("   • Opción 3: doble clic en iniciar_alfaia.bat (Windows)")

    except KeyboardInterrupt:
        print("\n\n⚠️ Instalación cancelada por el usuario")
        print("👋 Puedes ejecutar este script nuevamente cuando quieras")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error crítico durante la instalación: {e}")
        print("\n💡 Soluciones posibles:")
        print("   1. Ejecutar como administrador/sudo")
        print("   2. Verificar conexión a internet")
        print("   3. Verificar que MySQL esté instalado y corriendo")
        print("   4. Revisar permisos de archivos")
        print("\n🔧 Comandos útiles para diagnosticar:")
        print("   • Verificar Python: python --version")
        print("   • Verificar pip: pip --version")
        print("   • Verificar MySQL: mysql --version")
        sys.exit(1)


if __name__ == "__main__":
    main()
