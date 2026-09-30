from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash

from db import get_db
from utils import error, login_required

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    admin = get_db().execute("SELECT * FROM admins WHERE email=?",
                             (str(data.get("email", "")).strip().lower(),)).fetchone()
    if not admin or not check_password_hash(admin["password_hash"], str(data.get("password", ""))):
        return error("Sai email hoặc mật khẩu. Vui lòng thử lại.", 401)
    session["admin_id"] = admin["id"]
    return jsonify({"id": admin["id"], "email": admin["email"], "full_name": admin["full_name"]})


@bp.post("/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@bp.get("/me")
@login_required
def me():
    admin = get_db().execute("SELECT id, email, full_name FROM admins WHERE id=?", (session["admin_id"],)).fetchone()
    return jsonify(dict(admin))
