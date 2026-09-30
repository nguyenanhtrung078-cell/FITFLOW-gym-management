import sqlite3
from datetime import date, datetime

from flask import Blueprint, jsonify, request

from db import get_db
from utils import error, login_required, to_int

bp = Blueprint("attendance", __name__, url_prefix="/api/attendance")


@bp.get("")
@login_required
def list_attendance():
    day = request.args.get("date") or date.today().isoformat()
    rows = get_db().execute(
        "SELECT a.id, a.member_id, m.full_name, p.name AS package_name, a.checkin_at "
        "FROM attendance a JOIN members m ON m.id=a.member_id JOIN packages p ON p.id=m.package_id "
        "WHERE a.checkin_date=? ORDER BY a.checkin_at DESC", (day,))
    return jsonify([dict(r) for r in rows])


@bp.post("")
@login_required
def check_in():
    db = get_db()
    member_id = to_int((request.get_json(silent=True) or {}).get("member_id"))
    member = db.execute("SELECT * FROM members WHERE id=?", (member_id,)).fetchone() if member_id else None
    if not member:
        return error("Không tìm thấy hội viên.", 404)
    if member["end_date"] < date.today().isoformat():
        return error("Gói tập đã hết hạn, vui lòng gia hạn trước khi check-in.")
    now = datetime.now()
    try:
        cur = db.execute("INSERT INTO attendance (member_id, checkin_date, checkin_at) VALUES (?,?,?)",
                         (member_id, now.date().isoformat(), now.strftime("%Y-%m-%d %H:%M:%S")))
        db.commit()
    except sqlite3.IntegrityError:
        return error("Hội viên này đã check-in hôm nay.", 409)
    return jsonify({"id": cur.lastrowid, "member_id": member_id,
                    "checkin_at": now.strftime("%Y-%m-%d %H:%M:%S")}), 201
