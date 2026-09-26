from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, csv, io, os, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "database.sqlite3"
FRONTEND = ROOT / "frontend"

app = Flask(__name__, template_folder=str(FRONTEND), static_folder=str(FRONTEND / "static"))
app.secret_key = os.environ.get("SECRET_KEY", "CHANGE_THIS_SECRET_KEY_IN_PRODUCTION")

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'viewer'
    );

    CREATE TABLE IF NOT EXISTS penerima (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nik TEXT UNIQUE NOT NULL,
        nama_lengkap TEXT NOT NULL,
        alamat TEXT,
        desa TEXT,
        kecamatan TEXT,
        kabupaten TEXT,
        desil INTEGER,
        status_penerima TEXT,
        keterangan TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    admin = conn.execute("SELECT id FROM users WHERE username='admin'").fetchone()
    if not admin:
        conn.execute(
            "INSERT INTO users(username,password_hash,role) VALUES(?,?,?)",
            ("admin", generate_password_hash("admin123"), "admin")
        )
    sample = conn.execute("SELECT id FROM penerima LIMIT 1").fetchone()
    if not sample:
        rows = [
            ("7300000000000001","CONTOH NAMA 1","Jl. Contoh No. 1","Desa A","Kecamatan A","Kabupaten A",1,"Layak","Data contoh"),
            ("7300000000000002","CONTOH NAMA 2","Jl. Contoh No. 2","Desa B","Kecamatan B","Kabupaten B",2,"Layak","Data contoh")
        ]
        conn.executemany("""INSERT INTO penerima
            (nik,nama_lengkap,alamat,desa,kecamatan,kabupaten,desil,status_penerima,keterangan)
            VALUES(?,?,?,?,?,?,?,?,?)""", rows)
    conn.commit()
    conn.close()

def login_required():
    return session.get("user") is not None

@app.route("/")
def index():
    if not login_required():
        return redirect(url_for("login"))
    return render_template("index.html", user=session["user"])

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","")
        conn = db()
        user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password_hash"], password):
            session["user"] = {"username": user["username"], "role": user["role"]}
            return redirect(url_for("index"))
        flash("Username atau password salah.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.get("/api/penerima/<nik>")
def api_penerima(nik):
    if not login_required():
        return jsonify({"error":"unauthorized"}), 401
    if not re.fullmatch(r"\d{16}", nik):
        return jsonify({"error":"NIK harus 16 digit"}), 400
    conn = db()
    row = conn.execute("SELECT * FROM penerima WHERE nik=?", (nik,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"found":False,"message":"Data tidak ditemukan"}), 404
    return jsonify({"found":True,"data":dict(row)})

@app.post("/api/import")
def api_import():
    if not login_required() or session["user"]["role"] != "admin":
        return jsonify({"error":"forbidden"}), 403
    if "file" not in request.files:
        return jsonify({"error":"file CSV wajib diunggah"}), 400
    raw = request.files["file"].read()
    try:
        text = raw.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        required = {"NIK","NAMA_LENGKAP"}
        if not required.issubset(set(reader.fieldnames or [])):
            return jsonify({"error":"Kolom minimal: NIK,NAMA_LENGKAP"}), 400
        conn = db()
        count = 0
        for r in reader:
            nik = (r.get("NIK") or "").strip()
            if not re.fullmatch(r"\d{16}", nik):
                continue
            conn.execute("""INSERT INTO penerima
                (nik,nama_lengkap,alamat,desa,kecamatan,kabupaten,desil,status_penerima,keterangan)
                VALUES(?,?,?,?,?,?,?,?,?)
                ON CONFLICT(nik) DO UPDATE SET
                nama_lengkap=excluded.nama_lengkap,
                alamat=excluded.alamat,
                desa=excluded.desa,
                kecamatan=excluded.kecamatan,
                kabupaten=excluded.kabupaten,
                desil=excluded.desil,
                status_penerima=excluded.status_penerima,
                keterangan=excluded.keterangan,
                updated_at=CURRENT_TIMESTAMP
            """, (
                nik, r.get("NAMA_LENGKAP",""), r.get("ALAMAT",""),
                r.get("DESA",""), r.get("KECAMATAN",""), r.get("KABUPATEN",""),
                int(r["DESIL"]) if str(r.get("DESIL","")).isdigit() else None,
                r.get("STATUS_PENERIMA",""), r.get("KETERANGAN","")
            ))
            count += 1
        conn.commit()
        conn.close()
        return jsonify({"success":True,"processed":count})
    except Exception as e:
        return jsonify({"error":str(e)}), 400

if __name__ == "__main__":
    DB.parent.mkdir(parents=True, exist_ok=True)
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
