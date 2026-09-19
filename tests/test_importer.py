"""Prueba de extremo a extremo de la limpieza con el ventas.csv real."""
from decimal import Decimal
from pathlib import Path

from app.etl.importer import leer_y_limpiar

# Ruta del CSV calculada desde la ubicación de este archivo (funciona desde cualquier carpeta)
CSV = Path(__file__).resolve().parent.parent / "data" / "ventas.csv"


def test_reporte_de_limpieza():
    # Los números coinciden con el análisis manual del archivo
    filas, r = leer_y_limpiar(CSV)
    assert r.originales == 218
    assert r.descartadas_fecha == 6
    assert r.descartadas_monto == 5
    assert r.descartadas_region == 4
    assert r.descartadas_otros == 0
    assert r.validas == 203
    assert r.duplicados == 18
    assert len(filas) == 185


def test_sin_duplicados_ni_valores_sucios():
    filas, _ = leer_y_limpiar(CSV)
    # Ningún id_venta se repite
    ids = [f["id_venta"] for f in filas]
    assert len(ids) == len(set(ids))
    # Solo quedan las 5 regiones y los 3 estatus normalizados
    assert {f["region"] for f in filas} == {"Norte", "Sur", "Centro", "Occidente", "Bajío"}
    assert {f["estatus"] for f in filas} == {"cerrada", "abierta", "cancelada"}
    assert all(f["monto"] >= 0 for f in filas)
    assert sum(1 for f in filas if f["vendedor"] is None) >= 1   # vendedor vacío se conserva


def test_kpis_esperados_de_cerradas():
    # Con solo las ventas cerradas, el total debe coincidir con el valor esperado
    filas, _ = leer_y_limpiar(CSV)
    cerradas = [f for f in filas if f["estatus"] == "cerrada"]
    assert len(cerradas) == 106
    assert sum(f["monto"] for f in cerradas) == Decimal("4757842.10")
