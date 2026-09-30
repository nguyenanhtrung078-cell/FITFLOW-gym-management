from datetime import datetime

from flask import Blueprint, jsonify, request

from db import get_db
from utils import error, extend_membership, login_required, to_int

bp = Blueprint("payments", __name__, url_prefix="/api/payments")
BASE = ("SELECT pay.id, pay.member_id, m.full_name, pay.package_id, p.name AS package_name, "
        "pay.amount, pay.status, pay.created_at FROM payments pay "
        "JOIN members m ON m.id = pay.member_id JOIN packages p ON p.id = pay.package_id")


@bp.get("")
@login_required
def list_payments():
    status = request.args.get("status")
    sql, args = BASE, ()
    if status in ("paid", "pending"):
        sql, args = sql + " WHERE pay.status=?", (status,)
    return jsonify([dict(r) for r in get_db().execute(sql + " ORDER BY pay.id DESC", args)])


@bp.post("")
@login_required
def create_payment():
    db = get_db()
    data = request.get_json(silent=True) or {}
    member = db.execute("SELECT * FROM members WHERE id=?", (to_int(data.get("member_id")),)).fetchone()
    if not member:
        return error("Không tìm thấy hội viên.", 404)
    pkg = db.execute("SELECT * FROM packages WHERE id=?",
                     (to_int(data.get("package_id")) or member["package_id"],)).fetchone()
    if not pkg:
        return error("Gói tập không hợp lệ.")
    amount = to_int(data.get("amount")) if data.get("amount") is not None else pkg["price"]
    status = data.get("status", "paid")
    if amount is None or amount < 0 or status not in ("paid", "pending"):
        return error("Số tiền hoặc trạng thái không hợp lệ.")
    cur = db.execute("INSERT INTO payments (member_id, package_id, amount, status, created_at) VALUES (?,?,?,?,?)",
                     (member["id"], pkg["id"], amount, status, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    if status == "paid":
        extend_membership(db, member["id"], pkg)
    db.commit()
    return jsonify(dict(db.execute(BASE + " WHERE pay.id=?", (cur.lastrowid,)).fetchone())), 201


@bp.patch("/<int:payment_id>/pay")
@login_required
def mark_paid(payment_id):
    db = get_db()
    pay = db.execute("SELECT * FROM payments WHERE id=?", (payment_id,)).fetchone()
    if not pay:
        return error("Không tìm thấy giao dịch.", 404)
    if pay["status"] == "paid":
        return error("Giao dịch này đã được thanh toán.", 409)
    db.execute("UPDATE payments SET status='paid' WHERE id=?", (payment_id,))
    extend_membership(db, pay["member_id"], db.execute("SELECT * FROM packages WHERE id=?", (pay["package_id"],)).fetchone())
    db.commit()
    return jsonify(dict(db.execute(BASE + " WHERE pay.id=?", (payment_id,)).fetchone()))
