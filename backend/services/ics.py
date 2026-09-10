"""Build a minimal .ics for a confirmed meetup."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from services.scheduling import parse_slot


def _esc(s):
    return (s or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def build_ics(meetup, start, end, attendees, uid_suffix=""):
    tz = ZoneInfo(meetup["timezone"])
    s = parse_slot(start).replace(tzinfo=tz).astimezone(timezone.utc)
    e = parse_slot(end).replace(tzinfo=tz).astimezone(timezone.utc)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    desc = meetup["description"] or ""
    if attendees:
        desc = (desc + "\n\n" if desc else "") + "Who's coming: " + ", ".join(attendees)
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Meetup//EN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:meetup-{meetup['id']}{uid_suffix}@meetup",
        f"DTSTAMP:{stamp}",
        f"DTSTART:{s.strftime('%Y%m%dT%H%M%SZ')}",
        f"DTEND:{e.strftime('%Y%m%dT%H%M%SZ')}",
        f"SUMMARY:{_esc(meetup['title'])}",
        f"DESCRIPTION:{_esc(desc)}",
    ]
    if meetup["location"]:
        lines.append(f"LOCATION:{_esc(meetup['location'])}")
    lines += ["END:VEVENT", "END:VCALENDAR", ""]
    return "\r\n".join(lines).encode("utf-8")
