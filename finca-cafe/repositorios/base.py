import sqlite3

from excepciones import ErrorDeNegocio, NoEncontrado


class RepositorioBase:
    """CRUD genérico sobre una tabla. Cada tabla hereda y declara sus columnas."""

    tabla: str = ""
    modelo = None
    columnas: tuple = ()          # columnas editables
    busqueda: tuple = ()          # columnas donde busca el parámetro ?buscar=
    nombre_singular = "registro"
    orden = "id"
    mensajes_unicos: dict = {}    # "tabla.columna" -> mensaje claro

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def _a_modelo(self, fila):
        return self.modelo.desde_fila(fila) if fila is not None else None

    def listar(self, buscar: str | None = None) -> list:
        sql, params = f"SELECT * FROM {self.tabla}", []
        if buscar and self.busqueda:
            sql += " WHERE " + " OR ".join(f"{c} LIKE ?" for c in self.busqueda)
            params = [f"%{buscar}%"] * len(self.busqueda)
        sql += f" ORDER BY {self.orden}"
        return [self._a_modelo(f) for f in self.conn.execute(sql, params).fetchall()]

    def obtener(self, id: int):
        fila = self.conn.execute(f"SELECT * FROM {self.tabla} WHERE id = ?", (id,)).fetchone()
        return self._a_modelo(fila)

    def obtener_o_404(self, id: int):
        entidad = self.obtener(id)
        if entidad is None:
            raise NoEncontrado(f"No existe {self.nombre_singular} con id {id}.")
        return entidad

    def validar(self, datos: dict, id_actual: int | None = None) -> None:
        """Gancho para reglas de negocio propias de cada tabla."""

    def crear(self, datos: dict):
        self.validar(datos)
        columnas = ", ".join(self.columnas)
        marcas = ", ".join("?" for _ in self.columnas)
        try:
            cur = self.conn.execute(
                f"INSERT INTO {self.tabla} ({columnas}) VALUES ({marcas})",
                [datos[c] for c in self.columnas],
            )
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            raise ErrorDeNegocio(self._traducir(e)) from e
        return self.obtener(cur.lastrowid)

    def actualizar(self, id: int, datos: dict):
        self.obtener_o_404(id)
        self.validar(datos, id)
        asignaciones = ", ".join(f"{c} = ?" for c in self.columnas)
        try:
            self.conn.execute(
                f"UPDATE {self.tabla} SET {asignaciones} WHERE id = ?",
                [datos[c] for c in self.columnas] + [id],
            )
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            raise ErrorDeNegocio(self._traducir(e)) from e
        return self.obtener(id)

    def eliminar(self, id: int) -> None:
        self.obtener_o_404(id)
        try:
            self.conn.execute(f"DELETE FROM {self.tabla} WHERE id = ?", (id,))
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            raise ErrorDeNegocio(
                f"No se puede eliminar {self.nombre_singular}: tiene registros relacionados."
            ) from e

    def _traducir(self, error: sqlite3.IntegrityError) -> str:
        texto = str(error)
        for clave, mensaje in self.mensajes_unicos.items():
            if clave in texto:
                return mensaje
        if "CHECK" in texto:
            return "Uno de los valores no cumple las reglas permitidas."
        if "NOT NULL" in texto:
            return "Falta un dato obligatorio."
        if "FOREIGN KEY" in texto:
            return "Hace referencia a un registro que no existe."
        return "Los datos chocan con otro registro ya guardado."
