from modelos import Cosecha, Lote, Tarifa, Usuario, VentaCafe


def test_pago_de_una_cosecha():
    assert Cosecha(lote_id=1, trabajador_id=1, fecha="2026-11-08", latas=30).calcular_pago(35) == 1050


def test_rendimiento_de_un_lote():
    assert Lote(nombre="A", variedad="Catuaí", hectareas=2.0).rendimiento(50) == 25.0


def test_tarifa_vigente_para_una_fecha():
    t1 = Tarifa(temporada="A", precio_por_lata=30, fecha_inicio="2025-11-01", fecha_fin="2026-10-31")
    t2 = Tarifa(temporada="B", precio_por_lata=35, fecha_inicio="2026-11-01", fecha_fin="2027-10-31")
    assert Tarifa.vigente_para([t1, t2], "2026-10-31") is t1
    assert Tarifa.vigente_para([t1, t2], "2026-11-01") is t2
    assert Tarifa.vigente_para([t1, t2], "2030-01-01") is None


def test_total_de_una_venta():
    assert VentaCafe(fecha="2026-01-01", comprador="X", quintales=2.5, precio_quintal=8000).total() == 20000


def test_contrasena_encriptada_no_es_texto_plano():
    hash_ = Usuario.encriptar("secreta123")
    assert "secreta123" not in hash_
    u = Usuario(usuario="ana", nombre="Ana", password_hash=hash_)
    assert u.verificar("secreta123") and not u.verificar("otra")
    assert "password_hash" not in u.a_dict()
