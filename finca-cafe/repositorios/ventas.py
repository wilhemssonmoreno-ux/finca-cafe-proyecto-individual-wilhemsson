from excepciones import ErrorDeNegocio
from modelos import VentaCafe
from repositorios.base import RepositorioBase
from repositorios.inventario import quintales_disponibles


class RepositorioVentas(RepositorioBase):
    tabla = "ventas_cafe"
    modelo = VentaCafe
    columnas = ("fecha", "comprador", "quintales", "precio_quintal")
    busqueda = ("comprador", "fecha")
    nombre_singular = "la venta"
    orden = "fecha DESC, id DESC"

    def validar(self, datos, id_actual=None):
        """No se vende más café del que hay en bodega."""
        hay = quintales_disponibles(self.conn, excluir_venta=id_actual if id_actual is not None else -1)
        if datos["quintales"] > hay:
            raise ErrorDeNegocio(
                f"No hay suficiente café en bodega: quedan {hay:g} quintales y quieres vender "
                f"{datos['quintales']:g}. Registra primero la producción."
            )
