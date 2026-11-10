from dataclasses import dataclass

from modelos.base import Entidad


@dataclass(kw_only=True)
class Trabajador(Entidad):
    id: int | None = None
    nombre: str
    identidad: str
    telefono: str
