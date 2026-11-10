from esquemas import LoteEntrada, LoteSalida
from repositorios import RepositorioLotes
from routers.base import crear_router_crud

router = crear_router_crud("/lotes", "Lotes", RepositorioLotes, LoteEntrada, LoteSalida)
