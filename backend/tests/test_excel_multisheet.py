import pytest
import os
from io import BytesIO
import openpyxl
from app.services.excel_service import ExcelService

def test_parse_real_neu_lms_xls_multi_sheet():
    real_file_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "docs", "PTTC 66ECQ thứ 7 B301.xls"
    )
    if not os.path.exists(real_file_path):
        pytest.skip("Real sample file not found")

    with open(real_file_path, "rb") as f:
        file_bytes = f.read()

    data = ExcelService.parse_lms_excel(file_bytes, "PTTC 66ECQ thứ 7 B301.xls")

    assert data["course_name"] == "Phân tích tài chính"
    assert "B-201" in data["room_name"]
    # File has 3 sheets with 30 + 30 + 1 = 61 students
    assert len(data["students"]) == 61
    assert data["students"][0]["student_code"] == "11242145"
    assert data["students"][0]["full_name"] == "Bùi Phương Anh"
    assert data["students"][60]["student_code"] == "11242455"
    assert data["students"][60]["full_name"] == "Nguyễn Lê Hà Vy"
    # Verify continuous ordinals 1 to 61
    assert [s["ordinal"] for s in data["students"]] == list(range(1, 62))

def test_parse_xlsx_multi_sheet():
    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = "Page1"
    ws1.append(["Học phần: Kinh tế vi mô"])
    ws1.append(["Phòng: A1-502"])
    ws1.append(["Lớp học phần: KTVM01"])
    ws1.append(["TT", "Mã số SV", "Họ và tên đệm", "Tên"])
    ws1.append([1, "11200001", "Nguyễn Văn", "An"])
    ws1.append([2, "11200002", "Trần Thị", "Bình"])

    ws2 = wb.create_sheet("Page2")
    ws2.append(["TT", "Mã số SV", "Họ và tên đệm", "Tên"])
    ws2.append([3, "11200003", "Lê Hoàng", "Cường"])

    ws3 = wb.create_sheet("Page3")
    ws3.append(["TT", "Mã số SV", "Họ và tên đệm", "Tên"])
    ws3.append([4, "11200004", "Phạm Minh", "Dũng"])

    buf = BytesIO()
    wb.save(buf)

    data = ExcelService.parse_lms_excel(buf.getvalue(), "test.xlsx")
    assert data["course_name"] == "Kinh tế vi mô"
    assert len(data["students"]) == 4
    assert [s["student_code"] for s in data["students"]] == ["11200001", "11200002", "11200003", "11200004"]
