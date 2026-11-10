"""Errores de negocio y traducción de errores de validación a mensajes claros."""


class ErrorDeNegocio(Exception):
    """Una regla de negocio no se cumple (HTTP 400)."""
    codigo = 400

    def __init__(self, mensaje: str):
        super().__init__(mensaje)
        self.mensaje = mensaje


class NoEncontrado(ErrorDeNegocio):
    """El registro pedido no existe (HTTP 404)."""
    codigo = 404


def _texto_error(error: dict) -> str:
    tipo = error.get("type", "")
    ctx = error.get("ctx") or {}
    if tipo == "missing":
        return "es obligatorio"
    if tipo == "greater_than":
        return f"debe ser mayor que {ctx.get('gt'):g}"
    if tipo == "greater_than_equal":
        return f"debe ser como mínimo {ctx.get('ge'):g}"
    if tipo == "less_than":
        return f"debe ser menor que {ctx.get('lt'):g}"
    if tipo == "less_than_equal":
        return f"no puede ser mayor que {ctx.get('le'):g}"
    if tipo == "string_too_short":
        return f"debe tener al menos {ctx.get('min_length')} caracteres"
    if tipo == "string_too_long":
        return f"no puede pasar de {ctx.get('max_length')} caracteres"
    if tipo == "string_pattern_mismatch":
        return "tiene un formato inválido"
    if tipo == "int_from_float":
        return "debe ser un número entero"
    if tipo in ("int_parsing", "int_type", "float_parsing", "float_type"):
        return "debe ser un número válido"
    if tipo in ("date_parsing", "date_from_datetime_parsing", "date_type"):
        return "debe ser una fecha válida (AAAA-MM-DD)"
    if tipo == "string_type":
        return "debe ser texto"
    if tipo == "json_invalid":
        return "el cuerpo de la petición no es un JSON válido"
    if tipo == "value_error":
        return str(error.get("msg", "")).removeprefix("Value error, ")
    return str(error.get("msg", "dato inválido"))


def traducir_errores(errores: list[dict]) -> str:
    """Convierte la lista de errores de Pydantic en una sola frase en español."""
    partes = []
    for e in errores:
        campo = str(e["loc"][-1]) if len(e.get("loc", ())) > 1 else ""
        texto = _texto_error(e)
        partes.append(f"{campo}: {texto}" if campo else texto)
    return "; ".join(partes)
