---
name: context-file-locator
description: >-
  Use this skill to quickly locate the exact Backend, Frontend, Database, and Test
  files related to any module, Use Case (UC01-UC22), Business Rule (BR-01-BR-20),
  or Exception (EX-01-EX-18), along with exact line ranges (StartLine/EndLine) in
  docs/Quy_Trinh_Nghiep_Vu.md and docs/SYSTEM_DESIGN.md so agents never need to
  read entire large files.
---

# Context & File Locator Skill (Bản Đồ Định Vị Nhanh Code & Tài Liệu)

Sử dụng bảng chỉ mục này để mở **đúng file code cần sửa** và truyền **đúng `StartLine` / `EndLine`** khi gọi `read_file` trên các tài liệu gốc, tránh làm tràn ngữ cảnh.

---

## 1. Chỉ Mục Đọc Tài Liệu Gốc Theo Khoảng Dòng (`StartLine` – `EndLine`)

### A. [`docs/Quy_Trinh_Nghiep_Vu.md`](file:///Users/macprom2/Documents/NEU%20Agent/Code/Website%20gi%C3%BAp%20gi%E1%BA%A3ng%20vi%C3%AAn%20%C4%91i%E1%BB%83m%20danh%20sinh%20vi%C3%AAn%20nhanh%20ch%C3%B3ng/docs/Quy_Trinh_Nghiep_Vu.md) (Tổng 308 dòng)
- **Tổng quan, Cây thư mục & Nguyên lý 2 Vòng (GPS + Siêu âm)**: `StartLine: 16`, `EndLine: 46`
- **Actors (`PUBLIC`, `STUDENT`, `LECTURER`, `ADMIN`) & Ma trận phân quyền**: `StartLine: 49`, `EndLine: 84`
- **Luồng sự kiện 4 giai đoạn, State Machine & Sơ đồ QR vs PIN**: `StartLine: 87`, `EndLine: 180`
- **Nhóm Quy tắc Auth & Định danh SV (`BR-01` $\rightarrow$ `BR-03`)**: `StartLine: 186`, `EndLine: 190`
- **Nhóm Quy tắc Thư mục, Lớp học, Excel LMS & Quick Look (`BR-04` $\rightarrow$ `BR-06`)**: `StartLine: 191`, `EndLine: 206`
- **Nhóm Quy tắc Phiên, Reset, QR/PIN 60s & Phát Siêu âm (`BR-07` $\rightarrow$ `BR-10`)**: `StartLine: 207`, `EndLine: 216`
- **Nhóm Quy tắc Vòng 1 GPS, 4 thông tin PIN, Duyệt tại lớp & Vòng 2 Audio (`BR-11` $\rightarrow$ `BR-15`)**: `StartLine: 217`, `EndLine: 229`
- **Nhóm Quy tắc Device Lock, WebSocket, Chốt vắng, Xuất Excel & Override (`BR-16` $\rightarrow$ `BR-20`)**: `StartLine: 230`, `EndLine: 242`
- **Bảng 22 Use Cases (`UC01` $\rightarrow$ `UC22`)**: `StartLine: 245`, `EndLine: 273`
- **Bảng 18 Ngoại lệ (`EX-01` $\rightarrow$ `EX-18`)**: `StartLine: 276`, `EndLine: 300`

### B. [`docs/SYSTEM_DESIGN.md`](file:///Users/macprom2/Documents/NEU%20Agent/Code/Website%20gi%C3%BAp%20gi%E1%BA%A3ng%20vi%C3%AAn%20%C4%91i%E1%BB%83m%20danh%20sinh%20vi%C3%AAn%20nhanh%20ch%C3%B3ng/docs/SYSTEM_DESIGN.md) (Tổng 227 dòng)
- **Chương 1 & 2 (Kiến trúc 1 VPS, Docker `neu_internal_net`, `Caddyfile` 1 FE + 3 BE)**: `StartLine: 20`, `EndLine: 110`
- **Chương 3 (6 Nhóm Redis Key Schema & TTL)**: `StartLine: 114`, `EndLine: 126`
- **Chương 4 (Đồng bộ WebSocket đa Server qua Redis Pub/Sub `ws:session:{id}`)**: `StartLine: 129`, `EndLine: 162`
- **Chương 5 (Lưu trữ Phôi Excel `BYTEA` TOAST + Redis QuickLook)**: `StartLine: 166`, `EndLine: 182`
- **Chương 6 (`SQLAlchemy AsyncEngine` Pool & 4 B-Tree Unique Composite Indexes)**: `StartLine: 185`, `EndLine: 211`
- **Chương 7 (4 Quy tắc Bất biến & Quy trình 5 bước Redis-First)**: `StartLine: 214`, `EndLine: 227`

### C. [`database/docs/schema_design.md`](file:///Users/macprom2/Documents/NEU%20Agent/Code/Website%20gi%C3%BAp%20gi%E1%BA%A3ng%20vi%C3%AAn%20%C4%91i%E1%BB%83m%20danh%20sinh%20vi%C3%AAn%20nhanh%20ch%C3%B3ng/database/docs/schema_design.md) & [`docs/API_Specification.md`](file:///Users/macprom2/Documents/NEU%20Agent/Code/Website%20gi%C3%BAp%20gi%E1%BA%A3ng%20vi%C3%AAn%20%C4%91i%E1%BB%83m%20danh%20sinh%20vi%C3%AAn%20nhanh%20ch%C3%B3ng/docs/API_Specification.md)
- ERD 10 bảng: `schema_design.md` (`StartLine: 1`, `EndLine: 148`)
- Ràng buộc & Indexes: `schema_design.md` (`StartLine: 152`, `EndLine: 206`)
- Đặc tả REST & WS Endpoints: `API_Specification.md` (`StartLine: 1`, `EndLine: 119`)

---

## 2. Bản Đồ Ánh Xạ Từ Phân Hệ / Use Case Sang Đúng File Code Cần Sửa

| Phân hệ / Đợt | Mã UC / BR / EX | Các File Backend Cần Tập Trung | Các File Frontend Cần Tập Trung | Skill Đi Kèm |
| :--- | :--- | :--- | :--- | :--- |
| **Đợt 0B: Hạ tầng, Redis & DB 10 Bảng** | Chương 1–6 `SYSTEM_DESIGN.md` | `docker/Caddyfile`<br/>`docker/docker-compose.yml`<br/>`backend/app/core/{config,redis}.py`<br/>`backend/app/db/session.py`<br/>`backend/app/models/*.py` | - | `redis-stateless-guards` |
| **Đợt 1: Auth, Users, Students & Buildings** | `UC01`, `UC02`, `UC18`–`UC20`<br/>`BR-01`–`BR-03`<br/>`EX-01`, `EX-16` | `backend/app/api/deps.py`<br/>`backend/app/api/endpoints/{auth,buildings,system}.py`<br/>`backend/app/schemas/auth.py` | `frontend/src/lib/api.ts`<br/>`frontend/src/app/page.tsx`<br/>`frontend/src/app/login/page.tsx` | `neu-ui-design-system` |
| **Đợt 2: Thư mục, Lớp, Excel `BYTEA` & Quick Look** | `UC03`–`UC06`, `UC14`, `UC22`<br/>`BR-04`–`BR-06`, `BR-19`<br/>`EX-02`, `EX-03`, `EX-15`, `EX-17` | `backend/app/services/excel_service.py`<br/>`backend/app/api/endpoints/{folders,courses}.py`<br/>`backend/app/models/courses.py` | `frontend/src/app/dashboard/page.tsx`<br/>`frontend/src/components/{QuickLookModal,FolderCard}.tsx`<br/>`frontend/src/app/courses/[id]/page.tsx` | `excel-bytea-quicklook`<br/>`neu-ui-design-system` |
| **Đợt 3: Phiên (Open/Close/Reset), QR 60s, Phát Siêu âm & WS** | `UC07`–`UC10`, `UC12`, `UC13`, `UC15`<br/>`BR-07`–`BR-10`, `BR-15`, `BR-17`, `BR-18`<br/>`EX-04`, `EX-09`, `EX-11`, `EX-14` | `backend/app/services/{qr_service,audio_service,websocket_manager}.py`<br/>`backend/app/api/endpoints/sessions.py` | `frontend/src/hooks/useUltrasonicSender.ts`<br/>`frontend/src/app/projector/[session_id]/page.tsx` | `ultrasonic-2ring-protocol`<br/>`redis-stateless-guards` |
| **Đợt 4: Điểm danh 2 Vòng (QR & PIN 4 Trường), Duyệt PIN & Test** | `UC11`, `UC16`, `UC17`, `UC21`<br/>`BR-11`–`BR-14`, `BR-16`, `BR-20`<br/>`EX-05`–`EX-08`, `EX-10`, `EX-12`, `EX-13`, `EX-18` | `backend/app/services/{geo_service,audio_service}.py`<br/>`backend/app/api/endpoints/attendance.py`<br/>`backend/tests/*.py` | `frontend/src/hooks/{useUltrasonicReceiver,useGeolocation}.ts`<br/>`frontend/src/app/student/[pin_code]/page.tsx` | `ultrasonic-2ring-protocol`<br/>`redis-stateless-guards`<br/>`qa-verification-suite` |
