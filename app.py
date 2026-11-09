"""Modul backend autentikasi Flask dengan antarmuka web interaktif."""

import os
import sqlite3

from flask import Flask, jsonify, render_template, request
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# Lokasi database bisa diatur lewat environment variable (dipakai saat testing)
DB_PATH = os.environ.get("DB_PATH", "users.db")
APP_VERSION = os.environ.get("APP_VERSION", "dev")


def get_db_connection():
    """Membuka koneksi ke basis data SQLite."""
    return sqlite3.connect(DB_PATH)


def init_db():
    """Inisialisasi basis data dan membuat data pengguna awal."""
    admin_password = os.environ.get("ADMIN_PASSWORD", "supersecret")
    conn = get_db_connection()
    cursor = conn.cursor()
    # PRIMARY KEY agar INSERT OR IGNORE benar-benar mencegah data ganda
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS users "
        "(username TEXT PRIMARY KEY, password_hash TEXT NOT NULL)"
    )
    cursor.execute(
        "INSERT OR IGNORE INTO users VALUES (?, ?)",
        ("admin", generate_password_hash(admin_password)),
    )
    conn.commit()
    conn.close()


def verify_user(username, password):
    """Memeriksa kredensial pengguna dengan parameterized query."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT password_hash FROM users WHERE username = ?", (username,)
    )
    row = cursor.fetchone()
    conn.close()
    return row is not None and check_password_hash(row[0], password)


@app.route("/", methods=["GET", "POST"])
def index():
    """Menampilkan formulir login dan memproses autentikasi."""
    message = None
    status_class = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if verify_user(username, password):
            message = "Login Berhasil! Selamat datang."
            status_class = "success"
        else:
            message = "Login Gagal! Kredensial tidak valid."
            status_class = "danger"
    return render_template(
        "index.html", message=message, status_class=status_class
    )


@app.route("/health", methods=["GET"])
def health():
    """Endpoint health check yang dipakai pipeline setelah deploy."""
    return jsonify(status="ok", version=APP_VERSION), 200

def about():
    """Menampilkan informasi aplikasi."""
    return jsonify(app="Sistem Login Aman", version=APP_VERSION)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)  # nosemgrep
