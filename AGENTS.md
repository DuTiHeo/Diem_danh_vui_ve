# HƯỚNG DẪN DÀNH CHO AI AGENTS & DEVELOPER - HỆ THỐNG NEU ATTENDANCE 🤖

Tài liệu này cung cấp ngữ cảnh kỹ thuật, kiến trúc hệ thống, cấu trúc mã nguồn, chuẩn mực viết code và quy trình vận hành cho các AI Coding Agents (Antigravity, Cursor, Copilot, Claude Code...) và các lập trình viên tham gia phát triển dự án **NEU Attendance**.

---

## 1. Tổng Quan Hệ Thống (System Overview)

- **Tên dự án**: **NEU Attendance - Multi-Layer Smart Classroom Attendance System**
- **Mục tiêu**: Nền tảng hỗ trợ giảng viên Đại học Kinh tế Quốc dân (NEU) quản lý lớp học phần theo **Cây Thư mục Môn học (`SubjectFolder` $\rightarrow$ `Course`)**, xem trước phôi điểm danh chuẩn trường (**Quick Look Preview** như macOS) và điểm danh sinh viên nhanh chóng dưới 60 giây bằng **Mã QR/PIN động 60s** kết hợp **Xác thực hiện diện vật lý 2 vòng**:
  - **Vòng 1 (Không gian 2D)**: Định vị GPS Tòa nhà nội khu NEU (`A1`, `A2`, `B`, `C`, `D`, `D2`) qua công thức Haversine.
  - **Vòng 2 (Không gian 3D)**: Sóng âm thanh cận siêu âm ($18.1\text{ kHz} - 20.5\text{ kHz}$) qua Web Audio API (tùy chọn bật/tắt `require_audio`).
- **Tài liệu nghiệp vụ chuẩn (Single Source of Truth)**:
  > [!IMPORTANT]
  > Mọi quy định nghiệp vụ chi tiết, luồng xử lý, ma trận phân quyền, 20 Business Rules (`BR-01` $\rightarrow$ `BR-20`), 22 Use Cases (`UC01` $\rightarrow$ `UC22`) và 18 Ngoại lệ (`EX-01` $\rightarrow$ `EX-18`) được đặc tả tập trung tại [`docs/Quy_Trinh_Nghiep_Vu.md`](file:///Users/macprom2/Documents/NEU%20Agent/Code/Website%20giúp%20giảng%20viên%20điểm%20danh%20sinh%20viên%20nhanh%20chóng/docs/Quy_Trinh_Nghiep_Vu.md). Không định nghĩa lại các quy tắc nghiệp vụ tại tệp này để tránh sai lệch dữ liệu.

---

## 2. Tài Liệu Tham Chiếu Cốt Lõi (Documentation Index)

| Tài liệu | Đường dẫn | Nội dung phụ trách |
| :--- | :--- | :--- |
| **Đặc tả Quy trình & Nghiệp vụ** | [`docs/Quy_Trinh_Nghiep_Vu.md`](file:///Users/macprom2/Documents/NEU%20Agent/Code/Website%20giúp%20giảng%20viên%20điểm%20danh%20sinh%20viên%20nhanh%20chóng/docs/Quy_Trinh_Nghiep_Vu.md) | Luồng nghiệp vụ End-to-End, State Machine, 20 BR, 22 UC, 18 Ngoại lệ |
| **Thiết kế Kiến trúc Hệ thống** | [`docs/SYSTEM_DESIGN.md`](file:///Users/macprom2/Documents/NEU%20Agent/Code/Website%20giúp%20giảng%20viên%20điểm%20danh%20sinh%20viên%20nhanh%20chóng/docs/SYSTEM_DESIGN.md) | Kiến trúc 1 VPS, Caddy Load Balancer (1 FE + 3 BE), Redis Key Schema & Pub/Sub, DB Pool & `BYTEA` TOAST |
| **Đặc tả API & WebSocket** | [`docs/API_Specification.md`](file:///Users/macprom2/Documents/NEU%20Agent/Code/Website%20giúp%20giảng%20viên%20điểm%20danh%20sinh%20viên%20nhanh%20chóng/docs/API_Specification.md) | Chi tiết REST Endpoints, WebSocket Events & Schemas |
| **Thiết kế Cơ sở Dữ liệu** | [`database/docs/schema_design.md`](file:///Users/macprom2/Documents/NEU%20Agent/Code/Website%20giúp%20giảng%20viên%20điểm%20danh%20sinh%20viên%20nhanh%20chóng/database/docs/schema_design.md) | ERD 10 bảng chuẩn, Datatypes, Foreign Keys & Unique Composite Indexes |
| **Phôi Danh Sách Lớp Mẫu** | [`docs/PTTC 66ECQ thứ 7 B301.xls`](file:///Users/macprom2/Documents/NEU%20Agent/Code/Website%20giúp%20giảng%20viên%20điểm%20danh%20sinh%20viên%20nhanh%20chóng/docs/PTTC%2066ECQ%20th%E1%BB%A9%207%20B301.xls) | File Excel mẫu thực tế từ hệ thống LMS NEU để kiểm thử parser |

---

## 3. Công Nghệ Sử Dụng (Tech Stack)

| Tầng | Công nghệ | Chi tiết sử dụng |
| :--- | :--- | :--- |
| **Frontend** | Next.js (App Router), React 19, TypeScript | Tailwind CSS, Web Audio API (`OscillatorNode`, `AnalyserNode` FFT 8192 bins), HTML5 Geolocation API, WebSocket Client |
| **Backend** | Python 3.11+, FastAPI | Async REST API, WebSocket Server (`ConnectionManager`), Uvicorn / Gunicorn |
| **ORM & Migration** | SQLAlchemy 2.0+ (Async), Alembic | `AsyncSession`, 10 Declarative Models (`UUID` PK), Pydantic v2 DTO Schemas |
| **Bảo mật & Auth** | Microsoft OAuth 2.0 (Entra ID), PyJWT | Xác thực domain `@neu.edu.vn` & `@st.neu.edu.vn`, Role-based Dependencies (`deps.py`) |
| **Xử lý File Excel** | OpenPyXL, xlrd | Đọc/Ghi file LMS `.xls`/`.xlsx` đa Sheet; Lưu phôi nhị phân (`BYTEA`) trong DB + Cache JSON trên Redis cho Quick Look ($< 1\text{ms}$) |
| **Cache & Realtime** | Redis 7+ | Cache `QRToken` (TTL 60s), Cache JSON `QuickLook`, Atomic Set lớp, Anti-Proxy Device Lock, Rate Limiting, WebSocket Pub/Sub |
| **Database** | PostgreSQL 16+ | 10 bảng chuẩn hóa, `SQLAlchemy AsyncEngine Connection Pool`, B-Tree Unique Composite Indexes, Audit Logging |
| **DevOps & Load Balancer** | Docker, Docker Compose, Caddy 2 | **1 cổng Caddy** (Port 80/443) điều hướng **1 Frontend** (`:3000`) & cân bằng tải **3 Backend** (`:8000`) trong mạng nội bộ Docker |

---

## 4. Cấu Trúc Dự Án (Project Structure)

```text
[NEU-Attendance]/
├── .gitignore
├── .env.example                           # Biến môi trường mẫu
├── AGENTS.md                              # Tệp ngữ cảnh kỹ thuật & chỉ dẫn phát triển (Tệp này)
├── docker/
│   ├── Caddyfile                          # Cấu hình Caddy 2 Reverse Proxy & Load Balancer (1 FE + 3 BE)
│   └── docker-compose.yml                 # Cấu hình chạy Caddy, PostgreSQL, Redis, 3x Backend, Frontend
│
├── database/
│   └── docs/
│       └── schema_design.md               # Thiết kế ERD 10 bảng, kiểu dữ liệu và Unique Indexes
│
├── docs/                                  # Tài liệu đặc tả nghiệp vụ và kỹ thuật (Single Source of Truth)
│   ├── Quy_Trinh_Nghiep_Vu.md             # Đặc tả 22 UCs, 20 Business Rules (BR), 18 Exceptions (EX), State Machine
│   ├── SYSTEM_DESIGN.md                   # Đặc tả kiến trúc hệ thống, Redis Key Schema, Pub/Sub, DB Pool, BYTEA TOAST
│   ├── API_Specification.md               # Đặc tả REST API & WebSocket Endpoints
│   ├── Use_Cases_Analysis.md              # Phân tích kịch bản sử dụng ban đầu
│   └── PTTC 66ECQ thứ 7 B301.xls          # File mẫu danh sách lớp chuẩn Phòng QLĐT NEU
│
├── test_ultrasound/                       # PoC độc lập kiểm thử sóng cận siêu âm (15kHz - 21kHz)
│   ├── sender.html                        # Bộ phát qua OscillatorNode
│   ├── receiver.html                      # Bộ thu tắt lọc ồn + vẽ phổ FFT 8192 bins
│   └── server.py                          # HTTPS server nội bộ kiểm thử micro di động
│
├── backend/                               # Mã nguồn Backend API (FastAPI + Async SQLAlchemy)
│   ├── alembic.ini
│   ├── alembic/                           # Database Migrations
│   ├── requirements.txt
│   ├── main.py                            # Entrypoint FastAPI app, CORS, Lifespan
│   ├── tests/                             # Bộ kiểm thử Pytest tự động
│   └── app/
│       ├── core/                          # config.py, redis.py, security.py
│       ├── db/                            # session.py (AsyncEngine, get_db)
│       ├── models/                        # 10 SQLAlchemy ORM Models (users, students, buildings, courses, attendance)
│       ├── schemas/                       # Pydantic v2 DTOs
│       ├── crud/                          # Data Access Layer
│       ├── services/                      # excel_service, qr_service, geo_service, audio_service, websocket_manager
│       └── api/
│           ├── deps.py                    # Auth & RBAC Dependencies
│           ├── api_router.py              # Prefix /api/v1
│           └── endpoints/                 # Thin Controllers (auth, buildings, folders, courses, sessions, attendance, system)
│
└── frontend/                              # Mã nguồn Frontend Web Responsive (Next.js + TypeScript)
    ├── package.json
    ├── tsconfig.json
    └── src/
        ├── app/
        │   ├── page.tsx                   # Trang chủ: Đăng nhập GV / Cổng nhập PIN cho SV
        │   ├── login/                     # Trang đăng nhập Microsoft 365 / Mock Auth
        │   ├── dashboard/                 # Thư mục Môn học -> Lớp học phần + Quick Look Preview
        │   ├── courses/[id]/              # Chi tiết lớp, danh sách 15 buổi, Mở/Reset phiên
        │   ├── projector/[session_id]/    # Màn chiếu GV: QR/PIN 60s, phát siêu âm, WS realtime & duyệt PIN
        │   └── student/[pin_code]/        # Màn hình SV: Luồng QR (MS365) & Luồng PIN (4 thông tin) + GPS & Mic
        ├── components/                    # QuickLookModal, FolderCard, UltrasonicPlayer...
        ├── hooks/                         # useUltrasonicSender, useUltrasonicReceiver, useGeolocation
        └── lib/                           # api.ts (HTTP/WS client, Interceptors)
```

---

## 5. Lệnh Khởi Chạy & Vận Hành (Commands & Workflows)

### 5.1. Khởi chạy bằng Docker
```bash
# Chạy toàn bộ (PostgreSQL, Redis, Backend, Frontend)
docker compose -f docker/docker-compose.yml up --build -d

# Xem log Backend
docker compose -f docker/docker-compose.yml logs -f backend

# Dừng toàn bộ
docker compose -f docker/docker-compose.yml down
```

### 5.2. Chạy Backend thủ công (FastAPI)
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Chạy migration
alembic upgrade head

# Khởi động server (Port 8000)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 5.3. Chạy Frontend thủ công (Next.js)
```bash
cd frontend
npm install
npm run dev
```

### 5.4. Chạy Kiểm Thử Tự Động
```bash
pytest backend/tests/ -v
```

---

## 6. Quy Chuẩn Kỹ Thuật Bất Biến (Coding Standards & Invariants)

### 6.1. Backend & Database
1. **Kiến trúc 3 tầng nghiêm ngặt (Separation of Concerns)**:
   - **`endpoints/`**: Nhận request, validate Pydantic DTO, kiểm tra quyền via `Depends(deps.get_current_...)`, ủy quyền cho `services/` hoặc `crud/`.
   - **`services/`**: Xử lý logic thuần túy (`excel_service.py`, `geo_service.py`, `audio_service.py`, `qr_service.py`, `websocket_manager.py`).
   - **`models/` & `crud/`**: Đồng bộ chính xác với [`database/docs/schema_design.md`](file:///Users/macprom2/Documents/NEU%20Agent/Code/Website%20giúp%20giảng%20viên%20điểm%20danh%20sinh%20viên%20nhanh%20chóng/database/docs/schema_design.md).
2. **Transaction Database & Async Session**:
   - Sử dụng `AsyncSession` qua `get_db`.
   - Khi thực hiện **Reset Phiên** (`UC13` - `BR-07`), việc thu hồi `qr_tokens`, xóa `attendance_records` và cập nhật `session.status = PENDING` phải nằm trong cùng một Database Transaction.

### 6.2. Frontend & Web Audio API
1. **Không nhúng Camera quét QR trong Web (`BR-08`)**:
   - Sinh viên dùng ứng dụng Camera / trình quét mã mặc định trên điện thoại để quét mã QR và mở link `{{base_url}}/student/{pin_code}}`. Frontend chỉ xử lý các bước tiếp theo trên trình duyệt.
2. **Quy chuẩn Bộ Thu Sóng Siêu Âm (`useUltrasonicReceiver` - `BR-13`)**:
   - Bắt buộc tắt toàn bộ tính năng lọc âm thoại khi gọi `getUserMedia`:
     ```typescript
     const stream = await navigator.mediaDevices.getUserMedia({
       audio: {
         echoCancellation: false,
         noiseSuppression: false,
         autoGainControl: false,
         sampleRate: { ideal: 48000 }
       }
     });
     ```
   - Cấu hình `AnalyserNode`: `fftSize = 8192` ($\approx 5,86\text{ Hz/bin}$), chỉ tìm đỉnh trong dải $15.000\text{ Hz} - 22.000\text{ Hz}$ và đóng stream mic ngay sau khi lấy mẫu.
3. **Quy chuẩn Bộ Phát Sóng Siêu Âm (`useUltrasonicSender` - `BR-10`)**:
   - Dùng `OscillatorNode` dạng sóng `sine`.
   - Bắt buộc dùng `gainNode.gain.linearRampToValueAtTime` ($30\text{ms}-50\text{ms}$) khi chuyển tần số hoặc bật/tắt để tránh tiếng click/bụp trên loa giảng đường.

---

## 7. Phân Hệ Phụ Trách (Module Ownership Matrix)

Khi thực hiện task, các agent và lập trình viên đối chiếu phạm vi file và tài liệu nghiệp vụ tương ứng:

| Phân hệ | Nhánh Git gợi ý | Phạm vi File Backend & Frontend | Tham chiếu Use Cases & Rules |
| :--- | :--- | :--- | :--- |
| **Phân hệ 1: Auth, Users, Students & Buildings** | `feature/auth-users-buildings` | `models/{users, students, buildings}.py`<br/>`endpoints/{auth, buildings, system}.py`<br/>`frontend/src/app/login/` | `UC01`, `UC02`, `UC18`–`UC20`<br/>`BR-01`–`BR-03`<br/>`EX-01`, `EX-16` |
| **Phân hệ 2: Subject Folders, Courses, LMS Excel & Quick Look** | `feature/folders-courses-excel` | `models/courses.py`<br/>`services/excel_service.py`<br/>`endpoints/{folders, courses}.py`<br/>`frontend/src/app/dashboard/`<br/>`components/QuickLookModal.tsx` | `UC03`–`UC06`, `UC14`, `UC22`<br/>`BR-04`–`BR-06`, `BR-19`<br/>`EX-02`, `EX-03`, `EX-15`, `EX-17` |
| **Phân hệ 3: Sessions (Open/Close/Reset), QR/PIN 60s, Ultrasonic Sender & WS** | `feature/session-qr-ultrasonic-sender` | `models/attendance.py` (`AttendanceSession`, `QRToken`)<br/>`services/{qr_service, websocket_manager}.py`<br/>`endpoints/sessions.py`<br/>`frontend/src/app/projector/` | `UC07`–`UC10`, `UC12`, `UC13`, `UC15`<br/>`BR-07`–`BR-10`, `BR-15`, `BR-17`, `BR-18`<br/>`EX-04`, `EX-09`, `EX-11`, `EX-14` |
| **Phân hệ 4: 2-Ring Check-in (QR & 4-Field PIN), Approval & Manual Override** | `feature/attendance-2ring-verification` | `models/attendance.py` (`AttendanceRecord`, `AuditLog`)<br/>`services/{geo_service, audio_service}.py`<br/>`endpoints/attendance.py`<br/>`frontend/src/app/student/` | `UC11`, `UC16`, `UC17`, `UC21`<br/>`BR-11`–`BR-14`, `BR-16`, `BR-20`<br/>`EX-05`–`EX-08`, `EX-10`, `EX-12`, `EX-13`, `EX-18` |
