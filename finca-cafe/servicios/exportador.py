"""Exportación a CSV (con BOM para que Excel respete las tildes)."""
import csv
import io

COLUMNAS = {
    "lotes": ["id", "nombre", "variedad", "hectareas"],
    "trabajadores": ["id", "nombre", "identidad", "telefono"],
    "tarifas": ["id", "temporada", "precio_por_lata", "fecha_inicio", "fecha_fin"],
    "cosechas": ["id", "fecha", "lote_nombre", "trabajador_nombre", "latas", "precio_por_lata", "pago"],
    "produccion": ["id", "fecha", "lote_nombre", "quintales"],
    "ventas": ["id", "fecha", "comprador", "quintales", "precio_quintal", "total"],
    "planilla": ["nombre", "identidad", "dias", "latas", "pago"],
}


def a_csv(recurso: str, filas: list[dict]) -> str:
    salida = io.StringIO()
    escritor = csv.DictWriter(salida, fieldnames=COLUMNAS[recurso], extrasaction="ignore")
    escritor.writeheader()
    escritor.writerows(filas)
    return "\ufeff" + salida.getvalue()
