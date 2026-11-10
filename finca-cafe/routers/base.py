"""Fábrica de routers CRUD: evita repetir los mismos 5 endpoints por cada tabla."""
from fastapi import APIRouter, Depends, Query

from database import get_db
from seguridad import usuario_actual


def crear_router_crud(prefijo: str, etiqueta: str, clase_repo, entrada, salida) -> APIRouter:
    router = APIRouter(prefix=prefijo, tags=[etiqueta], dependencies=[Depends(usuario_actual)])
    # si el repositorio sabe devolver filas con nombres (JOIN), se usan en lugar de la entidad simple
    con_detalle = hasattr(clase_repo, "listar_detalle")

    def salir(repo, entidad) -> dict:
        return repo.detalle(entidad.id) if con_detalle else entidad.a_dict()

    @router.get("", response_model=list[salida], summary=f"Listar {etiqueta.lower()}")
    def listar(buscar: str | None = Query(None, description="Texto a buscar"), db=Depends(get_db)):
        repo = clase_repo(db)
        return repo.listar_detalle(buscar) if con_detalle else [m.a_dict() for m in repo.listar(buscar)]

    @router.get("/{item_id}", response_model=salida, summary="Ver uno")
    def obtener(item_id: int, db=Depends(get_db)):
        repo = clase_repo(db)
        return salir(repo, repo.obtener_o_404(item_id))

    @router.post("", response_model=salida, status_code=201, summary="Crear")
    def crear(datos: entrada, db=Depends(get_db)):
        repo = clase_repo(db)
        return salir(repo, repo.crear(datos.model_dump(mode="json")))

    @router.put("/{item_id}", response_model=salida, summary="Actualizar")
    def actualizar(item_id: int, datos: entrada, db=Depends(get_db)):
        repo = clase_repo(db)
        return salir(repo, repo.actualizar(item_id, datos.model_dump(mode="json")))

    @router.delete("/{item_id}", summary="Eliminar")
    def eliminar(item_id: int, db=Depends(get_db)):
        clase_repo(db).eliminar(item_id)
        return {"mensaje": "Registro eliminado correctamente."}

    return router
