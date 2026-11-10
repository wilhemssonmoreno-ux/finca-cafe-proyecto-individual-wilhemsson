from datetime import date

from fastapi import APIRouter, Depends, Query

from database import get_db
from esquemas import CosechaEntrada, CosechaSalida
from repositorios import RepositorioCosechas
from seguridad import usuario_actual

router = APIRouter(prefix="/cosechas", tags=["Cosechas"], dependencies=[Depends(usuario_actual)])


@router.get("", response_model=list[CosechaSalida], summary="Listar cosechas con pago calculado")
def listar(
    buscar: str | None = Query(None, description="Busca por lote, trabajador o fecha"),
    desde: date | None = None,
    hasta: date | None = None,
    db=Depends(get_db),
):
    return RepositorioCosechas(db).listar_detalle(
        buscar, desde.isoformat() if desde else None, hasta.isoformat() if hasta else None
    )


@router.get("/{item_id}", response_model=CosechaSalida, summary="Ver una cosecha")
def obtener(item_id: int, db=Depends(get_db)):
    return RepositorioCosechas(db).detalle(item_id)


@router.post("", response_model=CosechaSalida, status_code=201, summary="Registrar cosecha")
def crear(datos: CosechaEntrada, db=Depends(get_db)):
    repo = RepositorioCosechas(db)
    return repo.detalle(repo.crear(datos.model_dump(mode="json")).id)


@router.put("/{item_id}", response_model=CosechaSalida, summary="Actualizar cosecha")
def actualizar(item_id: int, datos: CosechaEntrada, db=Depends(get_db)):
    repo = RepositorioCosechas(db)
    repo.actualizar(item_id, datos.model_dump(mode="json"))
    return repo.detalle(item_id)


@router.delete("/{item_id}", summary="Eliminar cosecha")
def eliminar(item_id: int, db=Depends(get_db)):
    RepositorioCosechas(db).eliminar(item_id)
    return {"mensaje": "Registro eliminado correctamente."}
