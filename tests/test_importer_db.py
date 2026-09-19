"""Prueba de la carga a la base de datos (usa SQLite en memoria, no toca ventas.db)."""
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.etl.importer import importar
from app.models import Venta

CSV = Path(__file__).resolve().parent.parent / "data" / "ventas.csv"


def _contar(engine):
    with Session(engine) as db:
        return db.scalar(select(func.count()).select_from(Venta))


def test_importar_guarda_185_filas_y_se_puede_repetir():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    reporte = importar(CSV, engine)
    assert reporte.insertadas == 185
    assert _contar(engine) == 185

    # Importar otra vez, no debe duplicar las filas (el importador vacía la tabla antes de cargar)
    importar(CSV, engine)
    assert _contar(engine) == 185
