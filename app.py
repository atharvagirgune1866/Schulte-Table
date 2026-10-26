"""
Schulte Table Brain Trainer - Backend
Flask + SQLite. Serves the frontend and exposes a small JSON API.

Run:  python app.py   ->  http://127.0.0.1:5000
"""
import json
import os
import sqlite3
from contextlib import closing

from flask import Flask, g, jsonify, request, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("SCHULTE_DB", os.path.join(BASE_DIR, "schulte.db"))

VALID_SIZES = {3, 4, 5, 6, 7}
VALID_MODES = {"classic", "reverse", "shuffle"}
MIN_SECONDS_PER_CELL = 0.12  # faster than this per cell is not humanly plausible

# static_url_path="" so /style.css, /script.js ... work (and the same relative
# paths also work when the folder is hosted on GitHub Pages).
app = Flask(__name__, static_folder="static", static_url_path="")

# Set CORS_ORIGIN to your GitHub Pages URL (e.g. https://user.github.io) when the
# frontend and backend are hosted on different domains. "*" allows anyone.
CORS_ORIGIN = os.environ.get("CORS_ORIGIN", "*")


@app.after_request
def add_cors(resp):
    if request.path.startswith("/api/"):
        resp.headers["Access-Control-Allow-Origin"] = CORS_ORIGIN
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resp


@app.route("/api/<path:_any>", methods=["OPTIONS"])
def preflight(_any):
    return ("", 204)


# ---------------------------------------------------------------- database
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with closing(sqlite3.connect(DB_PATH)) as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS scores (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                player     TEXT    NOT NULL,
                size       INTEGER NOT NULL,
                mode       TEXT    NOT NULL,
                time_sec   REAL    NOT NULL,
                mistakes   INTEGER NOT NULL DEFAULT 0,
                splits     TEXT,
                created_at TEXT    NOT NULL DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_scores_board
                ON scores (size, mode, time_sec);
            CREATE INDEX IF NOT EXISTS idx_scores_player
                ON scores (player);
            """
        )
        db.commit()


# ---------------------------------------------------------------- helpers
def clean_name(raw):
    name = " ".join(str(raw or "").split())[:20]
    return name or "Player"


def error(msg, code=400):
    return jsonify({"error": msg}), code


# ---------------------------------------------------------------- routes
@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/health")
def health():
    return jsonify({"ok": True})


@app.post("/api/scores")
def submit_score():
    data = request.get_json(silent=True) or {}

    try:
        size = int(data.get("size"))
        time_sec = float(data.get("time"))
        mistakes = int(data.get("mistakes", 0))
    except (TypeError, ValueError):
        return error("size, time and mistakes must be numbers")

    mode = data.get("mode", "classic")
    splits = data.get("splits") or []

    if size not in VALID_SIZES:
        return error("invalid size")
    if mode not in VALID_MODES:
        return error("invalid mode")
    if mistakes < 0 or mistakes > 500:
        return error("invalid mistakes")
    if not isinstance(splits, list) or len(splits) > size * size:
        return error("invalid splits")
    # basic anti-cheat: reject impossible times
    if time_sec < size * size * MIN_SECONDS_PER_CELL or time_sec > 3600:
        return error("time not plausible")

    db = get_db()
    player = clean_name(data.get("player"))

    prev = db.execute(
        "SELECT MIN(time_sec + 2*mistakes) AS best FROM scores "
        "WHERE player=? AND size=? AND mode=?",
        (player, size, mode),
    ).fetchone()["best"]

    cur = db.execute(
        "INSERT INTO scores (player, size, mode, time_sec, mistakes, splits) "
        "VALUES (?,?,?,?,?,?)",
        (player, size, mode, round(time_sec, 2), mistakes,
         json.dumps([round(float(s), 2) for s in splits])),
    )
    db.commit()

    final = round(time_sec + 2 * mistakes, 2)
    rank = db.execute(
        "SELECT COUNT(*) + 1 AS r FROM scores "
        "WHERE size=? AND mode=? AND (time_sec + 2*mistakes) < ?",
        (size, mode, final),
    ).fetchone()["r"]

    return jsonify({
        "id": cur.lastrowid,
        "final_score": final,
        "rank": rank,
        "is_personal_best": prev is None or final < prev,
    }), 201


@app.get("/api/leaderboard")
def leaderboard():
    size = request.args.get("size", 5, type=int)
    mode = request.args.get("mode", "classic")
    limit = min(request.args.get("limit", 10, type=int), 50)
    if size not in VALID_SIZES or mode not in VALID_MODES:
        return error("invalid size or mode")

    rows = get_db().execute(
        "SELECT player, time_sec, mistakes, created_at, "
        "       (time_sec + 2*mistakes) AS final "
        "FROM scores WHERE size=? AND mode=? "
        "ORDER BY final ASC, created_at ASC LIMIT ?",
        (size, mode, limit),
    ).fetchall()

    return jsonify([
        {
            "rank": i,
            "player": r["player"],
            "time": r["time_sec"],
            "mistakes": r["mistakes"],
            "score": round(r["final"], 2),
            "date": r["created_at"],
        }
        for i, r in enumerate(rows, start=1)
    ])


@app.get("/api/stats")
def stats():
    player = clean_name(request.args.get("player"))
    rows = get_db().execute(
        "SELECT size, mode, COUNT(*) AS games, "
        "       MIN(time_sec + 2*mistakes) AS best, "
        "       AVG(time_sec + 2*mistakes) AS avg "
        "FROM scores WHERE player=? GROUP BY size, mode ORDER BY size, mode",
        (player,),
    ).fetchall()

    recent = get_db().execute(
        "SELECT size, mode, time_sec, mistakes, created_at "
        "FROM scores WHERE player=? ORDER BY id DESC LIMIT 20",
        (player,),
    ).fetchall()

    return jsonify({
        "player": player,
        "summary": [
            {"size": r["size"], "mode": r["mode"], "games": r["games"],
             "best": round(r["best"], 2), "avg": round(r["avg"], 2)}
            for r in rows
        ],
        "recent": [
            {"size": r["size"], "mode": r["mode"], "score":
             round(r["time_sec"] + 2 * r["mistakes"], 2),
             "date": r["created_at"]}
            for r in recent
        ][::-1],
    })


init_db()

if __name__ == "__main__":
    # Debug only for local development. In production use gunicorn (see Procfile).
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
