import re

from flask import Blueprint, jsonify, request

from db import get_db
from utils import error, login_required, to_int

bp = Blueprint("schedule", __name__, url_prefix="/api/schedule")
BASE = ("SELECT c.id, c.name, t.name AS trainer, c.weekday, c.start_time, c.capacity "
        "FROM classes c JOIN trainers t ON t.id = c.trainer_id")


@bp.get("")
@login_required
def list_classes():
    weekday = to_int(request.args.get("weekday"))
    sql, args = BASE, ()
    if weekday is not None:
        sql, args = sql + " WHERE c.weekday=?", (weekday,)
    rows = get_db().execute(sql + " ORDER BY c.weekday, c.start_time", args)
    return jsonify([dict(r) for r in rows])


@bp.post("")
@login_required
def create_class():
    data = request.get_json(silent=True) or {}
    name, trainer = str(data.get("name") or "").strip(), str(data.get("trainer") or "").strip()
    weekday, capacity = to_int(data.get("weekday")), to_int(data.get("capacity") or 20)
    start = str(data.get("start_time") or "")
    if not name or not trainer or weekday not in range(7) or not re.match(r"^([01]\d|2[0-3]):[0-5]\d$", start) \
            or capacity is None or capacity < 1:
        return error("Tên lớp, HLV, thứ (0-6), giờ (HH:MM) và sĩ số phải hợp lệ.")
    db = get_db()
    db.execute("INSERT OR IGNORE INTO trainers (name) VALUES (?)", (trainer,))
    tid = db.execute("SELECT id FROM trainers WHERE name=?", (trainer,)).fetchone()["id"]
    cur = db.execute("INSERT INTO classes (name, trainer_id, weekday, start_time, capacity) VALUES (?,?,?,?,?)",
                     (name, tid, weekday, start, capacity))
    db.commit()
    return jsonify(dict(db.execute(BASE + " WHERE c.id=?", (cur.lastrowid,)).fetchone())), 201


@bp.delete("/<int:class_id>")
@login_required
def delete_class(class_id):
    db = get_db()
    cur = db.execute("DELETE FROM classes WHERE id=?", (class_id,))
    db.commit()
    return jsonify({"ok": True}) if cur.rowcount else error("Không tìm thấy lớp tập.", 404)
