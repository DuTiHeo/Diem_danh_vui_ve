# Database Schema Design - NEU Attendance System

## 1. ERD (Entity-Relationship Diagram - 10 Bảng Chuẩn Hóa)

```mermaid
erDiagram
    users ||--o{ students : "links to (1-1 optional)"
    users ||--o{ subject_folders : "owns"
    users ||--o{ courses : "lectures"
    users ||--o{ audit_logs : "performs"
    
    subject_folders ||--o{ courses : "contains"
    
    buildings ||--o{ courses : "default location"
    buildings ||--o{ attendance_sessions : "held at"
    
    courses ||--o{ enrollments : "has"
    courses ||--o{ attendance_sessions : "has"
    
    students ||--o{ enrollments : "enrolled in"
    students ||--o{ attendance_records : "has"
    
    attendance_sessions ||--o{ qr_tokens : "generates"
    attendance_sessions ||--o{ attendance_records : "records"

    users {
        uuid id PK
        string email UK "e.g., gv@neu.edu.vn, 11242145@st.neu.edu.vn"
        string full_name
        string role "LECTURER | STUDENT | ADMIN"
        string microsoft_id UK "nullable"
        boolean is_active "default true"
        timestamp created_at
        timestamp updated_at
    }

    subject_folders {
        uuid id PK
        uuid lecturer_id FK "-> users.id"
        string folder_name "VD: Phân tích tài chính, Lập trình Web"
        string semester "VD: HK1 2026-2027"
        string color_tag "Mã màu thư mục trên Dashboard"
        int sort_order "Thứ tự hiển thị"
        timestamp created_at
        timestamp updated_at
    }

    students {
        uuid id PK
        string student_code UK "8 chữ số (VD: 11242145)"
        string last_name "Họ và tên đệm (VD: Bùi Phương)"
        string first_name "Tên (VD: Anh)"
        string full_name "Họ tên đầy đủ (VD: Bùi Phương Anh)"
        string date_of_birth "Ngày Sinh DD/MM/YYYY (VD: 08/09/2006)"
        string admin_class "Lớp chuyên ngành (VD: 66E.TCNH)"
        uuid user_id FK "nullable -> users.id"
        timestamp created_at
    }

    buildings {
        uuid id PK
        string code UK "A1, A2, B, C, D, D2"
        string name
        float latitude
        float longitude
        int radius_meters "Default 70m - 80m"
        boolean is_active "default true"
    }

    courses {
        uuid id PK
        uuid folder_id FK "nullable -> subject_folders.id (Thư mục môn học)"
        string course_code "Mã học phần (VD: NHTC1108)"
        string course_name "Tên học phần (VD: Phân tích tài chính)"
        string class_section "Mã lớp học phần (VD: NHTC1108(126))"
        string room_name "Phòng học (VD: B-201)"
        string date_range_text "VD: Từ: 08/08/2026 đến 21/11/2026"
        string schedule_text "VD: Thứ 7,tiết 3-4,B-201,Giảng đường B"
        string footer_date_text "VD: Hà Nội, ngày 30 tháng 7 năm 2026"
        uuid building_id FK "nullable -> buildings.id"
        uuid lecturer_id FK "-> users.id"
        bytea template_binary "Phôi Excel LMS gốc (~68KB) lưu nhị phân (PostgreSQL TOAST)"
        string template_filename "Tên file gốc (VD: PTTC 66ECQ thứ 7 B301.xls)"
        int total_sessions "Số buổi học (Mặc định 15 cột chuẩn NEU)"
        timestamp created_at
    }

    enrollments {
        uuid id PK
        uuid course_id FK "-> courses.id"
        uuid student_id FK "-> students.id"
        int ordinal_number "TT trong file Excel gốc (1..N)"
        string sheet_name "Tên sheet gốc trong Excel (nếu nhiều sheet)"
        int excel_row_index "Dòng thực tế trong file Excel gốc"
        string note "Cột Ghi chú trên phôi Excel"
    }

    attendance_sessions {
        uuid id PK
        uuid course_id FK "-> courses.id"
        int session_number "1..15 (Tương ứng cột điểm danh 1..15)"
        uuid building_id FK "-> buildings.id (Vòng 1: GPS Geofence)"
        string status "PENDING | OPEN | CLOSED"
        boolean require_audio "Default true (Bật/tắt Vòng 2: Sóng cận siêu âm)"
        int audio_tolerance_hz "Default 50 (Sai số tần số cho phép +-50Hz)"
        timestamp started_at "nullable"
        timestamp ended_at "nullable"
    }

    qr_tokens {
        uuid id PK
        uuid session_id FK "-> attendance_sessions.id"
        string token_hash "SHA-256 của pin_code + secret"
        string pin_code UK "6 digits (100000..999999)"
        int audio_freq_hz "Tần số cận siêu âm phát ra (18100..20500 Hz)"
        timestamp expires_at "created_at + 60s"
        boolean is_revoked "default false"
        timestamp created_at
    }

    attendance_records {
        uuid id PK
        uuid session_id FK "-> attendance_sessions.id"
        uuid student_id FK "-> students.id"
        string status "ATTENDED | ABSENT | PENDING_APPROVAL"
        timestamp marked_at "Thời điểm gửi / xác nhận"
        float latitude "nullable (Tọa độ SV)"
        float longitude "nullable (Tọa độ SV)"
        float gps_accuracy_meters "nullable (Sai số GPS thiết bị)"
        float distance_meters "nullable (Khoảng cách Haversine tới tòa nhà)"
        int detected_freq_hz "nullable (Tần số siêu âm mic SV thu được)"
        boolean audio_verified "Default false (Kết quả xác thực Vòng 2)"
        string method "QR | PIN_ANONYMOUS | MANUAL | EXCEL_IMPORT"
        string device_fingerprint "nullable (Chống 1 máy điểm danh hộ nhiều người)"
        string ip_address "nullable"
        uuid updated_by_lecturer_id FK "nullable -> users.id (Khi duyệt PIN hoặc MANUAL override)"
    }

    audit_logs {
        uuid id PK
        uuid user_id FK "nullable -> users.id"
        string action "OPEN_SESSION | CLOSE_SESSION | RESET_SESSION | APPROVE_PIN | REJECT_PIN | MANUAL_OVERRIDE | ..."
        string details "JSON/Text mô tả chi tiết"
        string ip_address
        string user_agent
        timestamp created_at
    }
```

---

## 2. Chi Tiết 10 Bảng & Ràng Buộc (Constraints & Indexes)

### 2.1. Bảng `users`
- Lưu trữ tài khoản đăng nhập qua Microsoft 365 Entra ID (`@neu.edu.vn` cho Giảng viên, `@st.neu.edu.vn` cho Sinh viên) và Quản trị viên (`ADMIN`).
- **Indexes:**
  - `ix_users_email` (`UNIQUE` trên `email`)
  - `ix_users_microsoft_id` (`UNIQUE` trên `microsoft_id`)

### 2.2. Bảng `subject_folders` (Thư mục Môn học của Giảng viên)
- Phục vụ tổ chức Dashboard của Giảng viên theo cấu trúc cây 2 cấp: **Thư mục Môn học (`SubjectFolder`) $\rightarrow$ Các Lớp học phần (`Course`)**.
- Hỗ trợ tự động gom nhóm (Auto-grouping) khi giảng viên kéo thả nhiều file Excel có cùng dòng tiêu đề `Học phần: <Tên môn>`.
- **Constraints & Indexes:**
  - `uq_lecturer_folder_semester`: `UNIQUE(lecturer_id, folder_name, semester)` — Tên thư mục của cùng một giảng viên trong cùng học kỳ không trùng nhau.
  - `ix_subject_folders_lecturer_id` (`INDEX` trên `lecturer_id`)

### 2.3. Bảng `students` (Hồ sơ Sinh viên khớp 100% phôi Phòng QLĐT NEU)
- Lưu tách biệt đầy đủ 5 trường thông tin cá nhân trên phôi Excel của trường NEU:
  1. `student_code`: Mã số SV 8 chữ số (`11242145`)
  2. `last_name`: Họ và tên đệm (`Bùi Phương`)
  3. `first_name`: Tên (`Anh`) — phục vụ in đậm và sắp xếp chuẩn bảng chữ cái Tiếng Việt trên chế độ **Quick Look Preview**
  4. `date_of_birth`: Ngày Sinh (`08/09/2006`)
  5. `admin_class`: Lớp chuyên ngành/hành chính (`66E.TCNH`)
- **4 trường đối soát bắt buộc cho luồng `PIN_ANONYMOUS`**: Khi sinh viên điểm danh bằng mã PIN không đăng nhập, sinh viên phải nhập đúng cả 4 thông tin (`student_code`, `full_name`, `date_of_birth`, `admin_class`).
- **Indexes:**
  - `ix_students_student_code` (`UNIQUE` trên `student_code`)
  - `ix_students_user_id` (`INDEX` trên `user_id`)

### 2.4. Bảng `buildings`
- Danh mục tọa độ tâm và bán kính phủ sóng của các tòa nhà giảng đường NEU (`A1`, `A2`, `B`, `C`, `D`, `D2`).
- **Indexes:**
  - `ix_buildings_code` (`UNIQUE` trên `code`)

### 2.5. Bảng `courses` & `enrollments`
- `courses`: Lớp học phần nằm trong `subject_folders`, lưu đầy đủ siêu dữ liệu từ phôi Excel (`class_section`, `date_range_text`, `schedule_text`, `footer_date_text`) để dựng giao diện **Quick Look Preview** giống hệt bản in của Phòng Quản lý Đào tạo NEU.
- Hỗ trợ đọc cả file Excel trống mới tinh lẫn **file Excel đã điểm danh sẵn một số buổi trước đó** (`method = 'EXCEL_IMPORT'`).
- **Constraints & Indexes:**
  - `uq_enrollment_course_student`: `UNIQUE(course_id, student_id)`
  - `ix_courses_folder_id` (`INDEX` trên `folder_id`)
  - `ix_enrollments_course_id` (`INDEX` trên `course_id`)

### 2.6. Bảng `attendance_sessions` & `qr_tokens`
- `attendance_sessions`: Đại diện cho từng cột buổi học (`session_number` từ `1..15`).
  - Hỗ trợ thao tác **Reset / Xóa phiên điểm danh (`RESET_SESSION`)**: Xóa toàn bộ `attendance_records` và `qr_tokens` của buổi đó, đưa trạng thái buổi học về lại `PENDING` (cột trống trên phôi Excel).
- `qr_tokens`: Quản lý mã PIN 6 số (`pin_code`) và tần số sóng cận siêu âm (`audio_freq_hz` trong dải $18.100\text{ Hz} - 20.500\text{ Hz}$) có thời hạn 60 giây.
- **Constraints & Indexes:**
  - `uq_session_course_number`: `UNIQUE(course_id, session_number)`
  - `ix_qr_tokens_pin_code` (`UNIQUE` B-Tree Index trên `pin_code`)

### 2.7. Bảng `attendance_records`
- Lưu trạng thái điểm danh 3 giá trị:
  - `ATTENDED`: Đã có mặt (Quét QR có đăng nhập MS365 thành công, hoặc đã được Giảng viên duyệt từ luồng PIN, hoặc Giảng viên tích chọn `MANUAL`, hoặc import sẵn từ file Excel `EXCEL_IMPORT`).
  - `PENDING_APPROVAL`: Sinh viên gửi từ luồng **Mã PIN không đăng nhập (`PIN_ANONYMOUS`)** đã vượt qua kiểm tra 4 thông tin cá nhân + Vòng 1 (GPS) + Vòng 2 (Audio), đang chờ Giảng viên nhìn mặt tại lớp bấm **[Xác nhận Có mặt]**.
  - `ABSENT`: Vắng mặt (Khi đóng phiên mà chưa điểm danh, hoặc bị Giảng viên bấm **[Từ chối]** yêu cầu duyệt PIN, hoặc Giảng viên đánh vắng thủ công).
- **Constraints & Indexes:**
  - `uq_attendance_session_student`: `UNIQUE(session_id, student_id)` — Đảm bảo quy tắc **One-time Attendance per Session**.
