# fix_demo_message.py - Arreglar el mensaje de modo demo
import re


def fix_app_context():
    """Arreglar el contexto de templates en app.py"""
    print("🔧 ARREGLANDO CONTEXTO DE TEMPLATES")
    print("=" * 40)

    # Leer el archivo app.py actual
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Buscar la función inject_global_vars y reemplazarla
    old_pattern = r'@app\.context_processor\ndef inject_global_vars\(\):\s*"""[^"]*"""\s*return\s*\{[^}]*\}'

    new_context = '''@app.context_processor
def inject_global_vars():
    """Inyectar variables globales a todos los templates"""
    return {
        'DB_AVAILABLE': DB_AVAILABLE,
        'db_available': DB_AVAILABLE,  # Para compatibilidad con templates
        'JUEGOS_AVAILABLE': EJERCICIOS_AVAILABLE,
        'current_year': datetime.now().year,
        'current_user': get_current_user()
    }'''

    # Reemplazar
    if '@app.context_processor' in content:
        # Encontrar y reemplazar el contexto existente
        content = re.sub(old_pattern, new_context, content, flags=re.DOTALL)
    else:
        # Agregar antes del main
        content = content.replace('if __name__ == \'__main__\':',
                                  f'{new_context}\n\n# ==================== MAIN ====================\n\nif __name__ == \'__main__\':')

    # Guardar el archivo actualizado
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("✅ Contexto de templates actualizado")


def fix_dashboard_route():
    """Arreglar la ruta del dashboard para pasar las variables correctas"""
    print("🔧 ARREGLANDO RUTA DASHBOARD")

    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Buscar la función dashboard y asegurar que pase db_available
    dashboard_pattern = r'(return render_template\(\'dashboard\.html\',.*?)\)'

    # Verificar si ya incluye db_available
    if 'db_available=' not in content:
        # Reemplazar el render_template del dashboard
        def replace_dashboard(match):
            original = match.group(1)
            if 'db_available=' not in original:
                # Agregar db_available al render_template
                return original + ',\n                           db_available=DB_AVAILABLE)'
            return original + ')'

        content = re.sub(dashboard_pattern, replace_dashboard, content, flags=re.DOTALL)

        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ Ruta dashboard actualizada")
    else:
        print("✅ Ruta dashboard ya está correcta")


def fix_login_route():
    """Arreglar la ruta de login"""
    print("🔧 ARREGLANDO RUTA LOGIN")

    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Buscar el render_template de login
    login_pattern = r'return render_template\(\'login\.html\'\)'

    if 'return render_template(\'login.html\')' in content:
        content = content.replace(
            'return render_template(\'login.html\')',
            'return render_template(\'login.html\', db_available=DB_AVAILABLE)'
        )

        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ Ruta login actualizada")
    else:
        print("✅ Ruta login ya está correcta")


def main():
    """Ejecutar todas las correcciones"""
    print("🔧 ARREGLANDO MENSAJE DE MODO DEMO")
    print("=" * 50)

    try:
        # 1. Arreglar contexto global
        fix_app_context()

        # 2. Arreglar ruta dashboard
        fix_dashboard_route()

        # 3. Arreglar ruta login
        fix_login_route()

        print("\n" + "=" * 50)
        print("✅ CORRECCIONES COMPLETADAS")
        print("=" * 50)
        print("🔄 Reinicia el servidor:")
        print("   python app.py")
        print("\n💡 Ahora el mensaje de 'Modo Demo' solo aparecerá")
        print("   cuando realmente no haya base de datos disponible")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()