---
name: redis-stateless-guards
description: >-
  Use this skill when implementing Redis 7 caching, the 6 standardized Redis Key
  Schemas, the 5-step Redis-First Attendance Check-in pipeline (attendance.py),
  Session Open/Close/Reset cache invalidation (sessions.py), or multi-server
  WebSocket synchronization via Redis Pub/Sub (websocket_manager.py).
---

# Redis 7 Stateless Architecture, 6-Key Schema & WebSocket Pub/Sub Runbook

Tài liệu chuẩn hóa tầng In-Memory Redis 7 giúp cụm 3 container Backend (`backend-1`, `backend-2`, `backend-3`) phía sau Caddy 2 hoạt động **100% Stateless** và chịu tải hàng nghìn sinh viên điểm danh đồng thời.

---

## 1. Bảng 6 Nhóm Khóa Redis Chuẩn Hóa (Chương 3 `SYSTEM_DESIGN.md`)

| STT | Mẫu Key (`Key Pattern`) | Kiểu Redis | TTL | Mục đích & Cấu trúc dữ liệu |
| :-: | :--- | :-: | :-: | :--- |
| **1** | `qr:pin:{pin_code}` | `STRING` (JSON) | `EX 60` | `{"session_id", "course_id", "audio_freq_hz", "require_audio", "tolerance_hz", "building_id", "building_name", "building_code", "building_lat", "building_lng", "radius_meters"}` |
| **2** | `session:{session_id}:enrolled` | `HASH` | `EX 7200` | Field: `student_code` $\rightarrow$ Value (JSON): `{"student_id", "full_name", "date_of_birth", "admin_class"}` |
| **3** | `session:{session_id}:marked` | `SET` | `EX 7200` | Tập hợp các `student_id` đã `ATTENDED` hoặc `PENDING_APPROVAL` trong phiên (dùng `SADD` nguyên tử chống bấm đúp `EX-05`). |
| **4** | `session:{session_id}:device:{fp}` | `STRING` | `NX EX 7200` | Giá trị là `student_code` đầu tiên dùng thiết bị có `device_fingerprint = fp` trong phiên (`BR-16`, `EX-12`). |
| **5** | `course:{course_id}:quicklook` | `STRING` (JSON) | `EX 3600` | Bản cache JSON ma trận bảng điểm danh chuẩn phôi Phòng QLĐT NEU cho cửa sổ Quick Look (`< 1ms`). |
| **6** | `ratelimit:pin:{client_ip}` | `STRING` (Int) | `EX 60` | Đếm số lần gửi sai mã PIN hoặc sai 4 thông tin từ 1 IP. Nếu $> 10$ lần/phút $\rightarrow$ Chặn `HTTP 429` (`EX-13`). |

---

## 2. Quy Trình 5 Bước Redis-First Khi Điểm Danh (`UC16` QR & `UC17` PIN)

Mọi request tới `POST /api/v1/attendance/qr` và `POST /api/v1/attendance/pin` bắt buộc đi qua 5 bước theo đúng thứ tự sau:

1. **Bước 1 — Chặn Brute-Force (`ratelimit:pin:{client_ip}`)**:
   - Đọc số lần lỗi từ `ratelimit:pin:{client_ip}`. Nếu $\ge 10$ $\rightarrow$ Raise `HTTP 429 Too Many Requests` (`EX-13`).
2. **Bước 2 — Kiểm tra Mã PIN 60s (`qr:pin:{pin_code}`)**:
   - Đọc `qr:pin:{pin_code}` từ Redis (có fallback kiểm tra DB nếu Redis vừa khởi động lại).
   - Nếu không tồn tại hoặc đã hết hạn 60s $\rightarrow$ Tăng `INCR ratelimit:pin:{client_ip}` (`EX 60`) và raise `HTTP 400/404` (`EX-04`).
3. **Bước 3 — Kiểm tra Vòng 1 (GPS) & Vòng 2 (Ultrasonic Audio) ngay trong RAM**:
   - Tính khoảng cách Haversine với `building_lat`, `building_lng`, `radius_meters` lấy từ payload `qr:pin:{pin_code}`. Nếu quá xa $\rightarrow$ Raise `HTTP 400` (`EX-08`).
   - Nếu `require_audio == True`: Kiểm tra `|detected_freq_hz - audio_freq_hz| <= tolerance_hz`. Nếu lệch hoặc thiếu $\rightarrow$ Raise `HTTP 400` (`EX-10`).
4. **Bước 4 — Đối soát Danh sách Lớp (`enrolled`), Khóa Thiết bị (`device:{fp}`) & Chống Bấm Đúp (`marked`)**:
   - Tra `HGET session:{session_id}:enrolled {student_code}`:
     - Với luồng **PIN (`UC17`)**: Bắt buộc kiểm tra khớp 100% cả **4 trường** (không phân biệt hoa thường/khoảng trắng thừa): `student_code`, `full_name`, `date_of_birth`, `admin_class`. Nếu sai bất kỳ trường nào $\rightarrow$ Tăng `INCR ratelimit:pin:{client_ip}` và raise `HTTP 400` (`EX-06`).
   - Kiểm tra **Anti-Proxy Device Lock (`BR-16`, `EX-12`)**:
     - Nếu có `device_fingerprint`: Kiểm tra `GET session:{session_id}:device:{fp}`. Nếu đã tồn tại và khác `student_code` hiện tại $\rightarrow$ Ghi `AuditLog(action="DEVICE_PROXY_DETECTED")` và raise `HTTP 403` (`EX-12`).
   - Kiểm tra **Chống bấm đúp (`EX-05`)**:
     - Kiểm tra `SISMEMBER session:{session_id}:marked {student_id}`. Nếu đã tồn tại $\rightarrow$ Raise `HTTP 400` (`EX-05`).
5. **Bước 5 — Ghi Database, Đánh dấu Redis & Bắn Sự kiện Pub/Sub**:
   - Đánh dấu `SET session:{session_id}:device:{fp} {student_code} NX EX 7200` và `SADD session:{session_id}:marked {student_id}`.
   - Ghi `AttendanceRecord` vào PostgreSQL:
     - Luồng `QR`: `status = AttendanceStatus.ATTENDED`, `method = AttendanceMethod.QR`.
     - Luồng `PIN`: `status = AttendanceStatus.PENDING_APPROVAL`, `method = AttendanceMethod.PIN_ANONYMOUS`.
   - Xóa cache `DEL course:{course_id}:quicklook`.
   - Phát sự kiện qua kênh Redis Pub/Sub `ws:session:{session_id}` (`ATTENDANCE_MARKED` hoặc `PIN_APPROVAL_REQUESTED`).

---

## 3. Đồng Bộ WebSocket Đa Container Qua Redis Pub/Sub (`websocket_manager.py`)

- Khi Giảng viên mở kết nối WebSocket `/api/v1/sessions/ws/{session_id}` tại bất kỳ container Backend nào, `ConnectionManager` giữ kết nối cục bộ VÀ lắng nghe kênh Redis Pub/Sub `ws:session:{session_id}`.
- Khi `broadcast_to_session(session_id, message)` được gọi ở bất kỳ container nào, nó thực hiện `redis.publish(f"ws:session:{session_id}", json.dumps(message))` (kèm fallback gửi trực tiếp nếu chạy môi trường test không bật tiến trình background listener).
