from excepciones import ErrorDeNegocio, NoEncontrado
from modelos import Cosecha, Tarifa
from repositorios.base import RepositorioBase
from repositorios.lotes import RepositorioLotes
from repositorios.tarifas import RepositorioTarifas
from repositorios.trabajadores import RepositorioTrabajadores


class RepositorioCosechas(RepositorioBase):
    tabla = "cosechas"
    modelo = Cosecha
    columnas = ("lote_id", "trabajador_id", "fecha", "latas")
    nombre_singular = "la cosecha"
    mensajes_unicos = {
        "cosechas.lote_id": "Ese trabajador ya tiene un registro en ese lote para esa fecha."
    }

    def validar(self, datos, id_actual=None):
        if RepositorioLotes(self.conn).obtener(datos["lote_id"]) is None:
            raise ErrorDeNegocio("El lote indicado no existe.")
        if RepositorioTrabajadores(self.conn).obtener(datos["trabajador_id"]) is None:
            raise ErrorDeNegocio("El trabajador indicado no existe.")
        if RepositorioTarifas(self.conn).vigente_en(datos["fecha"]) is None:
            raise ErrorDeNegocio(
                f"No hay una tarifa vigente para el {datos['fecha']}. "
                "Registra primero la tarifa de esa temporada."
            )
        repetida = self.conn.execute(
            "SELECT id FROM cosechas WHERE lote_id = ? AND trabajador_id = ? AND fecha = ? AND id != ?",
            (datos["lote_id"], datos["trabajador_id"], datos["fecha"], id_actual or -1),
        ).fetchone()
        if repetida:
            raise ErrorDeNegocio("Ese trabajador ya tiene un registro en ese lote para esa fecha.")

    def entre_fechas(self, desde: str | None = None, hasta: str | None = None) -> list[Cosecha]:
        filas = self.conn.execute(
            "SELECT * FROM cosechas WHERE (? IS NULL OR fecha >= ?) AND (? IS NULL OR fecha <= ?) "
            "ORDER BY fecha, id",
            (desde, desde, hasta, hasta),
        ).fetchall()
        return [Cosecha.desde_fila(f) for f in filas]

    def listar_detalle(self, buscar=None, desde=None, hasta=None, cosecha_id=None) -> list[dict]:
        """Cosechas con nombre de lote, nombre de trabajador, tarifa y pago calculado."""
        sql = (
            "SELECT c.*, l.nombre AS lote_nombre, t.nombre AS trabajador_nombre "
            "FROM cosechas c JOIN lotes l ON l.id = c.lote_id "
            "JOIN trabajadores t ON t.id = c.trabajador_id WHERE 1 = 1"
        )
        params: list = []
        if cosecha_id is not None:
            sql += " AND c.id = ?"
            params.append(cosecha_id)
        if buscar:
            sql += " AND (l.nombre LIKE ? OR t.nombre LIKE ? OR c.fecha LIKE ?)"
            params += [f"%{buscar}%"] * 3
        if desde:
            sql += " AND c.fecha >= ?"
            params.append(desde)
        if hasta:
            sql += " AND c.fecha <= ?"
            params.append(hasta)
        sql += " ORDER BY c.fecha DESC, c.id DESC"

        tarifas = RepositorioTarifas(self.conn).listar()
        resultado = []
        for fila in self.conn.execute(sql, params).fetchall():
            cosecha = Cosecha.desde_fila(fila)
            tarifa = Tarifa.vigente_para(tarifas, cosecha.fecha)
            datos = cosecha.a_dict()
            datos.update(
                lote_nombre=fila["lote_nombre"],
                trabajador_nombre=fila["trabajador_nombre"],
                precio_por_lata=tarifa.precio_por_lata if tarifa else None,
                pago=cosecha.calcular_pago(tarifa.precio_por_lata) if tarifa else None,
            )
            resultado.append(datos)
        return resultado

    def detalle(self, id: int) -> dict:
        filas = self.listar_detalle(cosecha_id=id)
        if not filas:
            raise NoEncontrado(f"No existe la cosecha con id {id}.")
        return filas[0]
