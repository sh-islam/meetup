"""End-to-end flow through the Flask test client on a throwaway database."""
import os
import sys
import tempfile

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

_tmp = tempfile.mkdtemp()
os.environ["DB_PATH"] = os.path.join(_tmp, "test.db")
os.environ["MAIL_LOG"] = os.path.join(_tmp, "mail.log")
os.environ["SMTP_USER"] = ""
os.environ["SMTP_PASS"] = ""

import config  # noqa: E402
config.DB_PATH = os.environ["DB_PATH"]
config.MAIL_LOG = os.environ["MAIL_LOG"]
config.SMTP_USER = config.SMTP_PASS = ""

from app import create_app  # noqa: E402
from datetime import date  # noqa: E402

D20 = date(2030, 9, 20).strftime("%a") + " Sep 20"
D21 = date(2030, 9, 21).strftime("%a") + " Sep 21"


@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.testing = True
    with app.test_client() as c:
        yield c


def hdr(token):
    return {"X-Meetup-Token": token}


def test_full_flow(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json["mail"] == "log"

    # planner creates a meetup with their own availability
    body = {
        "title": "Board game night",
        "description": "Bring snacks",
        "timezone": "America/Toronto",
        "hour_start": 18,
        "hour_end": 23,
        "dates": ["2030-09-20", "2030-09-21"],
        "paint_mode": "free",
        "planner": {"email": "sam@example.com", "name": "Sam"},
        "invitees": [{"email": "alex@example.com"}, {"email": "priya@example.com", "name": "Priya"}],
        "availability": [f"2030-09-20T{h:02d}:{m:02d}" for h in (19, 20, 21) for m in (0, 15, 30, 45)],
    }
    r = client.post("/meetups", json=body)
    assert r.status_code == 201, r.json
    planner_token = r.json["planner_token"]
    people = r.json["participants"]
    assert len(people) == 3
    assert all(r.json["mail_status"][e] == "logged" for e in r.json["mail_status"])
    alex = next(p for p in people if p["email"] == "alex@example.com")
    priya = next(p for p in people if p["email"] == "priya@example.com")
    alex_token = alex["url"].split("#/m/")[1]
    priya_token = priya["url"].split("#/m/")[1]

    # prefix stripping works
    r = client.get("/meetup-api/meetups/me", headers=hdr(planner_token))
    assert r.status_code == 200 and r.json["me"]["role"] == "planner"

    # invitee opens, has no name, sets one
    r = client.get("/meetups/me", headers=hdr(alex_token))
    assert r.json["me"]["name"] is None and "email" not in r.json["participants"][0]
    r = client.put("/meetups/me/name", json={"name": "Alex"}, headers=hdr(alex_token))
    assert r.json["me"]["name"] == "Alex"

    # invitee paints 7-9 PM on the 20th -> planner emailed
    slots = [f"2030-09-20T{h:02d}:{m:02d}" for h in (19, 20) for m in (0, 15, 30, 45)]
    r = client.put("/meetups/me/availability", json={"slots": slots}, headers=hdr(alex_token))
    assert r.status_code == 200 and len(r.json["my_slots"]) == 8
    log = open(config.MAIL_LOG, encoding="utf-8").read()
    assert 'Subject: Meetup: Alex sent their availability for "Board game night"' in log
    assert f"{D20}: 7:00 PM to 9:00 PM" in log

    # out-of-range slot rejected
    r = client.put("/meetups/me/availability", json={"slots": ["2030-09-22T19:00"]}, headers=hdr(alex_token))
    assert r.status_code == 400

    # planner stats: best window is 7-9 PM with 2 of 3
    r = client.get("/meetups/me/stats", headers=hdr(planner_token))
    assert r.status_code == 200
    top = r.json["windows"][0]
    assert top["count"] == 2 and top["start"] == "2030-09-20T19:00" and top["end"] == "2030-09-20T21:00"
    assert set(top["available"]) == {"Sam", "Alex"} and top["missing"] == ["Priya"]
    # invitee may not read stats
    assert client.get("/meetups/me/stats", headers=hdr(alex_token)).status_code == 403

    # nudge Priya for 7-9 PM, she taps yes
    r = client.post("/meetups/me/nudge", json={"participant_id": priya["id"], "start": "2030-09-20T19:00",
                                              "end": "2030-09-20T21:00"}, headers=hdr(planner_token))
    assert r.status_code == 200, r.json
    log = open(config.MAIL_LOG, encoding="utf-8").read()
    assert "67% of people (2 of 3) are available" in log
    assert "Available people are Sam and Alex" in log
    yes_url = [l for l in log.splitlines() if "/nudge/" in l and l.strip().endswith("/yes")][-1].split()[-1]
    path = yes_url.split("/meetup-api")[1]
    r = client.get(path)
    assert r.status_code == 200 and b"marked free" in r.data
    r = client.get("/meetups/me", headers=hdr(planner_token))
    pr = next(p for p in r.json["participants"] if p["id"] == priya["id"])
    assert pr["nudge"]["answer"] == "yes" and pr["responded"]
    r = client.get("/meetups/me/stats", headers=hdr(planner_token))
    assert r.json["windows"][0]["count"] == 3

    # restricted mode: invitee can't paint outside planner's cells
    r = client.patch("/meetups/me", json={"paint_mode": "restricted"}, headers=hdr(planner_token))
    assert r.status_code == 200 and r.json["changes"] == []
    r = client.put("/meetups/me/availability", json={"slots": ["2030-09-20T18:00"]}, headers=hdr(alex_token))
    assert r.status_code == 400
    r = client.patch("/meetups/me", json={"paint_mode": "free"}, headers=hdr(planner_token))

    # planner edits dates -> update email, stale slots dropped
    r = client.patch("/meetups/me", json={"dates": ["2030-09-21", "2030-09-27"], "title": "Board game night!"},
                     headers=hdr(planner_token))
    assert r.status_code == 200
    assert any(c.startswith("Dates:") for c in r.json["changes"])
    assert r.json["my_slots"] == []
    log = open(config.MAIL_LOG, encoding="utf-8").read()
    assert '"Board game night!" was updated' in log

    # confirm a block -> everyone emailed, further edits blocked
    r = client.post("/meetups/me/confirm", json={"start": "2030-09-21T19:00", "end": "2030-09-21T21:00"},
                    headers=hdr(planner_token))
    assert r.status_code == 200 and r.json["meetup"]["status"] == "confirmed"
    log = open(config.MAIL_LOG, encoding="utf-8").read()
    assert log.count(f"It's on: Board game night!, {D21} at 7:00 PM") == 3
    assert client.put("/meetups/me/availability", json={"slots": []}, headers=hdr(alex_token)).status_code == 409

    # bad token
    assert client.get("/meetups/me", headers=hdr("nope")).status_code == 401

    # icon accepted / rejected
    r = client.patch("/meetups/me", json={"icon": "pizza"}, headers=hdr(planner_token))
    assert r.status_code == 409  # confirmed meetups are locked
    assert client.post("/meetups/me/reopen", headers=hdr(planner_token)).status_code == 200
    r = client.patch("/meetups/me", json={"icon": "pizza"}, headers=hdr(planner_token))
    assert r.status_code == 200 and r.json["meetup"]["icon"] == "pizza"
    assert client.patch("/meetups/me", json={"icon": "nope"}, headers=hdr(planner_token)).status_code == 400

    # an invitee drops out: planner emailed, their link dies, they vanish from the meetup
    assert client.post("/meetups/me/leave", headers=hdr(planner_token)).status_code == 403
    assert client.post("/meetups/me/leave", headers=hdr(priya_token)).status_code == 200
    assert client.get("/meetups/me", headers=hdr(priya_token)).status_code == 401
    r = client.get("/meetups/me", headers=hdr(planner_token))
    assert [p["name"] for p in r.json["participants"]] == ["Sam", "Alex"]
    log = open(config.MAIL_LOG, encoding="utf-8").read()
    assert 'Subject: Meetup: priya dropped out of "Board game night!"' in log

    # invitee can't delete; planner can; links die; invitees emailed
    assert client.delete("/meetups/me", headers=hdr(alex_token)).status_code == 403
    assert client.delete("/meetups/me", headers=hdr(planner_token)).status_code == 200
    assert client.get("/meetups/me", headers=hdr(alex_token)).status_code == 401
    assert client.get("/meetups/me", headers=hdr(planner_token)).status_code == 401
    log = open(config.MAIL_LOG, encoding="utf-8").read()
    assert '"Board game night!" is off' in log
