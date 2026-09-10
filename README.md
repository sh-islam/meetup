# Meetup

Find a time when everyone is free. No accounts: every meetup has a planner link and one link per invitee.

- Frontend: Svelte + Vite, deployed to GitHub Pages by the workflow in `.github/`
- Backend: Flask + SQLite (`backend/`), self-hosted; the frontend build gets its URL from the `VITE_API_URL` variable
- Design decisions: `docs/DESIGN.md`. Email wording: `docs/EMAILS.md`. Endpoints: `docs/API.md`.
