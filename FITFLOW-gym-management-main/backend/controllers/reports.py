from datetime import date, timedelta

from flask import Blueprint, jsonify

from db import get_db
from utils import login_required, member_dict

bp = Blueprint("reports", __name__, url_prefix="/api/reports")


@bp.get("/dashboard")
@login_required
def dashboard():
    db = get_db()
    today = date.today()
    one = lambda sql, *a: db.execute(sql, a).fetchone()[0]
    total = one("SELECT COUNT(*) FROM members")
    shares = db.execute("SELECT p.name, COUNT(m.id) AS c FROM packages p "
                        "LEFT JOIN members m ON m.package_id=p.id GROUP BY p.id ORDER BY c DESC").fetchall()
    return jsonify({
        "total_members": total,
        "active_members": one("SELECT COUNT(*) FROM members WHERE end_date>=?", today.isoformat()),
        "revenue_month": one("SELECT COALESCE(SUM(amount),0) FROM payments WHERE status='paid' AND created_at LIKE ?",
                             today.strftime("%Y-%m") + "%"),
        "revenue_today": one("SELECT COALESCE(SUM(amount),0) FROM payments WHERE status='paid' AND created_at LIKE ?",
                             today.isoformat() + "%"),
        "pending_amount": one("SELECT COALESCE(SUM(amount),0) FROM payments WHERE status='pending'"),
        "pending_count": one("SELECT COUNT(*) FROM payments WHERE status='pending'"),
        "attendance_today": one("SELECT COUNT(*) FROM attendance WHERE checkin_date=?", today.isoformat()),
        "expiring_soon": one("SELECT COUNT(*) FROM members WHERE end_date BETWEEN ? AND ?",
                             today.isoformat(), (today + timedelta(days=7)).isoformat()),
        "package_share": [{"name": r["name"], "members": r["c"],
                           "percent": round(r["c"] * 100 / total) if total else 0} for r in shares],
    })


@bp.get("/expiring")
@login_required
def expiring():
    today = date.today()
    rows = get_db().execute(
        "SELECT m.*, p.name AS package_name FROM members m JOIN packages p ON p.id=m.package_id "
        "WHERE m.end_date BETWEEN ? AND ? ORDER BY m.end_date",
        (today.isoformat(), (today + timedelta(days=7)).isoformat()))
    return jsonify([member_dict(r) for r in rows])
