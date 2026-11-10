from esquemas import TarifaEntrada, TarifaSalida
from repositorios import RepositorioTarifas
from routers.base import crear_router_crud

router = crear_router_crud("/tarifas", "Tarifas", RepositorioTarifas, TarifaEntrada, TarifaSalida)
