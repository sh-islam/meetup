"""Token generation and token-based auth. Role comes from the participant row."""
import secrets
from functools import wraps

from flask import abort, g, request

from db import get_db


def new_token(nbytes=12):
    return secrets.token_urlsafe(nbytes)


def load_participant():
    token = request.headers.get("X-Meetup-Token") or request.args.get("token")
    if not token:
        return None
    return get_db().execute("SELECT * FROM participants WHERE token = ?", (token,)).fetchone()


def require(role=None):
    """Decorator: resolve the token to g.participant / g.meetup, optionally enforce role."""

    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            p = load_participant()
            if p is None:
                abort(401, description="This link is not valid.")
            if role and p["role"] != role:
                abort(403, description="Only the planner can do that.")
            g.participant = p
            g.meetup = get_db().execute("SELECT * FROM meetups WHERE id = ?", (p["meetup_id"],)).fetchone()
            return fn(*args, **kwargs)

        return wrapper

    return deco
