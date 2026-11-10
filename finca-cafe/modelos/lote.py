from dataclasses import dataclass

from modelos.base import Entidad


@dataclass(kw_only=True)
class Lote(Entidad):
    id: int | None = None
    nombre: str
    variedad: str
    hectareas: float

    def rendimiento(self, latas: int) -> float:
        """Latas cosechadas por hectárea."""
        return round(latas / self.hectareas, 2) if self.hectareas else 0.0

    def productividad(self, quintales: float) -> float:
        """Quintales de café procesado por hectárea."""
        return round(quintales / self.hectareas, 2) if self.hectareas else 0.0
