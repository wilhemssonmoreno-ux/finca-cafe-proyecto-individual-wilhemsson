from modelos import Trabajador
from repositorios.base import RepositorioBase


class RepositorioTrabajadores(RepositorioBase):
    tabla = "trabajadores"
    modelo = Trabajador
    columnas = ("nombre", "identidad", "telefono")
    busqueda = ("nombre", "identidad", "telefono")
    nombre_singular = "el trabajador"
    mensajes_unicos = {"trabajadores.identidad": "Ya existe un trabajador con esa identidad."}
