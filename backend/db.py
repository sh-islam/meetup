"""SQLite connection per request + schema bootstrap."""
import os
import sqlite3
from datetime import datetime, timezone

from flask import g

import config


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def get_db():
    if "db" not in g:
        conn = sqlite3.connect(config.DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(config.DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    with open(os.path.join(config.BASE_DIR, "schema.sql"), encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


def init_app(app):
    app.teardown_appcontext(close_db)
    init_db()


def rows(cur):
    return [dict(r) for r in cur.fetchall()]
