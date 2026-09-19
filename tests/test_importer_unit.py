"""Pruebas unitarias del importador con CSV pequeños y armados a mano.

Cada prueba crea su propio CSV temporal, así se ve exactamente qué se está probando.
"""
import csv
import os
import tempfile
from datetime import date
from decimal import Decimal

from app.etl.importer import leer_y_limpiar

ENCABEZADO = ["id_venta", "fecha", "vendedor", "region", "producto", "monto", "estatus"]


def _leer(filas, encoding="utf-8"):
    """Escribe las filas en un CSV temporal, lo procesa y borra el archivo."""
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="", encoding=encoding) as f:
        csv.writer(f).writerows([ENCABEZADO] + filas)
        ruta = f.name
    try:
        return leer_y_limpiar(ruta)
    finally:
        os.remove(ruta)


def test_reporte_con_un_caso_de_cada_tipo():
    filas, r = _leer([
        ["V1", "2026-03-04", "Ana", "norte", "X", "12,500.50", "Cerrado"],
        ["V1", "04/03/2026", " Ana ", "NORTE ", "X", "12500.50", "cerrada"],  # duplicado en otro formato
        ["V2", "ayer", "Luis", "Sur", "Y", "100", "abierta"],                 # fecha inválida
        ["V3", "2026-01-01", "", "Sur", "Y", "abc", "abierta"],               # monto inválido
        ["V4", "2026-01-01", "Luis", "", "Y", "100", "abierta"],              # región vacía
        ["V5", "2026-01-01", "", "Centro", "Y", "54608,19", "cancelada"],     # vendedor vacío: se conserva
    ])
    assert r.originales == 6
    assert (r.descartadas_fecha, r.descartadas_monto, r.descartadas_region) == (1, 1, 1)
    assert r.validas == 3
    assert r.duplicados == 1
    assert [f["id_venta"] for f in filas] == ["V1", "V5"]


def test_el_duplicado_queda_normalizado():
    filas, _ = _leer([
        ["V1", "04-03-2026", " Ana ", " NORTE ", "X", "$12,500.50", "  Cerrado "],
    ])
    v = filas[0]
    assert v["fecha"] == date(2026, 3, 4)
    assert v["region"] == "Norte"
    assert v["estatus"] == "cerrada"
    assert v["monto"] == Decimal("12500.50")
    assert v["vendedor"] == "Ana"


def test_vendedor_vacio_se_guarda_como_none():
    filas, _ = _leer([["V5", "2026-01-01", "", "Centro", "Y", "54608,19", "cancelada"]])
    assert filas[0]["vendedor"] is None
    assert filas[0]["monto"] == Decimal("54608.19")


def test_fila_invalida_no_bloquea_a_su_duplicado_valido():
    # Primero se descartan las inválidas y después se deduplica:
    # la copia válida de V9 debe sobrevivir aunque la primera aparición era inválida.
    filas, r = _leer([
        ["V9", "0000-00-00", "Ana", "Sur", "X", "100", "cerrada"],
        ["V9", "2026-02-01", "Ana", "Sur", "X", "100", "cerrada"],
    ])
    assert r.descartadas_fecha == 1
    assert len(filas) == 1 and filas[0]["fecha"] == date(2026, 2, 1)


def test_acentos_se_conservan_en_utf8():
    filas, _ = _leer([["V1", "2026-01-01", "Efraín Soto", "BAJÍO", "Implementación", "10", "cerrada"]])
    assert filas[0]["region"] == "Bajío"
    assert filas[0]["vendedor"] == "Efraín Soto"
    assert filas[0]["producto"] == "Implementación"


def test_tolera_un_bom_al_inicio():
    filas, _ = _leer([["V1", "2026-01-01", "Ana", "Sur", "X", "10", "cerrada"]], encoding="utf-8-sig")
    assert len(filas) == 1  # sin utf-8-sig, la primera columna se llamaría "\ufeffid_venta" y fallaría
