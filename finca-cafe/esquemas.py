"""Esquemas Pydantic: validan lo que entra y describen lo que sale."""
import re
from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Base(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


# ---------- Lotes ----------
class LoteEntrada(Base):
    nombre: str = Field(min_length=2, max_length=60, examples=["El Mirador"])
    variedad: str = Field(min_length=2, max_length=40, examples=["Catuaí"])
    hectareas: float = Field(gt=0, le=1000, examples=[3.5])


class LoteSalida(LoteEntrada):
    id: int


# ---------- Trabajadores ----------
class TrabajadorEntrada(Base):
    nombre: str = Field(min_length=3, max_length=80, examples=["José Armando Reyes"])
    identidad: str = Field(examples=["0301-1988-04512"])
    telefono: str = Field(examples=["9876-5521"])

    @field_validator("identidad", mode="before")
    @classmethod
    def normalizar_identidad(cls, v):
        if isinstance(v, str):
            d = re.sub(r"\D", "", v)
            if len(d) != 13:
                raise ValueError("debe tener 13 dígitos (ej. 0301-1988-04512)")
            return f"{d[:4]}-{d[4:8]}-{d[8:]}"
        return v

    @field_validator("telefono", mode="before")
    @classmethod
    def normalizar_telefono(cls, v):
        if isinstance(v, str):
            d = re.sub(r"\D", "", v)
            if len(d) != 8:
                raise ValueError("debe tener 8 dígitos (ej. 9876-5521)")
            return f"{d[:4]}-{d[4:]}"
        return v


class TrabajadorSalida(TrabajadorEntrada):
    id: int


# ---------- Tarifas ----------
class TarifaEntrada(Base):
    temporada: str = Field(min_length=3, max_length=60, examples=["Cosecha 2026-2027"])
    precio_por_lata: float = Field(gt=0, le=1000, examples=[35.0])
    fecha_inicio: date
    fecha_fin: date

    @model_validator(mode="after")
    def fechas_en_orden(self):
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("la fecha final no puede ser anterior a la fecha inicial")
        return self


class TarifaSalida(TarifaEntrada):
    id: int


# ---------- Cosechas ----------
class CosechaEntrada(Base):
    lote_id: int = Field(gt=0)
    trabajador_id: int = Field(gt=0)
    fecha: date
    latas: int = Field(gt=0, le=2000, examples=[32])


class CosechaSalida(CosechaEntrada):
    id: int
    lote_nombre: str
    trabajador_nombre: str
    precio_por_lata: float | None = None
    pago: float | None = None


# ---------- Producción de café (bodega) ----------
class ProduccionEntrada(Base):
    lote_id: int = Field(gt=0)
    fecha: date
    quintales: float = Field(gt=0, le=100000, examples=[12.5])


class ProduccionSalida(ProduccionEntrada):
    id: int
    lote_nombre: str


# ---------- Ventas de café ----------
class VentaEntrada(Base):
    fecha: date
    comprador: str = Field(min_length=2, max_length=80, examples=["Exportadora Santa Rosa"])
    quintales: float = Field(gt=0, le=100000, examples=[12.5])
    precio_quintal: float = Field(gt=0, le=1000000, examples=[8100.0])


class VentaSalida(VentaEntrada):
    id: int
    total: float


# ---------- Seguridad ----------
class LoginEntrada(Base):
    usuario: str = Field(min_length=1)
    password: str = Field(min_length=1)


class TokenSalida(BaseModel):
    token: str
    tipo: str = "bearer"
    usuario: str
    nombre: str
    expira: str


class UsuarioEntrada(Base):
    usuario: str = Field(min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_.-]+$")
    nombre: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=6, max_length=100)


class UsuarioSalida(BaseModel):
    id: int
    usuario: str
    nombre: str
    activo: int
