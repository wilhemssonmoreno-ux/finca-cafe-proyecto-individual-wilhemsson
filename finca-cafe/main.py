"""Finca de café · API de cosechas, planilla y ventas (FastAPI + SQLite)."""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from database import BASE_DIR, inicializar_bd
from excepciones import ErrorDeNegocio, traducir_errores
from routers import auth, cosechas, lotes, produccion, reportes, tarifas, trabajadores, ventas
from servicios.respaldo import HiloRespaldo


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    inicializar_bd()
    hilo = None
    if os.environ.get("FINCA_RESPALDO_AUTO", "1") != "0":
        hilo = HiloRespaldo(intervalo_segundos=int(os.environ.get("FINCA_RESPALDO_CADA", "3600")))
        hilo.start()
    yield
    if hilo:
        hilo.detener()


app = FastAPI(
    title="Finca de café",
    description="Cosecha por lote, jornales por lata, planilla, café en bodega y ventas.",
    version="1.0.0",
    lifespan=ciclo_de_vida,
)


@app.exception_handler(ErrorDeNegocio)
async def manejar_error_de_negocio(request: Request, exc: ErrorDeNegocio):
    return JSONResponse(status_code=exc.codigo, content={"detail": exc.mensaje})


@app.exception_handler(RequestValidationError)
async def manejar_validacion(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=400, content={"detail": traducir_errores(exc.errors())})


for modulo in (auth, lotes, trabajadores, tarifas, cosechas, produccion, ventas, reportes):
    app.include_router(modulo.router)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/", include_in_schema=False)
def sitio():
    return FileResponse(BASE_DIR / "static" / "index.html")
