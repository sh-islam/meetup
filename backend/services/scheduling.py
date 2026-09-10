"""Slot math, formatting, heatmap aggregation and 'best window' ranking."""
from datetime import date, datetime, timedelta

from config import SLOT_MINUTES

SLOT_FMT = "%Y-%m-%dT%H:%M"


# ---------- parsing / formatting ----------

def parse_slot(s):
    return datetime.strptime(s, SLOT_FMT)


def fmt_slot(dt):
    return dt.strftime(SLOT_FMT)


def fmt_time(dt):
    h = dt.hour % 12 or 12
    ampm = "AM" if dt.hour < 12 else "PM"
    return f"{h}:{dt.minute:02d} {ampm}"


def fmt_weekday(d):
    if isinstance(d, str):
        d = date.fromisoformat(d[:10])
    return d.strftime("%a")


def fmt_date(d):
    """'Sep 20' (no weekday; templates print {weekday} {date})."""
    if isinstance(d, str):
        d = date.fromisoformat(d[:10])
    return f"{d.strftime('%b')} {d.day}"


def fmt_day_full(d):
    """'Sat Sep 20'"""
    return f"{fmt_weekday(d)} {fmt_date(d)}"


def names_list(names):
    names = [n for n in names if n]
    if not names:
        return "nobody"
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


def display_name(p):
    """Participant row/dict -> name or email prefix."""
    name = p["name"] if p["name"] else None
    if name:
        return name
    return p["email"].split("@")[0]


# ---------- slots ----------

def day_slots(d, hour_start, hour_end):
    """All slot strings for one date within [hour_start, hour_end)."""
    if isinstance(d, str):
        d = date.fromisoformat(d)
    start = datetime.combine(d, datetime.min.time()) + timedelta(hours=hour_start)
    n = (hour_end - hour_start) * 60 // SLOT_MINUTES
    return [fmt_slot(start + timedelta(minutes=SLOT_MINUTES * i)) for i in range(n)]


def valid_slots(dates, hour_start, hour_end):
    out = set()
    for d in dates:
        out.update(day_slots(d, hour_start, hour_end))
    return out


def block_slots(start, end):
    """Slot strings covering [start, end) where start/end are slot strings; end exclusive."""
    s, e = parse_slot(start), parse_slot(end)
    out = []
    while s < e:
        out.append(fmt_slot(s))
        s += timedelta(minutes=SLOT_MINUTES)
    return out


def block_label(start, end):
    """'Sat Sep 20, 7:00 PM to 10:00 PM' -> dict of pieces for templates."""
    s, e = parse_slot(start), parse_slot(end)
    return {
        "weekday": fmt_weekday(s.date()),
        "date": fmt_date(s.date()),
        "start": fmt_time(s),
        "end": fmt_time(e),
        "day_full": fmt_day_full(s.date()),
    }


# ---------- aggregation ----------

def heatmap(db, meetup_id):
    """slot -> [participant_id, ...] for everyone in the meetup."""
    cur = db.execute(
        "SELECT a.slot, a.participant_id FROM availability a "
        "JOIN participants p ON p.id = a.participant_id WHERE p.meetup_id = ? ORDER BY a.slot",
        (meetup_id,),
    )
    out = {}
    for slot, pid in cur.fetchall():
        out.setdefault(slot, []).append(pid)
    return out


def available_for_block(slot_map, start, end):
    """Participant ids free for every slot of the block."""
    slots = block_slots(start, end)
    if not slots:
        return set()
    ids = set(slot_map.get(slots[0], []))
    for s in slots[1:]:
        ids &= set(slot_map.get(s, []))
    return ids


def ranked_windows(dates, hour_start, hour_end, slot_map, participants, limit=12, min_minutes=30):
    """
    Split each day into runs of consecutive slots where the exact same set of people is free.
    Rank: most people first, then longest, then earliest.
    """
    id2name = {p["id"]: display_name(p) for p in participants}
    total = len(participants)
    windows = []
    for d in sorted(dates):
        run = None
        for slot in day_slots(d, hour_start, hour_end):
            ids = frozenset(slot_map.get(slot, []))
            if run and run["ids"] == ids:
                run["n"] += 1
            else:
                if run and run["ids"]:
                    windows.append(run)
                run = {"ids": ids, "start": slot, "n": 1}
        if run and run["ids"]:
            windows.append(run)

    out = []
    for w in windows:
        minutes = w["n"] * SLOT_MINUTES
        if minutes < min_minutes:
            continue
        s = parse_slot(w["start"])
        e = s + timedelta(minutes=minutes)
        ids = sorted(w["ids"])
        missing = [p["id"] for p in participants if p["id"] not in w["ids"]]
        out.append({
            "start": fmt_slot(s),
            "end": fmt_slot(e),
            "date": s.date().isoformat(),
            "minutes": minutes,
            "count": len(ids),
            "total": total,
            "percent": round(100 * len(ids) / total) if total else 0,
            "available": [id2name[i] for i in ids],
            "missing": [id2name[i] for i in missing],
            "label": block_label(fmt_slot(s), fmt_slot(e)),
        })
    out.sort(key=lambda w: (-w["count"], -w["minutes"], w["start"]))
    return out[:limit]


def day_summary(dates, hour_start, hour_end, slot_map, participants):
    """Per date: how many people painted anything that day, and the best single-slot count."""
    total = len(participants)
    out = []
    for d in sorted(dates):
        anyone = set()
        best = 0
        for slot in day_slots(d, hour_start, hour_end):
            ids = slot_map.get(slot, [])
            anyone.update(ids)
            best = max(best, len(ids))
        out.append({
            "date": d,
            "label": fmt_day_full(d),
            "people_any": len(anyone),
            "percent_any": round(100 * len(anyone) / total) if total else 0,
            "best_count": best,
            "total": total,
        })
    out.sort(key=lambda x: (-x["best_count"], -x["people_any"], x["date"]))
    return out
