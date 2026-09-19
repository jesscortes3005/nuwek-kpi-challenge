"""Reglas de limpieza del reto, como funciones puras (solo librería estándar).

Cada función devuelve el valor limpio, o None si el valor debe provocar
que la fila se descarte (según las reglas del reto).
"""
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

# (patrón, formato strptime). El día se valida con strptime: "31/02/2026" falla.
_FORMATOS_FECHA = [
    (re.compile(r"\d{4}-\d{2}-\d{2}( 00:00:00)?"), "%Y-%m-%d"),  # año-mes-día (hora ignorada)
    (re.compile(r"\d{2}-\d{2}-\d{4}"), "%d-%m-%Y"),              # día-mes-año
    (re.compile(r"\d{2}/\d{2}/\d{4}"), "%d/%m/%Y"),              # día-mes-año con diagonales 
]
# Tabla de equivalencias: todas las variantes de estatus apuntan a una sola forma
_ESTATUS = {
    "cerrada": "cerrada", "cerrado": "cerrada",
    "abierta": "abierta", "abierto": "abierta",
    "cancelada": "cancelada", "cancelado": "cancelada",
}


def limpiar_texto(valor: Optional[str]) -> Optional[str]:
    """Quita espacios sobrantes. Vacío -> None."""
    if valor is None:
        return None
    valor = valor.strip()
    return valor or None # "" se considera falso, así que devuelve None


def limpiar_fecha(valor: Optional[str]) -> Optional[date]:
    """Interpreta los formatos de la práctica del reto. Vacía, ilegible o inexistente -> None."""
    valor = limpiar_texto(valor)
    if valor is None:
        return None
    # Se prueba cada formato hasta encontrar el que coincide con la forma del texto
    for patron, formato in _FORMATOS_FECHA:
        if patron.fullmatch(valor):
            try:
                 # valor[:10] se queda solo con la fecha y descarta la hora si la trae
                return datetime.strptime(valor[:10], formato).date()
            except ValueError:  # día/mes que no existen en el calendario
                return None
    return None


def limpiar_monto(valor: Optional[str]) -> Optional[Decimal]:
    """Normaliza a Decimal con 2 decimales. Vacío, no numérico o negativo -> None.

    - Se quitan '$' y espacios.
    - Si hay coma y punto (12,500.50): la coma es separador de miles.
    - Si solo hay coma (12500,50): la coma es el separador decimal.
    """
    if valor is None:
        return None
    # Paso 1: quitar '$' y cualquier espacio (incluye los usados como separador de miles)
    texto = re.sub(r"[$\s]", "", valor)
    if not texto:
        return None
    # Paso 2: decidir qué papel tiene la coma

    if "," in texto and "." in texto:
        texto = texto.replace(",", "") # 12,500.50 -> 12500.50
    elif "," in texto:
        texto = texto.replace(",", ".") # 12500,50 -> 12500.50

        # Paso 3: aceptar solo dígitos con un punto decimal opcional.
    # Esto rechaza 'abc', 'N/A' y también los negativos ('-3500.00').
    if not re.fullmatch(r"\d+(\.\d+)?", texto):
        return None
        # Se usa Decimal (no float) para no acumular errores de redondeo con dinero
    return Decimal(texto).quantize(Decimal("0.01"))


def limpiar_region(valor: Optional[str]) -> Optional[str]:
    """' BAJÍO ' -> 'Bajío'. Vacía -> None."""
    valor = limpiar_texto(valor)
    return valor.capitalize() if valor else None


def limpiar_estatus(valor: Optional[str]) -> Optional[str]:
    """'  Cerrado ' -> 'cerrada'. Valor desconocido -> None."""
    valor = limpiar_texto(valor)
    return _ESTATUS.get(valor.lower()) if valor else None
