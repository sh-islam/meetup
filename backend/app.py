"""Flask app factory. Run: gunicorn -b 127.0.0.1:5090 'app:create_app()'"""
import os

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

import config
import db as database


class StripPrefix:
    """Tailscale Funnel forwards '/meetup-api/...' unchanged; make Flask see '/...'."""

    def __init__(self, app, prefix):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")
        if self.prefix and (path == self.prefix or path.startswith(self.prefix + "/")):
            environ["SCRIPT_NAME"] = environ.get("SCRIPT_NAME", "") + self.prefix
            environ["PATH_INFO"] = path[len(self.prefix):] or "/"
        return self.app(environ, start_response)


def create_app():
    app = Flask(__name__, template_folder=os.path.join(config.BASE_DIR, "templates"))
    app.config["JSON_SORT_KEYS"] = False
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    CORS(app, origins=config.CORS_ORIGINS, allow_headers=["Content-Type", "X-Meetup-Token"],
         methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    database.init_app(app)

    from routes import availability, meetups, nudge, stats
    app.register_blueprint(meetups.bp)
    app.register_blueprint(availability.bp)
    app.register_blueprint(stats.bp)
    app.register_blueprint(nudge.bp)

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "mail": "smtp" if config.mail_configured() else "log"})

    # Optional: serve the built frontend at FRONTEND_MOUNT (before GitHub Pages exists).
    dist = os.path.abspath(config.FRONTEND_DIST)
    mount = config.FRONTEND_MOUNT.rstrip("/")
    # Tailscale Funnel strips the mount path before proxying, so requests for the frontend
    # arrive at '/' and '/assets/...'; serve it there and under FRONTEND_MOUNT for direct access.
    if os.path.isdir(dist):
        def _serve(filename="index.html"):
            if not os.path.isfile(os.path.join(dist, filename)):
                filename = "index.html"
            return send_from_directory(dist, filename)

        app.add_url_rule("/", "frontend_root", _serve)
        app.add_url_rule("/<path:filename>", "frontend_file", _serve)
        if mount:
            app.add_url_rule(f"{mount}/", "frontend_mount", _serve)
            app.add_url_rule(f"{mount}/<path:filename>", "frontend_mount_file", _serve)

    @app.errorhandler(HTTPException)
    def http_error(e):
        return jsonify({"error": e.description, "code": e.code}), e.code

    @app.errorhandler(Exception)
    def any_error(e):  # noqa: ANN001
        app.logger.exception("unhandled")
        return jsonify({"error": "Something went wrong on the server.", "code": 500}), 500

    app.wsgi_app = StripPrefix(app.wsgi_app, config.API_BASE_PATH)
    return app


if __name__ == "__main__":
    host, _, port = (os.environ.get("BIND") or "127.0.0.1:5090").partition(":")
    create_app().run(host=host, port=int(port or 5090), debug=True)
