"""
Cricket Registration - Flask Backend
Runs alongside nginx on SUSE Linux.
Data is persisted to data/registrations.json on disk.

Start:  python3 server.py
        (or use gunicorn for production: gunicorn -w 1 -b 127.0.0.1:5000 server:app)
"""

import json
import os
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

# ── Storage ──────────────────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).parent
DATA_DIR  = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "registrations.json"


def load_data() -> list:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_data(data: list) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = DATA_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(DATA_FILE)          # atomic write – avoids corrupt file on crash


# ── API routes ────────────────────────────────────────────────────────────────

@app.route("/api/registrations", methods=["GET"])
def get_registrations():
    return jsonify(load_data())


@app.route("/api/registrations", methods=["POST"])
def add_registration():
    team = request.get_json(silent=True)
    if not team or not isinstance(team, dict):
        return jsonify({"error": "Invalid JSON body"}), 400

    required = {"teamName", "captain", "players"}
    if not required.issubset(team.keys()):
        return jsonify({"error": f"Missing fields: {required - team.keys()}"}), 400

    if not isinstance(team["players"], list) or len(team["players"]) != 6:
        return jsonify({"error": "Exactly 6 players required"}), 400

    data = load_data()

    # Server-side duplicate check
    if any(s.get("teamName", "").strip().lower() == team["teamName"].strip().lower()
           for s in data):
        return jsonify({"error": f"Team '{team['teamName']}' already registered"}), 409

    # Server-side gender composition check
    males   = sum(1 for p in team["players"] if p.get("gender") == "Male")
    females = sum(1 for p in team["players"] if p.get("gender") == "Female")
    if males != 5 or females != 1:
        return jsonify({
            "error": f"Invalid composition: {males} Male, {females} Female. Need 5M + 1F."
        }), 422

    data.append(team)
    save_data(data)
    return jsonify({"success": True, "total": len(data)}), 201


@app.route("/api/registrations/<int:idx>", methods=["DELETE"])
def delete_registration(idx: int):
    data = load_data()
    if idx < 0 or idx >= len(data):
        return jsonify({"error": "Index out of range"}), 404
    data.pop(idx)
    save_data(data)
    return jsonify({"success": True, "remaining": len(data)})


# ── Availability ───────────────────────────────────────────────────────────────────
AVAILABILITY_FILE = DATA_DIR / "availability.json"


def load_availability() -> list:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if AVAILABILITY_FILE.exists():
        with open(AVAILABILITY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_availability(data: list) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = AVAILABILITY_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(AVAILABILITY_FILE)


@app.route("/api/availability", methods=["GET"])
def get_availability():
    return jsonify(load_availability())


@app.route("/api/availability", methods=["POST"])
def add_availability():
    entry = request.get_json(silent=True)
    if not entry or not isinstance(entry, dict):
        return jsonify({"error": "Invalid JSON body"}), 400

    required = {"name", "role", "availability"}
    if not required.issubset(entry.keys()):
        return jsonify({"error": f"Missing fields: {required - entry.keys()}"}), 400

    if entry["role"] not in ("Batting", "Bowling", "All Rounder"):
        return jsonify({"error": "Invalid role"}), 400

    if entry["availability"] not in ("Available", "Not Available"):
        return jsonify({"error": "Invalid availability value"}), 400

    data = load_availability()
    if any(e.get("name", "").strip().lower() == entry["name"].strip().lower()
           for e in data):
        return jsonify({"error": f"'{entry['name']}' has already responded"}), 409

    data.append(entry)
    save_availability(data)
    return jsonify({"success": True, "total": len(data)}), 201


@app.route("/api/availability/<int:idx>", methods=["DELETE"])
def delete_availability(idx: int):
    data = load_availability()
    if idx < 0 or idx >= len(data):
        return jsonify({"error": "Index out of range"}), 404
    data.pop(idx)
    save_availability(data)
    return jsonify({"success": True, "remaining": len(data)})


# ── Media uploads ─────────────────────────────────────────────────────────────
import time as _time
from werkzeug.utils import secure_filename

UPLOAD_DIR  = BASE_DIR / "uploads"
ALLOWED_VID = {'mp4', 'webm', 'mov', 'avi', 'mkv'}
ALLOWED_IMG = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
ALLOWED_EXT = ALLOWED_VID | ALLOWED_IMG


def _ext(name: str) -> str:
    return name.rsplit('.', 1)[-1].lower() if '.' in name else ''


@app.route("/api/media", methods=["GET"])
def list_media():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    files = []
    for f in sorted(UPLOAD_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if f.is_file():
            ext = f.suffix.lower().lstrip('.')
            files.append({"name": f.name, "type": "video" if ext in ALLOWED_VID else "image",
                          "url": f"/uploads/{f.name}", "size": f.stat().st_size})
    return jsonify(files)


@app.route("/api/upload", methods=["POST"])
def upload_media():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    f = request.files['file']
    if not f.filename:
        return jsonify({"error": "Empty filename"}), 400
    ext = _ext(f.filename)
    if ext not in ALLOWED_EXT:
        return jsonify({"error": f"Type .{ext} not allowed. Use jpg/png/gif/webp/mp4/webm/mov"}), 415
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    base = secure_filename(f.filename.rsplit('.', 1)[0])
    filename = f"{base}_{int(_time.time())}.{ext}"
    f.save(UPLOAD_DIR / filename)
    return jsonify({"success": True, "filename": filename, "url": f"/uploads/{filename}"}), 201


@app.route("/api/media/<path:filename>", methods=["DELETE"])
def delete_media(filename):
    safe = secure_filename(filename)
    path = UPLOAD_DIR / safe
    if not path.exists():
        return jsonify({"error": "Not found"}), 404
    path.unlink()
    return jsonify({"success": True})


# ── Serve the static HTML ──────────────────────────────────────────────────
# Pretty (extensionless) routes that nginx used to map to .html files.
PRETTY_ROUTES = {
    "":             "home.html",
    "cricket":      "cricket.html",
    "carrom":       "carrom.html",
    "admin":        "admin.html",
    "register":     "index.html",
    "availability": "availability.html",
    "schedule":     "schedule.html",
    "gallery":      "gallery.html",
}


@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(UPLOAD_DIR, filename)


@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"})


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_static(path):
    # Never expose the on-disk data folder (nginx used to deny it).
    if path == "data" or path.startswith("data/"):
        return jsonify({"error": "Forbidden"}), 403
    if path in PRETTY_ROUTES:
        path = PRETTY_ROUTES[path]
    return send_from_directory(BASE_DIR, path)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # Bind only to localhost; nginx will reverse-proxy from port 80
    app.run(host="127.0.0.1", port=port, debug=False)
