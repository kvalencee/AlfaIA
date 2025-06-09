# debug_login.py - Script para verificar el problema de autenticación

import mysql.connector
import bcrypt


def debug_demo_user():
    """Depurar y corregir el usuario demo"""

    # Configuración de conexión
    config = {
        'host': 'localhost',
        'database': 'alfaia',
        'user': 'alfaia_user',
        'password': 'alfaia2024',
        'port': 3306,
        'charset': 'utf8mb4',
        'auth_plugin': 'mysql_native_password'
    }

    try:
        # Conectar a la base de datos
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)

        print("🔍 DEPURANDO USUARIO DEMO...")
        print("=" * 50)

        # 1. Verificar si el usuario existe
        cursor.execute("SELECT * FROM usuarios WHERE username = %s", ('demo_user',))
        user = cursor.fetchone()

        if user:
            print("✅ Usuario demo_user encontrado:")
            print(f"   ID: {user['id']}")
            print(f"   Username: {user['username']}")
            print(f"   Email: {user['email']}")
            print(f"   Nombre: {user['nombre']} {user['apellido']}")
            print(f"   Hash actual: {user['password_hash'][:50]}...")

            # 2. Verificar la contraseña actual
            test_password = 'demo123'
            print(f"\n🔑 Probando contraseña: {test_password}")

            try:
                # Probar con bcrypt
                if bcrypt.checkpw(test_password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                    print("✅ Contraseña correcta con bcrypt")
                else:
                    print("❌ Contraseña incorrecta con bcrypt")

                    # Crear nuevo hash
                    new_hash = bcrypt.hashpw(test_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

                    # Actualizar en la base de datos
                    cursor.execute(
                        "UPDATE usuarios SET password_hash = %s WHERE username = %s",
                        (new_hash, 'demo_user')
                    )
                    conn.commit()
                    print(f"✅ Hash actualizado: {new_hash[:50]}...")

            except Exception as e:
                print(f"❌ Error con bcrypt: {e}")

                # Fallback a hash simple
                import hashlib
                simple_hash = hashlib.sha256(test_password.encode('utf-8')).hexdigest()

                if user['password_hash'] == simple_hash:
                    print("✅ Contraseña correcta con hash simple")
                else:
                    print("❌ Contraseña incorrecta con hash simple")

                    # Actualizar con hash simple
                    cursor.execute(
                        "UPDATE usuarios SET password_hash = %s WHERE username = %s",
                        (simple_hash, 'demo_user')
                    )
                    conn.commit()
                    print(f"✅ Hash simple actualizado: {simple_hash}")

            # 3. Verificar progreso y configuración
            cursor.execute("SELECT * FROM progreso_usuario WHERE usuario_id = %s", (user['id'],))
            progreso = cursor.fetchone()

            if progreso:
                print("✅ Progreso encontrado")
            else:
                print("❌ Progreso no encontrado, creando...")
                cursor.execute("INSERT INTO progreso_usuario (usuario_id) VALUES (%s)", (user['id'],))
                conn.commit()
                print("✅ Progreso creado")

            cursor.execute("SELECT * FROM configuraciones_usuario WHERE usuario_id = %s", (user['id'],))
            config_user = cursor.fetchone()

            if config_user:
                print("✅ Configuración encontrada")
            else:
                print("❌ Configuración no encontrada, creando...")
                cursor.execute("INSERT INTO configuraciones_usuario (usuario_id) VALUES (%s)", (user['id'],))
                conn.commit()
                print("✅ Configuración creada")

        else:
            print("❌ Usuario demo_user NO encontrado")
            print("🔧 Creando usuario demo...")

            # Crear usuario demo
            try:
                # Hash con bcrypt
                password_hash = bcrypt.hashpw('demo123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            except:
                # Fallback a hash simple
                import hashlib
                password_hash = hashlib.sha256('demo123'.encode('utf-8')).hexdigest()

            cursor.execute("""
                INSERT INTO usuarios (username, email, password_hash, nombre, apellido)
                VALUES (%s, %s, %s, %s, %s)
            """, ('demo_user', 'demo@alfaia.com', password_hash, 'Usuario', 'Demo'))

            user_id = cursor.lastrowid

            # Crear progreso y configuración
            cursor.execute("INSERT INTO progreso_usuario (usuario_id) VALUES (%s)", (user_id,))
            cursor.execute("INSERT INTO configuraciones_usuario (usuario_id) VALUES (%s)", (user_id,))

            conn.commit()
            print("✅ Usuario demo creado completamente")

        # 4. Verificar autenticación final
        cursor.execute("SELECT * FROM usuarios WHERE username = %s", ('demo_user',))
        final_user = cursor.fetchone()

        print(f"\n🧪 PRUEBA FINAL DE AUTENTICACIÓN:")
        print(f"   Username: demo_user")
        print(f"   Password: demo123")

        try:
            if bcrypt.checkpw('demo123'.encode('utf-8'), final_user['password_hash'].encode('utf-8')):
                print("✅ AUTENTICACIÓN EXITOSA")
                return True
            else:
                print("❌ AUTENTICACIÓN FALLIDA")
                return False
        except:
            # Probar hash simple
            import hashlib
            if final_user['password_hash'] == hashlib.sha256('demo123'.encode('utf-8')).hexdigest():
                print("✅ AUTENTICACIÓN EXITOSA (hash simple)")
                return True
            else:
                print("❌ AUTENTICACIÓN FALLIDA (hash simple)")
                return False

    except mysql.connector.Error as e:
        print(f"❌ Error de MySQL: {e}")
        return False
    except Exception as e:
        print(f"❌ Error general: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    debug_demo_user()