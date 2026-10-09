# Tài liệu Phân tích Nghiệp vụ và Use Cases
## Hệ thống Điểm danh Sinh viên bằng QR Động & Định vị GPS (NEU)

---

## 1. Actors và Vai trò

### 1.1 Giảng viên (Lecturer)
- **Vai trò:** Quản lý lớp học phần, tổ chức các phiên điểm danh trong giờ học, theo dõi danh sách có mặt theo thời gian thực và trích xuất dữ liệu điểm danh.
- **Quyền hạn:**
  - Đăng nhập hệ thống qua Microsoft 365 (domain cán bộ/giảng viên `@neu.edu.vn`).
  - Quản lý danh sách lớp học phần đang giảng dạy.
  - Upload file Excel danh sách lớp xuất từ LMS của trường (hệ thống tự lưu trữ file gốc làm template).
  - Xem trước (Preview) danh sách sinh viên và cấu trúc các cột buổi học được trích xuất từ file Excel.
  - Mở phiên điểm danh cho buổi học số N (chọn/xác nhận tòa nhà phòng học như A2, B, C, D, D2).
  - Phát mã QR động + PIN (thời hạn 60 giây, phát chung cho cả lớp) lên máy chiếu/màn hình.
  - Tạo mới mã QR trong cùng buổi học nếu sinh viên chưa quét kịp.
  - Theo dõi danh sách điểm danh realtime (ai đã có mặt, ai chưa điểm danh).
  - Can thiệp thủ công (Manual Override): Chuyển đổi trạng thái Có mặt / Vắng cho sinh viên gặp sự cố thiết bị.
  - Kết thúc phiên điểm danh và Export file Excel kết quả (điền trạng thái trực tiếp vào template gốc).

### 1.2 Sinh viên (Student)
- **Vai trò:** Tự xác nhận hiện diện tại lớp học thông qua thiết bị cá nhân (trình duyệt web trên smartphone, máy tính bảng hoặc laptop).
- **Hai phương thức điểm danh:**
  - **Phương thức 1 (Quét QR - Có đăng nhập):**
    - Sinh viên dùng điện thoại quét mã QR chiếu trên màn hình.
    - Trình duyệt mở đường dẫn `{{base_url}}/{pin_code}`.
    - Đăng nhập Microsoft 365 của trường (`@st.neu.edu.vn`) có xác thực qua app Authenticator (2FA).
    - Hệ thống tự bóc tách 8 chữ số đầu làm `student_code`.
    - Trình duyệt cấp quyền GPS, sinh viên bấm nút xác nhận: *"Xác nhận điểm danh Buổi [N] LHP [Tên Lớp]"*.
  - **Phương thức 2 (Nhập PIN - Không cần đăng nhập, dành cho SV hết pin/mượn máy):**
    - Sinh viên vào trang chủ `{{base_url}}`, bấm nút *"Điểm danh bằng mã PIN"*.
    - Nhập mã PIN (6 số thấy trên máy chiếu) $\rightarrow$ Chuyển sang `{{base_url}}/{pin_code}`.
    - Trình duyệt cấp quyền GPS của thiết bị đang dùng.
    - Nhập thông tin theo form: Họ và tên chuẩn (ví dụ: *"Dương Văn Nghĩa"*), Mã sinh viên (ví dụ: *"11232345"*).
    - Bấm nút *"Điểm danh bằng mã PIN"* (**không cần đăng nhập Microsoft**).
    - Hệ thống xác thực Mã SV + Họ tên khớp với danh sách lớp và GPS nằm trong bán kính Tòa nhà học.

### 1.3 Hệ thống (System)
- **Vai trò:** Xử lý logic nghiệp vụ tự động, bảo mật và lưu trữ dữ liệu.
- **Chức năng:**
  - Xác thực Microsoft OAuth 2.0 / Entra ID và phân loại vai trò (Lecturer / Student).
  - Đọc, chuẩn hóa dữ liệu từ file Excel LMS (nhận diện thông tin phòng học, tòa nhà, danh sách sinh viên, danh sách cột buổi học).
  - Quản lý vòng đời mã QR/PIN động 60 giây (Dynamic Broadcast Token).
  - Kiểm tra tính hợp lệ của sinh viên trong lớp học phần (Enrollment check).
  - Tính toán khoảng cách địa lý (Haversine Formula) giữa tọa độ GPS của sinh viên và mốc tọa độ cố định của Tòa nhà phòng học (NEU campus geofencing).
  - Ghi nhận trạng thái điểm danh (AttendanceRecord) và đẩy sự kiện realtime tới màn hình giảng viên.
  - Điền kết quả điểm danh vào file Excel template gốc và trả về file hoàn chỉnh cho giảng viên tải về.

---

## 2. Business Rules (BR)

### BR-001: Đăng nhập Microsoft 365 & Nhận diện vai trò
- Người dùng bắt buộc phải đăng nhập thông qua Microsoft 365 Entra ID của trường Đại học Kinh tế Quốc dân (NEU).
- **Phân loại vai trò:**
  - **Giảng viên (Lecturer):** Tài khoản cán bộ với email thuộc domain `@neu.edu.vn`.
  - **Sinh viên (Student):** Tài khoản sinh viên với email thuộc domain `@st.neu.edu.vn`.
- **Cơ chế nhận diện sinh viên (Identity Mapping):**
  - Email sinh viên có định dạng chuẩn: `[Mã_SV]@st.neu.edu.vn` (ví dụ: `11243929@st.neu.edu.vn`).
  - Hệ thống tự động trích xuất **8 ký tự số đầu tiên** của email làm Mã sinh viên (`student_code`).
  - Mã sinh viên này được dùng làm khóa định danh duy nhất để đối chiếu với cột "Mã sinh viên" trong danh sách lớp import từ LMS.

### BR-002: Quản lý lớp học phần & Trích xuất thông tin phòng học
- Mỗi lớp học phần thuộc quyền sở hữu của một Giảng viên tạo lập.
- Khi tải file Excel LMS lên, hệ thống tự động bóc tách:
  - Mã học phần, Tên môn học, Mã lớp học phần.
  - Lịch học và phòng học từ chuỗi mô tả trong file (ví dụ: *"Thứ 7 tiết 3-4, B-201. Giảng đường B"* -> Tự động xác định phòng học là `B-201` và Tòa nhà mặc định là `Giảng đường B` / mã `B`).
- Giảng viên có quyền kiểm tra và thay đổi lại Tòa nhà học nếu có lịch đổi phòng học thực tế.

### BR-003: Upload danh sách lớp & Lưu trữ file template gốc
- Giảng viên tải lên file Excel trích xuất trực tiếp từ LMS của trường NEU.
- **Cấu trúc file Excel đầu vào:**
  - Phần tiêu đề: Thông tin học phần, giảng viên, phòng học, thời gian.
  - Phần bảng sinh viên: STT, Mã sinh viên, Họ và tên (hoặc Họ đệm, Tên), Lớp sinh viên,...
  - Phần cột điểm danh: Các cột tương ứng với các buổi học (Buổi 1, Buổi 2, ..., Buổi 10/15). Hệ thống tự động đếm và tạo trước các slot buổi học (Session 1..N).
- **Lưu trữ file gốc:** Hệ thống lưu trữ file `.xlsx` gốc lên server. File này vừa dùng làm bằng chứng đối soát, vừa làm **phôi (template)** để khi xuất file chỉ việc điền kết quả vào đúng tọa độ các ô buổi học mà vẫn giữ nguyên 100% định dạng, phông chữ, chữ ký và bố cục của nhà trường.

### BR-004: Vòng đời Buổi điểm danh (Attendance Session Lifecycle)
- Mỗi lớp học phần có $N$ buổi học tương ứng với các cột trong file Excel (ví dụ 10 buổi hoặc 15 buổi).
- Mỗi buổi số $N$ chỉ có **duy nhất 1 phiên điểm danh** (`AttendanceSession`).
- Buổi học có các trạng thái:
  - `PENDING`: Chưa bắt đầu điểm danh.
  - `OPEN`: Đang mở điểm danh (cho phép quét mã QR / nhập PIN).
  - `CLOSED`: Giảng viên đã kết thúc buổi điểm danh (chốt danh sách, không nhận thêm request quét mã).
- Khi kết thúc phiên (`CLOSED`), toàn bộ sinh viên chưa điểm danh thành công được hệ thống chốt trạng thái mặc định là **Vắng mặt (`ABSENT`)**.

### BR-005: Cơ chế QR Code & PIN động (Broadcast Dynamic QR)
- Mã QR và PIN được chiếu công khai trên màn hình/máy chiếu phòng học.
- **Cấu trúc liên kết:** Mã QR chứa đường dẫn trực tiếp: `{{base_url}}/{pin_code}` (ví dụ: `https://diemdanh.neu.edu.vn/786232`).
- **Mã PIN 6 số:** Vừa là đuôi đường dẫn URL, vừa dùng để sinh viên nhập tay trên trang chủ nếu không quét được QR.
- **Tính chất phát sóng (Broadcast):** Trong thời gian hiệu lực, **toàn bộ sinh viên trong lớp đều quét/nhập chung mã này**.
- **Thời hạn hiệu lực:** Mã QR và PIN chỉ có hiệu lực trong **60 giây**.
- **Cơ chế làm mới:** Hết 60 giây, mã cũ tự động hết hạn. Nếu còn sinh viên chưa quét kịp, giảng viên bấm nút "Tạo mã mới" (sinh mã QR/PIN mới trong cùng phiên đó) để sinh viên tiếp tục quét.

### BR-006: Xác thực sinh viên & Chống quét lặp
- **Kiểm tra danh sách lớp:**
  - Với **Phương thức 1 (Quét QR có đăng nhập):** Mã SV trích xuất tự động từ email Microsoft (`[MSSV]@st.neu.edu.vn`) phải nằm trong danh sách `Enrollment`.
  - Với **Phương thức 2 (Nhập PIN không đăng nhập):** Cặp thông tin [Mã SV + Họ tên] do sinh viên tự nhập phải khớp chính xác với hồ sơ sinh viên trong danh sách `Enrollment` của lớp.
- **One-time Attendance per Session:** Mỗi sinh viên chỉ được ghi nhận có mặt **duy nhất 1 lần** trong một buổi học.
- Các yêu cầu quét lại từ cùng một sinh viên đã có mặt sẽ bị hệ thống từ chối và hiển thị thông báo đã điểm danh thành công trước đó.

### BR-007: Kiểm tra định vị GPS theo Tòa nhà NEU (Bắt buộc cho cả 2 phương thức)
- Hệ thống duy trì danh mục tọa độ chuẩn của các Tòa nhà giảng đường chính tại NEU (A2, B, C, D, D2) kèm bán kính phủ sóng an toàn `radius_meters` (60m - 100m).
- **Nguyên tắc an ninh tối quan trọng:** Dù sinh viên dùng **Phương thức 1 (có login)** hay **Phương thức 2 (nhập PIN không login)**, trình duyệt thiết bị **bắt buộc phải bật định vị GPS** và gửi tọa độ (`lat_sv`, `lng_sv`, `accuracy_sv`).
- **Điều kiện hợp lệ về vị trí:**
  $$\text{Khoảng cách}(SV, \text{Tòa nhà lớp học}) \le \text{Bán kính tòa nhà} + \text{accuracy\_sv}$$
- **Mục đích:** Chặn đứng hoàn toàn nguy cơ sinh viên trong lớp chụp/nhắn mã PIN cho bạn bè ở nhà hoặc ở xa trường điểm danh hộ. Sinh viên ở ngoài bán kính tòa nhà sẽ bị từ chối ngay lập tức.

### BR-008: Ghi nhận điểm danh & Trạng thái nhị phân
- Hệ thống áp dụng **mô hình trạng thái nhị phân**:
  - `ATTENDED`: Có mặt.
  - `ABSENT`: Vắng mặt.
- Khi sinh viên xác thực thành công hoặc được giảng viên điều chỉnh: Hệ thống ghi nhận `status = ATTENDED`, lưu thời điểm `marked_at`, tọa độ GPS, độ chính xác và phương thức điểm danh:
  - `QR`: Quét mã QR và đăng nhập Microsoft 365 chính chủ.
  - `PIN_ANONYMOUS`: Nhập mã PIN + Form [Họ tên + Mã SV] không cần đăng nhập (đã qua kiểm tra GPS tại lớp).
  - `MANUAL`: Giảng viên can thiệp thủ công trực tiếp trên màn hình realtime.
- Tất cả sinh viên trong danh sách lớp chưa được ghi nhận `ATTENDED` khi đóng phiên sẽ mang trạng thái `ABSENT`.

### BR-009: Cập nhật Realtime cho Giảng viên
- Giao diện màn hình của giảng viên hiển thị danh sách lớp theo thời gian thực (realtime qua WebSocket hoặc Polling chu kỳ 2s).
- Khi một sinh viên xác thực thành công, dòng của sinh viên đó lập tức chuyển sang màu xanh (Có mặt) kèm thời gian quét chính xác đến từng giây.
- Hiển thị bộ đếm tổng quan: `Tổng số SV`, `Đã có mặt (kèm %)`, `Vắng mặt`.

### BR-010: Quy ước xuất kết quả ra file Excel
- Giảng viên có thể tải file Excel bất cứ lúc nào (sau mỗi buổi hoặc cuối kỳ).
- Dữ liệu được ghi thẳng vào các cột buổi học trên **file phôi gốc (template)**:
  - Sinh viên **Có mặt (`ATTENDED`)**: Ghi ký tự **`1`**.
  - Sinh viên **Vắng mặt (`ABSENT`)**: **Để trống** (không ghi gì).
- File tải về giữ nguyên vẹn 100% định dạng, công thức và bố cục ban đầu của trường NEU.

### BR-011: Quyền can thiệp thủ công của Giảng viên (Manual Attendance Override)
- Giảng viên có quyền tối cao trong việc điều chỉnh trạng thái điểm danh:
  - Có thể bấm trực tiếp để chuyển đổi trạng thái của bất kỳ sinh viên nào từ Vắng $\leftrightarrow$ Có mặt ngay trên bảng realtime.
  - Xử lý kịp thời các tình huống thực tế tại lớp: Sinh viên hết pin, điện thoại hỏng camera, mạng 4G chập chờn, hoặc định vị GPS bị lỗi trong phòng học kín.
- Ghi nhận phương thức `method = MANUAL` kèm mã giảng viên thực hiện override để phục vụ đối soát.

---

## 3. Exceptions (EX)

### EX-001: Lỗi xác thực Microsoft OAuth
- **Nguyên nhân:** Tài khoản không thuộc tổ chức NEU, token hết hạn, người dùng hủy đăng nhập, hoặc sự cố mạng từ Microsoft.
- **Xử lý:** Hiển thị thông báo lỗi rõ ràng, yêu cầu đăng nhập lại bằng đúng tài khoản email nhà trường cấp (`@neu.edu.vn` hoặc `@st.neu.edu.vn`).

### EX-002: File Excel LMS không hợp lệ
- **Nguyên nhân:** File tải lên không đúng định dạng `.xlsx`, bị mã hóa mật khẩu, thiếu cột Mã sinh viên hoặc thông tin phòng học bị sai cấu trúc.
- **Xử lý:** Từ chối xử lý, hiển thị chi tiết dòng/cột bị lỗi và hướng dẫn giảng viên tải đúng file mẫu danh sách lớp từ hệ thống LMS.

### EX-003: Mã QR / PIN đã hết hạn
- **Nguyên nhân:** Sinh viên bấm xác nhận sau khi mã 60 giây đã kết thúc.
- **Xử lý:** Từ chối điểm danh, thông báo "Mã QR/PIN đã hết hạn. Vui lòng nhìn máy chiếu và quét mã mới nhất!".

### EX-004: Điểm danh trùng lặp (Duplicate Attendance)
- **Nguyên nhân:** Sinh viên đã được ghi nhận có mặt trong buổi học này nhưng cố tình quét lại mã lần nữa.
- **Xử lý:** Hiển thị thông báo "Bạn đã điểm danh thành công lúc [HH:mm:ss]. Không cần điểm danh lại." và không ghi đè dữ liệu.

### EX-005: Sinh viên không thuộc danh sách lớp học phần
- **Nguyên nhân:** Mã SV (trích xuất từ email Microsoft) không có tên trong danh sách lớp học phần đang mở điểm danh.
- **Xử lý:** Từ chối truy cập, thông báo "Mã sinh viên [MSSV] không thuộc danh sách lớp học phần này!".

### EX-006: Thiết bị không bật GPS hoặc từ chối cấp quyền vị trí
- **Nguyên nhân:** Trình duyệt di động bị chặn quyền Location, sinh viên chưa bật định vị thiết bị.
- **Xử lý:** Hiển thị popup hướng dẫn bật GPS trên iOS (Safari) / Android (Chrome) và yêu cầu tải lại trang để điểm danh.

### EX-007: Vị trí GPS nằm ngoài phạm vi Tòa nhà lớp học
- **Nguyên nhân:** Tọa độ GPS của sinh viên cách xa tòa nhà lớp học vượt quá bán kính quy định (sinh viên đang ở ký túc xá, quán cafe, ở nhà...).
- **Xử lý:** Từ chối điểm danh, thông báo "Vị trí của bạn không nằm trong khu vực [Tên Tòa nhà] của lớp học!".

### EX-008: Buổi điểm danh đã đóng (Session Closed)
- **Nguyên nhân:** Sinh viên quét mã khi giảng viên đã bấm kết thúc buổi điểm danh.
- **Xử lý:** Từ chối và thông báo "Phiên điểm danh buổi này đã kết thúc bởi Giảng viên. Vui lòng liên hệ Giảng viên để được hỗ trợ!".

### EX-009: Lỗi kết nối máy chủ / Cơ sở dữ liệu
- **Nguyên nhân:** Mất kết nối internet đột ngột, quá tải kết nối đồng thời trong vài giây cao điểm.
- **Xử lý:** Frontend có cơ chế thử lại tự động (retry sau 1-2s), nếu vẫn lỗi thì hiển thị thông báo để sinh viên thử lại hoặc báo giảng viên can thiệp thủ công.

### EX-010: Lỗi trích xuất file Excel
- **Nguyên nhân:** File template gốc bị lỗi cấu trúc hoặc dung lượng bộ nhớ tạm thời bị nghẽn.
- **Xử lý:** Báo lỗi thân thiện, cho phép tải lại sau vài giây hoặc xuất dữ liệu thô dạng CSV dự phòng.

---

## 4. Use Cases (UC)

### UC-01: Giảng viên đăng nhập
- **Actor:** Giảng viên
- **Mô tả:** Giảng viên đăng nhập vào hệ thống bằng tài khoản Microsoft 365 trường NEU.
- **Precondition:** Giảng viên có tài khoản `@neu.edu.vn`.
- **Flow:**
  1. GV truy cập website và chọn "Đăng nhập Cán bộ / Giảng viên".
  2. Hệ thống chuyển hướng sang trang đăng nhập Microsoft Entra ID.
  3. GV nhập thông tin và xác thực thành công.
  4. Hệ thống kiểm tra vai trò (domain `@neu.edu.vn`), tạo phiên làm việc JWT và chuyển hướng vào Dashboard Giảng viên.
- **BR:** BR-001 | **EX:** EX-001

### UC-02: Giảng viên tải lên danh sách lớp từ LMS
- **Actor:** Giảng viên
- **Mô tả:** Giảng viên upload file Excel danh sách lớp lấy từ LMS.
- **Precondition:** GV đã đăng nhập.
- **Flow:**
  1. GV chọn "Tạo lớp học phần mới" hoặc "Import danh sách lớp".
  2. GV chọn file `.xlsx` từ máy tính.
  3. Hệ thống lưu file gốc làm template, parse dữ liệu: Mã lớp, Tên môn, Lịch học, Phòng học/Tòa nhà, Danh sách sinh viên, Số lượng buổi học.
  4. Hệ thống hiển thị bảng Xem trước (Preview) để GV rà soát.
  5. GV bấm "Xác nhận tạo lớp", hệ thống lưu Course, Student, Enrollment và khởi tạo các Session slot vào database.
- **BR:** BR-002, BR-003 | **EX:** EX-002

### UC-03: Giảng viên mở buổi điểm danh & phát QR/PIN
- **Actor:** Giảng viên
- **Mô tả:** GV mở phiên điểm danh cho buổi học số N và chiếu QR động cho cả lớp.
- **Precondition:** Lớp học phần đã được khởi tạo.
- **Flow:**
  1. GV vào lớp học phần, chọn Buổi số N (ví dụ: Buổi 01).
  2. Hệ thống hiển thị Tòa nhà mặc định đã parse từ Excel (ví dụ: Tòa B); GV có thể bấm xác nhận hoặc chọn lại nếu đổi tòa nhà.
  3. GV bấm "Bắt đầu điểm danh".
  4. Hệ thống chuyển trạng thái Buổi sang `OPEN`, sinh mã QR động + PIN (thời hạn 60 giây).
  5. Màn hình chiếu QR code phóng to toàn màn hình kèm đồng hồ đếm ngược 60 giây và mã PIN.
  6. Khi đồng hồ về 0, GV có thể bấm "Tạo mã tiếp theo" nếu còn sinh viên cần quét.
- **BR:** BR-004, BR-005, BR-007 | **EX:** EX-008

### UC-04: Giảng viên theo dõi danh sách điểm danh realtime
- **Actor:** Giảng viên
- **Mô tả:** GV quan sát danh sách sinh viên có mặt cập nhật tức thì trên màn hình.
- **Precondition:** Phiên điểm danh đang ở trạng thái `OPEN`.
- **Flow:**
  1. GV theo dõi bảng danh sách lớp cạnh màn chiếu mã QR.
  2. Khi có SV điểm danh thành công, hệ thống đẩy sự kiện realtime cập nhật trạng thái của SV sang `Có mặt` kèm thời gian xác nhận.
  3. Bộ đếm sĩ số tự động tăng lên tương ứng.
- **BR:** BR-009 | **EX:** EX-009

### UC-05: Giảng viên can thiệp thủ công (Manual Override)
- **Actor:** Giảng viên
- **Mô tả:** GV đổi trạng thái điểm danh thủ công cho sinh viên gặp sự cố thiết bị/GPS.
- **Precondition:** Phiên điểm danh đang mở hoặc trong thời gian buổi học.
- **Flow:**
  1. GV tìm kiếm sinh viên theo tên hoặc Mã SV trên bảng danh sách.
  2. GV click trực tiếp vào nút trạng thái của sinh viên đó để đổi thành "Có mặt" (hoặc ngược lại).
  3. Hệ thống cập nhật bản ghi trong cơ sở dữ liệu với `method = MANUAL`.
  4. Trạng thái và bộ đếm cập nhật tức thì.
- **BR:** BR-011

### UC-06: Giảng viên kết thúc buổi điểm danh (Close Session)
- **Actor:** Giảng viên
- **Mô tả:** GV đóng phiên điểm danh, chốt danh sách vắng mặt.
- **Precondition:** Phiên điểm danh đang `OPEN`.
- **Flow:**
  1. GV bấm nút "Kết thúc điểm danh".
  2. Hệ thống xác nhận và chuyển trạng thái session sang `CLOSED`.
  3. Toàn bộ mã QR/PIN của phiên lập tức mất hiệu lực.
  4. Hệ thống tự động ghi nhận trạng thái `ABSENT` cho toàn bộ sinh viên chưa có mặt.
- **BR:** BR-004, BR-008

### UC-07: Giảng viên xuất file Excel điểm danh
- **Actor:** Giảng viên
- **Mô tả:** GV tải file Excel kết quả điểm danh chuẩn mẫu LMS.
- **Precondition:** Buổi học đã có dữ liệu điểm danh.
- **Flow:**
  1. GV bấm nút "Xuất file Excel".
  2. Hệ thống lấy file template gốc đã lưu, điền ký hiệu `1` vào các cột buổi học tương ứng với sinh viên có mặt, để trống với sinh viên vắng.
  3. Hệ thống xuất file `.xlsx` và gửi về máy GV.
- **BR:** BR-010 | **EX:** EX-010

### UC-08: Sinh viên đăng nhập
- **Actor:** Sinh viên
- **Mô tả:** SV đăng nhập trên trình duyệt điện thoại bằng tài khoản Microsoft trường NEU.
- **Precondition:** SV có tài khoản `@st.neu.edu.vn`.
- **Flow:**
  1. SV truy cập website trên điện thoại, bấm "Đăng nhập Sinh viên".
  2. Xác thực thành công qua Microsoft 365.
  3. Hệ thống bóc tách 8 chữ số đầu tiên của email làm `student_code`.
  4. Hệ thống cấp JWT và chuyển SV vào màn hình điểm danh.
- **BR:** BR-001 | **EX:** EX-001

### UC-09: Sinh viên quét QR điểm danh (Có đăng nhập Microsoft)
- **Actor:** Sinh viên
- **Mô tả:** SV quét mã QR trên máy chiếu và đăng nhập Microsoft để điểm danh.
- **Precondition:** GV đang chiếu mã QR/PIN.
- **Flow:**
  1. SV dùng điện thoại quét mã QR trên màn hình.
  2. Điện thoại mở đường dẫn `{{base_url}}/{pin_code}`.
  3. Hệ thống chuyển hướng yêu cầu SV đăng nhập Microsoft 365 (`@st.neu.edu.vn`) có xác thực qua Authenticator (2FA).
  4. Trình duyệt xin quyền và nhận tọa độ GPS của SV (`lat_sv`, `lng_sv`, `accuracy_sv`).
  5. Màn hình hiển thị nút: *"Xác nhận điểm danh Buổi [N] Lớp [Tên Lớp]"*.
  6. SV bấm nút xác nhận.
  7. Hệ thống validate:
     - Mã PIN còn hạn trong 60 giây (BR-005).
     - Mã SV (bóc từ email) có tên trong danh sách lớp (BR-006).
     - SV chưa điểm danh buổi này (BR-006).
     - Tọa độ SV nằm trong bán kính Tòa nhà học (BR-007).
  8. Nếu hợp lệ: Ghi nhận `status = ATTENDED`, `method = QR`, cập nhật realtime trên máy GV và hiển thị kết quả thành công cho SV.
  9. Nếu không hợp lệ: Báo lỗi tương ứng (EX-003 đến EX-007).
- **BR:** BR-001, BR-005, BR-006, BR-007, BR-008 | **EX:** EX-001, EX-003, EX-004, EX-005, EX-006, EX-007

### UC-10: Sinh viên điểm danh bằng mã PIN (Không cần đăng nhập)
- **Actor:** Sinh viên
- **Mô tả:** SV không tiện dùng điện thoại / hết pin / mượn máy tính vào web nhập mã PIN và thông tin cá nhân.
- **Precondition:** GV đang mở phiên và chiếu mã PIN 6 số.
- **Flow:**
  1. SV truy cập trang chủ `{{base_url}}`, bấm nút *"Điểm danh bằng mã PIN"*.
  2. SV nhập mã PIN (6 số) thấy trên máy chiếu $\rightarrow$ Hệ thống chuyển sang `{{base_url}}/{pin_code}`.
  3. Trình duyệt yêu cầu và nhận quyền truy cập GPS của thiết bị (`lat_sv`, `lng_sv`, `accuracy_sv`).
  4. SV nhập Form thông tin gồm: Họ và tên chuẩn (ví dụ: *"Dương Văn Nghĩa"*) và Mã sinh viên (ví dụ: *"11232345"*).
  5. SV bấm nút *"Điểm danh bằng mã PIN"*.
  6. Hệ thống validate:
     - Mã PIN còn hiệu lực trong 60 giây.
     - Cặp [Mã SV + Họ tên] khớp chính xác với danh sách sinh viên của lớp học phần tương ứng với phiên điểm danh.
     - Sinh viên chưa được ghi nhận có mặt trong buổi này.
     - Tọa độ GPS của thiết bị nằm trong bán kính Tòa nhà phòng học.
  7. Nếu hợp lệ: Ghi nhận `status = ATTENDED`, `method = PIN_ANONYMOUS`, cập nhật realtime trên máy GV và thông báo thành công.
  8. Nếu không hợp lệ: Báo lỗi tương ứng (Sai thông tin, Ngoài bán kính GPS, Hết hạn).
- **BR:** BR-005, BR-006, BR-007, BR-008 | **EX:** EX-003, EX-004, EX-005, EX-006, EX-007

### UC-11: Sinh viên xem lịch sử điểm danh
- **Actor:** Sinh viên
- **Mô tả:** SV xem lại kết quả các buổi học đã tham gia điểm danh (yêu cầu đăng nhập).
- **Precondition:** SV đã đăng nhập Microsoft 365.
- **Flow:**
  1. SV vào mục "Lịch sử điểm danh".
  2. Hệ thống hiển thị các lớp học phần SV đang theo học và trạng thái từng buổi (Có mặt / Vắng).

### UC-12: Hệ thống kiểm tra Geofence Tòa nhà NEU
- **Actor:** Hệ thống
- **Mô tả:** Tính toán khoảng cách địa lý giữa SV và Tòa nhà học (áp dụng cho cả 2 luồng điểm danh).
- **Flow:**
  1. Lấy tọa độ mốc của Tòa nhà lớp học (`lat_b`, `lng_b`, `radius_b`).
  2. Lấy tọa độ của SV (`lat_sv`, `lng_sv`, `accuracy_sv`).
  3. Tính khoảng cách qua công thức Haversine:
     $$d = 2R \cdot \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta \varphi}{2}\right) + \cos(\varphi_1)\cos(\varphi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)}\right)$$
  4. So sánh: Nếu $d \le \text{radius\_b} + \text{accuracy\_sv}$ thì Hợp lệ, ngược lại Không hợp lệ.
- **BR:** BR-007 | **EX:** EX-007

### UC-13: Hệ thống quản lý và hủy hiệu lực QR/PIN
- **Actor:** Hệ thống
- **Mô tả:** Tự động hết hạn token sau 60 giây hoặc khi session kết thúc.
- **Flow:**
  1. Khi sinh token: Lưu `expires_at = now() + 60s`.
  2. Bất kỳ request nào sau `expires_at` đều bị từ chối với lỗi EX-003.
  3. Khi GV kết thúc session: Cập nhật toàn bộ token của session sang `is_revoked = true`.
- **BR:** BR-004, BR-005 | **EX:** EX-003, EX-008

---

## 5. Tóm tắt ma trận Traceability

| ID | Loại | Tên mục |
|----|------|---------|
| **BR-001** | Business Rule | Đăng nhập Microsoft 365 & Nhận diện vai trò |
| **BR-002** | Business Rule | Quản lý lớp học phần & Trích xuất thông tin phòng học |
| **BR-003** | Business Rule | Upload danh sách lớp & Lưu trữ file template gốc |
| **BR-004** | Business Rule | Vòng đời Buổi điểm danh (1 session/buổi) |
| **BR-005** | Business Rule | QR/PIN Generation (Broadcast Dynamic QR 60s qua link URL) |
| **BR-006** | Business Rule | Xác thực sinh viên (One-time attendance) |
| **BR-007** | Business Rule | Kiểm tra GPS theo Tòa nhà NEU (Bắt buộc cho cả 2 phương thức) |
| **BR-008** | Business Rule | Ghi nhận điểm danh & Trạng thái nhị phân (ATTENDED / ABSENT) |
| **BR-009** | Business Rule | Cập nhật Realtime cho Giảng viên |
| **BR-010** | Business Rule | Quy ước xuất kết quả ra file Excel (1 / để trống) |
| **BR-011** | Business Rule | Quyền can thiệp thủ công của Giảng viên (Manual Override) |
| **EX-001** | Exception | Lỗi xác thực Microsoft OAuth |
| **EX-002** | Exception | File Excel LMS không hợp lệ |
| **EX-003** | Exception | Mã QR / PIN đã hết hạn (sau 60s) |
| **EX-004** | Exception | Điểm danh trùng lặp |
| **EX-005** | Exception | Sinh viên không thuộc danh sách lớp |
| **EX-006** | Exception | Thiết bị không bật GPS / từ chối cấp quyền |
| **EX-007** | Exception | Vị trí GPS ngoài phạm vi Tòa nhà |
| **EX-008** | Exception | Buổi điểm danh đã đóng |
| **EX-009** | Exception | Lỗi kết nối máy chủ / Cơ sở dữ liệu |
| **EX-010** | Exception | Lỗi trích xuất file Excel |
| **UC-01** | Use Case | Giảng viên đăng nhập |
| **UC-02** | Use Case | Giảng viên tải lên danh sách lớp từ LMS |
| **UC-03** | Use Case | Giảng viên mở buổi điểm danh & phát QR/PIN |
| **UC-04** | Use Case | Giảng viên theo dõi danh sách điểm danh realtime |
| **UC-05** | Use Case | Giảng viên can thiệp thủ công (Manual Override) |
| **UC-06** | Use Case | Giảng viên kết thúc buổi điểm danh (Close Session) |
| **UC-07** | Use Case | Giảng viên xuất file Excel điểm danh |
| **UC-08** | Use Case | Sinh viên đăng nhập Microsoft |
| **UC-09** | Use Case | Sinh viên quét QR điểm danh (Có login Microsoft) |
| **UC-10** | Use Case | Sinh viên điểm danh bằng mã PIN (Không cần login, kiểm tra GPS) |
| **UC-11** | Use Case | Sinh viên xem lịch sử điểm danh |
| **UC-12** | Use Case | Hệ thống kiểm tra Geofence Tòa nhà NEU |
| **UC-13** | Use Case | Hệ thống quản lý và hủy hiệu lực QR/PIN |

---

## 6. Định hướng Thực thể Dữ liệu (Sẵn sàng xây dựng DB Schema)

Dựa trên nghiệp vụ đã thống nhất, cơ sở dữ liệu sẽ bao gồm các bảng cốt lõi sau:

1. **`users`**: Tài khoản người dùng (id, email, full_name, role `LECTURER`/`STUDENT`, microsoft_id, created_at).
2. **`students`**: Hồ sơ sinh viên (id, student_code [8 ký tự số duy nhất], full_name, user_id nullable).
3. **`buildings`**: Danh mục Tòa nhà NEU (id, code [A2, B, C, D, D2], name, latitude, longitude, radius_meters).
4. **`courses`**: Lớp học phần (id, course_code, course_name, class_section, room_name, building_id, lecturer_id, excel_template_path, total_sessions, created_at).
5. **`enrollments`**: Danh sách sinh viên thuộc lớp (id, course_id, student_id, ordinal_number [STT trong Excel]).
6. **`attendance_sessions`**: Buổi điểm danh (id, course_id, session_number [1..N], building_id, status `PENDING`/`OPEN`/`CLOSED`, started_at, ended_at).
7. **`qr_tokens`**: Token QR/PIN động (id, session_id, token_hash, pin_code, expires_at, is_revoked, created_at).
8. **`attendance_records`**: Kết quả điểm danh (id, session_id, student_id, status `ATTENDED`/`ABSENT`, marked_at, latitude, longitude, distance_meters, method `QR`/`PIN_ANONYMOUS`/`MANUAL`, updated_by_lecturer_id).
9. **`audit_logs`**: Nhật ký bảo mật và thao tác (id, user_id, action, ip_address, user_agent, details, created_at).
