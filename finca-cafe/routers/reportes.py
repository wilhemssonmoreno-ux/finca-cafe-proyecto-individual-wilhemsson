from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from database import get_db
from excepciones import ErrorDeNegocio, NoEncontrado
from repositorios import (
    RepositorioCosechas, RepositorioLotes, RepositorioProduccion, RepositorioTarifas,
    RepositorioTrabajadores, RepositorioVentas,
)
from seguridad import usuario_actual
from servicios.exportador import COLUMNAS, a_csv
from servicios.reportes import ServicioReportes
from servicios.respaldo import lanzar_respaldo_en_hilo, listar_respaldos

router = APIRouter(tags=["Reportes y archivos"], dependencies=[Depends(usuario_actual)])


def _rango(desde: date, hasta: date) -> tuple[str, str]:
    if desde > hasta:
        raise ErrorDeNegocio("La fecha «desde» no puede ser posterior a «hasta».")
    return desde.isoformat(), hasta.isoformat()


@router.get("/planilla", summary="Pago por trabajador y rendimiento por lote en un rango de fechas")
def planilla(desde: date = Query(..., description="AAAA-MM-DD"),
             hasta: date = Query(..., description="AAAA-MM-DD"), db=Depends(get_db)):
    return ServicioReportes(db).planilla(*_rango(desde, hasta))


@router.get("/reportes/rendimiento-lotes", summary="Latas por hectárea de cada lote")
def rendimiento(desde: date | None = None, hasta: date | None = None, db=Depends(get_db)):
    if desde and hasta:
        _rango(desde, hasta)
    return ServicioReportes(db).rendimiento_lotes(
        desde.isoformat() if desde else None, hasta.isoformat() if hasta else None
    )


@router.get("/inventario", summary="Café en bodega: producido, vendido y disponible por lote")
def inventario(db=Depends(get_db)):
    return ServicioReportes(db).inventario()


@router.get("/reportes/ventas", summary="Ventas de café por comprador y por mes")
def reporte_ventas(desde: date | None = None, hasta: date | None = None, db=Depends(get_db)):
    if desde and hasta:
        _rango(desde, hasta)
    return ServicioReportes(db).ventas_resumen(
        desde.isoformat() if desde else None, hasta.isoformat() if hasta else None
    )


@router.get("/reportes/resumen", summary="Totales y agrupaciones de toda la finca")
def resumen(db=Depends(get_db)):
    return ServicioReportes(db).resumen()


@router.get("/exportar/{recurso}", summary="Descargar un listado en CSV")
def exportar(recurso: str, desde: date | None = None, hasta: date | None = None, db=Depends(get_db)):
    if recurso not in COLUMNAS:
        raise NoEncontrado(f"No se puede exportar «{recurso}». Opciones: {', '.join(COLUMNAS)}.")
    if recurso == "planilla":
        if not (desde and hasta):
            raise ErrorDeNegocio("Para exportar la planilla indica «desde» y «hasta».")
        filas = ServicioReportes(db).planilla(*_rango(desde, hasta))["trabajadores"]
    elif recurso == "cosechas":
        filas = RepositorioCosechas(db).listar_detalle(
            desde=desde.isoformat() if desde else None, hasta=hasta.isoformat() if hasta else None
        )
    elif recurso == "produccion":
        filas = RepositorioProduccion(db).listar_detalle()
    else:
        repos = {"lotes": RepositorioLotes, "trabajadores": RepositorioTrabajadores,
                 "tarifas": RepositorioTarifas, "ventas": RepositorioVentas}
        filas = [m.a_dict() for m in repos[recurso](db).listar()]
    return Response(
        content=a_csv(recurso, filas),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{recurso}_{date.today()}.csv"'},
    )


@router.post("/respaldos", status_code=201, summary="Iniciar un respaldo en segundo plano (hilo)")
def crear_respaldo():
    archivo, _ = lanzar_respaldo_en_hilo()
    return {"mensaje": "Respaldo iniciado en segundo plano.", "archivo": archivo}


@router.get("/respaldos", summary="Listar respaldos guardados")
def respaldos():
    return listar_respaldos()
