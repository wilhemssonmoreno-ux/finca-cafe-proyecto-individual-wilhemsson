import hashlib
import hmac
import secrets
from dataclasses import dataclass

from modelos.base import Entidad

ITERACIONES = 200_000


@dataclass(kw_only=True)
class Usuario(Entidad):
    id: int | None = None
    usuario: str
    nombre: str
    password_hash: str = ""
    activo: int = 1

    @staticmethod
    def encriptar(password: str, sal: bytes | None = None) -> str:
        """PBKDF2-SHA256 con sal aleatoria. Formato: algoritmo$iteraciones$sal$hash."""
        sal = sal or secrets.token_bytes(16)
        h = hashlib.pbkdf2_hmac("sha256", password.encode(), sal, ITERACIONES)
        return f"pbkdf2_sha256${ITERACIONES}${sal.hex()}${h.hex()}"

    def verificar(self, password: str) -> bool:
        try:
            _, iteraciones, sal, esperado = self.password_hash.split("$")
            h = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(sal), int(iteraciones))
        except ValueError:
            return False
        return hmac.compare_digest(h.hex(), esperado)

    def a_dict(self) -> dict:
        datos = super().a_dict()
        datos.pop("password_hash", None)   # nunca se expone la contraseña
        return datos
