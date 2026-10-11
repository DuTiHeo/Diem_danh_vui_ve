# API Specification

## 1. Authentication (REST)
- **POST `/api/v1/auth/mock-login`**: (Chỉ chạy khi `DEV_MOCK_AUTH=true`) Đăng nhập giả lập.
  - Body: `{"email": "...", "role": "LECTURER | STUDENT"}`
  - Response: `{"access_token": "...", "token_type": "bearer"}`
- **GET `/api/v1/auth/microsoft`**: Redirect URL to Microsoft Entra ID.
- **GET `/api/v1/auth/callback`**: Microsoft OAuth callback.
- **GET `/api/v1/auth/me`**: Lấy thông tin user hiện tại (JWT required).

## 2. Courses & Enrollments
- **GET `/api/v1/courses`**: Lấy danh sách lớp của giảng viên (Role: LECTURER).
- **POST `/api/v1/courses/upload`**: Upload file Excel (`multipart/form-data`). 
  - Trả về preview thông tin lớp và sinh viên.
- **POST `/api/v1/courses`**: Xác nhận tạo lớp học phần sau khi preview.
- **GET `/api/v1/courses/{id}`**: Lấy thông tin chi tiết và danh sách sinh viên.

## 3. Sessions & QR
- **GET `/api/v1/courses/{course_id}/sessions`**: Lấy danh sách các buổi học.
- **POST `/api/v1/sessions/{session_id}/open`**: Mở phiên điểm danh. Trả về `qr_token` & `pin_code`.
- **POST `/api/v1/sessions/{session_id}/close`**: Kết thúc phiên điểm danh, update những SV chưa điểm danh thành ABSENT.
- **POST `/api/v1/sessions/{session_id}/refresh-qr`**: Hủy mã cũ, tạo QR/PIN mới (60s).
- **GET `/api/v1/qr/{pin_code}`**: Lấy thông tin phiên điểm danh từ PIN (Public, dùng cho Frontend validate).

## 4. Attendance
- **POST `/api/v1/attendance/qr`**: Sinh viên quét QR/đăng nhập và xác nhận (Role: STUDENT).
  - Body: `{"pin_code": "...", "latitude": float, "longitude": float, "accuracy": float}`
- **POST `/api/v1/attendance/pin`**: Sinh viên nhập PIN không cần login (Public).
  - Body: `{"pin_code": "...", "student_code": "...", "full_name": "...", "latitude": float, "longitude": float, "accuracy": float}`
- **POST `/api/v1/attendance/manual`**: Giảng viên override thủ công (Role: LECTURER).
  - Body: `{"session_id": "...", "student_id": "...", "status": "ATTENDED | ABSENT"}`

## 5. Export
- **GET `/api/v1/courses/{course_id}/export`**: Download file `.xlsx` kết quả điểm danh.

## 6. Realtime (WebSocket)
- **WS `/api/v1/ws/sessions/{session_id}`**: 
  - Giảng viên connect để nhận cập nhật.
  - Sự kiện trả về: `{"event": "ATTENDANCE_MARKED", "student_id": "...", "marked_at": "..."}`
  - Sự kiện trả về: `{"event": "SESSION_CLOSED"}`

