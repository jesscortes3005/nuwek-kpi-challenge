"""Configuración de la aplicación.

Aquí se leen las variables de entorno definidas en el archivo .env.
Así evitamos escribir datos sensibles (contraseñas, llaves, cadenas de
conexión) directamente en el código, que sí se sube a GitHub.
"""
import os  # sirve para leer variables de entorno

from dotenv import load_dotenv  # carga el contenido del archivo .env

# Carga las variables del archivo .env (si existe) al entorno del programa.
load_dotenv()

# Cadena de conexión a la base de datos.
# Si no existe DATABASE_URL en el .env, se usa un archivo SQLite local (ventas.db).
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ventas.db")
