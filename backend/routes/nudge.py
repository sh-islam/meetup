"""Nudge one person toward a time block, and the one-click Yes / No landing pages."""
from flask import Blueprint, abort, g, jsonify, render_template_string, request

import config
from db import get_db, now_iso
from routes import base_ctx, get_dates, get_participants, get_planner, meetup_view, my_slots, participant_url
from routes.availability import notify_planner_saved, save_slots
from services import mailer
from services.scheduling import (
    available_for_block, block_label, block_slots, display_name, heatmap, names_list, valid_slots,
)
from tokens import new_token, require

bp = Blueprint("nudge", __name__)


@bp.post("/meetups/me/nudge")
@require("planner")
def send_nudge():
    body = request.get_json(silent=True) or {}
    m = g.meetup
    if m["status"] != "collecting":
        abort(409, description="This meetup is already confirmed.")
    db = get_db()
    try:
        pid = int(body.get("participant_id"))
    except (TypeError, ValueError):
        abort(400, description="Pick a person to nudge.")
    target = db.execute("SELECT * FROM participants WHERE id=? AND meetup_id=?", (pid, m["id"])).fetchone()
    if not target or target["role"] == "planner":
        abort(400, description="Pick an invitee to nudge.")
    start, end = str(body.get("start") or ""), str(body.get("end") or "")
    dates = get_dates(db, m["id"])
    allowed = valid_slots(dates, m["hour_start"], m["hour_end"])
    slots = block_slots(start, end) if start and end else []
    if not slots or any(s not in allowed for s in slots):
        abort(400, description="Pick a time block inside the meetup's dates and hours.")

    people = get_participants(db, m["id"])
    hm = heatmap(db, m["id"])
    avail_ids = available_for_block(hm, start, end)
    others = [display_name(p) for p in people if p["id"] in avail_ids and p["id"] != target["id"]]
    avail_count = len(avail_ids - {target["id"]})

    token = new_token()
    db.execute(
        "INSERT INTO nudges (meetup_id, participant_id, block_start, block_end, token, sent_at) VALUES (?,?,?,?,?,?)",
        (m["id"], target["id"], start, end, token, now_iso()),
    )
    db.commit()

    ctx = base_ctx(m, people, dates)
    label = block_label(start, end)
    status = mailer.send(
        "nudge", target["email"],
        f"Can you make {label['weekday']} {label['date']} at {label['start']}? ({m['title']})",
        dict(ctx, name=display_name(target), url=participant_url(target["token"]), label=label,
             available_count=avail_count,
             available_percent=round(100 * avail_count / len(people)) if people else 0,
             other_names=names_list(others),
             yes_url=f"{config.API_PUBLIC_URL}/nudge/{token}/yes",
             no_url=f"{config.API_PUBLIC_URL}/nudge/{token}/no"),
        meetup_id=m["id"], participant_id=target["id"],
    )
    view = meetup_view(db, m, g.participant)
    view["mail_status"] = {target["email"]: status}
    return jsonify(view)


PAGE = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Meetup</title>
<style>
body{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#f6f7f9;color:#1c1f24}
main{max-width:520px;margin:12vh auto;padding:28px 24px;background:#fff;border-radius:14px;box-shadow:0 8px 30px rgba(0,0,0,.06)}
h1{font-size:22px;margin:0 0 10px} p{line-height:1.5;margin:8px 0} a.btn{display:inline-block;margin-top:14px;padding:10px 16px;border-radius:8px;background:#2563eb;color:#fff;text-decoration:none;font-weight:600}
.muted{color:#6b7280;font-size:14px}
</style></head><body><main>
<h1>{{ heading }}</h1>
<p>{{ body }}</p>
{% if url %}<a class="btn" href="{{ url }}">Open your times</a>{% endif %}
<p class="muted">Meetup</p>
</main></body></html>"""


def _page(heading, body, url=None, code=200):
    return render_template_string(PAGE, heading=heading, body=body, url=url), code


@bp.get("/nudge/<token>/<answer>")
def answer_nudge(token, answer):
    if answer not in ("yes", "no"):
        abort(404)
    db = get_db()
    n = db.execute("SELECT * FROM nudges WHERE token=?", (token,)).fetchone()
    if not n:
        return _page("This link isn't valid", "It may have been mistyped. Check the email you got.", code=404)
    m = db.execute("SELECT * FROM meetups WHERE id=?", (n["meetup_id"],)).fetchone()
    p = db.execute("SELECT * FROM participants WHERE id=?", (n["participant_id"],)).fetchone()
    if not m or not p:
        return _page("This link isn't valid", "The meetup no longer exists.", code=404)
    url = participant_url(p["token"])
    label = block_label(n["block_start"], n["block_end"])
    when = f"{label['weekday']} {label['date']}, {label['start']} to {label['end']}"
    people = get_participants(db, m["id"])
    planner = get_planner(people)
    planner_name = display_name(planner)

    if m["status"] != "collecting":
        return _page("This meetup is already confirmed", f'"{m["title"]}" has a time already. Open your link for the details.', url)

    db.execute("UPDATE nudges SET answer=?, answered_at=? WHERE id=?", (answer, now_iso(), n["id"]))
    db.commit()
    name = display_name(p)

    if answer == "yes":
        slots = sorted(set(my_slots(db, p["id"])) | set(block_slots(n["block_start"], n["block_end"])))
        slots = save_slots(db, m, p, slots)
        notify_planner_saved(
            db, m, p, slots,
            nudge_line=f"{name} said yes to your nudge for {when}.",
            subject=f"{name} said yes to {label['weekday']} {label['date']} at {label['start']}",
        )
        return _page(
            f"You're marked free for {when}",
            f'Thanks {name}. {planner_name} has been told. Changed your mind? Open your times and adjust them.',
            url,
        )

    ctx = base_ctx(m, people, get_dates(db, m["id"]))
    mailer.send(
        "response_saved", planner["email"],
        f"{name} said no to {label['weekday']} {label['date']} at {label['start']}",
        dict(ctx, name=name, windows=[], responded_count=0, no_form=True,
             nudge_line=f'{name} said no to your nudge for {when} for "{m["title"]}".'),
        meetup_id=m["id"], participant_id=p["id"],
    )
    return _page("Got it", f"{planner_name} has been told you can't make {when}. Your times are unchanged.", url)
