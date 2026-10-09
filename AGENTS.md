# AGENTS.md - Hướng dẫn cho Coding Agents

## Dự án này là gì?
Website hỗ trợ giảng viên điểm danh sinh viên nhanh chóng bằng QR động và xác thực vị trí GPS. Hệ thống cho phép upload danh sách Excel từ LMS, tạo QR/PIN cho từng buổi học, sinh viên quét QR để xác nhận có mặt với kiểm tra GPS/geofence.

## Cấu trúc dự án (sắp tới)
```
├── backend/          # FastAPI (Python 3.11+)
├── frontend/         # Web Responsive (React / Next.js / TypeScript)
├── docker/           # Dockerfile, docker-compose.yml
├── database/         # Migration files (Alembic)
└── docs/             # Tài liệu thiết kế & phân tích nghiệp vụ
```

## Cách build/run/test
- **Docker:** `docker-compose up --build` (chạy cả BE + FE + DB)
- **Backend:** `cd backend && pip install -r requirements.txt && uvicorn main:app --reload`
- **Frontend:** `cd frontend && npm install && npm run dev`
- **Database:** PostgreSQL (qua Docker), chạy migrations: `alembic upgrade head`
- **Test:** `pytest backend/tests/` (backend) và `npm test` (frontend)

## Quy ước code
- **Backend:** Python 3.11+, FastAPI, Pydantic, SQLAlchemy, Alembic
- **Frontend:** React / Next.js, TypeScript, Tailwind CSS (giao diện Responsive cho cả Desktop và Mobile Web)
- REST API design với OpenAPI/Swagger spec
- Git commit với conventional commits
- Code review trước khi merge

## Thư mục quan trọng
- `backend/`: FastAPI server, authentication (OAuth Microsoft), QR generation, GPS validation, Excel import/export
- `frontend/`: Web Responsive (Desktop cho Giảng viên trình chiếu, Mobile Web hoặc Desktop cho Sinh viên quét QR/PIN, trong trường hợp sinh viên không thể sử dụng điện thoại vì có thể dùng máy tính và điểm danh trên máy tính)
- `docker/`: Dockerfile, docker-compose.yml để chạy BE + FE + DB
- `database/`: Schema PostgreSQL và migrations

## ⚠️ KHÔNG BAO GIỜ
- **Viết secrets vào code:** API keys, passwords phải trong `.env`
- **Commit file `.env`:** Luôn check `.gitignore`
- **Hardcode credentials:** Dùng environment variables
- **Bỏ qua validation:** Luôn validate input từ client
- **Quên error handling:** Xử lý lỗi đầy đủ, log đầy đủ

## Tích hợp Microsoft 365
- Sử dụng OAuth 2.0 / Entra ID
- Cấu hình trong `.env` với `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET`
- Không hardcode tenant ID hoặc client secrets
