from esquemas import ProduccionEntrada, ProduccionSalida
from repositorios import RepositorioProduccion
from routers.base import crear_router_crud

router = crear_router_crud(
    "/produccion", "Producción de café", RepositorioProduccion, ProduccionEntrada, ProduccionSalida
)
