from dataclasses import dataclass

from modelos.base import Entidad


@dataclass(kw_only=True)
class Tarifa(Entidad):
    id: int | None = None
    temporada: str
    precio_por_lata: float
    fecha_inicio: str   # AAAA-MM-DD
    fecha_fin: str

    def vigente_en(self, fecha: str) -> bool:
        return self.fecha_inicio <= fecha <= self.fecha_fin

    def se_traslapa_con(self, inicio: str, fin: str) -> bool:
        return self.fecha_inicio <= fin and inicio <= self.fecha_fin

    @staticmethod
    def vigente_para(tarifas: list["Tarifa"], fecha: str) -> "Tarifa | None":
        """Devuelve la tarifa vigente de una fecha (o None si no hay)."""
        return next((t for t in tarifas if t.vigente_en(fecha)), None)
