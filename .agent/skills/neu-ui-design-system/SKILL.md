---
name: neu-ui-design-system
description: >-
  Use this skill when building or modifying any Frontend UI page or component in
  frontend/src/ (Landing page, Dashboard Subject Folders, macOS Quick Look Preview
  Modal, Lecturer Projector screen with PIN approval alert, or Student 2-Ring
  Check-in page).
---

# NEU Attendance UI/UX Design System & Component Specification

Tài liệu chuẩn hóa thiết kế giao diện cho Frontend Next.js (App Router + Tailwind CSS) của **NEU Attendance**.

---

## 1. Hệ Màu & Typography Thương Hiệu NEU
- **Primary Brand Color**: `#003366` / `#1E3A8A` (Xanh dương đậm truyền thống Đại học Kinh tế Quốc dân).
- **Secondary / Accent**: `#0284C7` (Xanh lam sáng), `#10B981` (Xanh lá `ATTENDED`), `#F59E0B` (Vàng hổ phách `PENDING_APPROVAL`), `#EF4444` (Đỏ `ABSENT` / Cảnh báo).
- **Font chữ**: Hệ thống Sans-serif hiện đại (`Inter` / `-apple-system`) cho Dashboard, và kiểu **Times New Roman / Serif trang trọng** bên trong tờ giấy A4 của **Modal Quick Look Preview** để tái hiện 100% phôi in của Phòng Quản lý Đào tạo NEU.

---

## 2. Đặc Tả 5 Màn Hình & Component Cốt Lõi

### 2.1. Trang Chủ (`src/app/page.tsx`) & Đăng Nhập (`src/app/login/page.tsx`)
- Chia làm 2 khối rõ ràng:
  1. **Cổng Điểm Danh Nhanh Cho Sinh Viên (`PUBLIC` / `STUDENT`)**: Ô nhập **Mã PIN 6 chữ số** lớn (`inputMode="numeric"`, `maxLength={6}`) $\rightarrow$ Gọi `GET /api/v1/sessions/qr/{pin_code}` (`UC15`). Nếu hợp lệ chuyển ngay tới `/student/{pin_code}`, nếu hết hạn báo lỗi `EX-04`.
  2. **Cổng Quản Trị Lớp Học Cho Giảng Viên (`LECTURER` / `ADMIN`)**: Nút đăng nhập Microsoft 365 (`@neu.edu.vn`) / Dev Mock Login $\rightarrow$ Điều hướng tới `/dashboard`.

### 2.2. Dashboard Cây Thư Mục Môn Học (`src/app/dashboard/page.tsx` & `FolderCard.tsx`)
- Hiển thị cấu trúc 2 cấp (`BR-04`):
  - **Cấp 1 — Thư mục Môn học (`SubjectFolder`)**: Card thư mục có dải màu `color_tag`, tên môn (VD: *Phân tích tài chính*), học kỳ (`HK1 2026-2027`), số lượng lớp bên trong, nút Đổi tên/Màu và nút Xóa thư mục (hộp thoại hỏi giữ lại lớp hay xóa kèm lớp `EX-17`).
  - **Cấp 2 — Các Lớp học phần (`Course`)**: Nằm bên trong thư mục đang mở (hoặc vùng "Chưa phân loại" nếu `folder_id = null`).
- **Tương tác bàn phím chuẩn macOS (`UC06`)**:
  - Khi giảng viên click chọn (focus) một thẻ Lớp học phần và bấm phím **`Space`** (hoặc bấm nút **"👁️ Xem trước / Quick Look"**), lập tức mở `QuickLookModal.tsx`.

### 2.3. Cửa Sổ Xem Trước Nhanh `QuickLookModal.tsx` (`UC06`, `BR-19`, `BR-20`)
- Giao diện khung cửa sổ nổi kiểu macOS Finder Quick Look (thanh tiêu đề xám mờ, nút Đóng `ESC`/`Space`, nút **Tải file Excel `.xlsx`** và hướng dẫn *"Mẹo: Click đúp vào ô điểm danh 1..15 để đánh dấu Có mặt / Vắng mặt"*).
- Bên trong là **Khung trang giấy chuẩn Phòng Quản lý Đào tạo NEU** (lấy dữ liệu từ `GET /api/v1/courses/{id}/quick-look`):
  - **Phần Đầu trang (Header 2 cột)**:
    - Trái: `TRƯỜNG ĐẠI HỌC KINH TẾ QUỐC DÂN` / `PHÒNG QUẢN LÝ ĐÀO TẠO`
    - Phải: `CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM` / `Độc lập - Tự do - Hạnh phúc`
  - **Tiêu đề chính**: `DANH SÁCH LỚP HỌC PHẦN` + `Học phần: {course_name}` + `Lớp học phần: {class_section}` + `{date_range_text}` + `{schedule_text}`.
  - **Bảng lưới sinh viên chuẩn 100% cột của trường**:
    - Các cột: `TT` | `Lớp` (`admin_class`) | `Mã số SV` (`student_code`) | `Họ và tên đệm` (`last_name`) | **`Tên` (`first_name` - bắt buộc in đậm `font-bold`)** | `Ngày Sinh` (`date_of_birth`) | Nhóm 15 cột `Số lần điểm danh` (`1` $\rightarrow$ `15`) | `Ghi chú` (`note`).
    - Giá trị ô buổi học `1..15`: Hiển thị số **`1`** nếu `ATTENDED`, chữ **`?`** nền vàng nếu `PENDING_APPROVAL`, và **để trống** nếu `ABSENT` hoặc `PENDING`.
    - **Click đúp (Double-click)** vào bất kỳ ô `(student_id, session_number)` nào sẽ gọi `POST /api/v1/attendance/manual` để đảo trạng thái `ATTENDED` (`1`) $\leftrightarrow$ `ABSENT` (trống) tức thì.
  - **Phần Chân trang (Footer)**:
    - Dòng ngày tháng bên phải: `{footer_date_text}` (VD: *Hà Nội, ngày 30 tháng 7 năm 2026*).
    - 3 cột chữ ký cân đối: **`Người lập danh sách`** | **`Cán bộ giảng dạy`** | **`Xác nhận bộ môn`**.

### 2.4. Màn Chiếu Giảng Viên (`src/app/projector/[session_id]/page.tsx`)
- **Cột Trái (Khu vực Tín hiệu 60s)**:
  - Mã QR kích thước lớn (nhúng link `{{base_url}}/student/{pin_code}`) + Mã PIN 6 chữ số cỡ chữ cực lớn + Thanh đếm ngược 60s (tự động gọi `POST /refresh-qr` khi về 0).
  - Bộ điều khiển **Sóng Cận Siêu Âm (Vòng 2)**: Hiển thị tần số đang phát (VD: `18,900 Hz`), trạng thái phát sóng và công tắc bật/tắt nhanh `PATCH /audio-toggle` (`EX-11`).
- **Cột Phải (Khu vực Realtime & Duyệt PIN tại lớp)**:
  - **Khu vực Cảnh báo Vàng nổi (`PENDING_APPROVAL` - `UC10`, `BR-12`)**: Khi có sinh viên điểm danh bằng Mã PIN, hiển thị thẻ vàng nổi bật trên cùng:
    > 👋 **Yêu cầu xác nhận tại lớp (Điểm danh qua PIN):**
    > Sinh viên **{full_name}** (`{student_code}` – Lớp `{admin_class}`) — *Đề nghị SV giơ tay xác nhận!*
    > Nút xanh **[✓ Xác nhận Có mặt]** và nút đỏ **[✕ Từ chối]** (gọi `POST /api/v1/attendance/approve-pin`).
  - Danh sách toàn bộ sinh viên trong lớp cập nhật tức thì qua WebSocket, cho phép Giảng viên bấm nút đổi trạng thái thủ công (`MANUAL`) hoặc bấm nút **Kết thúc điểm danh (`close`)** / **Reset phiên (`reset`)**.

### 2.5. Màn Hình Sinh Viên Điểm Danh (`src/app/student/[pin_code]/page.tsx`)
- **Tuyệt đối không nhúng Camera quét QR trong trang web (`BR-08`)**.
- Hiển thị thông tin buổi học (Tên môn, Buổi số $N$, Phòng học, Tòa nhà).
- **Bước Cấp Quyền Thiết Bị (`EX-07`)**: Kiểm tra quyền Vị trí (GPS) và Microphone (nếu `require_audio = true`). Nếu chưa cấp quyền, hiển thị hướng dẫn trực quan và khóa nút gửi.
- **2 Chế độ (Tabs) Điểm danh rõ ràng**:
  1. **Tab 1 — Điểm danh bằng Tài khoản MS365 (`QR` - Khuyên dùng)**:
     - Nếu SV đã đăng nhập `@st.neu.edu.vn`: Hiển thị tên & Mã SV $\rightarrow$ Bấm **"Xác nhận điểm danh"** (tự động lấy GPS + thu mẫu siêu âm FFT 1.5s và gọi `POST /api/v1/attendance/qr`) $\rightarrow$ Nhận kết quả xanh **`ATTENDED`** ngay lập tức.
     - Nếu chưa đăng nhập: Có nút đăng nhập nhanh `@st.neu.edu.vn`.
  2. **Tab 2 — Điểm danh Dự phòng bằng Mã PIN (`PIN_ANONYMOUS` - Không cần đăng nhập)**:
     - Form bắt buộc nhập đủ **4 trường thông tin khớp phôi Excel (`BR-12`)**:
       1. `Mã số sinh viên` (VD: `11242145`)
       2. `Họ và tên đầy đủ` (VD: `Bùi Phương Anh`)
       3. `Ngày sinh` (Định dạng `DD/MM/YYYY`, VD: `08/09/2006`)
       4. `Lớp chuyên ngành` (VD: `66E.TCNH`)
     - Bấm **"Gửi yêu cầu điểm danh"** (lấy GPS + thu mẫu siêu âm FFT 1.5s và gọi `POST /api/v1/attendance/pin`) $\rightarrow$ Chuyển sang màn hình thông báo màu vàng **`PENDING_APPROVAL`**: *"Đã gửi yêu cầu! Vui lòng chú ý màn chiếu và GIƠ TAY khi Giảng viên gọi tên để được xác nhận Có mặt."*
