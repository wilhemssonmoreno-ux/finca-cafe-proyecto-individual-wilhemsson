"""Existencias de café en bodega = café producido - café vendido."""


def quintales_disponibles(conn, excluir_venta: int = -1, excluir_produccion: int = -1) -> float:
    """Quintales que hay en bodega. Se puede excluir un registro (para validar una edición)."""
    producido = conn.execute(
        "SELECT COALESCE(SUM(quintales), 0) FROM produccion_cafe WHERE id != ?", (excluir_produccion,)
    ).fetchone()[0]
    vendido = conn.execute(
        "SELECT COALESCE(SUM(quintales), 0) FROM ventas_cafe WHERE id != ?", (excluir_venta,)
    ).fetchone()[0]
    return round(producido - vendido, 2)
