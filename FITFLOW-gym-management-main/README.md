# FITFLOW — Hệ thống quản lý phòng gym

Website quản trị phòng gym dạng giao diện một trang, phù hợp để mở và phát triển tiếp trong Visual Studio Code.

## Đăng nhập quản trị

- Email: `admin@fitflow.vn`
- Mật khẩu: `admin123`

## Cách chạy

1. Mở thư mục dự án bằng Visual Studio Code.
2. Mở file `index.html` bằng tiện ích **Live Server**, hoặc mở trực tiếp bằng trình duyệt.

## Chức năng có sẵn

- Đăng nhập và đăng xuất quản trị.
- Bảng tổng quan: hội viên, doanh thu, điểm danh và gói sắp hết hạn.
- Quản lý hội viên, gói tập, lịch tập, điểm danh và thanh toán.
- Báo cáo hoạt động cơ bản.
- Trợ lý AI mẫu: hỗ trợ tóm tắt gia hạn và tiếp nhận yêu cầu.
- Giao diện thích ứng trên điện thoại.


## Backend (Flask + SQLite)

```
backend/
├── app.py            # khởi tạo Flask, phục vụ giao diện
├── db.py             # kết nối SQLite, tạo bảng, dữ liệu mẫu
├── schema.sql        # cấu trúc database
├── utils.py          # kiểm tra dữ liệu, đăng nhập, tính trạng thái hội viên
└── controllers/      # auth, members, packages, schedule, attendance, payments, reports
```

Cách chạy:

```bash
pip install -r backend/requirements.txt
python backend/app.py
```

Mở http://localhost:5000. Lần chạy đầu tiên sẽ tự tạo `backend/fitflow.db` cùng dữ liệu mẫu (tài khoản admin ở trên). Nếu mở `index.html` trực tiếp mà không chạy backend, giao diện vẫn dùng `localStorage` như trước.

### Các API chính (cần đăng nhập, trừ `login`)

| Nhóm | Endpoint |
|---|---|
| Đăng nhập | `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me` |
| Hội viên | `GET/POST /api/members`, `GET/PUT/DELETE /api/members/<id>` (`?q=` để tìm kiếm) |
| Gói tập | `GET/POST /api/packages`, `PUT/DELETE /api/packages/<id>` |
| Lịch tập | `GET/POST /api/schedule` (`?weekday=0..6`), `DELETE /api/schedule/<id>` |
| Điểm danh | `GET /api/attendance` (`?date=`), `POST /api/attendance` với `{"member_id": 1}` |
| Thanh toán | `GET/POST /api/payments`, `PATCH /api/payments/<id>/pay` (thanh toán xong sẽ tự gia hạn gói) |
| Báo cáo | `GET /api/reports/dashboard`, `GET /api/reports/expiring` |
