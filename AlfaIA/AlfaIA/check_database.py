# check_database.py - Verificar estado actual de la base de datos
import mysql.connector


def check_database_status():
    """Verificar qué hay en la base de datos actualmente"""
    print("🔍 VERIFICANDO ESTADO DE LA BASE DE DATOS")
    print("=" * 50)

    try:
        # Conectar
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='tired2019',
            database='alfaia_db',
            charset='utf8mb4'
        )

        cursor = connection.cursor()
        print("✅ Conectado a alfaia_db")

        # Verificar qué tablas existen
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        print(f"\n📋 Tablas encontradas ({len(tables)}):")
        if tables:
            for table in tables:
                print(f"   - {table[0]}")
        else:
            print("   ❌ No hay tablas en la base de datos")
            return False

        # Verificar si existe tabla usuarios
        if any('usuarios' in table for table in tables):
            cursor.execute("SELECT COUNT(*) FROM usuarios")
            user_count = cursor.fetchone()[0]
            print(f"\n👥 Usuarios en la base de datos: {user_count}")

            if user_count > 0:
                cursor.execute("SELECT username, nombre, apellido FROM usuarios LIMIT 5")
                users = cursor.fetchall()
                print("   Usuarios encontrados:")
                for user in users:
                    print(f"   - {user[0]} ({user[1]} {user[2]})")
            else:
                print("   ❌ No hay usuarios en la tabla")
                return False
        else:
            print("   ❌ Tabla 'usuarios' no existe")
            return False

        # Verificar usuario demo específicamente
        cursor.execute("SELECT * FROM usuarios WHERE username = 'demo_user'")
        demo_user = cursor.fetchone()

        if demo_user:
            print(f"\n✅ Usuario demo encontrado: {demo_user[1]} ({demo_user[4]} {demo_user[5]})")
            return True
        else:
            print("\n❌ Usuario demo_user NO encontrado")
            return False

    except mysql.connector.Error as e:
        print(f"❌ Error de base de datos: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    status = check_database_status()

    print("\n" + "=" * 50)
    if status:
        print("✅ BASE DE DATOS COMPLETA - Todo funcionando")
        print("🚀 Puedes usar demo_user / demo123")
    else:
        print("❌ BASE DE DATOS INCOMPLETA")
        print("💡 Necesitas ejecutar el setup de base de datos")
        print("   Ejecuta: python setup_database.py")