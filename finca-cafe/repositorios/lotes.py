from modelos import Lote
from repositorios.base import RepositorioBase


class RepositorioLotes(RepositorioBase):
    tabla = "lotes"
    modelo = Lote
    columnas = ("nombre", "variedad", "hectareas")
    busqueda = ("nombre", "variedad")
    nombre_singular = "el lote"
    mensajes_unicos = {"lotes.nombre": "Ya existe un lote con ese nombre."}
