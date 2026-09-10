"""Environment-driven settings. Copy .env.example to .env and fill it in."""
import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

DB_PATH = os.environ.get("DB_PATH", os.path.join(BASE_DIR, "meetup.db"))

# Where the frontend lives; personal links are built from this.
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://sh-islam.github.io/meetup/").rstrip("/") + "/"
# Public URL of this API; nudge Yes/No buttons point here.
API_PUBLIC_URL = os.environ.get("API_PUBLIC_URL", "").rstrip("/")   # set in .env
# Path prefix the Funnel forwards without stripping. Stripped by middleware in app.py.
API_BASE_PATH = os.environ.get("API_BASE_PATH", "/meetup-api").rstrip("/")
# Optional: serve a built frontend from this directory at /meetup/ (used before GitHub Pages exists).
FRONTEND_DIST = os.environ.get("FRONTEND_DIST", os.path.join(BASE_DIR, "..", "frontend", "dist"))
FRONTEND_MOUNT = os.environ.get("FRONTEND_MOUNT", "/meetup")

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
MAIL_FROM = os.environ.get("MAIL_FROM", SMTP_USER)
MAIL_FROM_NAME = os.environ.get("MAIL_FROM_NAME", "Meetup")
# Every outgoing email is appended here (also when really sent), handy for testing without SMTP.
MAIL_LOG = os.environ.get("MAIL_LOG", os.path.join(BASE_DIR, "mail.log"))

# Comma-separated list in .env; the GitHub Pages origin plus local dev by default.
CORS_ORIGINS = [o.strip() for o in os.environ.get(
    "CORS_ORIGINS", "https://sh-islam.github.io,http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]

SLOT_MINUTES = 15
MAX_DATES = 21


def mail_configured():
    return bool(SMTP_USER and SMTP_PASS)
