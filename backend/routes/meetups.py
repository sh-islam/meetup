"""Create / read / update / confirm a meetup, manage invitees, set my name."""
import re
from datetime import date

from flask import Blueprint, abort, g, jsonify, request

import config
from db import get_db, now_iso
from routes import (
    base_ctx, get_dates, get_participants, get_planner, meetup_view, participant_url,
)
from services import mailer
from services.ics import build_ics
from services.scheduling import (
    available_for_block, block_label, block_slots, display_name, fmt_day_full, heatmap, valid_slots,
)
from tokens import new_token, require

bp = Blueprint("meetups", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ICONS = {"", "dice-5", "gamepad-2", "pizza", "utensils", "coffee", "beer", "cake", "party-popper", "film",
         "music", "dumbbell", "tent", "plane", "book-open"}


def _clean_icon(i):
    i = (i or "").strip()
    if i not in ICONS:
        abort(400, description="Unknown icon.")
    return i


# ---------- validation helpers ----------

def _clean_email(e):
    e = (e or "").strip().lower()
    if not EMAIL_RE.match(e):
        abort(400, description=f"'{e}' is not a valid email address.")
    return e


def _clean_dates(ds):
    if not isinstance(ds, list) or not ds:
        abort(400, description="Pick at least one date.")
    out = set()
    for d in ds:
        try:
            out.add(date.fromisoformat(str(d)).isoformat())
        except ValueError:
            abort(400, description=f"'{d}' is not a valid date.")
    if len(out) > config.MAX_DATES:
        abort(400, description=f"At most {config.MAX_DATES} dates.")
    return sorted(out)


def _clean_hours(hs, he):
    try:
        hs, he = int(hs), int(he)
    except (TypeError, ValueError):
        abort(400, description="Hours must be whole numbers.")
    if not (0 <= hs < he <= 24):
        abort(400, description="Start hour must be before end hour.")
    return hs, he


def _clean_mode(m):
    m = m or "free"
    if m not in ("free", "restricted"):
        abort(400, description="Unknown painting mode.")
    return m


def _clean_slots(slots, allowed):
    if slots is None:
        return []
    if not isinstance(slots, list):
        abort(400, description="Slots must be a list.")
    out = sorted(set(str(s) for s in slots))
    bad = [s for s in out if s not in allowed]
    if bad:
        abort(400, description="Some times are outside the meetup's dates or hours.")
    return out


def _clean_tz(tz):
    tz = (tz or "").strip() or "UTC"
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
    try:
        ZoneInfo(tz)
    except (ZoneInfoNotFoundError, ValueError):
        abort(400, description="Unknown timezone.")
    return tz


def _send_invite(db, meetup, invitee, ctx):
    name = display_name(invitee)
    status = mailer.send(
        "invite", invitee["email"],
        f"{ctx['planner_name']} wants to meet up: {meetup['title']}",
        dict(ctx, name=name, url=participant_url(invitee["token"])),
        meetup_id=meetup["id"], participant_id=invitee["id"],
    )
    return status


# ---------- routes ----------

@bp.post("/meetups")
def create_meetup():
    body = request.get_json(silent=True) or {}
    title = (body.get("title") or "").strip()
    if not title:
        abort(400, description="Give the meetup a title.")
    description = (body.get("description") or "").strip()
    location = (body.get("location") or "").strip()
    icon = _clean_icon(body.get("icon"))
    tz = _clean_tz(body.get("timezone"))
    hs, he = _clean_hours(body.get("hour_start", 8), body.get("hour_end", 24))
    dates = _clean_dates(body.get("dates"))
    mode = _clean_mode(body.get("paint_mode"))
    planner_in = body.get("planner") or {}
    planner_email = _clean_email(planner_in.get("email"))
    planner_name = (planner_in.get("name") or "").strip()
    if not planner_name:
        abort(400, description="Tell us your name.")
    invitees_in = body.get("invitees") or []
    seen = {planner_email}
    invitees = []
    for inv in invitees_in:
        em = _clean_email(inv.get("email") if isinstance(inv, dict) else inv)
        if em in seen:
            continue
        seen.add(em)
        invitees.append({"email": em, "name": (inv.get("name") or "").strip() or None if isinstance(inv, dict) else None})
    slots = _clean_slots(body.get("availability"), valid_slots(dates, hs, he))

    db = get_db()
    now = now_iso()
    cur = db.execute(
        "INSERT INTO meetups (title, description, location, icon, timezone, hour_start, hour_end, paint_mode, "
        "status, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,'collecting',?,?)",
        (title, description, location, icon, tz, hs, he, mode, now, now),
    )
    mid = cur.lastrowid
    db.executemany("INSERT INTO meetup_dates (meetup_id, date) VALUES (?,?)", [(mid, d) for d in dates])
    db.execute(
        "INSERT INTO participants (meetup_id, email, name, token, role, last_saved_at, created_at) "
        "VALUES (?,?,?,?,'planner',?,?)",
        (mid, planner_email, planner_name, new_token(), now if slots else None, now),
    )
    planner_id = db.execute("SELECT id FROM participants WHERE meetup_id=? AND role='planner'", (mid,)).fetchone()["id"]
    db.executemany("INSERT INTO availability (participant_id, slot) VALUES (?,?)", [(planner_id, s) for s in slots])
    for inv in invitees:
        db.execute(
            "INSERT INTO participants (meetup_id, email, name, token, role, created_at) VALUES (?,?,?,?,'invitee',?)",
            (mid, inv["email"], inv["name"], new_token(), now),
        )
    db.commit()

    meetup = db.execute("SELECT * FROM meetups WHERE id=?", (mid,)).fetchone()
    people = get_participants(db, mid)
    planner = get_planner(people)
    ctx = base_ctx(meetup, people, dates)

    mail = {}
    mail[planner["email"]] = mailer.send(
        "planner_link", planner["email"], f'Your planner link for "{title}"', ctx,
        meetup_id=mid, participant_id=planner["id"],
    )
    for p in people:
        if p["role"] == "invitee":
            mail[p["email"]] = _send_invite(db, meetup, p, ctx)

    view = meetup_view(db, meetup, planner)
    view["planner_token"] = planner["token"]
    view["mail_status"] = mail
    return jsonify(view), 201


@bp.get("/meetups/me")
@require()
def get_me():
    return jsonify(meetup_view(get_db(), g.meetup, g.participant))


@bp.put("/meetups/me/name")
@require()
def set_name():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        abort(400, description="Name can't be empty.")
    db = get_db()
    db.execute("UPDATE participants SET name=? WHERE id=?", (name[:80], g.participant["id"]))
    db.commit()
    me = db.execute("SELECT * FROM participants WHERE id=?", (g.participant["id"],)).fetchone()
    return jsonify(meetup_view(db, g.meetup, me))


@bp.patch("/meetups/me")
@require("planner")
def update_meetup():
    body = request.get_json(silent=True) or {}
    m = g.meetup
    if m["status"] != "collecting":
        abort(409, description="This meetup is already confirmed.")
    db = get_db()
    old_dates = get_dates(db, m["id"])

    title = (body.get("title") if "title" in body else m["title"]) or ""
    title = title.strip()
    if not title:
        abort(400, description="Give the meetup a title.")
    description = (body.get("description") if "description" in body else m["description"]) or ""
    location = (body.get("location") if "location" in body else m["location"]) or ""
    icon = _clean_icon(body.get("icon")) if "icon" in body else m["icon"]
    hs, he = _clean_hours(body.get("hour_start", m["hour_start"]), body.get("hour_end", m["hour_end"]))
    dates = _clean_dates(body["dates"]) if "dates" in body else old_dates
    mode = _clean_mode(body.get("paint_mode", m["paint_mode"]))

    changes = []
    if title != m["title"]:
        changes.append(f'Title: now "{title}"')
    if description.strip() != (m["description"] or "").strip():
        changes.append("Description was updated")
    if location.strip() != (m["location"] or ""):
        changes.append(f"Location: now {location.strip() or 'to be announced'}")
    if dates != old_dates:
        added = [fmt_day_full(d) for d in dates if d not in old_dates]
        removed = [fmt_day_full(d) for d in old_dates if d not in dates]
        parts = []
        if added:
            parts.append("added " + ", ".join(added))
        if removed:
            parts.append("removed " + ", ".join(removed))
        changes.append("Dates: " + "; ".join(parts))
    if (hs, he) != (m["hour_start"], m["hour_end"]):
        from services.scheduling import fmt_time
        from datetime import datetime
        f = lambda h: fmt_time(datetime(2000, 1, 1 + (h // 24), h % 24, 0))  # noqa: E731
        changes.append(f"Hours: now {f(hs)} to {f(he)}")

    db.execute(
        "UPDATE meetups SET title=?, description=?, location=?, icon=?, hour_start=?, hour_end=?, paint_mode=?, updated_at=? "
        "WHERE id=?",
        (title, description.strip(), location.strip(), icon, hs, he, mode, now_iso(), m["id"]),
    )
    if dates != old_dates:
        db.execute("DELETE FROM meetup_dates WHERE meetup_id=?", (m["id"],))
        db.executemany("INSERT INTO meetup_dates (meetup_id, date) VALUES (?,?)", [(m["id"], d) for d in dates])
    if dates != old_dates or (hs, he) != (m["hour_start"], m["hour_end"]):
        allowed = valid_slots(dates, hs, he)
        cur = db.execute(
            "SELECT a.participant_id, a.slot FROM availability a JOIN participants p ON p.id=a.participant_id "
            "WHERE p.meetup_id=?", (m["id"],))
        stale = [(pid, s) for pid, s in cur.fetchall() if s not in allowed]
        db.executemany("DELETE FROM availability WHERE participant_id=? AND slot=?", stale)
    db.commit()

    meetup = db.execute("SELECT * FROM meetups WHERE id=?", (m["id"],)).fetchone()
    people = get_participants(db, m["id"])
    if changes:
        ctx = base_ctx(meetup, people, dates)
        for p in people:
            if p["role"] == "invitee":
                mailer.send(
                    "meetup_updated", p["email"], f'"{title}" was updated',
                    dict(ctx, name=display_name(p), url=participant_url(p["token"]), changes=changes),
                    meetup_id=m["id"], participant_id=p["id"],
                )
    me = db.execute("SELECT * FROM participants WHERE id=?", (g.participant["id"],)).fetchone()
    view = meetup_view(db, meetup, me)
    view["changes"] = changes
    return jsonify(view)


@bp.post("/meetups/me/invitees")
@require("planner")
def add_invitees():
    body = request.get_json(silent=True) or {}
    m = g.meetup
    db = get_db()
    existing = {p["email"] for p in get_participants(db, m["id"])}
    added = []
    for inv in body.get("invitees") or []:
        em = _clean_email(inv.get("email") if isinstance(inv, dict) else inv)
        if em in existing:
            continue
        existing.add(em)
        nm = (inv.get("name") or "").strip() or None if isinstance(inv, dict) else None
        db.execute(
            "INSERT INTO participants (meetup_id, email, name, token, role, created_at) VALUES (?,?,?,?,'invitee',?)",
            (m["id"], em, nm, new_token(), now_iso()),
        )
        added.append(em)
    db.commit()
    people = get_participants(db, m["id"])
    ctx = base_ctx(m, people, get_dates(db, m["id"]))
    mail = {}
    for p in people:
        if p["email"] in added:
            mail[p["email"]] = _send_invite(db, m, p, ctx)
    view = meetup_view(db, m, g.participant)
    view["mail_status"] = mail
    return jsonify(view)


@bp.delete("/meetups/me/invitees/<int:pid>")
@require("planner")
def remove_invitee(pid):
    db = get_db()
    p = db.execute("SELECT * FROM participants WHERE id=? AND meetup_id=?", (pid, g.meetup["id"])).fetchone()
    if not p:
        abort(404, description="No such person.")
    if p["role"] == "planner":
        abort(400, description="The planner can't be removed.")
    db.execute("DELETE FROM participants WHERE id=?", (pid,))
    db.commit()
    return jsonify(meetup_view(db, g.meetup, g.participant))


@bp.post("/meetups/me/confirm")
@require("planner")
def confirm():
    body = request.get_json(silent=True) or {}
    m = g.meetup
    if m["status"] != "collecting":
        abort(409, description="This meetup is already confirmed.")
    start, end = str(body.get("start") or ""), str(body.get("end") or "")
    db = get_db()
    dates = get_dates(db, m["id"])
    allowed = valid_slots(dates, m["hour_start"], m["hour_end"])
    slots = block_slots(start, end) if start and end else []
    if not slots or any(s not in allowed for s in slots):
        abort(400, description="Pick a time block inside the meetup's dates and hours.")

    people = get_participants(db, m["id"])
    hm = heatmap(db, m["id"])
    coming_ids = available_for_block(hm, start, end)
    coming = [display_name(p) for p in people if p["id"] in coming_ids]

    db.execute(
        "UPDATE meetups SET status='confirmed', confirmed_start=?, confirmed_end=?, updated_at=? WHERE id=?",
        (start, end, now_iso(), m["id"]),
    )
    db.commit()
    meetup = db.execute("SELECT * FROM meetups WHERE id=?", (m["id"],)).fetchone()

    ctx = base_ctx(meetup, people, dates)
    label = block_label(start, end)
    ics = build_ics(meetup, start, end, coming)
    for p in people:
        mailer.send(
            "confirmed", p["email"],
            f"It's on: {meetup['title']}, {label['weekday']} {label['date']} at {label['start']}",
            dict(ctx, name=display_name(p), url=participant_url(p["token"]),
                 attendee_names=coming, label=label),
            meetup_id=m["id"], participant_id=p["id"],
            attachments=[("meetup.ics", "text/calendar", ics)],
        )
    return jsonify(meetup_view(db, meetup, g.participant))


@bp.post("/meetups/me/leave")
@require("invitee")
def leave_meetup():
    """An invitee drops out: their times and link go away; the planner is told by email."""
    db = get_db()
    m = g.meetup
    me = g.participant
    people = get_participants(db, m["id"])
    planner = get_planner(people)
    ctx = base_ctx(m, people, get_dates(db, m["id"]))
    name = display_name(me)
    db.execute("DELETE FROM participants WHERE id=?", (me["id"],))
    db.commit()
    remaining = get_participants(db, m["id"])
    mailer.send(
        "dropped_out", planner["email"], f'{name} dropped out of "{m["title"]}"',
        dict(ctx, name=name, people_count=len(remaining),
             responded_count=sum(1 for p in remaining if p["last_saved_at"])),
        meetup_id=m["id"], participant_id=planner["id"],
    )
    return jsonify({"ok": True})


@bp.delete("/meetups/me")
@require("planner")
def delete_meetup():
    """Delete the meetup for everyone. Invitees are told by email (cancelled) when mail is configured."""
    db = get_db()
    m = g.meetup
    people = get_participants(db, m["id"])
    ctx = base_ctx(m, people, get_dates(db, m["id"]))
    for p in people:
        if p["role"] == "invitee":
            mailer.send(
                "cancelled", p["email"], f'"{m["title"]}" is off',
                dict(ctx, name=display_name(p)),
                meetup_id=m["id"], participant_id=p["id"],
            )
    db.execute("DELETE FROM meetups WHERE id=?", (m["id"],))
    db.commit()
    return jsonify({"ok": True})


@bp.post("/meetups/me/reopen")
@require("planner")
def reopen():
    """Undo a confirmation (no email; the planner can re-confirm)."""
    db = get_db()
    db.execute(
        "UPDATE meetups SET status='collecting', confirmed_start=NULL, confirmed_end=NULL, updated_at=? WHERE id=?",
        (now_iso(), g.meetup["id"]),
    )
    db.commit()
    meetup = db.execute("SELECT * FROM meetups WHERE id=?", (g.meetup["id"],)).fetchone()
    return jsonify(meetup_view(db, meetup, g.participant))
