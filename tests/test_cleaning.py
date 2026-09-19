"""Pruebas de las reglas de limpieza (app/etl/cleaning.py)."""
from datetime import date
from decimal import Decimal

from app.etl.cleaning import (limpiar_estatus, limpiar_fecha, limpiar_monto,
                              limpiar_region, limpiar_texto)


def test_fecha_formatos_validos():
    # Cada formato del reto debe producir la fecha correcta
    assert limpiar_fecha("2026-03-04") == date(2026, 3, 4)
    assert limpiar_fecha("2026-03-04 00:00:00") == date(2026, 3, 4)  # la hora se ignora
    assert limpiar_fecha("04-03-2026") == date(2026, 3, 4)   # día-mes-año: 4 de marzo, no 3 de abril
    assert limpiar_fecha("04/03/2026") == date(2026, 3, 4)


def test_fecha_invalida_se_descarta():
    # Vacías, ilegibles o inexistentes deben devolver None (la fila se descarta)
    for valor in ["2026-13-45", "0000-00-00", "", "   ", "ayer", "31/02/2026", "2026/02/30", None]:
        assert limpiar_fecha(valor) is None, valor


def test_monto_formatos():
    # Todos los formatos de monto del CSV deben quedar como número decimal
    assert limpiar_monto("20591.14") == Decimal("20591.14")
    assert limpiar_monto(" 36010.45 ") == Decimal("36010.45")   # espacios alrededor
    assert limpiar_monto("60,901.75") == Decimal("60901.75")   # coma = miles
    assert limpiar_monto("$82,482.90") == Decimal("82482.90")  # símbolo de moneda
    assert limpiar_monto("72 760.95") == Decimal("72760.95")   # espacio = miles
    assert limpiar_monto("54608,19") == Decimal("54608.19")    # solo coma = decimal
    assert limpiar_monto("4 340.10") == Decimal("4340.10")


def test_monto_invalido_se_descarta():
    # Texto, vacío o negativo deben devolver None
    for valor in ["abc", "N/A", "", "  ", "-3500.00", None]:
        assert limpiar_monto(valor) is None, valor


def test_region_y_estatus():
    # Región: se unifican mayúsculas y espacios
    assert limpiar_region(" Bajío ") == "Bajío"
    assert limpiar_region("BAJÍO") == "Bajío"
    assert limpiar_region("norte") == "Norte"
    assert limpiar_region("  ") is None
    # Estatus: cerrado y cerrada son lo mismo (igual para abierta y cancelada)
    assert limpiar_estatus("Cerrado") == "cerrada"
    assert limpiar_estatus("  cerrada  ") == "cerrada"
    assert limpiar_estatus("CANCELADA") == "cancelada"
    assert limpiar_estatus("Abierto") == "abierta"
    assert limpiar_estatus("otra cosa") is None


def test_vendedor_vacio_es_none():
    # Un vendedor vacío se guarda como None (la fila se conserva)
    assert limpiar_texto("") is None
    assert limpiar_texto("  Ana López ") == "Ana López"
