import secrets
from datetime import datetime, timedelta, timezone

from modelos import Usuario
from repositorios.base import RepositorioBase


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class RepositorioUsuarios(RepositorioBase):
    tabla = "usuarios"
    modelo = Usuario
    columnas = ("usuario", "nombre", "password_hash")
    busqueda = ("usuario", "nombre")
    nombre_singular = "el usuario"
    mensajes_unicos = {"usuarios.usuario": "Ese nombre de usuario ya existe."}

    def por_nombre(self, usuario: str) -> Usuario | None:
        fila = self.conn.execute("SELECT * FROM usuarios WHERE usuario = ?", (usuario,)).fetchone()
        return self._a_modelo(fila)


class RepositorioTokens:
    """Sesiones por token: se guardan en la tabla tokens y vencen solas."""

    def __init__(self, conn):
        self.conn = conn

    def emitir(self, usuario_id: int, horas: int = 8) -> tuple[str, str]:
        token = secrets.token_urlsafe(32)
        expira = (datetime.now(timezone.utc) + timedelta(hours=horas)).isoformat(timespec="seconds")
        self.conn.execute("DELETE FROM tokens WHERE expira < ?", (_ahora(),))
        self.conn.execute(
            "INSERT INTO tokens (token, usuario_id, creado, expira) VALUES (?, ?, ?, ?)",
            (token, usuario_id, _ahora(), expira),
        )
        self.conn.commit()
        return token, expira

    def usuario_de_token(self, token: str) -> Usuario | None:
        fila = self.conn.execute(
            "SELECT u.* FROM tokens t JOIN usuarios u ON u.id = t.usuario_id "
            "WHERE t.token = ? AND t.expira > ? AND u.activo = 1",
            (token, _ahora()),
        ).fetchone()
        return Usuario.desde_fila(fila) if fila else None

    def revocar(self, token: str) -> None:
        self.conn.execute("DELETE FROM tokens WHERE token = ?", (token,))
        self.conn.commit()
