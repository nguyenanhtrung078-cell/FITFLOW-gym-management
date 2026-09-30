import re
from datetime import date, timedelta
from functools import wraps

from flask import jsonify, session

PHONE_RE = re.compile(r"^(0|\+84)[0-9]{9,10}$")


def error(message, status=400):
    return jsonify({"error": message}), status


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "admin_id" not in session:
            return error("Chưa đăng nhập.", 401)
        return view(*args, **kwargs)
    return wrapper


def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def member_status(end_date):
    days = (date.fromisoformat(end_date) - date.today()).days
    if days < 0:
        return "Đã hết hạn", "gray"
    if days <= 7:
        return "Sắp hết hạn", "orange"
    return f"Còn {days} ngày", "active"


def member_dict(row):
    status, badge = member_status(row["end_date"])
    return {
        "id": row["id"], "full_name": row["full_name"], "phone": row["phone"],
        "package_id": row["package_id"], "package_name": row["package_name"],
        "start_date": row["start_date"], "end_date": row["end_date"],
        "days_left": (date.fromisoformat(row["end_date"]) - date.today()).days,
        "status": status, "badge": badge,
    }


def find_package(db, data):
    if data.get("package_id") is not None:
        return db.execute("SELECT * FROM packages WHERE id=?", (to_int(data["package_id"]),)).fetchone()
    if data.get("package_name"):
        return db.execute("SELECT * FROM packages WHERE name=?", (data["package_name"],)).fetchone()
    return None


def extend_membership(db, member_id, package):
    """Gia hạn: cộng thêm thời hạn gói vào ngày hết hạn hiện tại (hoặc từ hôm nay nếu đã hết hạn)."""
    row = db.execute("SELECT end_date FROM members WHERE id=?", (member_id,)).fetchone()
    base = max(date.today(), date.fromisoformat(row["end_date"]))
    new_end = base + timedelta(days=package["duration_months"] * 30)
    db.execute("UPDATE members SET package_id=?, end_date=? WHERE id=?",
               (package["id"], new_end.isoformat(), member_id))
