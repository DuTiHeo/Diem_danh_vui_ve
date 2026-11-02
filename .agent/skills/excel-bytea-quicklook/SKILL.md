---
name: excel-bytea-quicklook
description: >-
  Use this skill when implementing or modifying ExcelService (excel_service.py),
  Course upload/export endpoints (courses.py, folders.py), PostgreSQL BYTEA TOAST
  storage, auto-importing pre-marked attendance columns (UC22), or Redis QuickLook
  caching.
---

# Excel Multi-Sheet Parser, `BYTEA` TOAST & Quick Look Runbook

Quy trình chuẩn xử lý file Excel danh sách lớp của Phòng Quản lý Đào tạo NEU (`.xls` và `.xlsx` đa sheet), đối chiếu với file thực tế [`docs/PTTC 66ECQ thứ 7 B301.xls`](file:///Users/macprom2/Documents/NEU%20Agent/Code/Website%20gi%C3%BAp%20gi%E1%BA%A3ng%20vi%C3%AAn%20%C4%91i%E1%BB%83m%20danh%20sinh%20vi%C3%AAn%20nhanh%20ch%C3%B3ng/docs/PTTC%2066ECQ%20th%E1%BB%A9%207%20B301.xls).

---

## 1. Cấu Trúc Thực Tế Của Phôi Excel LMS NEU (`BR-05`)

Một file `.xls` hoặc `.xlsx` xuất từ LMS của NEU có thể gồm **1 đến 4+ Sheets** (do hệ thống trường ngắt trang in theo từng Sheet `Page 1`, `Page 2`...). Trên mỗi Sheet có:
1. **Khối Siêu dữ liệu đầu trang (Rows 0..9)**:
   - Dòng Học phần: `Học phần: Phân tích tài chính` $\rightarrow$ `course_name`
   - Dòng Lớp học phần: `Lớp học phần: NHTC1108(126)_01` $\rightarrow$ `class_section` (tách `course_code = NHTC1108`)
   - Dòng Thời gian: `Từ: 08/08/2026 đến 21/11/2026` $\rightarrow$ `date_range_text`
   - Dòng Lịch học & Địa điểm: `Thứ 7,tiết 3-4,B-301,Giảng đường B` $\rightarrow$ `schedule_text` & tách `room_name` (`B-301`) + tự động dò mã Tòa nhà (`B`).
2. **Dòng Tiêu đề Bảng Sinh Viên**:
   - Các cột định danh:
     - `TT` $\rightarrow$ `ordinal_number` (int)
     - `Lớp` $\rightarrow$ `admin_class` (VD: `66E.TCNH`, `TCDN66A`)
     - `Mã số SV` $\rightarrow$ `student_code` (8 chữ số, xử lý sạch đuôi `.0` nếu `xlrd` đọc thành float)
     - `Họ và tên đệm` $\rightarrow$ `last_name` (VD: `Bùi Phương`)
     - `Tên` $\rightarrow$ `first_name` (VD: `Anh`) $\rightarrow$ Ghép `full_name = f"{last_name} {first_name}".strip()`
     - `Ngày Sinh` $\rightarrow$ `date_of_birth` (Chuẩn hóa chuỗi `DD/MM/YYYY`, xử lý cả trường hợp cell kiểu Date/Float trong Excel)
   - Nhóm 15 cột điểm danh: Nằm dưới tiêu đề gộp `Số lần điểm danh`, dòng phụ đánh số từ `1` đến `15`.
   - Cột cuối: `Ghi chú` $\rightarrow$ `note`.
3. **Khối Chân trang ( ở Sheet cuối cùng)**:
   - Ngày tháng năm: VD `Hà Nội, ngày 30 tháng 7 năm 2026` $\rightarrow$ `footer_date_text`.

> [!WARNING]
> **Xử lý Ngoại lệ `EX-02` & `EX-03`**:
> - Nếu file không có đuôi `.xls`/`.xlsx` hoặc lỗi đọc binary $\rightarrow$ Raise `HTTP 400` (`EX-02`).
> - Nếu quét qua tất cả các Sheet mà không tìm thấy dòng header có cột `Mã số SV` và `Họ và tên đệm`/`Tên` (hoặc không có sinh viên nào) $\rightarrow$ Raise `HTTP 400` (`EX-03`).

---

## 2. Tự Động Đồng Bộ Các Buổi Đã Điểm Danh Sẵn (`UC22`, `BR-06`)

Khi Giảng viên tải lên một file Excel đã được điểm danh sẵn ở một vài buổi trước đó:
1. Luôn khởi tạo đủ **15 bản ghi `AttendanceSession`** (`session_number` từ `1` đến `15`) cho `Course`.
2. Với mỗi cột buổi học thứ $K \in [1..15]$:
   - Kiểm tra xem trong cột $K$ của toàn bộ sinh viên trong lớp có ít nhất 1 ô được đánh dấu đi học (`"1"`, `"1.0"`, `"x"`, `"X"`, `"✓"`, `"v"`, `"V"`) hay không:
     - **Nếu CÓ ít nhất 1 SV được đánh dấu ở cột $K$**:
       - Đặt trạng thái buổi học thứ $K$ là `AttendanceSession.status = SessionStatus.CLOSED`.
       - Sinh viên có dấu đi học $\rightarrow$ Tạo `AttendanceRecord(status='ATTENDED', method='EXCEL_IMPORT')`.
       - Sinh viên để trống ở cột $K$ đó $\rightarrow$ Tạo `AttendanceRecord(status='ABSENT', method='EXCEL_IMPORT')`.
     - **Nếu cột $K$ trống hoàn toàn ở mọi sinh viên**:
       - Giữ nguyên `AttendanceSession.status = SessionStatus.PENDING` và chưa tạo `AttendanceRecord`.

---

## 3. Chiến Lược Lưu Trữ `BYTEA` TOAST & Cache Redis QuickLook (`BR-06`, Chương 5 `SYSTEM_DESIGN.md`)

1. **Tuyệt đối không tạo thư mục `uploads/` trên ổ cứng**.
2. Trong `models/courses.py`:
   ```python
   from sqlalchemy.orm import deferred
   from sqlalchemy import Column, LargeBinary

   template_binary = deferred(Column(LargeBinary, nullable=True))
   ```
3. Khi Upload (`POST /api/v1/courses/upload`):
   - Lưu `contents` (bytes của file upload) trực tiếp vào `course.template_binary`.
   - Nếu `folder_id` không được truyền lên, tự động tìm hoặc tạo `SubjectFolder` của giảng viên có `folder_name == parsed_data["course_name"]` (`BR-04`).
4. Khi Xem Trước Nhanh (`GET /api/v1/courses/{course_id}/quick-look`):
   - Kiểm tra khóa Redis `course:{course_id}:quicklook`. Nếu có, trả về ngay lập tức ($< 1\text{ms}$).
   - Nếu chưa có trên Redis: Truy vấn `Course`, `Enrollment` + `Student`, `AttendanceSession` (`1..15`), `AttendanceRecord`, đóng gói thành JSON ma trận đầy đủ và lưu vào `course:{course_id}:quicklook` với `EX 3600` (1 giờ).
   - **Bắt buộc xóa cache (`DEL course:{course_id}:quicklook`)** mỗi khi có thay đổi điểm danh (Check-in QR, Duyệt PIN, Manual Override, Đóng phiên, Reset phiên).
5. Khi Xuất File Excel (`GET /api/v1/courses/{course_id}/export` - `UC14`, `BR-19`, `EX-15`):
   - Tạo file `.xlsx` giữ nguyên 100% bố cục Phòng Quản lý Đào tạo NEU (Quốc hiệu, tiêu đề lớp, 6 cột thông tin SV với cột `Tên` in đậm, 15 cột `1..15` điền số **`1`** cho `ATTENDED` và **để trống** cho `ABSENT`/`PENDING`, cột `Ghi chú`, cùng 3 chữ ký cuối trang: `Người lập danh sách`, `Cán bộ giảng dạy`, `Xác nhận bộ môn`).
