import time

DATOS_COSECHA = {"lote_id": 1, "trabajador_id": 1, "fecha": "2026-11-08", "latas": 30}


# ---------- Seguridad ----------
def test_login_correcto_devuelve_token(sin_sesion):
    r = sin_sesion.post("/auth/login", json={"usuario": "admin", "password": "admin123"})
    assert r.status_code == 200
    assert r.json()["token"]


def test_login_con_clave_incorrecta_es_rechazado(sin_sesion):
    r = sin_sesion.post("/auth/login", json={"usuario": "admin", "password": "mala"})
    assert r.status_code == 401
    assert "incorrectos" in r.json()["detail"]


def test_endpoint_protegido_sin_token(sin_sesion):
    assert sin_sesion.get("/lotes").status_code == 401


# ---------- CRUD de lotes ----------
def test_crud_completo_de_lotes(cliente):
    r = cliente.post("/lotes", json={"nombre": "Lote Nuevo", "variedad": "Bourbon", "hectareas": 2.5})
    assert r.status_code == 201
    id_lote = r.json()["id"]

    assert cliente.get(f"/lotes/{id_lote}").json()["nombre"] == "Lote Nuevo"

    r = cliente.put(f"/lotes/{id_lote}", json={"nombre": "Lote Nuevo", "variedad": "Catuaí", "hectareas": 3})
    assert r.status_code == 200 and r.json()["variedad"] == "Catuaí"

    assert cliente.delete(f"/lotes/{id_lote}").status_code == 200
    assert cliente.get(f"/lotes/{id_lote}").status_code == 404


def test_lote_con_hectareas_cero_da_400_con_mensaje_claro(cliente):
    r = cliente.post("/lotes", json={"nombre": "Malo", "variedad": "Bourbon", "hectareas": 0})
    assert r.status_code == 400
    assert "hectareas: debe ser mayor que 0" in r.json()["detail"]


def test_lote_inexistente_da_404(cliente):
    assert cliente.get("/lotes/9999").status_code == 404


def test_no_se_elimina_un_lote_con_cosechas(cliente):
    r = cliente.delete("/lotes/1")
    assert r.status_code == 400
    assert "relacionados" in r.json()["detail"]


def test_buscar_trabajadores_por_nombre(cliente):
    r = cliente.get("/trabajadores", params={"buscar": "María"})
    assert r.status_code == 200
    assert r.json() and all("María" in t["nombre"] for t in r.json())


def test_identidad_se_normaliza_y_no_se_repite(cliente):
    nuevo = {"nombre": "Pedro Pérez", "identidad": "0301199900123", "telefono": "99887766"}
    r = cliente.post("/trabajadores", json=nuevo)
    assert r.status_code == 201
    assert r.json()["identidad"] == "0301-1999-00123"
    assert r.json()["telefono"] == "9988-7766"
    assert cliente.post("/trabajadores", json=nuevo).status_code == 400


# ---------- Reglas de negocio de cosechas ----------
def test_latas_deben_ser_mayores_a_cero(cliente):
    r = cliente.post("/cosechas", json={**DATOS_COSECHA, "latas": 0})
    assert r.status_code == 400
    assert "latas" in r.json()["detail"]


def test_pago_usa_la_tarifa_vigente_de_la_fecha(cliente):
    nueva = cliente.post("/cosechas", json=DATOS_COSECHA)            # temporada 2026-2027: L 35
    assert nueva.status_code == 201
    assert nueva.json()["precio_por_lata"] == 35 and nueva.json()["pago"] == 30 * 35

    vieja = cliente.post("/cosechas", json={**DATOS_COSECHA, "fecha": "2026-10-30"})  # temporada 2025-2026: L 32
    assert vieja.status_code == 201
    assert vieja.json()["precio_por_lata"] == 32 and vieja.json()["pago"] == 30 * 32


def test_un_registro_por_trabajador_lote_y_dia(cliente):
    assert cliente.post("/cosechas", json=DATOS_COSECHA).status_code == 201
    r = cliente.post("/cosechas", json=DATOS_COSECHA)
    assert r.status_code == 400
    assert "ya tiene un registro" in r.json()["detail"]


def test_no_se_registra_cosecha_sin_tarifa_vigente(cliente):
    r = cliente.post("/cosechas", json={**DATOS_COSECHA, "fecha": "2030-01-15"})
    assert r.status_code == 400
    assert "tarifa vigente" in r.json()["detail"]


def test_tarifas_no_se_traslapan(cliente):
    r = cliente.post("/tarifas", json={
        "temporada": "Choque", "precio_por_lata": 40,
        "fecha_inicio": "2027-01-01", "fecha_fin": "2027-12-31",
    })
    assert r.status_code == 400
    assert "traslapan" in r.json()["detail"]


# ---------- Ventas, planilla y archivos ----------
def test_venta_calcula_el_total(cliente):
    r = cliente.post("/ventas", json={
        "fecha": "2026-11-05", "comprador": "Beneficio Montecristo",
        "quintales": 10, "precio_quintal": 8000,
    })
    assert r.status_code == 201
    assert r.json()["total"] == 80000


def test_planilla_suma_lo_mismo_que_las_cosechas(cliente):
    r = cliente.get("/planilla", params={"desde": "2026-10-19", "hasta": "2026-11-08"})
    assert r.status_code == 200
    datos = r.json()
    assert datos["total_pago"] == round(sum(t["pago"] for t in datos["trabajadores"]), 2)
    cosechas = cliente.get("/cosechas", params={"desde": "2026-10-19", "hasta": "2026-11-08"}).json()
    assert datos["total_latas"] == sum(c["latas"] for c in cosechas)
    assert datos["total_pago"] == round(sum(c["pago"] for c in cosechas), 2)
    ritmos = [l["latas_por_hectarea"] for l in datos["rendimiento_lotes"]]
    assert ritmos == sorted(ritmos, reverse=True)


def test_planilla_con_fechas_al_reves_da_400(cliente):
    r = cliente.get("/planilla", params={"desde": "2026-11-08", "hasta": "2026-10-19"})
    assert r.status_code == 400


def test_exportar_cosechas_a_csv(cliente):
    r = cliente.get("/exportar/cosechas")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    primera = r.content.decode("utf-8-sig").splitlines()[0]
    assert primera.startswith("id,fecha,lote_nombre")


def test_respaldo_en_segundo_plano_crea_el_archivo(cliente):
    r = cliente.post("/respaldos")
    assert r.status_code == 201
    for _ in range(30):                       # el hilo termina en milisegundos
        archivos = [a["archivo"] for a in cliente.get("/respaldos").json()]
        if r.json()["archivo"] in archivos:
            break
        time.sleep(0.1)
    assert r.json()["archivo"] in archivos


# ---------- Café en bodega y ventas ----------
def test_inventario_parte_de_lo_producido_menos_lo_vendido(cliente):
    inv = cliente.get("/inventario").json()
    assert inv["disponible"] == round(inv["producido"] - inv["vendido"], 2)
    assert inv["disponible"] > 0
    assert sum(l["quintales"] for l in inv["por_lote"]) == inv["producido"]


def test_no_se_vende_mas_cafe_del_que_hay_en_bodega(cliente):
    disponible = cliente.get("/inventario").json()["disponible"]
    venta = {"fecha": "2026-11-08", "comprador": "Exportadora Santa Rosa",
             "quintales": disponible + 1, "precio_quintal": 8500}
    r = cliente.post("/ventas", json=venta)
    assert r.status_code == 400
    assert "No hay suficiente café en bodega" in r.json()["detail"]


def test_vender_descuenta_de_la_bodega(cliente):
    antes = cliente.get("/inventario").json()["disponible"]
    r = cliente.post("/ventas", json={"fecha": "2026-11-08", "comprador": "Beneficio Montecristo",
                                      "quintales": 5, "precio_quintal": 8500})
    assert r.status_code == 201
    assert cliente.get("/inventario").json()["disponible"] == round(antes - 5, 2)


def test_registrar_produccion_aumenta_la_bodega(cliente):
    antes = cliente.get("/inventario").json()["disponible"]
    r = cliente.post("/produccion", json={"lote_id": 1, "fecha": "2026-11-08", "quintales": 7.5})
    assert r.status_code == 201
    assert r.json()["lote_nombre"] == "El Mirador"
    assert cliente.get("/inventario").json()["disponible"] == round(antes + 7.5, 2)


def test_no_se_elimina_produccion_que_ya_se_vendio(cliente):
    disponible = cliente.get("/inventario").json()["disponible"]
    cliente.post("/ventas", json={"fecha": "2026-11-08", "comprador": "Café Selecto",
                                  "quintales": disponible, "precio_quintal": 8500})
    r = cliente.delete("/produccion/1")
    assert r.status_code == 400
    assert "ya se vendió" in r.json()["detail"]


def test_reporte_de_ventas_agrupa_por_comprador(cliente):
    r = cliente.get("/reportes/ventas").json()
    assert r["monto"] == round(sum(c["monto"] for c in r["por_comprador"]), 2)
    assert r["precio_promedio"] == round(r["monto"] / r["quintales"], 2)
