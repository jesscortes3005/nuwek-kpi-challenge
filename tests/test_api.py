"""Pruebas del endpoint con una BD SQLite en memoria (no toca ventas.db)."""
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Venta

# Datos de prueba: (id, fecha, región, monto, estatus).
# Solo V1, V2, V4 y V6 son cerradas, así que solo esas deben contarse.
DATOS = [
    ("V1", date(2026, 1, 10), "Norte", 100.00, "cerrada"),
    ("V2", date(2026, 3, 31), "Sur", 300.50, "cerrada"),
    ("V3", date(2026, 4, 1), "Sur", 999.00, "abierta"),       # abierta: no debe contarse
    ("V4", date(2026, 2, 15), "Norte", 50.25, "cerrada"),
    ("V5", date(2026, 5, 1), "Centro", 700.00, "cancelada"),  # cancelada: no debe contarse
    ("V6", date(2026, 6, 30), "Centro", 200.00, "cerrada"),
]


@pytest.fixture()
def client():
    """Prepara un cliente de pruebas con una base de datos temporal en memoria."""
    # StaticPool mantiene una sola conexión, necesaria para que la BD en memoria no desaparezca
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add_all([Venta(id_venta=i, fecha=f, vendedor=None, region=r, producto="X", monto=m, estatus=e)
                    for i, f, r, m, e in DATOS])
        db.commit()

    def _get_db():
        with Session(engine) as db:
            yield db

    # Se reemplaza la BD real por la de pruebas
    app.dependency_overrides[get_db] = _get_db
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()  # se restaura la configuración original al terminar


def test_sin_filtros_solo_cerradas_y_orden_descendente(client):
    r = client.get("/api/ventas/resumen")
    assert r.status_code == 200
    assert r.json() == {
        "total_ventas": 650.75,
        "numero_ventas": 4,
        "por_region": [  # de mayor a menor total
            {"region": "Sur", "total": 300.5},
            {"region": "Centro", "total": 200.0},
            {"region": "Norte", "total": 150.25},
        ],
    }


def test_filtro_por_rango(client):
    r = client.get("/api/ventas/resumen?fecha_inicio=2026-01-01&fecha_fin=2026-03-31")
    assert r.status_code == 200
    assert r.json()["numero_ventas"] == 3
    assert r.json()["total_ventas"] == 450.75


def test_rango_inclusivo_en_ambos_extremos(client):
    # V2 ocurrió exactamente el 2026-03-31: debe incluirse cuando ese día es inicio y fin
    r = client.get("/api/ventas/resumen?fecha_inicio=2026-03-31&fecha_fin=2026-03-31")
    assert r.json()["numero_ventas"] == 1
    assert r.json()["total_ventas"] == 300.5


def test_periodo_sin_ventas(client):
    # Un periodo sin ventas no es error: responde 200 con ceros
    r = client.get("/api/ventas/resumen?fecha_inicio=2030-01-01")
    assert r.status_code == 200
    assert r.json() == {"total_ventas": 0, "numero_ventas": 0, "por_region": []}


@pytest.mark.parametrize("query", [
    "fecha_inicio=hola",                            # no es una fecha
    "fecha_fin=2026-02-30",                         # día inexistente
    "fecha_inicio=2026-06-01&fecha_fin=2026-01-01", # inicio posterior a fin
])
def test_parametros_invalidos_devuelven_400(client, query):
    r = client.get(f"/api/ventas/resumen?{query}")
    assert r.status_code == 400
    assert "error" in r.json()


def test_error_interno_no_expone_detalles(client):
    # Simula una falla interna cuyo mensaje contiene datos sensibles
    def _roto():
        raise RuntimeError("password=SECRETO host=db.interno")
        yield  # pragma: no cover

    app.dependency_overrides[get_db] = _roto
    r = client.get("/api/ventas/resumen")
    # El cliente solo debe ver un mensaje genérico, sin secretos ni trazas
    assert r.status_code == 500
    assert r.json() == {"error": "Error interno del servidor."}
    assert "SECRETO" not in r.text and "Traceback" not in r.text
