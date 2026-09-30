import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from flask import current_app, g
from werkzeug.security import generate_password_hash

SCHEMA = Path(__file__).with_name("schema.sql")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Tạo bảng và nạp dữ liệu mẫu nếu database còn trống."""
    con = sqlite3.connect(current_app.config["DATABASE"])
    con.executescript(SCHEMA.read_text(encoding="utf-8"))
    if con.execute("SELECT COUNT(*) FROM admins").fetchone()[0] == 0:
        _seed(con)
    con.commit()
    con.close()


def _seed(con):
    today = date.today()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    con.execute(
        "INSERT INTO admins (email, password_hash, full_name) VALUES (?,?,?)",
        ("admin@fitflow.vn", generate_password_hash("admin123"), "Admin Nguyễn"),
    )
    con.executemany(
        "INSERT INTO packages (name, price, duration_months) VALUES (?,?,?)",
        [("Gói Premium", 1200000, 6), ("Gói Standard", 750000, 3), ("Gói Basic", 300000, 1)],
    )
    pkg = {r[1]: (r[0], r[2]) for r in con.execute("SELECT id, name, price FROM packages")}

    # (họ tên, số điện thoại, gói, số ngày còn lại) - chèn ngược để hội viên đầu tiên có id lớn nhất
    demo = [
        ("Nguyễn Minh Anh", "0901000001", "Gói Premium", 24),
        ("Trần Quốc Bảo", "0901000002", "Gói Standard", 12),
        ("Lê Ngọc Hân", "0901000003", "Gói Premium", 5),
        ("Phạm Gia Huy", "0901000004", "Gói Basic", -3),
        ("Vũ Thanh Mai", "0901000005", "Gói Standard", 50),
    ]
    for name, phone, pk, left in reversed(demo):
        end = today + timedelta(days=left)
        start = end - timedelta(days=30)
        cur = con.execute(
            "INSERT INTO members (full_name, phone, package_id, start_date, end_date) VALUES (?,?,?,?,?)",
            (name, phone, pkg[pk][0], start.isoformat(), end.isoformat()),
        )
        con.execute(
            "INSERT INTO payments (member_id, package_id, amount, status, created_at) VALUES (?,?,?,?,?)",
            (cur.lastrowid, pkg[pk][0], pkg[pk][1], "paid", now),
        )

    for t in ("HLV Minh", "HLV Khánh", "HLV Lan", "HLV Huy"):
        con.execute("INSERT INTO trainers (name) VALUES (?)", (t,))
    tid = {r[1]: r[0] for r in con.execute("SELECT id, name FROM trainers")}
    for wd in (0, 2, 4):
        for cls, tr, hh in (("Yoga cơ bản", "HLV Minh", "06:00"), ("Cardio đốt mỡ", "HLV Khánh", "08:30"),
                            ("Body Pump", "HLV Lan", "17:30"), ("Boxing nhóm", "HLV Huy", "19:00")):
            con.execute(
                "INSERT INTO classes (name, trainer_id, weekday, start_time) VALUES (?,?,?,?)",
                (cls, tid[tr], wd, hh),
            )

    for (mid,) in con.execute("SELECT id FROM members WHERE phone IN ('0901000001','0901000002','0901000003')").fetchall():
        con.execute(
            "INSERT INTO attendance (member_id, checkin_date, checkin_at) VALUES (?,?,?)",
            (mid, today.isoformat(), now),
        )
