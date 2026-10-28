import pytest
import httpx
import os
import openpyxl
from io import BytesIO

BASE_URL = "http://localhost:8000/api/v1"

def create_dummy_excel():
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.append(["Môn học: Lập trình Web", "Phòng: D2-201", "Lớp học phần: LTW_01"])
    sheet.append([])
    sheet.append(["STT", "Mã SV", "Họ và tên", "Ghi chú"])
    sheet.append([1, "11223344", "Nguyen Van A", ""])
    sheet.append([2, "11223355", "Tran Thi B", ""])
    
    file_bytes = BytesIO()
    wb.save(file_bytes)
    file_bytes.seek(0)
    return file_bytes.read()

def test_full_flow():
    with httpx.Client(base_url=BASE_URL) as client:
        # 1. Login Lecturer
        res = client.post("/auth/mock-login", json={
            "email": "gv_test@neu.edu.vn",
            "full_name": "Giang Vien Test",
            "role": "LECTURER"
        })
        assert res.status_code == 200, res.text
        token_gv = res.json()["access_token"]
        headers_gv = {"Authorization": f"Bearer {token_gv}"}
        
        # 2. Upload Course
        excel_bytes = create_dummy_excel()
        res = client.post("/courses/upload", headers=headers_gv, files={"file": ("danh_sach.xlsx", excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        assert res.status_code == 200, res.text
        course_id = res.json()["id"]
        
        # 3. Open Session
        res = client.post(f"/sessions/{course_id}/open", headers=headers_gv, json={
            "session_number": 1,
            "building_id": None,
            "duration_seconds": 60
        })
        assert res.status_code == 200, res.text
        session_id = res.json()["session_id"]
        pin_code = res.json()["pin_code"]
        
        # 5. Login Student 1
        res = client.post("/auth/mock-login", json={
            "email": "11223344@st.neu.edu.vn",
            "full_name": "Nguyen Van A",
            "role": "STUDENT"
        })
        assert res.status_code == 200, res.text
        token_st = res.json()["access_token"]
        headers_st = {"Authorization": f"Bearer {token_st}"}
        
        # 6. Student Marks Attendance via QR (within campus geofence)
        res = client.post("/attendance/qr", headers=headers_st, json={
            "pin_code": pin_code,
            "latitude": 20.99920,
            "longitude": 105.84230,
            "accuracy": 5.0
        })
        assert res.status_code == 200, res.text
        
        # 7. Student 2 Marks Attendance via PIN
        res = client.post("/attendance/pin", json={
            "pin_code": pin_code,
            "student_code": "11223355",
            "full_name": "Tran Thi B",
            "latitude": 20.99920,
            "longitude": 105.84230,
            "accuracy": 5.0
        })
        assert res.status_code == 200, res.text

        # 8. Check Session Detail
        res = client.get(f"/sessions/{session_id}")
        assert res.status_code == 200, res.text
        session_detail = res.json()
        assert session_detail["attended_count"] == 2
        assert len(session_detail["students"]) == 2

        # 9. Test QR Lookup by PIN
        res = client.get(f"/sessions/qr/{pin_code}")
        assert res.status_code == 200, res.text
        assert res.json()["session_id"] == session_id

        # 10. Close Session
        res = client.post(f"/sessions/{session_id}/close", headers=headers_gv)
        assert res.status_code == 200, res.text

        # 11. Check Course Detail
        res = client.get(f"/courses/{course_id}", headers=headers_gv)
        assert res.status_code == 200, res.text
        course_detail = res.json()
        assert len(course_detail["students"]) == 2
        assert len(course_detail["sessions"]) == 1

        # 12. Test Excel Export
        res = client.get(f"/courses/{course_id}/export", headers=headers_gv)
        assert res.status_code == 200, res.text
        assert "application/vnd.openxmlformats" in res.headers["content-type"]
        assert len(res.content) > 1000

        # 13. Test Real NEU LMS .xls Upload
        if os.path.exists("docs/PTTC 66ECQ thứ 7 B301.xls"):
            with open("docs/PTTC 66ECQ thứ 7 B301.xls", "rb") as f:
                xls_bytes = f.read()
            res = client.post(
                "/courses/upload",
                headers=headers_gv,
                files={"file": ("PTTC 66ECQ thứ 7 B301.xls", xls_bytes, "application/vnd.ms-excel")}
            )
            assert res.status_code == 200, res.text
            neu_course = res.json()
            assert neu_course["total_students"] == 61
            assert "Phân tích tài chính" in neu_course["course_name"]

        print("All tests passed successfully!")

