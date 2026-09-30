import sqlite3

from flask import Blueprint, jsonify, request

from db import get_db
from utils import error, login_required, to_int

bp = Blueprint("packages", __name__, url_prefix="/api/packages")
BASE = ("SELECT p.*, (SELECT COUNT(*) FROM members m WHERE m.package_id = p.id) AS member_count "
        "FROM packages p")


def _parse(data):
    name = str(data.get("name") or "").strip()
    price, months = to_int(data.get("price")), to_int(data.get("duration_months"))
    if not name or price is None or price < 0 or months is None or months < 1:
        return None
    return name, price, months


@bp.get("")
@login_required
def list_packages():
    return jsonify([dict(r) for r in get_db().execute(BASE + " ORDER BY p.price DESC")])


@bp.post("")
@login_required
def create_package():
    parsed = _parse(request.get_json(silent=True) or {})
    if not parsed:
        return error("Tên gói, giá và thời hạn (tháng) phải hợp lệ.")
    db = get_db()
    try:
        cur = db.execute("INSERT INTO packages (name, price, duration_months) VALUES (?,?,?)", parsed)
        db.commit()
    except sqlite3.IntegrityError:
        return error("Tên gói tập đã tồn tại.", 409)
    return jsonify(dict(db.execute(BASE + " WHERE p.id=?", (cur.lastrowid,)).fetchone())), 201


@bp.put("/<int:package_id>")
@login_required
def update_package(package_id):
    db = get_db()
    if not db.execute("SELECT 1 FROM packages WHERE id=?", (package_id,)).fetchone():
        return error("Không tìm thấy gói tập.", 404)
    parsed = _parse(request.get_json(silent=True) or {})
    if not parsed:
        return error("Tên gói, giá và thời hạn (tháng) phải hợp lệ.")
    try:
        db.execute("UPDATE packages SET name=?, price=?, duration_months=? WHERE id=?", (*parsed, package_id))
        db.commit()
    except sqlite3.IntegrityError:
        return error("Tên gói tập đã tồn tại.", 409)
    return jsonify(dict(db.execute(BASE + " WHERE p.id=?", (package_id,)).fetchone()))


@bp.delete("/<int:package_id>")
@login_required
def delete_package(package_id):
    db = get_db()
    try:
        cur = db.execute("DELETE FROM packages WHERE id=?", (package_id,))
        db.commit()
    except sqlite3.IntegrityError:
        return error("Không thể xóa: gói tập đang có hội viên hoặc giao dịch.", 409)
    return jsonify({"ok": True}) if cur.rowcount else error("Không tìm thấy gói tập.", 404)
