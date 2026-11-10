from esquemas import TrabajadorEntrada, TrabajadorSalida
from repositorios import RepositorioTrabajadores
from routers.base import crear_router_crud

router = crear_router_crud(
    "/trabajadores", "Trabajadores", RepositorioTrabajadores, TrabajadorEntrada, TrabajadorSalida
)
