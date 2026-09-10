"""Planner stats: ranked best windows and per-day summary."""
from flask import Blueprint, g, jsonify

from db import get_db
from routes import get_dates, get_participants
from services.scheduling import day_summary, heatmap, ranked_windows
from tokens import require

bp = Blueprint("stats", __name__)


@bp.get("/meetups/me/stats")
@require("planner")
def get_stats():
    db = get_db()
    m = g.meetup
    dates = get_dates(db, m["id"])
    people = get_participants(db, m["id"])
    hm = heatmap(db, m["id"])
    return jsonify({
        "windows": ranked_windows(dates, m["hour_start"], m["hour_end"], hm, people),
        "days": day_summary(dates, m["hour_start"], m["hour_end"], hm, people),
        "responded": sum(1 for p in people if p["last_saved_at"]),
        "total": len(people),
    })
