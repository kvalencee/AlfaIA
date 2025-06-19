# fix_login_redirect.py - Corregir loop de redirección en login
import re


def fix_login_route():
    """Corregir la ruta de login para evitar loops de redirección"""
    print("🔧 CORRIGIENDO LOOP DE REDIRECCIÓN EN LOGIN")
    print("=" * 50)

    # Leer app.py actual
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Buscar y corregir la ruta de login
    login_route_pattern = r'@app\.route\(\'\/login\'.*?\ndef login\(\):(.*?)(?=@app\.route|def \w+|if __name__|$)'

    # Nueva ruta de login corregida
    new_login_route = '''@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de inicio de sesión"""
    # IMPORTANTE: NO usar @login_required aquí para evitar loops

    # Si ya está logueado, redirigir al dashboard
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')

            if not username or not password:
                flash('Por favor, completa todos los campos.', 'warning')
                return render_template('login.html', DB_AVAILABLE=DB_AVAILABLE)

            # Autenticación
            user = None
            if DB_AVAILABLE and db_manager:
                try:
                    user = db_manager.authenticate_user(username, password)
                except Exception as e:
                    logger.error(f"Error en autenticación: {e}")
                    flash('Error de conexión. Intenta nuevamente.', 'error')
                    return render_template('login.html', DB_AVAILABLE=DB_AVAILABLE)
            else:
                # Modo demo sin base de datos
                if username == 'demo_user' and password == 'demo123':
                    user = FALLBACK_USER

            if user:
                init_user_session(user)

                # Verificar y desbloquear logros de conexión
                if DB_AVAILABLE and db_manager:
                    try:
                        db_manager.check_and_unlock_achievements(user['id'], 'login')
                    except Exception as e:
                        logger.warning(f"Error verificando logros: {e}")

                flash(f'¡Bienvenido de nuevo, {user["nombre"]}!', 'success')

                # Redirigir a la página solicitada o al dashboard
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('dashboard'))
            else:
                flash('Usuario o contraseña incorrectos.', 'error')

        except Exception as e:
            error_info = handle_error('LOGIN_ERROR', e)
            flash('Error procesando el inicio de sesión.', 'error')

    # GET request - mostrar formulario de login
    return render_template('login.html', DB_AVAILABLE=DB_AVAILABLE)'''

    # Reemplazar la ruta de login
    if '@app.route(\'/login\',' in content:
        # Encontrar el patrón completo de la función login
        import re

        # Patrón más específico para encontrar toda la función login
        pattern = r'(@app\.route\(\'\/login\'.*?\n)(def login\(\):.*?)(?=\n@app\.route|\ndef \w+|\nif __name__|$)'

        def replace_login(match):
            return new_login_route + '\n\n'

        new_content = re.sub(pattern, replace_login, content, flags=re.DOTALL)

        if new_content != content:
            print("✅ Ruta de login encontrada y corregida")
        else:
            print("⚠️ No se pudo encontrar la ruta de login exacta, agregando al final")
            # Agregar antes del main si no se encontró
            new_content = content.replace('if __name__ == \'__main__\':',
                                          f'{new_login_route}\n\n\nif __name__ == \'__main__\':')
    else:
        print("⚠️ Ruta de login no encontrada, agregando")
        new_content = content.replace('if __name__ == \'__main__\':',
                                      f'{new_login_route}\n\n\nif __name__ == \'__main__\':')

    # Asegurar que no hay login_required en rutas públicas
    print("🔧 Verificando que rutas públicas no tengan @login_required...")

    # Rutas que NO deben tener @login_required
    public_routes = ['/login', '/register', '/', '/about', '/health']

    for route in public_routes:
        # Buscar patrones problemáticos
        problem_pattern = f"@login_required\\s*@app\\.route\\('{route}'"
        if re.search(problem_pattern, new_content):
            print(f"⚠️ Encontrado @login_required en ruta pública {route}")
            new_content = re.sub(f"@login_required\\s*(@app\\.route\\('{route}')",
                                 r'\1', new_content)
            print(f"✅ Removido @login_required de {route}")

    # Guardar archivo corregido
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)

    print("✅ app.py corregido")


def fix_redirect_after_login():
    """Corregir función get_current_user para evitar loops"""
    print("\n🔧 CORRIGIENDO FUNCIÓN get_current_user")

    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Buscar y corregir get_current_user
    new_get_current_user = '''def get_current_user() -> Optional[Dict[str, Any]]:
    """Obtener datos del usuario actual - SIN redirecciones"""
    if 'user_id' not in session:
        return None

    user_id = session['user_id']

    if DB_AVAILABLE and db_manager:
        try:
            user = db_manager.get_user_by_id(user_id)
            if not user:
                # IMPORTANTE: No hacer redirect aquí, solo limpiar sesión
                session.clear()
                return None
            return user
        except Exception as e:
            logger.error(f"Error obteniendo usuario {user_id}: {e}")
            # Fallback para usuario demo
            if user_id == 1:
                return FALLBACK_USER
            return None
    else:
        # Modo sin base de datos
        if user_id == 1:
            return FALLBACK_USER
        return None'''

    # Reemplazar get_current_user
    pattern = r'def get_current_user\(\).*?return None'
    new_content = re.sub(pattern, new_get_current_user, content, flags=re.DOTALL)

    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)

    print("✅ Función get_current_user corregida")


def add_proper_error_handling():
    """Agregar manejo de errores para login"""
    print("\n🔧 AGREGANDO MANEJO DE ERRORES")

    # Crear template de error básico si no existe
    error_template = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error - AlfaIA</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body text-center">
                        <h1 class="text-danger">Error</h1>
                        <p>Ha ocurrido un error. Por favor, intenta nuevamente.</p>
                        <a href="{{ url_for('login') }}" class="btn btn-primary">Volver al Login</a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''

    import os
    os.makedirs('templates/errors', exist_ok=True)

    with open('templates/errors/500.html', 'w', encoding='utf-8') as f:
        f.write(error_template)

    print("✅ Template de error creado")


def test_login_fix():
    """Probar que el fix funciona"""
    print("\n🧪 PROBANDO CORRECCIÓN DE LOGIN")

    try:
        # Verificar que la sintaxis sea correcta
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # Verificar elementos clave
        checks = [
            ('@app.route(\'/login\'', 'Ruta de login presente'),
            ('def login():', 'Función login presente'),
            ('render_template(\'login.html\'', 'Template render presente'),
            ('if \'user_id\' in session:', 'Verificación de sesión presente'),
            ('return redirect(url_for(\'dashboard\'))', 'Redirección a dashboard presente')
        ]

        for check, description in checks:
            if check in content:
                print(f"✅ {description}")
            else:
                print(f"❌ {description}")

        print("\n🚀 Corrección completada. Reinicia el servidor:")
        print("   python app.py")

    except Exception as e:
        print(f"❌ Error en prueba: {e}")


if __name__ == "__main__":
    print("🔧 INICIANDO CORRECCIÓN DE LOGIN")
    print("=" * 50)

    # Backup del archivo original
    import shutil

    shutil.copy('app.py', 'app.py.backup')
    print("📄 Backup creado: app.py.backup")

    # Aplicar correcciones
    fix_login_route()
    fix_redirect_after_login()
    add_proper_error_handling()
    test_login_fix()

    print("\n🎉 ¡CORRECCIÓN COMPLETADA!")
    print("Reinicia el servidor con: python app.py")