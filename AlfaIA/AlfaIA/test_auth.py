# test_auth.py - Probar autenticación directamente
from modules.config import get_database_config
from modules.database_manager import DatabaseManager


def test_authentication():
    """Probar si la autenticación funciona"""
    print("🔐 PROBANDO AUTENTICACIÓN")
    print("=" * 40)

    try:
        # Inicializar Database Manager
        db_config = get_database_config()
        db_manager = DatabaseManager(db_config)
        print("✅ Database Manager inicializado")

        # Probar autenticación
        username = "demo_user"
        password = "demo123"

        print(f"🧪 Probando login: {username} / {password}")

        user = db_manager.authenticate_user(username, password)

        if user:
            print("✅ AUTENTICACIÓN EXITOSA")
            print(f"   Usuario: {user['username']}")
            print(f"   Nombre: {user['nombre']} {user['apellido']}")
            print(f"   Email: {user['email']}")
            print(f"   ID: {user['id']}")
            return True
        else:
            print("❌ AUTENTICACIÓN FALLÓ")
            print("   El usuario existe pero la contraseña no coincide")

            # Verificar si el usuario existe
            try:
                query = "SELECT username, password_hash FROM usuarios WHERE username = %s"
                result = db_manager.execute_query(query, (username,), fetch='one')
                if result:
                    print(f"   Usuario encontrado: {result['username']}")
                    print(f"   Hash almacenado: {result['password_hash'][:20]}...")
                else:
                    print("   Usuario no encontrado en la BD")
            except Exception as e:
                print(f"   Error verificando usuario: {e}")

            return False

    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    success = test_authentication()

    print("\n" + "=" * 40)
    if success:
        print("✅ AUTENTICACIÓN FUNCIONANDO")
        print("💡 El problema puede estar en el app.py")
    else:
        print("❌ PROBLEMA CON AUTENTICACIÓN")
        print("💡 Necesitamos arreglar el hash de contraseña")