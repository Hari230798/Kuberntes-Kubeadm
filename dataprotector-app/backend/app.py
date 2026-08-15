import os
import time

import mysql.connector
from mysql.connector import Error
from flask import Flask, request, jsonify, abort
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------------------------
# Configuration (all values injected via environment / Kubernetes Secrets)
# ---------------------------------------------------------------------------
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "mysql"),
    "port": int(os.environ.get("DB_PORT", "3306")),
    "user": os.environ.get("DB_USER", "appuser"),
    "password": os.environ.get("DB_PASSWORD", "AppPass123"),
    "database": os.environ.get("DB_NAME", "dataprotector"),
}

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin@123")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "super-secret-admin-token")

VALID_STATUSES = {"Pending", "Approved", "Rejected"}


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def init_db():
    """Create the engineers table, retrying until MySQL is reachable."""
    last_error = None
    for attempt in range(1, 31):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS engineers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    experience VARCHAR(50) NOT NULL,
                    contact VARCHAR(20) NOT NULL,
                    qualification VARCHAR(100) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'Pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
            cur.close()
            conn.close()
            print("Database initialised.", flush=True)
            return
        except Error as exc:  # pragma: no cover - startup path
            last_error = exc
            print(f"[init_db] attempt {attempt}: DB not ready ({exc})", flush=True)
            time.sleep(5)
    raise RuntimeError(f"Database not available after retries: {last_error}")


def require_admin():
    auth = request.headers.get("Authorization", "")
    token = auth[7:] if auth.startswith("Bearer ") else auth
    if token != ADMIN_TOKEN:
        abort(401, description="Invalid or missing admin token")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/api/engineers", methods=["POST"])
def add_engineer():
    """Public endpoint: a support engineer submits their details."""
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get("name") or "").strip()
    experience = (data.get("experience") or "").strip()
    contact = (data.get("contact") or "").strip()
    qualification = (data.get("qualification") or "").strip()

    if not all([name, experience, contact, qualification]):
        return jsonify({"error": "name, experience, contact and qualification are required"}), 400

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO engineers (name, experience, contact, qualification, status) "
        "VALUES (%s, %s, %s, %s, 'Pending')",
        (name, experience, contact, qualification),
    )
    conn.commit()
    new_id = cur.lastrowid
    cur.close()
    conn.close()
    return jsonify({"message": "Details submitted successfully", "id": new_id}), 201


@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json(force=True, silent=True) or {}
    if data.get("username") == ADMIN_USERNAME and data.get("password") == ADMIN_PASSWORD:
        return jsonify({"token": ADMIN_TOKEN}), 200
    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/api/engineers", methods=["GET"])
def list_engineers():
    """Admin only: list all submitted engineers."""
    require_admin()
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT id, name, experience, contact, qualification, status, created_at "
        "FROM engineers ORDER BY created_at DESC"
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    for row in rows:
        if row.get("created_at") is not None:
            row["created_at"] = row["created_at"].isoformat()
    return jsonify(rows), 200


@app.route("/api/engineers/<int:engineer_id>", methods=["PUT"])
def validate_engineer(engineer_id):
    """Admin only: approve or reject an engineer record."""
    require_admin()
    data = request.get_json(force=True, silent=True) or {}
    status = (data.get("status") or "").strip().capitalize()
    if status not in VALID_STATUSES:
        return jsonify({"error": f"status must be one of {sorted(VALID_STATUSES)}"}), 400

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE engineers SET status = %s WHERE id = %s", (status, engineer_id))
    conn.commit()
    affected = cur.rowcount
    cur.close()
    conn.close()
    if affected == 0:
        return jsonify({"error": "Engineer not found"}), 404
    return jsonify({"message": f"Engineer {engineer_id} set to {status}"}), 200


# Initialise the schema at import time so it also runs under gunicorn workers.
init_db()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
