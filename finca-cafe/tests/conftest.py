import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def cliente(tmp_path, monkeypatch):
    """Cliente con base temporal (copia fresca de crear_bd.sql) y sesión iniciada."""
    monkeypatch.setenv("FINCA_DB", str(tmp_path / "prueba.db"))
    monkeypatch.setenv("FINCA_RESPALDOS", str(tmp_path / "respaldos"))
    monkeypatch.setenv("FINCA_RESPALDO_AUTO", "0")
    from main import app

    with TestClient(app) as c:
        r = c.post("/auth/login", json={"usuario": "admin", "password": "admin123"})
        assert r.status_code == 200
        c.headers.update({"Authorization": f"Bearer {r.json()['token']}"})
        yield c


@pytest.fixture()
def sin_sesion(cliente):
    """Mismo servidor, pero sin el encabezado de autorización."""
    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app) as c:
        yield c
