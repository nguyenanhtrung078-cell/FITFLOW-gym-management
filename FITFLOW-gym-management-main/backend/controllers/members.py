import re
import sqlite3
from datetime import date, timedelta, datetime

from flask import Blueprint, jsonify, request

from db import get_db
from utils import PHONE_RE, error, find_package, login_required, member_dict

bp = Blueprint("members", __name__, url_prefix="/api/members")
BASE = "SELECT m.*, p.name AS package_name FROM members m JOIN packages p ON p.id = m.package_id"


def _phone(value):
    return re.sub(r"[ .-]", "", str(value or ""))


@bp.get("")
@login_required
def list_members():
    q = request.args.get("q", "").strip().casefold()
    rows = get_db().execute(BASE + " ORDER BY m.id DESC").fetchall()
    out = [member_dict(r) for r in rows]
    if q:
        out = [m for m in out if q in m["full_name"].casefold()
               or q in m["package_name"].casefold() or q in m["phone"]]
    return jsonify(out)


@bp.get("/<int:member_id>")
@login_required
def get_member(member_id):
    row = get_db().execute(BASE + " WHERE m.id=?", (member_id,)).fetchone()
    return jsonify(member_dict(row)) if row else error("Không tìm thấy hội viên.", 404)


@bp.post("")
@login_required
def create_member():
    db = get_db()
    data = request.get_json(silent=True) or {}
    name, phone = str(data.get("full_name") or "").strip(), _phone(data.get("phone"))
    if not name or not phone:
        return error("Vui lòng nhập họ tên và số điện thoại.")
    if not PHONE_RE.match(phone):
        return error("Số điện thoại chưa đúng định dạng.")
    pkg = find_package(db, data)
    if not pkg:
        return error("Gói tập không hợp lệ.")
    if db.execute("SELECT 1 FROM members WHERE phone=?", (phone,)).fetchone():
        return error("Số điện thoại này đã được đăng ký.", 409)

    start = date.today()
    end = start + timedelta(days=pkg["duration_months"] * 30)
    cur = db.execute(
        "INSERT INTO members (full_name, phone, package_id, start_date, end_date) VALUES (?,?,?,?,?)",
        (name, phone, pkg["id"], start.isoformat(), end.isoformat()))
    db.execute("INSERT INTO payments (member_id, package_id, amount, status, created_at) VALUES (?,?,?,?,?)",
               (cur.lastrowid, pkg["id"], pkg["price"], "paid", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    return jsonify(member_dict(db.execute(BASE + " WHERE m.id=?", (cur.lastrowid,)).fetchone())), 201


@bp.put("/<int:member_id>")
@login_required
def update_member(member_id):
    db = get_db()
    current = db.execute(BASE + " WHERE m.id=?", (member_id,)).fetchone()
    if not current:
        return error("Không tìm thấy hội viên.", 404)
    data = request.get_json(silent=True) or {}
    name = str(data.get("full_name") or current["full_name"]).strip()
    phone = _phone(data.get("phone") or current["phone"])
    if not name or not PHONE_RE.match(phone):
        return error("Họ tên hoặc số điện thoại chưa hợp lệ.")
    package_id = current["package_id"]
    if "package_id" in data or "package_name" in data:
        pkg = find_package(db, data)
        if not pkg:
            return error("Gói tập không hợp lệ.")
        package_id = pkg["id"]
    try:
        db.execute("UPDATE members SET full_name=?, phone=?, package_id=? WHERE id=?",
                   (name, phone, package_id, member_id))
        db.commit()
    except sqlite3.IntegrityError:
        return error("Số điện thoại này đã được đăng ký.", 409)
    return jsonify(member_dict(db.execute(BASE + " WHERE m.id=?", (member_id,)).fetchone()))


@bp.delete("/<int:member_id>")
@login_required
def delete_member(member_id):
    db = get_db()
    if not db.execute("SELECT 1 FROM members WHERE id=?", (member_id,)).fetchone():
        return error("Không tìm thấy hội viên.", 404)
    db.execute("DELETE FROM members WHERE id=?", (member_id,))
    db.commit()
    return jsonify({"ok": True})
