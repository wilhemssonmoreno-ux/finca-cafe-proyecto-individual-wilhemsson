from esquemas import VentaEntrada, VentaSalida
from repositorios import RepositorioVentas
from routers.base import crear_router_crud

router = crear_router_crud("/ventas", "Ventas de café", RepositorioVentas, VentaEntrada, VentaSalida)
