# Meetup - design and decisions log

Status: structure locked 2026-09-09. Wording for all UI text and emails still to be approved (see EMAILS.md).

## Problem
Find a date and time that works for a group of friends without anyone creating an account.

## Roles and access
- No passwords. Access is by secret token in a link.
- Planner: creates the meetup, gets a planner token. Sees everything invitees see plus a dashboard.
- Invitee: gets their own personal token by email. Opening it identifies them, so their saved picks load.
- Every participant, including the planner, can paint their own availability.
- "Existing meetup" on the home page accepts any token pasted by hand.

## Flow
1. Home: two buttons only, "New meetup" and "Existing meetup".
2. New meetup, step 1: pick dates (any dates, need not be contiguous), set visible hour range
   (default 08:00 to 24:00), paint availability on the grid.
3. New meetup, step 2: title (required), description (optional, always shown), location (Google Maps pin,
   later feature), invitee emails. Submit creates the meetup and emails everyone.
4. Invitee opens link: asked for a display name on first open, then sees title/description/location
   read-only, the grid with the group heatmap, and paints their own availability.
   One "save" button. Saving sends one email to the planner with that person's picks.
5. Planner dashboard adds: stats (ranked best windows, % free per window, who is free/missing),
   Confirm (drag an exact block on the heatmap, locks the meetup, emails all with a calendar file),
   Nudge (pick a person and a target block; app emails them "% and names free then, can you move things
   around" with one-click Yes / No buttons; Yes paints the block into their availability, both answers
   email the planner via response_saved), and editing of dates/hours/details.
   Dashboard shows nudge status next to each name: "nudged {date} {time}, waiting" / "said yes" / "said no".
6. Planner edits after invites went out: allowed. Changes to dates/hours send one "meetup updated" email
   to all invitees. Painted slots outside the new range are dropped.

## The grid
- Press-and-drag to paint, must work on touch. Snap to 15-minute anchors.
- Labels every 30 minutes, one faint sub-line between labels marking the 15-minute steps.
- Columns are the planner's chosen dates. Rows are the visible hour range.
- Heatmap: darker cell = more people free. Hover/tap shows names. Visible to invitees and planner.
- Timezone is fixed per meetup to the planner's zone. Viewers elsewhere see converted times with a notice.

## Meetup settings (shown under the meetup, planner only)
- Time selection: "Anyone can select any time" (default; goal is to discover when everyone is free)
  or "Restrict to planner's times" (cells the planner did not paint are greyed out for invitees).

## Status lifecycle
collecting -> confirmed (or cancelled). Confirmed meetups are read-only for invitees.

## Data model (SQLite)
- meetups: id, title, description, timezone, hour_start, hour_end, paint_mode, status,
  confirmed_start, confirmed_end, location_json, created_at, updated_at
- meetup_dates: meetup_id, date
- participants: id, meetup_id, email, name, token, role (planner|invitee), last_saved_at
- availability: participant_id, slot (meetup-local YYYY-MM-DDTHH:MM, 15-minute aligned)
- nudges: id, meetup_id, participant_id, block_start, block_end, token, sent_at, answer (null|yes|no), answered_at
- email_log: id, meetup_id, participant_id, kind, sent_at, status, error

## Hosting
- Frontend: GitHub repo sh-islam/meetup, Pages via Actions, hash routing (#/new, #/open, #/m/<token>).
- Backend: gunicorn on 127.0.0.1:<port>, systemd unit meetup-api, Tailscale Funnel path
  <API_URL> -> 127.0.0.1:<port> .
- CORS: https://sh-islam.github.io only, plus localhost for dev.

## Email
- Transport: Gmail SMTP with an app password, credentials in backend/.env (a dedicated account, not the personal one).
- mailer.py exposes a single send(kind, to, context) so a future standalone mail service can replace SMTP
  by config alone.
- Email kinds: planner_link, invite, response_saved, meetup_updated, confirmed, nudge.

## Later features
- Google Maps location picker with pin preview (MapPicker.svelte stubbed).
- Standalone mail service on the server once a domain exists.

## Open items
- All user-facing wording (UI labels, button names, email copy): to be approved by owner before shipping.
- Gmail account and app password: to be provided by owner into backend/.env.


## UI v2 - Midnight Glass (2026-09-10)
Decided after the v1 review ("too much info per screen on mobile"). Mockup (removed 2026-09-10 once the app matched it)
. Tokens live in frontend/src/app.css header comment.

- Theme: single-hue navy ground with a slow background drift + 12s highlight sweep (off under reduced-motion),
  frosted glass panels, cyan accent, mint for "you". Manrope. 8pt rhythm, 24px screen margins, 44px+ targets.
  Thin floating scrollbars. The grid stays crisp on a solid dark surface.
- Phone: one job per screen, primary action fixed at the bottom. New meetup = 6 steps in the hash
  (#/new/1..6: days, your times, what, who are you, invitees, review with collapsed Options) + #/new/done links.
  Draft persists in sessionStorage.
- Invitee: name prompt, then title row (disclosure -> details sheet), legend, full-height grid,
  floating "Send my availability" appears once something changed. Tap a time = who's free pill.
- Planner: bottom tab bar Times / Best / People / Settings (#/m/<token>/best etc.). Wide screens (>=900px):
  sidebar shell (brand, title, nav) + full-width grid; sheets become a right-hand panel.
- Decide flow = select-then-act: tap a time (phone) or press the small "Confirm" button (both; on desktop it is
  the only way to open the panel). The same-people run highlights; the sheet shows the day, start/end steppers
  (15 min), who's free / missing, "Confirm this time" (-> review -> "Send confirmation") and one
  "Nudge {name}" per missing invitee (-> preview -> send). No block-drag mode, no buttons above the grid.
- Grid interaction: tap = report cell; desktop click-drag or touch press-and-hold (280ms) then drag = paint.
- Settings: list rows, each edits one thing in a sheet. People: rows open a person sheet (copy link / remove),
  "Invite more people" sheet. Confirmed: banner, grid read-only with the block outlined, Undo in Settings.
