from dataclasses import asdict, fields


class Entidad:
    """Clase base de todas las entidades del dominio."""

    @classmethod
    def desde_fila(cls, fila):
        """Construye la entidad desde una fila de SQLite ignorando columnas extra."""
        nombres = {f.name for f in fields(cls)}
        return cls(**{k: fila[k] for k in fila.keys() if k in nombres})

    def a_dict(self) -> dict:
        return asdict(self)
