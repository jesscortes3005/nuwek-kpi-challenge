"""Aplicación FastAPI. Se ejecuta con:  uvicorn app.main:app --reload"""
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import ventas

# Logger para registrar errores en el servidor (no en la respuesta al cliente)
logger = logging.getLogger("nuwek-kpi")

# Crea la aplicación; el título y la descripción aparecen en Swagger (/docs)
app = FastAPI(title="Nuwek KPI API", version="1.0.0",
              description="API sencilla para consultar KPIs de ventas cerradas.")

# Registra las rutas definidas en app/api/ventas.py
app.include_router(ventas.router)


@app.exception_handler(Exception)
async def error_interno(request: Request, exc: Exception):
    """Captura cualquier error inesperado y responde con un mensaje genérico."""
    # El detalle (traza, cadena de conexión, etc.) queda SOLO en el log del servidor.
    logger.exception("Error no controlado en %s", request.url.path)
    # Al cliente nunca se le muestran contraseñas, credenciales ni trazas de stack
    return JSONResponse(status_code=500, content={"error": "Error interno del servidor."})
