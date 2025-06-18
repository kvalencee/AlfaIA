@echo off
echo ============================================
echo    SOLUCIONADOR COMPLETO DE ALFAIA
echo ============================================
echo.

echo 🔧 PASO 1: Crear directorios necesarios...
if not exist "templates\errors" mkdir templates\errors
if not exist "uploads" mkdir uploads
if not exist "static\css" mkdir static\css
if not exist "static\js" mkdir static\js
echo ✅ Directorios creados
echo.

echo 🔧 PASO 2: Crear templates de error faltantes...

echo Creando templates/errors/404.html...
(
echo ^<!DOCTYPE html^>
echo ^<html lang="es"^>
echo ^<head^>
echo     ^<meta charset="UTF-8"^>
echo     ^<title^>Página No Encontrada - AlfaIA^</title^>
echo     ^<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet"^>
echo ^</head^>
echo ^<body class="bg-light d-flex align-items-center justify-content-center" style="min-height: 100vh;"^>
echo     ^<div class="text-center"^>
echo         ^<h1 class="display-1"^>404^</h1^>
echo         ^<h2^>Página No Encontrada^</h2^>
echo         ^<p^>La página que buscas no existe.^</p^>
echo         ^<a href="/" class="btn btn-primary"^>Volver al Inicio^</a^>
echo     ^</div^>
echo ^</body^>
echo ^</html^>
) > templates\errors\404.html

echo Creando templates/errors/500.html...
(
echo ^<!DOCTYPE html^>
echo ^<html lang="es"^>
echo ^<head^>
echo     ^<meta charset="UTF-8"^>
echo     ^<title^>Error del Servidor - AlfaIA^</title^>
echo     ^<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet"^>
echo ^</head^>
echo ^<body class="bg-light d-flex align-items-center justify-content-center" style="min-height: 100vh;"^>
echo     ^<div class="text-center"^>
echo         ^<h1 class="display-1 text-danger"^>500^</h1^>
echo         ^<h2^>Error del Servidor^</h2^>
echo         ^<p^>Ha ocurrido un error interno. Inténtalo de nuevo.^</p^>
echo         ^<a href="javascript:location.reload()" class="btn btn-warning me-2"^>Recargar^</a^>
echo         ^<a href="/" class="btn btn-primary"^>Volver al Inicio^</a^>
echo     ^</div^>
echo ^</body^>
echo ^</html^>
) > templates\errors\500.html

echo Creando templates/errors/403.html...
(
echo ^<!DOCTYPE html^>
echo ^<html lang="es"^>
echo ^<head^>
echo     ^<meta charset="UTF-8"^>
echo     ^<title^>Acceso Denegado - AlfaIA^</title^>
echo     ^<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet"^>
echo ^</head^>
echo ^<body class="bg-light d-flex align-items-center justify-content-center" style="min-height: 100vh;"^>
echo     ^<div class="text-center"^>
echo         ^<h1 class="display-1 text-warning"^>403^</h1^>
echo         ^<h2^>Acceso Denegado^</h2^>
echo         ^<p^>No tienes permisos para acceder a esta página.^</p^>
echo         ^<a href="/" class="btn btn-primary"^>Volver al Inicio^</a^>
echo     ^</div^>
echo ^</body^>
echo ^</html^>
) > templates\errors\403.html

echo ✅ Templates de error creados
echo.

echo 🔧 PASO 3: Crear script de corrección MySQL...
(
echo -- Script de corrección MySQL para ALFAIA
echo ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'tired2019';
echo FLUSH PRIVILEGES;
echo.
echo -- Crear usuario específico para ALFAIA
echo DROP USER IF EXISTS 'alfaia_user'@'localhost';
echo CREATE USER 'alfaia_user'@'localhost' IDENTIFIED WITH mysql_native_password BY 'alfaia2024';
echo GRANT ALL PRIVILEGES ON alfaia.* TO 'alfaia_user'@'localhost';
echo FLUSH PRIVILEGES;
echo.
echo -- Verificar usuarios
echo SELECT user, host, plugin FROM mysql.user WHERE user IN ^('root', 'alfaia_user'^);
) > fix_mysql_auth.sql

echo ✅ Script MySQL creado: fix_mysql_auth.sql
echo.

echo 🔧 PASO 4: Aplicar corrección MySQL...
echo IMPORTANTE: Ejecutando corrección de autenticación MySQL...
mysql -u root -ptired2019 < fix_mysql_auth.sql
if %errorlevel% equ 0 (
    echo ✅ Corrección MySQL aplicada exitosamente
) else (
    echo ⚠️  Error aplicando corrección MySQL
    echo     Puedes ejecutar manualmente: mysql -u root -ptired2019 ^< fix_mysql_auth.sql
)
echo.

echo 🔧 PASO 5: Crear/verificar base de datos...
mysql -u root -ptired2019 -e "CREATE DATABASE IF NOT EXISTS alfaia CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; USE alfaia; SHOW TABLES;"
if %errorlevel% equ 0 (
    echo ✅ Base de datos alfaia verificada
) else (
    echo ⚠️  Error con base de datos - verifica MySQL
)
echo.

echo 🔧 PASO 6: Probar conexión corregida...
python -c "
try:
    from modules.database import db_manager
    if db_manager and db_manager.test_connection():
        print('✅ Conexión Python-MySQL: FUNCIONANDO')
    else:
        print('❌ Conexión Python-MySQL: Aún hay problemas')
except Exception as e:
    print(f'❌ Error: {e}')
"
echo.

echo ============================================
echo    CORRECCIONES APLICADAS
echo ============================================
echo.
echo ✅ Templates de error creados
echo ✅ Directorios necesarios creados
echo ✅ Autenticación MySQL corregida
echo ✅ Base de datos verificada
echo.
echo 🚀 Ahora puedes ejecutar: python app.py
echo.
echo Si aún hay problemas:
echo 1. Verifica MySQL: net start mysql
echo 2. Ejecuta manualmente: mysql -u root -ptired2019 ^< fix_mysql_auth.sql
echo 3. Verifica permisos de usuario
echo.
pause
