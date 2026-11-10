from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from database import get_db
from esquemas import LoginEntrada, TokenSalida, UsuarioEntrada, UsuarioSalida
from modelos import Usuario
from repositorios import RepositorioTokens, RepositorioUsuarios
from seguridad import esquema_bearer, usuario_actual

router = APIRouter(prefix="/auth", tags=["Seguridad"])


@router.post("/login", response_model=TokenSalida, summary="Iniciar sesión y recibir un token")
def login(datos: LoginEntrada, db=Depends(get_db)):
    usuario = RepositorioUsuarios(db).por_nombre(datos.usuario)
    if usuario is None or not usuario.activo or not usuario.verificar(datos.password):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos.")
    token, expira = RepositorioTokens(db).emitir(usuario.id)
    return {"token": token, "usuario": usuario.usuario, "nombre": usuario.nombre, "expira": expira}


@router.get("/yo", response_model=UsuarioSalida, summary="Datos del usuario con sesión")
def yo(usuario: Usuario = Depends(usuario_actual)):
    return usuario.a_dict()


@router.post("/registro", response_model=UsuarioSalida, status_code=201,
             summary="Crear otro usuario (requiere sesión)")
def registro(datos: UsuarioEntrada, db=Depends(get_db), _: Usuario = Depends(usuario_actual)):
    nuevo = RepositorioUsuarios(db).crear({
        "usuario": datos.usuario,
        "nombre": datos.nombre,
        "password_hash": Usuario.encriptar(datos.password),
    })
    return nuevo.a_dict()


@router.post("/logout", summary="Cerrar sesión")
def logout(
    credenciales: HTTPAuthorizationCredentials = Depends(esquema_bearer),
    db=Depends(get_db),
    _: Usuario = Depends(usuario_actual),
):
    RepositorioTokens(db).revocar(credenciales.credentials)
    return {"mensaje": "Sesión cerrada."}
