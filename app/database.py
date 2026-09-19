"""Conexión a la base de datos y manejo de sesiones con SQLAlchemy."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import DATABASE_URL

# SQLite solo permite usar una conexión en el hilo que la creó, pero FastAPI
# atiende las peticiones en varios hilos. Este parámetro lo permite.
# Con otros motores (por ejemplo PostgreSQL) no hace falta, por eso queda vacío.
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# El "engine" es el objeto que administra la conexión con la base de datos.
engine = create_engine(DATABASE_URL, connect_args=_connect_args)

# Fábrica de sesiones: cada sesión es una "conversación" con la base de datos.
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    """Clase base de la que heredan todos los modelos (tablas)."""


def get_db():
    """Dependencia de FastAPI: abre una sesión por petición y la cierra al terminar."""
    db = SessionLocal()
    try:
        yield db  # FastAPI entrega la sesión al endpoint que la pidió
    finally:
        db.close()  # se ejecuta siempre, aunque haya ocurrido un error
