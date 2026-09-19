"""Endpoint GET /api/ventas/resumen."""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.kpi_service import obtener_resumen
from app.validators import ParametroInvalido, validar_rango
# Todas las rutas de este archivo empiezan con /api/ventas
router = APIRouter(prefix="/api/ventas", tags=["ventas"])

# Los siguientes modelos describen la forma de la respuesta la cual aparece en el Swagger
class TotalRegion(BaseModel):
    region: str
    total: float


class Resumen(BaseModel):
    total_ventas: float
    numero_ventas: int
    por_region: List[TotalRegion]


@router.get("/resumen", response_model=Resumen)
def resumen(
    fecha_inicio: Optional[str] = Query(None, description="YYYY-MM-DD, inclusivo", examples=["2026-01-01"]),
    fecha_fin: Optional[str] = Query(None, description="YYYY-MM-DD, inclusivo", examples=["2026-03-31"]),
    db: Session = Depends(get_db),
):
    """KPIs de ventas **cerradas**. Sin parámetros devuelve todo el histórico."""
    # Los parámetros llegan como texto para responder 400 pero FastAPI usaría 422 por defecto.
    try:
        inicio, fin = validar_rango(fecha_inicio, fecha_fin)
    except ParametroInvalido as error:
         # Parámetros incorrectos: código 400 con un mensaje claro
        return JSONResponse(status_code=400, content={"error": str(error)})
     # Parámetros correctos: se consulta y se devuelve el resumen (código 200)
    return obtener_resumen(db, inicio, fin)
