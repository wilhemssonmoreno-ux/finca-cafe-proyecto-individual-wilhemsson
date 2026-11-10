"""Respaldo de la base en segundo plano (hilos)."""
import sqlite3
import threading
from datetime import datetime

from database import carpeta_respaldos, ruta_bd


def nombre_respaldo() -> str:
    return f"finca_{datetime.now():%Y%m%d_%H%M%S}.db"


def hacer_respaldo(nombre: str | None = None, conservar: int = 10):
    """Copia la base con la API de respaldo de SQLite (segura aunque haya escrituras)."""
    carpeta = carpeta_respaldos()
    carpeta.mkdir(parents=True, exist_ok=True)
    destino = carpeta / (nombre or nombre_respaldo())
    origen, copia = sqlite3.connect(ruta_bd()), sqlite3.connect(destino)
    try:
        origen.backup(copia)
    finally:
        copia.close()
        origen.close()
    for viejo in sorted(carpeta.glob("finca_*.db"))[:-conservar]:
        viejo.unlink(missing_ok=True)
    return destino


def lanzar_respaldo_en_hilo() -> tuple[str, threading.Thread]:
    """Respaldo manual: responde de inmediato y el hilo termina la copia solo."""
    nombre = nombre_respaldo()
    hilo = threading.Thread(target=hacer_respaldo, kwargs={"nombre": nombre}, daemon=True,
                            name="respaldo-manual")
    hilo.start()
    return nombre, hilo


def listar_respaldos() -> list[dict]:
    carpeta = carpeta_respaldos()
    if not carpeta.exists():
        return []
    return [
        {"archivo": p.name, "kb": round(p.stat().st_size / 1024, 1)}
        for p in sorted(carpeta.glob("finca_*.db"), reverse=True)
    ]


class HiloRespaldo(threading.Thread):
    """Respalda al iniciar y luego cada cierto tiempo mientras la API esté encendida."""

    def __init__(self, intervalo_segundos: int = 3600, conservar: int = 10):
        super().__init__(name="hilo-respaldo", daemon=True)
        self.intervalo = intervalo_segundos
        self.conservar = conservar
        self._parar = threading.Event()

    def run(self):
        hacer_respaldo(conservar=self.conservar)
        while not self._parar.wait(self.intervalo):
            hacer_respaldo(conservar=self.conservar)

    def detener(self):
        self._parar.set()
