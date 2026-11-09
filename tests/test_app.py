"""Unit test untuk aplikasi Flask autentikasi."""

import pytest

import app as app_module


@pytest.fixture(name="client")
def fixture_client(tmp_path, monkeypatch):
    """Membuat test client dengan database sementara."""
    monkeypatch.setattr(app_module, "DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("ADMIN_PASSWORD", "rahasia123")
    app_module.init_db()
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as test_client:
        yield test_client


def test_halaman_login_tampil(client):
    """Halaman utama harus menampilkan form login."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Portal Login" in response.data


def test_login_berhasil(client):
    """Kredensial benar harus berhasil login."""
    response = client.post(
        "/", data={"username": "admin", "password": "rahasia123"}
    )
    assert b"Login Berhasil" in response.data


def test_login_gagal(client):
    """Password salah harus ditolak."""
    response = client.post(
        "/", data={"username": "admin", "password": "salah"}
    )
    assert b"Login Gagal" in response.data


def test_sql_injection_ditolak(client):
    """Payload SQL Injection klasik tidak boleh lolos login."""
    response = client.post(
        "/", data={"username": "admin' --", "password": "' OR '1'='1"}
    )
    assert b"Login Gagal" in response.data


def test_password_tidak_disimpan_plaintext(client):
    """Password di database harus berupa hash, bukan teks asli."""
    assert client is not None
    conn = app_module.get_db_connection()
    row = conn.execute(
        "SELECT password_hash FROM users WHERE username = 'admin'"
    ).fetchone()
    conn.close()
    assert row[0] != "rahasia123"


def test_health_check(client):
    """Endpoint /health harus mengembalikan status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_about(client):
    """Endpoint /about harus mengembalikan nama aplikasi."""
    response = client.get("/about")
    assert response.status_code == 200
    assert response.get_json()["app"] == "Sistem Login Aman"