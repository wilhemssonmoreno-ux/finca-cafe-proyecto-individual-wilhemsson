"""Reportes con colecciones: planilla, rendimiento por lote y resumen de la finca."""
from collections import Counter, defaultdict

from modelos import Tarifa
from repositorios import (
    RepositorioCosechas, RepositorioLotes, RepositorioProduccion, RepositorioTarifas,
    RepositorioTrabajadores, RepositorioVentas,
)


class ServicioReportes:
    def __init__(self, conn):
        self.cosechas = RepositorioCosechas(conn)
        self.lotes = RepositorioLotes(conn)
        self.trabajadores = RepositorioTrabajadores(conn)
        self.tarifas = RepositorioTarifas(conn)
        self.ventas = RepositorioVentas(conn)
        self.produccion = RepositorioProduccion(conn)

    def _cosechas_con_pago(self, desde=None, hasta=None):
        """Lista de (cosecha, pago); el pago es None si la fecha no tiene tarifa vigente."""
        tarifas = self.tarifas.listar()
        resultado = []
        for c in self.cosechas.entre_fechas(desde, hasta):
            tarifa = Tarifa.vigente_para(tarifas, c.fecha)
            resultado.append((c, c.calcular_pago(tarifa.precio_por_lata) if tarifa else None))
        return resultado

    def _rendimiento(self, latas_por_lote: dict) -> list[dict]:
        filas = [
            {
                "lote_id": l.id, "nombre": l.nombre, "variedad": l.variedad,
                "hectareas": l.hectareas, "latas": latas_por_lote.get(l.id, 0),
                "latas_por_hectarea": l.rendimiento(latas_por_lote.get(l.id, 0)),
            }
            for l in self.lotes.listar()
        ]
        return sorted(filas, key=lambda f: (-f["latas_por_hectarea"], f["nombre"]))

    def rendimiento_lotes(self, desde=None, hasta=None) -> list[dict]:
        latas = defaultdict(int)
        for c, _ in self._cosechas_con_pago(desde, hasta):
            latas[c.lote_id] += c.latas
        return self._rendimiento(latas)

    def planilla(self, desde: str, hasta: str) -> dict:
        latas, pagos = defaultdict(int), defaultdict(float)
        dias, latas_lote = defaultdict(set), defaultdict(int)
        sin_tarifa = 0
        for c, pago in self._cosechas_con_pago(desde, hasta):
            latas[c.trabajador_id] += c.latas
            dias[c.trabajador_id].add(c.fecha)
            latas_lote[c.lote_id] += c.latas
            if pago is None:
                sin_tarifa += 1
            else:
                pagos[c.trabajador_id] += pago

        trabajadores = {t.id: t for t in self.trabajadores.listar()}
        filas = [
            {
                "trabajador_id": tid, "nombre": trabajadores[tid].nombre,
                "identidad": trabajadores[tid].identidad, "dias": len(dias[tid]),
                "latas": latas[tid], "pago": round(pagos[tid], 2),
            }
            for tid in latas
        ]
        filas.sort(key=lambda f: (-f["pago"], f["nombre"]))
        return {
            "desde": desde, "hasta": hasta,
            "trabajadores": filas,
            "total_latas": sum(f["latas"] for f in filas),
            "total_pago": round(sum(f["pago"] for f in filas), 2),
            "cosechas_sin_tarifa": sin_tarifa,
            "rendimiento_lotes": self._rendimiento(latas_lote),
        }

    def inventario(self) -> dict:
        """Café en bodega: producido, vendido y disponible, con la productividad de cada lote."""
        producido = defaultdict(float)
        for p in self.produccion.listar():
            producido[p.lote_id] += p.quintales
        total_prod = round(sum(producido.values()), 2)
        total_vend = round(sum(v.quintales for v in self.ventas.listar()), 2)
        por_lote = sorted(
            ({"lote_id": l.id, "nombre": l.nombre, "variedad": l.variedad, "hectareas": l.hectareas,
              "quintales": round(producido.get(l.id, 0.0), 2),
              "quintales_por_hectarea": l.productividad(producido.get(l.id, 0.0))}
             for l in self.lotes.listar()),
            key=lambda f: (-f["quintales_por_hectarea"], f["nombre"]),
        )
        return {"producido": total_prod, "vendido": total_vend,
                "disponible": round(total_prod - total_vend, 2), "por_lote": por_lote}

    def ventas_resumen(self, desde=None, hasta=None) -> dict:
        """Ventas de café agrupadas por comprador y por mes, con el precio promedio ponderado."""
        ventas = [v for v in self.ventas.listar()
                  if (not desde or v.fecha >= desde) and (not hasta or v.fecha <= hasta)]
        por_comprador = defaultdict(lambda: {"quintales": 0.0, "monto": 0.0, "ventas": 0})
        por_mes = defaultdict(lambda: {"quintales": 0.0, "monto": 0.0})
        for v in ventas:
            for grupo, clave in ((por_comprador, v.comprador), (por_mes, v.fecha[:7])):
                grupo[clave]["quintales"] += v.quintales
                grupo[clave]["monto"] += v.total()
            por_comprador[v.comprador]["ventas"] += 1
        quintales = sum(v.quintales for v in ventas)
        monto = sum(v.total() for v in ventas)
        return {
            "ventas": len(ventas),
            "quintales": round(quintales, 2),
            "monto": round(monto, 2),
            "precio_promedio": round(monto / quintales, 2) if quintales else 0.0,
            "por_comprador": sorted(
                ({"comprador": k, **{n: round(x, 2) for n, x in d.items()}} for k, d in por_comprador.items()),
                key=lambda f: -f["monto"]),
            "por_mes": [{"mes": m, **{n: round(x, 2) for n, x in d.items()}} for m, d in sorted(por_mes.items())],
        }

    def resumen(self) -> dict:
        por_mes, por_trabajador = defaultdict(int), Counter()
        pago_total, latas_total = 0.0, 0
        nombres = {t.id: t.nombre for t in self.trabajadores.listar()}
        for c, pago in self._cosechas_con_pago():
            por_mes[c.fecha[:7]] += c.latas
            por_trabajador[c.trabajador_id] += c.latas
            latas_total += c.latas
            pago_total += pago or 0.0

        compradores = defaultdict(lambda: {"quintales": 0.0, "monto": 0.0})
        for v in self.ventas.listar():
            compradores[v.comprador]["quintales"] += v.quintales
            compradores[v.comprador]["monto"] += v.total()
        por_comprador = sorted(
            ({"comprador": k, "quintales": round(d["quintales"], 2), "monto": round(d["monto"], 2)}
             for k, d in compradores.items()),
            key=lambda f: -f["monto"],
        )
        lotes = self.lotes.listar()
        bodega = self.inventario()
        monto_ventas = round(sum(f["monto"] for f in por_comprador), 2)
        return {
            "lotes": len(lotes),
            "hectareas_total": round(sum(l.hectareas for l in lotes), 2),
            "trabajadores": len(nombres),
            "latas_total": latas_total,
            "pago_total": round(pago_total, 2),
            "latas_por_mes": [{"mes": m, "latas": n} for m, n in sorted(por_mes.items())],
            "top_cortadores": [
                {"nombre": nombres[tid], "latas": n} for tid, n in por_trabajador.most_common(5)
            ],
            "ventas": {
                "quintales": round(sum(f["quintales"] for f in por_comprador), 2),
                "monto": monto_ventas,
                "por_comprador": por_comprador,
            },
            "bodega": {k: bodega[k] for k in ("producido", "vendido", "disponible")},
            "produccion_por_lote": bodega["por_lote"],
            # ventas menos jornales: no incluye otros gastos de la finca
            "utilidad_sobre_jornales": round(monto_ventas - pago_total, 2),
        }
