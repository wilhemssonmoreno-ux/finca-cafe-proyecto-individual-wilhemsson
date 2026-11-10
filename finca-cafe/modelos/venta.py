from dataclasses import dataclass

from modelos.base import Entidad


@dataclass(kw_only=True)
class VentaCafe(Entidad):
    id: int | None = None
    fecha: str
    comprador: str
    quintales: float
    precio_quintal: float

    def total(self) -> float:
        return round(self.quintales * self.precio_quintal, 2)

    def a_dict(self) -> dict:
        datos = super().a_dict()
        datos["total"] = self.total()
        return datos
