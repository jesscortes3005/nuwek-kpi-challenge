"""Modelo de la tabla `ventas` (cómo se representa en Python cada fila de la BD)."""
from datetime import date
from typing import Optional

from sqlalchemy import CheckConstraint, Date, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Venta(Base):
    __tablename__ = "ventas"  # nombre real de la tabla en la base de datos

    # Restricciones e índice de la tabla
    __table_args__ = (
        # La base de datos rechaza montos negativos
        CheckConstraint("monto >= 0", name="ck_ventas_monto_no_negativo"),
        # Solo se aceptan los tres estatus normalizados
        CheckConstraint(
            "estatus IN ('cerrada','abierta','cancelada')", name="ck_ventas_estatus"
        ),
        # Acelera la consulta principal: WHERE estatus = 'cerrada' AND fecha ...
        Index("idx_ventas_estatus_fecha", "estatus", "fecha"),
    )

    # Clave primaria: no puede haber dos ventas con el mismo id_venta (evita duplicados)
    id_venta: Mapped[str] = mapped_column(String, primary_key=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    # El vendedor puede venir vacío, por eso acepta NULL (el reto conserva esas filas)
    vendedor: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    region: Mapped[str] = mapped_column(String, nullable=False)
    # El reto no define regla de descarte para producto, así que acepta NULL
    producto: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    # asdecimal=False: SQLite no soporta Decimal de forma nativa, así que se devuelve
    # como float y se redondea a 2 decimales al responder
    monto: Mapped[float] = mapped_column(Numeric(12, 2, asdecimal=False), nullable=False)
    estatus: Mapped[str] = mapped_column(String, nullable=False)
