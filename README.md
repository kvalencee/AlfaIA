# AlfaIA

AlfaIA es una aplicación web para el aprendizaje de lectura y pronunciación en español. Utiliza Flask, MySQL y procesamiento de audio para ofrecer ejercicios interactivos.

## Requisitos

- Python 3.8 o superior
- MySQL Server
- FFmpeg (para convertir y analizar grabaciones de audio)

## Instalación

1. Clona este repositorio.
2. Instala las dependencias de Python:
   ```bash
   pip install -r AlfaIA/requirements.txt
   ```
3. Crea la base de datos ejecutando el script SQL:
   ```bash
   mysql -u <usuario> -p < AlfaIA/database_structure.sql
   ```
   Ajusta las credenciales en `AlfaIA/modules/database.py` si es necesario.
4. Asegúrate de que FFmpeg esté instalado y accesible desde la línea de comandos.

## Ejecución

Desde la raíz del proyecto, ejecuta:

```bash
python AlfaIA/AlfaIA/app.py
```

El servidor se iniciará en `http://localhost:5000`.

## Notas

- La carpeta `AlfaIA/AlfaIA/uploads/` almacena archivos de audio subidos por los usuarios y puede vaciarse en cualquier momento.
- Si no cuentas con MySQL o las librerías de audio instaladas, la aplicación se ejecutará en **modo demo** con funcionalidad limitada.


