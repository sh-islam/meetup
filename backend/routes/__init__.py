"""Shared helpers for route modules: loading a meetup's people/dates, building views and email context."""
import config
from db import rows
from services.scheduling import (
    display_name,
    fmt_day_full,
    heatmap,
    ranked_windows,
)


def participant_url(token):
    return f"{config.FRONTEND_URL}#/m/{token}"


def get_dates(db, meetup_id):
    return [r["date"] for r in db.execute(
        "SELECT date FROM meetup_dates WHERE meetup_id = ? ORDER BY date", (meetup_id,)).fetchall()]


def get_participants(db, meetup_id):
    return rows(db.execute(
        "SELECT * FROM participants WHERE meetup_id = ? ORDER BY role = 'planner' DESC, id", (meetup_id,)))


def get_planner(participants):
    return next(p for p in participants if p["role"] == "planner")


def my_slots(db, participant_id):
    return [r["slot"] for r in db.execute(
        "SELECT slot FROM availability WHERE participant_id = ? ORDER BY slot", (participant_id,)).fetchall()]


def base_ctx(meetup, participants, dates):
    """Context every email template can rely on."""
    planner = get_planner(participants)
    return {
        "title": meetup["title"],
        "description": meetup["description"],
        "location": meetup["location"],
        "timezone": meetup["timezone"],
        "planner_name": display_name(planner),
        "planner_url": participant_url(planner["token"]),
        "people_count": len(participants),
        "invited_count": len(participants) - 1,
        "date_list": [fmt_day_full(d) for d in dates],
        "frontend_url": config.FRONTEND_URL,
    }


def latest_nudges(db, meetup_id):
    """participant_id -> most recent nudge row (as dict)."""
    out = {}
    for r in db.execute(
        "SELECT * FROM nudges WHERE meetup_id = ? ORDER BY sent_at", (meetup_id,)).fetchall():
        out[r["participant_id"]] = dict(r)
    return out


def meetup_view(db, meetup, me):
    """Everything the frontend needs for one screen, filtered by role."""
    mid = meetup["id"]
    dates = get_dates(db, mid)
    people = get_participants(db, mid)
    planner = get_planner(people)
    is_planner = me["role"] == "planner"
    nudges = latest_nudges(db, mid) if is_planner else {}

    plist = []
    for p in people:
        item = {
            "id": p["id"],
            "name": display_name(p),
            "has_name": bool(p["name"]),
            "role": p["role"],
            "responded": p["last_saved_at"] is not None,
        }
        if is_planner:
            item["email"] = p["email"]
            item["url"] = participant_url(p["token"])
            n = nudges.get(p["id"])
            item["nudge"] = None if not n else {
                "block_start": n["block_start"], "block_end": n["block_end"],
                "answer": n["answer"], "sent_at": n["sent_at"], "answered_at": n["answered_at"],
            }
        plist.append(item)

    hm = heatmap(db, mid)
    best = ranked_windows(dates, meetup["hour_start"], meetup["hour_end"], hm, people, limit=1)

    return {
        "meetup": {
            "id": mid,
            "title": meetup["title"],
            "description": meetup["description"],
            "location": meetup["location"],
            "icon": meetup["icon"],
            "timezone": meetup["timezone"],
            "hour_start": meetup["hour_start"],
            "hour_end": meetup["hour_end"],
            "paint_mode": meetup["paint_mode"],
            "status": meetup["status"],
            "confirmed_start": meetup["confirmed_start"],
            "confirmed_end": meetup["confirmed_end"],
            "dates": dates,
        },
        "me": {
            "id": me["id"],
            "name": me["name"],
            "display_name": display_name(me),
            "email": me["email"],
            "role": me["role"],
        },
        "participants": plist,
        "my_slots": my_slots(db, me["id"]),
        "planner_slots": my_slots(db, planner["id"]),
        "heatmap": hm,
        "best": best[0] if best else None,
        "responded": sum(1 for p in people if p["last_saved_at"]),
        "mail_configured": config.mail_configured(),
    }
