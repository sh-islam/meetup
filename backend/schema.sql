-- Meetup schema. Times are stored in the meetup's own timezone as 'YYYY-MM-DDTHH:MM',
-- aligned to 15-minute slots. hour_start / hour_end are whole hours (0-24).

CREATE TABLE IF NOT EXISTS meetups (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  title           TEXT NOT NULL,
  description     TEXT NOT NULL DEFAULT '',
  location        TEXT NOT NULL DEFAULT '',
  location_json   TEXT,
  icon            TEXT NOT NULL DEFAULT '',
  timezone        TEXT NOT NULL,
  hour_start      INTEGER NOT NULL DEFAULT 8,
  hour_end        INTEGER NOT NULL DEFAULT 24,
  paint_mode      TEXT NOT NULL DEFAULT 'free',        -- free | restricted
  status          TEXT NOT NULL DEFAULT 'collecting',  -- collecting | confirmed | cancelled
  confirmed_start TEXT,
  confirmed_end   TEXT,
  created_at      TEXT NOT NULL,
  updated_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS meetup_dates (
  meetup_id INTEGER NOT NULL REFERENCES meetups(id) ON DELETE CASCADE,
  date      TEXT NOT NULL,                              -- YYYY-MM-DD
  PRIMARY KEY (meetup_id, date)
);

CREATE TABLE IF NOT EXISTS participants (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  meetup_id     INTEGER NOT NULL REFERENCES meetups(id) ON DELETE CASCADE,
  email         TEXT NOT NULL,
  name          TEXT,                                   -- NULL until the person sets it
  token         TEXT NOT NULL UNIQUE,
  role          TEXT NOT NULL,                          -- planner | invitee
  last_saved_at TEXT,
  created_at    TEXT NOT NULL,
  UNIQUE (meetup_id, email)
);

CREATE TABLE IF NOT EXISTS availability (
  participant_id INTEGER NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
  slot           TEXT NOT NULL,                         -- YYYY-MM-DDTHH:MM, start of a 15-minute slot
  PRIMARY KEY (participant_id, slot)
);

CREATE TABLE IF NOT EXISTS nudges (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  meetup_id      INTEGER NOT NULL REFERENCES meetups(id) ON DELETE CASCADE,
  participant_id INTEGER NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
  block_start    TEXT NOT NULL,
  block_end      TEXT NOT NULL,                         -- exclusive
  token          TEXT NOT NULL UNIQUE,
  sent_at        TEXT NOT NULL,
  answer         TEXT,                                  -- NULL | yes | no
  answered_at    TEXT
);

CREATE TABLE IF NOT EXISTS email_log (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  meetup_id      INTEGER,
  participant_id INTEGER,
  kind           TEXT NOT NULL,
  to_email       TEXT NOT NULL,
  subject        TEXT NOT NULL,
  status         TEXT NOT NULL,                         -- sent | logged | failed
  error          TEXT,
  sent_at        TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_participants_meetup ON participants(meetup_id);
CREATE INDEX IF NOT EXISTS idx_nudges_participant ON nudges(participant_id);
