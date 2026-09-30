import os
from pathlib import Path

from flask import Flask, abort, send_from_directory

from controllers import register_blueprints
from db import close_db, init_db

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent  # thư mục chứa index.html, app.js, style.css
ASSETS = {"app.js", "style.css"}


def create_app(database=None):
    app = Flask(__name__, static_folder=None)
    app.config.update(
        SECRET_KEY=os.environ.get("FITFLOW_SECRET", "dev-secret-doi-khi-trien-khai"),
        DATABASE=str(database or BASE / "fitflow.db"),
    )
    app.teardown_appcontext(close_db)
    register_blueprints(app)
    with app.app_context():
        init_db()

    @app.get("/")
    def index():
        return send_from_directory(ROOT, "index.html")

    @app.get("/<name>")
    def asset(name):
        if name not in ASSETS:  # chỉ phục vụ file giao diện, không lộ file database
            abort(404)
        return send_from_directory(ROOT, name)

    return app


if __name__ == "__main__":
    create_app().run(debug=True, port=5000)
