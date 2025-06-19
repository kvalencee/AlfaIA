# fix_demo_password.py - Arreglar contraseña del usuario demo
import mysql.connector
import bcrypt


def fix_demo_password():
    """Actualizar la contraseña del usuario demo"""
    print("🔧 ARREGLANDO CONTRASEÑA DEL USUARIO DEMO")
    print("=" * 50)

    try:
        # Conectar a la base de datos
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='tired2019',
            database='alfaia_db',
            charset='utf8mb4'
        )

        cursor = connection.cursor()
        print("✅ Conectado a alfaia_db")

        # Generar nuevo hash para 'demo123'
        password = 'demo123'
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        print(f"🔐 Generando nuevo hash para: {password}")
        print(f"   Nuevo hash: {password_hash[:30]}...")

        # Actualizar la contraseña del usuario demo
        update_query = """
            UPDATE usuarios 
            SET password_hash = %s 
            WHERE username = 'demo_user'
        """

        cursor.execute(update_query, (password_hash,))

        if cursor.rowcount > 0:
            connection.commit()
            print("✅ Contraseña actualizada exitosamente")

            # Verificar la actualización
            cursor.execute("SELECT username, password_hash FROM usuarios WHERE username = 'demo_user'")
            result = cursor.fetchone()
            print(f"✅ Verificación: {result[0]} - Hash: {result[1][:30]}...")

            return True
        else:
            print("❌ No se pudo actualizar la contraseña")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()


def test_new_password():
    """Probar la nueva contraseña"""
    print("\n🧪 PROBANDO NUEVA CONTRASEÑA")
    print("=" * 30)

    try:
        from modules.config import get_database_config
        from modules.database_manager import DatabaseManager

        # Inicializar Database Manager
        db_config = get_database_config()
        db_manager = DatabaseManager(db_config)

        # Probar autenticación
        user = db_manager.authenticate_user("demo_user", "demo123")

        if user:
            print("✅ AUTENTICACIÓN EXITOSA")
            print(f"   Usuario: {user['username']}")
            print(f"   Nombre: {user['nombre']} {user['apellido']}")
            return True
        else:
            print("❌ Autenticación aún falla")
            return False

    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False


if __name__ == "__main__":
    # Arreglar contraseña
    if fix_demo_password():
        # Probar nueva contraseña
        if test_new_password():
            print("\n🎉 ¡PROBLEMA SOLUCIONADO!")
            print("🚀 Ahora puedes hacer login con:")
            print("   Usuario: demo_user")
            print("   Contraseña: demo123")
            print("\n💡 Reinicia el servidor: python app.py")
        else:
            print("\n❌ Aún hay problemas con la autenticación")
    else:
        print("\n❌ No se pudo arreglar la contraseña")