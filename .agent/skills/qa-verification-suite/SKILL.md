---
name: qa-verification-suite
description: >-
  Use this skill when writing or running automated Pytest suites in backend/tests/,
  verifying the 22 Use Cases (UC01-UC22), 20 Business Rules (BR-01-BR-20), and
  18 Exceptions (EX-01-EX-18), or validating the Next.js production build and
  Docker Compose configuration.
---

# QA Verification Suite & 18-Exception Test Matrix

Hướng dẫn chuẩn cho Subagent `qa-test-runner` để kiểm thử toàn diện hệ thống **NEU Attendance**.

---

## 1. Các Lệnh Kiểm Thử Chuẩn

```bash
# 1. Chạy toàn bộ bộ kiểm thử tự động Backend với Pytest
pytest backend/tests/ -v

# 2. Kiểm tra đảm bảo không có thư mục uploads/ nào bị tạo ra trên ổ cứng
test ! -d backend/uploads && test ! -d uploads && echo "PASS: Zero disk uploads"

# 3. Kiểm tra biên dịch TypeScript & Next.js Production Build
cd frontend && npm run build
```

---

## 2. Ma Trận Kiểm Thử Bắt Buộc Cho 18 Ngoại Lệ (`EX-01` $\rightarrow$ `EX-18`) & Nghiệp Vụ Cốt Lõi

Bộ test trong `backend/tests/` phải có các test cases kiểm chứng rõ ràng từng mục sau:

| Mã Kiểm Thử | Nội dung kịch bản kiểm thử | Kỳ vọng Kết quả (Assertion) |
| :--- | :--- | :--- |
| **`EX-01` & `BR-01..03`** | Đăng nhập bằng email ngoài tên miền `@neu.edu.vn` / `@st.neu.edu.vn` (VD: `@gmail.com`) vs đăng nhập `11242145@st.neu.edu.vn`. | `@gmail.com` bị chặn `HTTP 400/401/403`; `11242145@st.neu.edu.vn` tự động gán role `STUDENT` và tách `student_code = "11242145"`. |
| **`EX-02` & `EX-03`** | Upload file không phải `.xls`/`.xlsx` hoặc file Excel trống không có cột `Mã số SV`. | Trả về `HTTP 400` với thông báo lỗi rõ ràng. |
| **`UC04`, `UC22` & `BR-04..06`** | Upload file mẫu thật [`docs/PTTC 66ECQ thứ 7 B301.xls`](file:///Users/macprom2/Documents/NEU%20Agent/Code/Website%20gi%C3%BAp%20gi%E1%BA%A3ng%20vi%C3%AAn%20%C4%91i%E1%BB%83m%20danh%20sinh%20vi%C3%AAn%20nhanh%20ch%C3%B3ng/docs/PTTC%2066ECQ%20th%E1%BB%A9%207%20B301.xls) và file `.xlsx` có đánh dấu sẵn số `1` ở Buổi 1. | Tự động tạo `SubjectFolder`, lưu `template_binary` (`BYTEA`), bóc tách đủ 6 cột (`last_name`, `first_name`, `date_of_birth`, `admin_class`), Buổi 1 tự động `CLOSED` với `method='EXCEL_IMPORT'`, các buổi 2..15 ở trạng thái `PENDING`. |
| **`UC06` & `UC14`** | Gọi `GET /api/v1/courses/{id}/quick-look` và `GET /api/v1/courses/{id}/export`. | Quick Look trả về đủ ma trận 15 buổi và siêu dữ liệu; Export trả về file `.xlsx` điền số `1` cho SV có mặt và giữ nguyên 3 cột chữ ký cuối trang. |
| **`EX-04` & `EX-09`** | Điểm danh với mã PIN sai/hết hạn/đã thu hồi hoặc khi phiên đã `CLOSED`/`PENDING`. | Trả về `HTTP 400/404`. |
| **`EX-05`** | Sinh viên đã `ATTENDED` hoặc đang `PENDING_APPROVAL` bấm gửi điểm danh lần 2. | Trả về `HTTP 400` chặn ghi đè. |
| **`EX-06` & `BR-12`** | Luồng PIN (`POST /api/v1/attendance/pin`): Nhập sai 1 trong **4 thông tin** (`student_code`, `full_name`, `date_of_birth`, `admin_class`). | Trả về `HTTP 400` nếu sai bất kỳ trường nào trong 4 trường; chỉ khi khớp cả 4 trường mới nhận `status = "PENDING_APPROVAL"`. |
| **`EX-08` & `BR-11`** | Gửi tọa độ GPS cách tòa nhà 500m (vượt quá `radius_meters + accuracy`). | Trả về `HTTP 400` kèm khoảng cách lệch (mét). |
| **`EX-10`, `EX-11` & `BR-14..15`** | Khi `require_audio = True`: gửi `detected_freq_hz` lệch quá $\pm 50\text{ Hz}$ $\rightarrow$ Bị chặn. Sau đó Giảng viên gọi `PATCH /audio-toggle` (`require_audio = False`) $\rightarrow$ Điểm danh thành công chỉ với Vòng 1 GPS. | Kiểm chứng cả `EX-10` (`HTTP 400`) và `EX-11` (`HTTP 200` sau khi tắt công tắc siêu âm). |
| **`EX-12` & `BR-16`** | Dùng cùng 1 `device_fingerprint` để điểm danh cho Sinh viên A, sau đó điểm danh tiếp cho Sinh viên B trong cùng phiên. | Sinh viên B bị chặn `HTTP 403` và có bản ghi cảnh báo trong `audit_logs`. |
| **`EX-13`** | Gửi sai mã PIN liên tiếp quá 10 lần từ cùng 1 IP. | Lần thứ 11 trả về `HTTP 429 Too Many Requests`. |
| **`UC10` & `EX-18`** | Giảng viên gọi `POST /api/v1/attendance/approve-pin` với `approved=True` và `approved=False`. | `approved=True` chuyển bản ghi sang `ATTENDED`; `approved=False` chuyển sang `ABSENT` và ghi `audit_logs`. |
| **`UC13` & `BR-07`** | Giảng viên gọi `DELETE /api/v1/sessions/{session_id}/reset` trên buổi học đã điểm danh. | Xóa toàn bộ `attendance_records` của buổi đó, thu hồi `qr_tokens`, trạng thái buổi học quay về `PENDING` (cột trống hoàn toàn trên Quick Look). |
| **`EX-16` & `EX-17`** | Xóa tòa nhà đang được gắn với lớp học phần; Tạo thư mục môn học trùng tên trong cùng học kỳ. | Đều bị chặn hoặc xử lý an toàn theo đúng đặc tả. |
