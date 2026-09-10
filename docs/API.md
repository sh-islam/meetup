# API (draft)

Base: <API_URL>
Auth: X-Meetup-Token header carrying a participant token. Role comes from the token.

- POST   /meetups                          create (returns planner token)
- GET    /meetups/me                       meetup as seen by the token (role-aware)
- PATCH  /meetups/me                       planner: title, description, location, hours, dates, settings
- PUT    /meetups/me/name                  set my display name
- GET    /meetups/me/availability          my painted slots
- PUT    /meetups/me/availability          replace my painted slots, then email planner
- GET    /meetups/me/heatmap               counts + names per slot
- GET    /meetups/me/stats                 planner: ranked windows
- POST   /meetups/me/invitees              planner: add invitees (sends invite)
- POST   /meetups/me/confirm               planner: {start, end}
- POST   /meetups/me/nudge                 planner: {participant_id, start, end}
- GET    /nudge/<token>/yes                one-click from email, no header auth
- GET    /nudge/<token>/no
- GET    /health
