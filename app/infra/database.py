"""Conexión a base de datos para la API. Usa DATABASE_URL (PostgreSQL en Docker) o SQLite por defecto."""
import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.repositories.models import Base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./fintech.db"
)
# Ajuste para SQLite (check_same_thread=False para uso con FastAPI)
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=os.getenv("SQL_ECHO", "0") == "1",
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Crea las tablas si no existen."""
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Context manager para obtener una sesión (uso en scripts o tests)."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """Dependency de FastAPI: yield una sesión por request."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
