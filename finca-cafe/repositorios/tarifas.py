from excepciones import ErrorDeNegocio
from modelos import Tarifa
from repositorios.base import RepositorioBase


class RepositorioTarifas(RepositorioBase):
    tabla = "tarifas"
    modelo = Tarifa
    columnas = ("temporada", "precio_por_lata", "fecha_inicio", "fecha_fin")
    busqueda = ("temporada",)
    nombre_singular = "la tarifa"
    orden = "fecha_inicio"
    mensajes_unicos = {"tarifas.temporada": "Ya existe una tarifa con ese nombre de temporada."}

    def vigente_en(self, fecha: str) -> Tarifa | None:
        return Tarifa.vigente_para(self.listar(), fecha)

    def validar(self, datos, id_actual=None):
        for otra in self.listar():
            if otra.id != id_actual and otra.se_traslapa_con(datos["fecha_inicio"], datos["fecha_fin"]):
                raise ErrorDeNegocio(
                    f"Las fechas se traslapan con la temporada «{otra.temporada}». "
                    "Dos tarifas no pueden estar vigentes el mismo día."
                )

    def eliminar(self, id: int) -> None:
        tarifa = self.obtener_o_404(id)
        usadas = self.conn.execute(
            "SELECT COUNT(*) FROM cosechas WHERE fecha BETWEEN ? AND ?",
            (tarifa.fecha_inicio, tarifa.fecha_fin),
        ).fetchone()[0]
        if usadas:
            raise ErrorDeNegocio(
                f"No se puede eliminar la tarifa: {usadas} cosechas de esas fechas dependen de ella."
            )
        super().eliminar(id)
