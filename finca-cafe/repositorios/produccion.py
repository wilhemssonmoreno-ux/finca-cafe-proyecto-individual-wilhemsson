from excepciones import ErrorDeNegocio, NoEncontrado
from modelos import ProduccionCafe
from repositorios.base import RepositorioBase
from repositorios.inventario import quintales_disponibles
from repositorios.lotes import RepositorioLotes


class RepositorioProduccion(RepositorioBase):
    tabla = "produccion_cafe"
    modelo = ProduccionCafe
    columnas = ("lote_id", "fecha", "quintales")
    nombre_singular = "el registro de producción"

    def validar(self, datos, id_actual=None):
        if RepositorioLotes(self.conn).obtener(datos["lote_id"]) is None:
            raise ErrorDeNegocio("El lote indicado no existe.")
        if id_actual is not None:
            # al editar, la bodega no puede quedar con menos café del que ya se vendió
            if quintales_disponibles(self.conn, excluir_produccion=id_actual) + datos["quintales"] < 0:
                raise ErrorDeNegocio(
                    "No se puede bajar esa producción: ese café ya se vendió y la bodega quedaría en negativo."
                )

    def eliminar(self, id: int) -> None:
        self.obtener_o_404(id)
        if quintales_disponibles(self.conn, excluir_produccion=id) < 0:
            raise ErrorDeNegocio(
                "No se puede eliminar: ese café ya se vendió y la bodega quedaría en negativo."
            )
        super().eliminar(id)

    def listar_detalle(self, buscar=None, produccion_id=None) -> list[dict]:
        sql = ("SELECT p.*, l.nombre AS lote_nombre FROM produccion_cafe p "
               "JOIN lotes l ON l.id = p.lote_id WHERE 1 = 1")
        params: list = []
        if produccion_id is not None:
            sql += " AND p.id = ?"
            params.append(produccion_id)
        if buscar:
            sql += " AND (l.nombre LIKE ? OR p.fecha LIKE ?)"
            params += [f"%{buscar}%"] * 2
        sql += " ORDER BY p.fecha DESC, p.id DESC"
        return [{**ProduccionCafe.desde_fila(f).a_dict(), "lote_nombre": f["lote_nombre"]}
                for f in self.conn.execute(sql, params).fetchall()]

    def detalle(self, id: int) -> dict:
        filas = self.listar_detalle(produccion_id=id)
        if not filas:
            raise NoEncontrado(f"No existe {self.nombre_singular} con id {id}.")
        return filas[0]
