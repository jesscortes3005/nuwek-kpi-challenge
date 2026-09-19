"""Proceso ETL: ventas.csv -> normalizar -> descartar inválidas -> deduplicar -> BD."""
import csv
from dataclasses import dataclass
from pathlib import Path

from app.etl.cleaning import (
    limpiar_estatus,
    limpiar_fecha,
    limpiar_monto,
    limpiar_region,
    limpiar_texto,
)


@dataclass
class Reporte:
    originales: int = 0
    descartadas_fecha: int = 0
    descartadas_monto: int = 0
    descartadas_region: int = 0
    descartadas_otros: int = 0   # id vacío o estatus desconocido (protegen la PK y el CHECK)
    validas: int = 0
    duplicados: int = 0
    insertadas: int = 0

    @property
    def descartadas(self) -> int:
        return (self.descartadas_fecha + self.descartadas_monto
                + self.descartadas_region + self.descartadas_otros)
    
    # Texto que se imprime en consola al ejecutar el script
    def __str__(self) -> str:
        return (
            f"Registros originales:          {self.originales}\n"
            f"Descartados por fecha:         {self.descartadas_fecha}\n"
            f"Descartados por monto:         {self.descartadas_monto}\n"
            f"Descartados por región vacía:  {self.descartadas_region}\n"
            f"Descartados (otros):           {self.descartadas_otros}\n"
            f"Registros válidos:             {self.validas}\n"
            f"Duplicados eliminados:         {self.duplicados}\n"
            f"Registros insertados:          {self.insertadas}"
        )


def leer_y_limpiar(ruta_csv):
    """Devuelve (filas_limpias, reporte). No toca la base de datos."""
    reporte = Reporte()
    # Diccionario id_venta -> fila. Al usar el id como llave, no puede haber
    # dos filas con el mismo id: así se eliminan los duplicados.
    limpias = {}  
    
    # utf-8-sig: el archivo es UTF-8 sin BOM, pero esta opción tolera uno si apareciera.
    # newline="" es lo que recomienda el módulo csv para leer bien los saltos de línea.
    with open(ruta_csv, encoding="utf-8-sig", newline="") as f:
        for fila in csv.DictReader(f):
            reporte.originales += 1

            # Primera etapa 1: Normalizar (limpiar cada campo con las reglas del reto)
            id_venta = limpiar_texto(fila.get("id_venta"))
            fecha = limpiar_fecha(fila.get("fecha"))
            monto = limpiar_monto(fila.get("monto"))
            region = limpiar_region(fila.get("region"))
            estatus = limpiar_estatus(fila.get("estatus"))

            # 2) Descartar inválidas (se cuenta un solo motivo por fila )
            if fecha is None:
                reporte.descartadas_fecha += 1
                continue # pasa a la siguiente fila 
            if monto is None:
                reporte.descartadas_monto += 1
                continue
            if region is None:
                reporte.descartadas_region += 1
                continue
            if id_venta is None or estatus is None:
                reporte.descartadas_otros += 1
                continue

            reporte.validas += 1

            # 3) Deduplicar por id_venta, conservando la primera aparicion
            if id_venta in limpias:
                reporte.duplicados += 1
                continue

            limpias[id_venta] = {
                "id_venta": id_venta,
                "fecha": fecha,
                "vendedor": limpiar_texto(fila.get("vendedor")),  # vacío -> NULL, la fila se conserva
                "region": region,
                "producto": limpiar_texto(fila.get("producto")),
                "monto": monto,
                "estatus": estatus,
            }

    return list(limpias.values()), reporte


def guardar(filas, reporte, engine=None):
    """Crea la tabla si no existe y la recarga con las filas limpias (idempotente)."""
    # Se importa aquí para poder probar la limpieza sin necesitar la base de datos.
    from sqlalchemy import delete
    from sqlalchemy.orm import Session

    from app.database import Base
    from app.database import engine as engine_por_defecto
    from app.models import Venta

    engine = engine or engine_por_defecto # si no se indica otro, usa el de la configuración
    Base.metadata.create_all(engine)      # crea la tabla ventas solo si todavía no existe
    with Session(engine) as db:
        db.execute(delete(Venta))          # vacía la tabla: así se puede importar varias veces
        db.add_all([Venta(**fila) for fila in filas])  # convierte cada diccionario en una fila
        db.commit()                       # confirma todos los cambios de una vez
    reporte.insertadas = len(filas)
    return reporte


def importar(ruta_csv, engine=None):
    ruta_csv = Path(ruta_csv)
    filas, reporte = leer_y_limpiar(ruta_csv)
    return guardar(filas, reporte, engine)
