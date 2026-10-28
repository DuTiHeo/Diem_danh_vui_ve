import pytest
import httpx
import os
import openpyxl
from io import BytesIO

BASE_URL = "http://localhost:8000/api/v1"

def create_sample_excel():
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.append(["Môn học: Kinh tế phát triển", "Phòng: A2-301", "Lớp học phần: KTPT_02"])
    sheet.append([])
    sheet.append(["STT", "Mã SV", "Họ và tên", "Ghi chú"])
    sheet.append([1, "11240001", "Đặng Văn C", ""])
    sheet.append([2, "11240002", "Lê Thị D", ""])
    file_bytes = BytesIO()
    wb.save(file_bytes)
    file_bytes.seek(0)
    return file_bytes.read()

def test_attendance_edge_cases():
    with httpx.Client(base_url=BASE_URL) as client:
        # 1. Login Lecturer
        res = client.post("/auth/mock-login", json={
            "email": "gv_edge@neu.edu.vn",
            "full_name": "Giang Vien Edge",
            "role": "LECTURER"
        })
        assert res.status_code == 200
        token_gv = res.json()["access_token"]
        headers_gv = {"Authorization": f"Bearer {token_gv}"}

        # 2. Upload Course
        excel_bytes = create_sample_excel()
        res = client.post(
            "/courses/upload",
            headers=headers_gv,
            files={"file": ("ktpt.xlsx", excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        assert res.status_code == 200
        course_id = res.json()["id"]

        # 3. Open Session
        res = client.post(f"/sessions/{course_id}/open", headers=headers_gv, json={
            "session_number": 1,
            "duration_seconds": 60
        })
        assert res.status_code == 200
        session_id = res.json()["session_id"]
        pin_code = res.json()["pin_code"]

        # 4. Out-of-geofence rejection test
        res = client.post("/attendance/pin", json={
            "pin_code": pin_code,
            "student_code": "11240001",
            "full_name": "Đặng Văn C",
            "latitude": 10.762622, # TP.HCM
            "longitude": 106.660172,
            "accuracy": 5.0
        })
        assert res.status_code == 400
        assert "Vị trí quá xa" in res.json()["detail"]

        # 5. Wrong student code rejection test
        res = client.post("/attendance/pin", json={
            "pin_code": pin_code,
            "student_code": "99999999", # Not enrolled
            "full_name": "Người Ngoài Lớp",
            "latitude": 20.99965,
            "longitude": 105.84315,
            "accuracy": 5.0
        })
        assert res.status_code == 400

        # 6. Valid PIN attendance (at Nhà A2 coordinates)
        res = client.post("/attendance/pin", json={
            "pin_code": pin_code,
            "student_code": "11240001",
            "full_name": "Đặng Văn C",
            "latitude": 20.99965,
            "longitude": 105.84315,
            "accuracy": 5.0
        })
        assert res.status_code == 200

        # 7. Duplicate attendance rejection test
        res = client.post("/attendance/pin", json={
            "pin_code": pin_code,
            "student_code": "11240001",
            "full_name": "Đặng Văn C",
            "latitude": 20.99965,
            "longitude": 105.84315,
            "accuracy": 5.0
        })
        assert res.status_code == 400
        assert "đã điểm danh thành công trước đó" in res.json()["detail"]

        # 8. Manual Override by Lecturer (mark student 2 as ATTENDED)
        res_detail = client.get(f"/sessions/{session_id}")
        student_2 = [s for s in res_detail.json()["students"] if s["student_code"] == "11240002"][0]
        
        res = client.post("/attendance/manual", headers=headers_gv, json={
            "session_id": session_id,
            "student_id": student_2["id"],
            "status": "ATTENDED"
        })
        assert res.status_code == 200

        # 9. Verify updated attendance
        res_detail = client.get(f"/sessions/{session_id}")
        assert res_detail.json()["attended_count"] == 2

        # 10. Refresh QR code
        res_refresh = client.post(f"/sessions/{session_id}/refresh-qr", headers=headers_gv)
        assert res_refresh.status_code == 200
        new_pin = res_refresh.json()["pin_code"]
        assert new_pin != pin_code

        # Old PIN should now fail
        res_old = client.get(f"/sessions/qr/{pin_code}")
        assert res_old.status_code == 404

        # New PIN should succeed
        res_new = client.get(f"/sessions/qr/{new_pin}")
        assert res_new.status_code == 200

        # 11. Buildings list test
        res_b = client.get("/buildings/")
        assert res_b.status_code == 200
        assert len(res_b.json()) >= 5
