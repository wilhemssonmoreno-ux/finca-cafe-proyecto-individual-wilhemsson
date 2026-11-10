"""Conexión a SQLite, rutas de trabajo y creación de la base desde crear_bd.sql."""
import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def ruta_bd() -> Path:
    return Path(os.environ.get("FINCA_DB", BASE_DIR / "finca.db"))


def carpeta_respaldos() -> Path:
    return Path(os.environ.get("FINCA_RESPALDOS", BASE_DIR / "respaldos"))


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(ruta_bd(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db():
    """Dependencia de FastAPI: una conexión por petición."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def inicializar_bd(forzar: bool = False) -> None:
    """Crea finca.db con crear_bd.sql si todavía no existe (o si se fuerza)."""
    ruta = ruta_bd()
    if ruta.exists() and not forzar:
        return
    ruta.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(ruta)
    try:
        conn.executescript((BASE_DIR / "crear_bd.sql").read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()
