from dataclasses import dataclass

from modelos.base import Entidad


@dataclass(kw_only=True)
class ProduccionCafe(Entidad):
    """Café procesado de un lote que ya está en bodega, listo para vender."""
    id: int | None = None
    lote_id: int
    fecha: str
    quintales: float
