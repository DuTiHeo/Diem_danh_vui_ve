# API Specification - NEU Attendance System (`/api/v1`)

## 1. Authentication (`/api/v1/auth`)
- **POST `/api/v1/auth/mock-login`**: (Khi `DEV_MOCK_AUTH=true`) Đăng nhập giả lập (`UC01`).
  - Body: `{"email": "gv@neu.edu.vn | 11242145@st.neu.edu.vn", "full_name": "...", "role": "LECTURER | STUDENT | ADMIN"}`
  - Response: `{"access_token": "...", "token_type": "bearer", "role": "..."}`
- **GET `/api/v1/auth/microsoft`**: Chuyển hướng đăng nhập Microsoft Entra ID (`UC01`).
- **GET `/api/v1/auth/callback`**: Callback OAuth2 từ Microsoft Entra ID.
- **GET `/api/v1/auth/me`**: Lấy thông tin hồ sơ người dùng hiện tại (`UC02`).

---

## 2. Subject Folders - Thư mục Môn học (`/api/v1/folders`)
- **GET `/api/v1/folders`**: Lấy danh sách Thư mục Môn học của Giảng viên kèm các Lớp học phần bên trong (`UC03`).
- **POST `/api/v1/folders`**: Tạo Thư mục Môn học mới (`UC03`).
  - Body: `{"folder_name": "Phân tích tài chính", "semester": "HK1 2026-2027", "color_tag": "#3b82f6"}`
- **PUT `/api/v1/folders/{folder_id}`**: Đổi tên, màu sắc hoặc học kỳ của Thư mục Môn học (`UC03`).
- **DELETE `/api/v1/folders/{folder_id}?delete_courses=false`**: Xóa Thư mục Môn học (`UC03`, `EX-17`).
  - Nếu `delete_courses=false`: Giữ lại các lớp học phần bên trong (đưa về vùng chưa phân loại `folder_id = null`).
  - Nếu `delete_courses=true`: Xóa toàn bộ thư mục kèm các lớp học phần bên trong.

---

## 3. Courses & Quick Look Preview (`/api/v1/courses`)
- **GET `/api/v1/courses`**: Lấy danh sách tất cả Lớp học phần của Giảng viên (`UC05`).
- **POST `/api/v1/courses/upload`**: Upload 1 hoặc nhiều file Excel LMS (`.xls` / `.xlsx` gốc hoặc đã điểm danh sẵn 1 số buổi) (`UC04`, `UC22`).
  - Form-data: `file` (hoặc `files`), `folder_id` (tùy chọn — nếu bỏ trống sẽ tự động gom vào thư mục theo dòng `Học phần:` trong file Excel).
- **GET `/api/v1/courses/{course_id}`**: Lấy chi tiết lớp học phần, danh sách sinh viên và 15 buổi học (`UC05`).
- **GET `/api/v1/courses/{course_id}/quick-look`**: Lấy toàn bộ dữ liệu ma trận chuẩn phôi Phòng Quản lý Đào tạo NEU (`TT`, `Lớp`, `Mã số SV`, `Họ và tên đệm`, `Tên`, `Ngày Sinh`, các cột điểm danh `1..15`, `Ghi chú`, tiêu đề & chân trang) để hiển thị **Modal Quick Look Preview** (`UC06`).
- **PUT `/api/v1/courses/{course_id}`**: Cập nhật thông tin lớp (Đổi phòng học, tòa nhà `building_id`, hoặc di chuyển sang thư mục khác `folder_id`) (`UC05`).
- **DELETE `/api/v1/courses/{course_id}`**: Xóa lớp học phần kèm các phiên điểm danh và file template (`UC05`, `EX-17`).
- **GET `/api/v1/courses/{course_id}/export`**: Xuất và tải xuống file Excel kết quả điểm danh chuẩn phôi NEU (`UC14`).

---

## 4. Attendance Sessions & Dynamic QR/Audio (`/api/v1/sessions`)
- **POST `/api/v1/sessions/{course_id}/open`**: Mở phiên điểm danh cho buổi học số $N$ (`1..15`) (`UC07`).
  - Body:
    ```json
    {
      "session_number": 1,
      "building_id": "uuid-optional",
      "require_audio": true,
      "duration_seconds": 60
    }
    ```
  - Response:
    ```json
    {
      "session_id": "...",
      "pin_code": "786232",
      "audio_freq_hz": 18900,
      "require_audio": true,
      "expires_in_seconds": 60
    }
    ```
- **GET `/api/v1/sessions/{session_id}`**: Lấy trạng thái chi tiết của phiên điểm danh, mã PIN hiện tại, tần số siêu âm `audio_freq_hz`, danh sách sinh viên (`ATTENDED`, `PENDING_APPROVAL`, `ABSENT`, `PENDING`) (`UC08`, `UC10`).
- **POST `/api/v1/sessions/{session_id}/refresh-qr`**: Thu hồi mã cũ, sinh mã PIN 6 số mới (60s) và nhảy sang tần số siêu âm `audio_freq_hz` mới (`UC09`).
- **PATCH `/api/v1/sessions/{session_id}/audio-toggle`**: Bật/tắt nhanh công tắc `require_audio` ngay trên màn hình trình chiếu (`BR-15`, `EX-11`).
- **POST `/api/v1/sessions/{session_id}/close`**: Kết thúc phiên điểm danh (`CLOSED`), thu hồi mọi QR/PIN và chốt `ABSENT` cho các sinh viên chưa điểm danh (`UC12`).
- **DELETE `/api/v1/sessions/{session_id}/reset`**: **Xóa / Đặt lại (Reset) Phiên điểm danh** mở nhầm/chạy thử — xóa toàn bộ bản ghi điểm danh của buổi đó và đưa trạng thái buổi học về lại `PENDING` (`UC13`, `BR-07`).
- **GET `/api/v1/sessions/qr/{pin_code}`**: (Public) Kiểm tra mã PIN 6 số khả dụng và trả về thông tin buổi học, tên môn, phòng học, cờ `require_audio` (`UC15`).

---

## 5. Attendance Check-in & Approval (`/api/v1/attendance`)

### 5.1. Luồng 1: Sinh viên có điện thoại Quét QR + Đăng nhập Microsoft 365 (`UC16`)
- **POST `/api/v1/attendance/qr`** (Role: `STUDENT` - Yêu cầu JWT):
  - Body:
    ```json
    {
      "pin_code": "786232",
      "latitude": 20.99990,
      "longitude": 105.84270,
      "accuracy": 15.0,
      "detected_freq_hz": 18902,
      "device_fingerprint": "fp_hash_..."
    }
    ```
  - Xử lý: Kiểm tra mã PIN 60s + Enrollment + Device Lock + Vòng 1 (GPS) + Vòng 2 (Audio) $\rightarrow$ Ghi nhận ngay **`status = "ATTENDED"`** (`method = "QR"`).

### 5.2. Luồng 2: Sinh viên dùng Mã PIN (Không đăng nhập - Nhập 4 thông tin cá nhân) (`UC17`)
- **POST `/api/v1/attendance/pin`** (Role: `PUBLIC` - Không yêu cầu JWT):
  - Body:
    ```json
    {
      "pin_code": "786232",
      "student_code": "11242145",
      "full_name": "Bùi Phương Anh",
      "date_of_birth": "08/09/2006",
      "admin_class": "66E.TCNH",
      "latitude": 20.99990,
      "longitude": 105.84270,
      "accuracy": 15.0,
      "detected_freq_hz": 18902,
      "device_fingerprint": "fp_hash_..."
    }
    ```
  - Xử lý: Kiểm tra mã PIN 60s + Khớp 100% **4 thông tin (`student_code`, `full_name`, `date_of_birth`, `admin_class`)** + Device Lock + Vòng 1 (GPS) + Vòng 2 (Audio) $\rightarrow$ Ghi nhận **`status = "PENDING_APPROVAL"`** (`method = "PIN_ANONYMOUS"`) và đẩy cảnh báo vàng lên màn chiếu để Giảng viên nhìn mặt duyệt.

### 5.3. Giảng viên Duyệt / Từ chối Yêu cầu PIN & Can thiệp Thủ công (`UC10`, `UC11`)
- **POST `/api/v1/attendance/approve-pin`** (Role: `LECTURER`):
  - Body: `{"session_id": "...", "student_id": "...", "approved": true}`
  - Xử lý: Nếu `approved = true` $\rightarrow$ Chuyển sang `ATTENDED`; nếu `approved = false` $\rightarrow$ Chuyển sang `ABSENT` và ghi `audit_logs` (`EX-18`).
- **POST `/api/v1/attendance/manual`** (Role: `LECTURER`):
  - Body: `{"session_id": "...", "student_id": "...", "status": "ATTENDED | ABSENT"}`
  - Xử lý: Đổi trạng thái điểm danh thủ công (`method = "MANUAL"`) từ màn chiếu hoặc từ bảng **Quick Look Preview**.

---

## 6. Realtime WebSocket (`/api/v1/sessions/ws/{session_id}`)
- Giảng viên kết nối vào WebSocket của phiên học để nhận các sự kiện thời gian thực:
  - `ATTENDANCE_MARKED`: Sinh viên quét QR thành công (`status = "ATTENDED"`).
  - `PIN_APPROVAL_REQUESTED`: Sinh viên gửi yêu cầu điểm danh qua mã PIN (`status = "PENDING_APPROVAL"`) — bật thẻ vàng yêu cầu sinh viên giơ tay.
  - `PIN_APPROVAL_RESOLVED`: Giảng viên đã bấm Duyệt hoặc Từ chối yêu cầu PIN.
  - `ATTENDANCE_MANUAL_OVERRIDE`: Giảng viên thay đổi trạng thái thủ công.
  - `QR_REFRESHED`: Mã PIN 6 số và tần số siêu âm `audio_freq_hz` vừa được làm mới.
  - `SESSION_CLOSED` / `SESSION_RESET`: Phiên điểm danh đã đóng hoặc đã được đặt lại về `PENDING`.
