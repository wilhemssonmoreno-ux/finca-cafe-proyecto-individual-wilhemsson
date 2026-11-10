from dataclasses import dataclass

from modelos.base import Entidad


@dataclass(kw_only=True)
class Cosecha(Entidad):
    id: int | None = None
    lote_id: int
    trabajador_id: int
    fecha: str
    latas: int

    def calcular_pago(self, precio_por_lata: float) -> float:
        """Pago por jornal = latas x tarifa vigente de la fecha."""
        return round(self.latas * precio_por_lata, 2)
