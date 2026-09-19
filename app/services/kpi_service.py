"""Consultas de KPIs (lógica de negocio). Solo cuentan las ventas con estatus 'cerrada'."""
from datetime import date
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Venta


def obtener_resumen(db: Session, fecha_inicio: Optional[date] = None, fecha_fin: Optional[date] = None) -> dict:
    """Calcula total vendido, número de ventas y total por región."""

    # Paso 1: armar los filtros. Siempre se exige estatus 'cerrada' (regla del reto).
    filtros = [Venta.estatus == "cerrada"]
    if fecha_inicio:
        filtros.append(Venta.fecha >= fecha_inicio)   # >= porque el rango es inclusivo
    if fecha_fin:
        filtros.append(Venta.fecha <= fecha_fin)      # <= porque el rango es inclusivo

    # Paso 2: totales generales. coalesce evita None cuando no hay ventas (devuelve 0).
    numero, total = db.execute(
        select(func.count(), func.coalesce(func.sum(Venta.monto), 0)).where(*filtros)
    ).one()

    # Paso 3: total por región, de mayor a menor.
    # Si dos regiones empatan, la región (A-Z) desempata para que el orden sea estable.
    total_region = func.sum(Venta.monto).label("total")
    filas = db.execute(
        select(Venta.region, total_region)
        .where(*filtros)
        .group_by(Venta.region)
        .order_by(total_region.desc(), Venta.region)
    ).all()

    # Paso 4: armar la respuesta, redondeando a 2 decimales
    return {
        "total_ventas": round(float(total), 2),
        "numero_ventas": numero,
        "por_region": [{"region": r, "total": round(float(t), 2)} for r, t in filas],
    }
