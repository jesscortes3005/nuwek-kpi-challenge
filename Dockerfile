# Imagen base de Python, ligera
FROM python:3.12-slim

# Evita archivos .pyc y hace que los logs salgan al momento
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Primero solo requirements.txt: así Docker reutiliza la instalación
# de librerías si el código cambia pero las dependencias no
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Después se copia el resto del proyecto (lo que excluye .dockerignore no entra)
COPY . .

EXPOSE 8000

# Al arrancar: importa el CSV (crea ventas.db) y luego levanta la API.
# La importación es idempotente, así que se puede repetir sin duplicar datos.
# El puerto sale de la variable PORT (la usan plataformas como Render);
# si no existe, usa 8000, como en local.
CMD ["sh", "-c", "python -m scripts.import_ventas && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
