"""Autenticación por token: dependencia que protege los endpoints."""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from database import get_db
from modelos import Usuario
from repositorios import RepositorioTokens

esquema_bearer = HTTPBearer(auto_error=False)


def usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(esquema_bearer),
    db=Depends(get_db),
) -> Usuario:
    if credenciales is None:
        raise HTTPException(status_code=401, detail="Falta el token. Inicia sesión en /auth/login.")
    usuario = RepositorioTokens(db).usuario_de_token(credenciales.credentials)
    if usuario is None:
        raise HTTPException(status_code=401, detail="El token no es válido o ya venció. Entra de nuevo.")
    return usuario
