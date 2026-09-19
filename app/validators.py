"""Validación de los parámetros de fecha del endpoint.

Solo usa la librería estándar, por eso se puede probar sin levantar la API.
"""
import re
from datetime import date, datetime
from typing import Optional, Tuple

# Formato exacto permitido: 4 dígitos, guion, 2 dígitos, guion, 2 dígitos
_PATRON = re.compile(r"\d{4}-\d{2}-\d{2}")


class ParametroInvalido(ValueError):
    """Error propio: su mensaje se muestra tal cual al cliente (HTTP 400)."""


def _parsear(nombre: str, valor: Optional[str]) -> Optional[date]:
    """Convierte un texto YYYY-MM-DD en una fecha. Si no viene, devuelve None."""
    # Los parámetros son opcionales: si no se enviaron, no hay nada que validar
    if valor is None:
        return None

    # Primero se revisa la forma del texto (evita cosas como "hola" o "2026-1-5")
    if not _PATRON.fullmatch(valor):
        raise ParametroInvalido(f"{nombre} inválida. Use el formato YYYY-MM-DD (ej. 2026-01-31).")

    # Después se revisa que la fecha exista en el calendario (rechaza 2026-02-30)
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except ValueError:
        raise ParametroInvalido(f"{nombre} no es una fecha real del calendario.")


def validar_rango(fecha_inicio: Optional[str], fecha_fin: Optional[str]) -> Tuple[Optional[date], Optional[date]]:
    """Valida ambas fechas y que el rango tenga sentido. Devuelve (inicio, fin)."""
    inicio = _parsear("fecha_inicio", fecha_inicio)
    fin = _parsear("fecha_fin", fecha_fin)

    # Si vienen las dos, el inicio no puede ser posterior al fin
    if inicio and fin and inicio > fin:
        raise ParametroInvalido("fecha_inicio no puede ser posterior a fecha_fin.")
    return inicio, fin
