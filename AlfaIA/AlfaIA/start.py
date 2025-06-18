#!/usr/bin/env python3
# start.py - Script de Inicio Rápido para AlfaIA
# Ubicación: AlfaIA/start.py

import os
import sys
import subprocess
import time
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class AlfaIAStarter:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.app_file = self.project_root / "app.py"

    def print_banner(self):
        """Mostrar banner de inicio"""
        banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║        🚀 ALFAIA - Sistema de Aprendizaje de Lectura con IA       ║
║                                                                  ║
║               Iniciando tu plataforma educativa...               ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""
        print(banner)

    def check_requirements(self):
        """Verificar requisitos básicos"""
        print("🔍 Verificando requisitos del sistema...")

        checks = []

        # Verificar Python
        if sys.version_info >= (3, 8):
            checks.append(("✅ Python", f"{sys.version_info.major}.{sys.version_info.minor}"))
        else:
            checks.append(("❌ Python", f"Requiere 3.8+, tienes {sys.version_info.major}.{sys.version_info.minor}"))
            return False

        # Verificar archivo principal
        if self.app_file.exists():
            checks.append(("✅ app.py", "Encontrado"))
        else:
            checks.append(("❌ app.py", "No encontrado"))
            return False

        # Verificar módulos
        modules_dir = self.project_root / "modules"
        if modules_dir.exists():
            checks.append(("✅ Módulos", "Directorio encontrado"))
        else:
            checks.append(("❌ Módulos", "Directorio no encontrado"))
            return False

        # Verificar dependencias críticas
        try:
            import flask
            checks.append(("✅ Flask", f"v{flask.__version__}"))
        except ImportError:
            checks.append(("❌ Flask", "No instalado"))
            return False

        try:
            import mysql.connector
            checks.append(("✅ MySQL Connector", "Disponible"))
        except ImportError:
            checks.append(("⚠️ MySQL Connector", "No instalado - funcionalidad limitada"))

        # Mostrar resultados
        for check, status in checks:
            print(f"   {check}: {status}")

        return True

    def check_database_connection(self):
        """Verificar conexión a base de datos"""
        print("\n🗄️ Verificando conexión a base de datos...")

        try:
            # Intentar importar el módulo de base de datos
            sys.path.append(str(self.project_root))
            from modules.database import db_manager

            if db_manager and db_manager.test_connection():
                print("   ✅ Conexión a MySQL exitosa")
                return True
            else:
                print("   ⚠️ No se puede conectar a MySQL")
                print("   💡 La aplicación funcionará con funcionalidades limitadas")
                return False

        except Exception as e:
            print(f"   ⚠️ Error verificando base de datos: {e}")
            print("   💡 Ejecuta 'python install.py' para configurar la base de datos")
            return False

    def check_audio_system(self):
        """Verificar sistema de audio"""
        print("\n🎤 Verificando sistema de audio...")

        try:
            from modules.procesarAudio import test_microphone_setup

            audio_status = test_microphone_setup()

            if audio_status.get('ready_for_processing'):
                print("   ✅ Sistema de audio completamente configurado")
                return True
            else:
                print("   ⚠️ Sistema de audio parcialmente configurado")
                print("   💡 Algunas funciones de pronunciación pueden estar limitadas")
                return False

        except Exception as e:
            print(f"   ⚠️ Error verificando audio: {e}")
            print("   💡 Instala las dependencias de audio para funcionalidad completa")
            return False

    def create_missing_directories(self):
        """Crear directorios faltantes"""
        print("\n📁 Verificando estructura de directorios...")

        required_dirs = [
            "logs",
            "data",
            "config",
            "static/uploads",
            "temp",
            "templates"
        ]

        created = 0
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                try:
                    full_path.mkdir(parents=True, exist_ok=True)
                    created += 1
                except Exception as e:
                    print(f"   ⚠️ No se pudo crear {dir_path}: {e}")

        if created > 0:
            print(f"   ✅ {created} directorios creados")
        else:
            print("   ✅ Estructura de directorios verificada")

    def show_startup_options(self):
        """Mostrar opciones de inicio"""
        print("\n" + "=" * 60)
        print("🚀 OPCIONES DE INICIO")
        print("=" * 60)
        print("1. 🏃 Inicio rápido (modo desarrollo)")
        print("2. 🔧 Verificar configuración completa")
        print("3. 📦 Ejecutar instalación/configuración")
        print("4. 🧪 Ejecutar tests del sistema")
        print("5. 📖 Mostrar información del proyecto")
        print("6. ❌ Salir")
        print("=" * 60)

        while True:
            try:
                choice = input("\nSelecciona una opción (1-6): ").strip()

                if choice == "1":
                    return self.quick_start()
                elif choice == "2":
                    return self.full_check()
                elif choice == "3":
                    return self.run_installation()
                elif choice == "4":
                    return self.run_tests()
                elif choice == "5":
                    return self.show_info()
                elif choice == "6":
                    print("👋 ¡Hasta luego!")
                    return False
                else:
                    print("❌ Opción inválida. Por favor selecciona 1-6.")

            except KeyboardInterrupt:
                print("\n\n👋 ¡Hasta luego!")
                return False

    def quick_start(self):
        """Inicio rápido de la aplicación"""
        print("\n🏃 INICIO RÁPIDO")
        print("-" * 30)

        # Verificaciones mínimas
        if not self.check_requirements():
            print("❌ No se pueden cumplir los requisitos mínimos")
            return False

        self.create_missing_directories()

        print("\n🚀 Iniciando AlfaIA en modo desarrollo...")
        print("📱 La aplicación estará disponible en: http://127.0.0.1:5000")
        print("🔄 Presiona Ctrl+C para detener la aplicación")
        print("\n" + "=" * 60)

        try:
            # Ejecutar la aplicación
            os.chdir(self.project_root)
            subprocess.run([sys.executable, "app.py"], check=True)

        except subprocess.CalledProcessError as e:
            print(f"\n❌ Error ejecutando la aplicación: {e}")
            print("💡 Intenta ejecutar 'python install.py' primero")
            return False

        except KeyboardInterrupt:
            print("\n\n⏹️ Aplicación detenida por el usuario")
            print("👋 ¡Gracias por usar AlfaIA!")
            return True

    def full_check(self):
        """Verificación completa del sistema"""
        print("\n🔧 VERIFICACIÓN COMPLETA")
        print("-" * 40)

        # Realizar todas las verificaciones
        checks = [
            ("Requisitos básicos", self.check_requirements),
            ("Estructura de directorios", self.create_missing_directories),
            ("Conexión base de datos", self.check_database_connection),
            ("Sistema de audio", self.check_audio_system),
        ]

        results = []
        for name, check_func in checks:
            print(f"\n🔍 Verificando: {name}")
            try:
                result = check_func()
                results.append((name, result))
            except Exception as e:
                print(f"   ❌ Error: {e}")
                results.append((name, False))

        # Mostrar resumen
        print("\n" + "=" * 50)
        print("📊 RESUMEN DE VERIFICACIÓN")
        print("=" * 50)

        passed = 0
        for name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {name}")
            if result:
                passed += 1

        print(f"\n🎯 Resultado: {passed}/{len(results)} verificaciones exitosas")

        if passed == len(results):
            print("🎉 ¡Sistema completamente funcional!")
            return self.quick_start()
        elif passed >= len(results) // 2:
            print("⚠️ Sistema parcialmente funcional")
            response = input("¿Continuar con el inicio? (s/n): ").strip().lower()
            if response in ['s', 'si', 'y', 'yes']:
                return self.quick_start()
        else:
            print("❌ Demasiados problemas encontrados")
            print("💡 Ejecuta la instalación primero")

        return False

    def run_installation(self):
        """Ejecutar script de instalación"""
        print("\n📦 EJECUTANDO INSTALACIÓN")
        print("-" * 35)

        install_script = self.project_root / "install.py"

        if not install_script.exists():
            print("❌ Script de instalación no encontrado")
            print("💡 Asegúrate de que install.py está en el directorio raíz")
            return False

        try:
            print("🔄 Ejecutando instalación...")
            subprocess.run([sys.executable, str(install_script)], check=True)

            print("\n✅ Instalación completada")
            response = input("¿Iniciar la aplicación ahora? (s/n): ").strip().lower()

            if response in ['s', 'si', 'y', 'yes']:
                return self.quick_start()

        except subprocess.CalledProcessError as e:
            print(f"❌ Error durante la instalación: {e}")
            return False
        except KeyboardInterrupt:
            print("\n⏹️ Instalación cancelada por el usuario")
            return False

        return True

    def run_tests(self):
        """Ejecutar tests del sistema"""
        print("\n🧪 EJECUTANDO TESTS DEL SISTEMA")
        print("-" * 40)

        tests = [
            ("Test de importación de módulos", self.test_module_imports),
            ("Test de configuración", self.test_configuration),
            ("Test de base de datos", self.test_database),
            ("Test de generadores", self.test_generators),
        ]

        passed = 0
        for test_name, test_func in tests:
            print(f"\n🔬 {test_name}...")
            try:
                if test_func():
                    print(f"   ✅ {test_name} - PASS")
                    passed += 1
                else:
                    print(f"   ❌ {test_name} - FAIL")
            except Exception as e:
                print(f"   ❌ {test_name} - ERROR: {e}")

        print(f"\n📊 Resultado de tests: {passed}/{len(tests)} exitosos")

        if passed == len(tests):
            print("🎉 ¡Todos los tests pasaron!")
        else:
            print("⚠️ Algunos tests fallaron - revisa la configuración")

        input("\nPresiona Enter para continuar...")
        return True

    def test_module_imports(self):
        """Test de importación de módulos"""
        try:
            sys.path.append(str(self.project_root))

            from modules.database import DatabaseManager
            from modules.config import ConfigManager
            from modules.generador_ejercicios import GeneradorEjercicios
            from modules.juegos_interactivos import JuegosInteractivos
            from modules.progreso_usuario import ProgresoUsuario
            from modules.retroalimentacion import RetroalimentacionPersonalizada
            from modules.auth import AuthManager
            from modules.utils import limpiar_texto

            return True
        except ImportError as e:
            print(f"      Error importando: {e}")
            return False

    def test_configuration(self):
        """Test de configuración"""
        try:
            from modules.config import config_manager

            # Verificar que la configuración se puede cargar
            db_config = config_manager.get_database_config()
            audio_config = config_manager.get_audio_config()

            # Verificar que tiene valores básicos
            return bool(db_config and audio_config)
        except Exception as e:
            print(f"      Error en configuración: {e}")
            return False

    def test_database(self):
        """Test de base de datos"""
        try:
            from modules.database import db_manager

            if db_manager:
                return db_manager.test_connection()
            return False
        except Exception as e:
            print(f"      Error en base de datos: {e}")
            return False

    def test_generators(self):
        """Test de generadores de ejercicios"""
        try:
            from modules.generador_ejercicios import GeneradorEjercicios
            from modules.juegos_interactivos import JuegosInteractivos

            # Test generador de ejercicios
            gen = GeneradorEjercicios()
            ejercicio = gen.generar_ordena_frase(1)

            if not ejercicio or 'frase_correcta' not in ejercicio:
                return False

            # Test juegos interactivos
            juegos = JuegosInteractivos()
            memoria = juegos.generar_juego_memoria(1)

            if not memoria or len(memoria) == 0:
                return False

            return True
        except Exception as e:
            print(f"      Error en generadores: {e}")
            return False

    def show_info(self):
        """Mostrar información del proyecto"""
        info = """
╔══════════════════════════════════════════════════════════════════╗
║                        📖 INFORMACIÓN DEL PROYECTO               ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  🎯 ALFAIA - Sistema de Aprendizaje de Lectura con IA            ║
║                                                                  ║
║  📋 Descripción:                                                 ║
║     Plataforma educativa inteligente para mejorar habilidades    ║
║     de lectura, escritura y pronunciación.                      ║
║                                                                  ║
║  🔧 Tecnologías:                                                 ║
║     • Backend: Python + Flask                                   ║
║     • Base de datos: MySQL                                      ║
║     • Frontend: HTML5 + Bootstrap + JavaScript                  ║
║     • Audio: librosa + scipy                                    ║
║     • IA: Procesamiento de lenguaje natural                     ║
║                                                                  ║
║  📦 Módulos incluidos:                                          ║
║     • Sistema de autenticación                                  ║
║     • Generador de ejercicios                                   ║
║     • Juegos interactivos                                       ║
║     • Análisis de pronunciación                                 ║
║     • Seguimiento de progreso                                   ║
║     • Retroalimentación personalizada                           ║
║                                                                  ║
║  🚀 Comandos útiles:                                            ║
║     • python start.py      - Iniciar con este menú             ║
║     • python install.py    - Configuración completa            ║
║     • python app.py        - Inicio directo                    ║
║                                                                  ║
║  📞 Soporte:                                                    ║
║     • Revisa los logs en /logs/alfaia.log                      ║
║     • Verifica la configuración en /config/                    ║
║     • Consulta la documentación                                ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""
        print(info)

        # Mostrar estadísticas del proyecto
        print("\n📊 ESTADÍSTICAS DEL PROYECTO:")
        print("-" * 40)

        try:
            # Contar archivos Python
            py_files = list(self.project_root.rglob("*.py"))
            print(f"📝 Archivos Python: {len(py_files)}")

            # Contar templates
            html_files = list(self.project_root.rglob("*.html"))
            print(f"🌐 Templates HTML: {len(html_files)}")

            # Verificar módulos
            modules_dir = self.project_root / "modules"
            if modules_dir.exists():
                module_files = list(modules_dir.glob("*.py"))
                print(f"🧩 Módulos: {len(module_files)}")

            # Tamaño del proyecto
            total_size = sum(f.stat().st_size for f in self.project_root.rglob("*") if f.is_file())
            print(f"💾 Tamaño total: {total_size / (1024 * 1024):.1f} MB")

        except Exception as e:
            print(f"⚠️ Error calculando estadísticas: {e}")

        input("\nPresiona Enter para continuar...")
        return True

    def check_port_availability(self, port=5000):
        """Verificar si el puerto está disponible"""
        import socket

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return True
        except OSError:
            return False

    def get_system_info(self):
        """Obtener información del sistema"""
        import platform

        return {
            'os': platform.system(),
            'version': platform.version(),
            'python': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'architecture': platform.architecture()[0]
        }


def main():
    """Función principal"""
    starter = AlfaIAStarter()

    # Verificar que estamos en el directorio correcto
    if not starter.app_file.exists():
        print("❌ ERROR: No se encuentra app.py")
        print("   Asegúrate de ejecutar este script desde el directorio raíz de AlfaIA")
        sys.exit(1)

    try:
        starter.print_banner()

        # Mostrar información del sistema
        system_info = starter.get_system_info()
        print(f"💻 Sistema: {system_info['os']} | 🐍 Python: {system_info['python']}")

        # Verificar disponibilidad del puerto
        if not starter.check_port_availability():
            print("⚠️ Puerto 5000 ocupado - la aplicación usará otro puerto disponible")

        # Mostrar opciones principales
        starter.show_startup_options()

    except KeyboardInterrupt:
        print("\n\n👋 ¡Hasta luego!")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        print("💡 Intenta ejecutar 'python install.py' para resolver problemas")


if __name__ == "__main__":
    main()

