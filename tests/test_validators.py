"""Pruebas de la validación de fechas (app/validators.py)."""
from datetime import date

from app.validators import ParametroInvalido, validar_rango


def _falla(inicio, fin):
    """Ayuda: devuelve True si validar_rango lanza ParametroInvalido."""
    try:
        validar_rango(inicio, fin)
    except ParametroInvalido:
        return True
    return False


def test_rango_valido_y_opcional():
    assert validar_rango(None, None) == (None, None)  # ambos parámetros son opcionales
    assert validar_rango("2026-01-01", "2026-03-31") == (date(2026, 1, 1), date(2026, 3, 31))
    # Inicio y fin iguales es un rango válido (un solo día)
    assert validar_rango("2026-03-31", "2026-03-31") == (date(2026, 3, 31), date(2026, 3, 31))


def test_rango_invalido():
    assert _falla("hola", None)                # texto que no es fecha
    assert _falla(None, "2026-02-30")          # no existe en el calendario
    assert _falla("2026-1-5", None)            # formato sin ceros
    assert _falla("", None)                    # cadena vacía
    assert _falla("2026-06-01", "2026-01-01")  # inicio posterior a fin
