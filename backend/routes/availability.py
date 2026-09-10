"""Load / save a participant's painted slots; group heatmap."""
from flask import Blueprint, abort, g, jsonify, request

from db import get_db, now_iso
from routes import base_ctx, get_dates, get_participants, get_planner, meetup_view, my_slots
from services import mailer
from services.scheduling import (
    display_name, fmt_day_full, fmt_time, heatmap, parse_slot, valid_slots,
)
from tokens import require
from datetime import timedelta

from config import SLOT_MINUTES

bp = Blueprint("availability", __name__)


def windows_for(slots):
    """['2026-09-20T18:00', ...] -> ['Sat Sep 20: 6:00 PM to 10:00 PM', ...]"""
    out = []
    run_start = prev = None
    for s in sorted(slots):
        dt = parse_slot(s)
        if prev is not None and dt == prev + timedelta(minutes=SLOT_MINUTES):
            prev = dt
            continue
        if run_start is not None:
            out.append(_win(run_start, prev))
        run_start = prev = dt
    if run_start is not None:
        out.append(_win(run_start, prev))
    return out


def _win(a, b):
    end = b + timedelta(minutes=SLOT_MINUTES)
    return f"{fmt_day_full(a.date())}: {fmt_time(a)} to {fmt_time(end)}"


def save_slots(db, meetup, participant, slots):
    """Replace a participant's slots after validating against dates/hours/paint mode."""
    dates = get_dates(db, meetup["id"])
    allowed = valid_slots(dates, meetup["hour_start"], meetup["hour_end"])
    if meetup["paint_mode"] == "restricted" and participant["role"] != "planner":
        planner = get_planner(get_participants(db, meetup["id"]))
        allowed &= set(my_slots(db, planner["id"]))
    slots = sorted(set(str(s) for s in slots))
    if any(s not in allowed for s in slots):
        abort(400, description="Some times are outside what this meetup allows.")
    db.execute("DELETE FROM availability WHERE participant_id=?", (participant["id"],))
    db.executemany("INSERT INTO availability (participant_id, slot) VALUES (?,?)",
                   [(participant["id"], s) for s in slots])
    db.execute("UPDATE participants SET last_saved_at=? WHERE id=?", (now_iso(), participant["id"]))
    db.commit()
    return slots


def notify_planner_saved(db, meetup, participant, slots, nudge_line=None, subject=None):
    people = get_participants(db, meetup["id"])
    planner = get_planner(people)
    ctx = base_ctx(meetup, people, get_dates(db, meetup["id"]))
    responded = sum(1 for p in people if p["last_saved_at"])
    name = display_name(participant)
    mailer.send(
        "response_saved", planner["email"],
        subject or f'{name} sent their availability for "{meetup["title"]}"',
        dict(ctx, name=name, windows=windows_for(slots), responded_count=responded,
             nudge_line=nudge_line, no_form=False),
        meetup_id=meetup["id"], participant_id=participant["id"],
    )


@bp.get("/meetups/me/availability")
@require()
def get_availability():
    return jsonify({"slots": my_slots(get_db(), g.participant["id"])})


@bp.put("/meetups/me/availability")
@require()
def put_availability():
    if g.meetup["status"] != "collecting":
        abort(409, description="This meetup is already confirmed.")
    body = request.get_json(silent=True) or {}
    slots = body.get("slots")
    if not isinstance(slots, list):
        abort(400, description="Slots must be a list.")
    db = get_db()
    slots = save_slots(db, g.meetup, g.participant, slots)
    if g.participant["role"] == "invitee":
        notify_planner_saved(db, g.meetup, g.participant, slots)
    me = db.execute("SELECT * FROM participants WHERE id=?", (g.participant["id"],)).fetchone()
    return jsonify(meetup_view(db, g.meetup, me))


@bp.get("/meetups/me/heatmap")
@require()
def get_heatmap():
    db = get_db()
    people = get_participants(db, g.meetup["id"])
    return jsonify({
        "heatmap": heatmap(db, g.meetup["id"]),
        "names": {p["id"]: display_name(p) for p in people},
        "total": len(people),
    })
