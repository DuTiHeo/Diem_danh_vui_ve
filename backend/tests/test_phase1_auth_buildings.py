import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from app.db.session import AsyncSessionLocal
from app.models.courses import Course
from app.models.attendance import AuditLog


@pytest.mark.asyncio
async def test_ex01_and_br01_domain_validation():
    """
    Kiểm thử EX-01 & BR-01:
    - Chặn mọi email ngoài tên miền @neu.edu.vn và @st.neu.edu.vn (HTTP 403).
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        for invalid_email in [
            "hacker@gmail.com",
            "student@yahoo.com",
            "user@neu.com",
            "@neu.edu.vn",
            "not-an-email",
        ]:
            res = await ac.post(
                "/api/v1/auth/mock-login",
                json={
                    "email": invalid_email,
                    "full_name": "Invalid User",
                    "role": "LECTURER",
                },
            )
            assert res.status_code == 403, f"Expected 403 for {invalid_email}, got {res.status_code}"
            assert "EX-01" in res.json()["detail"]


@pytest.mark.asyncio
async def test_uc01_uc02_br02_br03_roles_and_student_extraction():
    """
    Kiểm thử UC01, UC02, BR-02, BR-03:
    - @st.neu.edu.vn tự động gán STUDENT (kể cả khi truyền role khác) và tách 8 chữ số đầu làm student_code.
    - @neu.edu.vn tự động gán LECTURER (hoặc ADMIN).
    - /auth/me trả về đầy đủ hồ sơ kèm thông tin sinh viên.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Đăng nhập Sinh viên 11242145@st.neu.edu.vn
        res_st = await ac.post(
            "/api/v1/auth/mock-login",
            json={
                "email": "11242145@st.neu.edu.vn",
                "full_name": "Bùi Phương Anh",
                "role": "LECTURER",  # Cố tình truyền LECTURER -> BR-02 vẫn phải ép về STUDENT
            },
        )
        assert res_st.status_code == 200, res_st.text
        data_st = res_st.json()
        assert data_st["role"] == "STUDENT"
        assert data_st["user"]["student_code"] == "11242145"
        assert data_st["user"]["last_name"] == "Bùi Phương"
        assert data_st["user"]["first_name"] == "Anh"

        token_st = data_st["access_token"]
        headers_st = {"Authorization": f"Bearer {token_st}"}

        # 2. Kiểm tra UC02 (/api/v1/auth/me)
        res_me = await ac.get("/api/v1/auth/me", headers=headers_st)
        assert res_me.status_code == 200
        me = res_me.json()
        assert me["email"] == "11242145@st.neu.edu.vn"
        assert me["role"] == "STUDENT"
        assert me["student_code"] == "11242145"

        # 3. Kiểm tra EX-01 khi gọi /auth/me với token rác hoặc không có token
        res_unauth = await ac.get("/api/v1/auth/me")
        assert res_unauth.status_code == 401
        res_bad_token = await ac.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer invalid.jwt.token"}
        )
        assert res_bad_token.status_code == 401

        # 4. Đăng nhập Giảng viên @neu.edu.vn
        res_gv = await ac.post(
            "/api/v1/auth/mock-login",
            json={
                "email": "gv_phase1@neu.edu.vn",
                "full_name": "Nguyễn Trọng Hưng",
            },
        )
        assert res_gv.status_code == 200
        assert res_gv.json()["role"] == "LECTURER"

        # 5. Đăng nhập Quản trị viên @neu.edu.vn
        res_admin = await ac.post(
            "/api/v1/auth/mock-login",
            json={
                "email": "admin_phase1@neu.edu.vn",
                "full_name": "Quản trị viên NEU",
                "role": "ADMIN",
            },
        )
        assert res_admin.status_code == 200
        assert res_admin.json()["role"] == "ADMIN"

        # 6. Kiểm tra UC18 (/api/v1/auth/my-attendance)
        res_hist = await ac.get("/api/v1/auth/my-attendance", headers=headers_st)
        assert res_hist.status_code == 200
        hist = res_hist.json()
        assert hist["student_code"] == "11242145"
        assert isinstance(hist["courses"], list)


@pytest.mark.asyncio
async def test_uc19_ex16_buildings_and_uc21_audit_logs():
    """
    Kiểm thử UC19, EX-16 & UC21:
    - Seed đủ 6 tòa nhà chuẩn NEU (A1, A2, B, C, D, D2).
    - Admin CRUD tòa nhà.
    - EX-16: Chặn xóa cứng tòa nhà đang gắn với lớp học phần (HTTP 400), chỉ cho phép chuyển is_active = false.
    - UC21: Tra cứu AuditLog.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Lấy danh sách 6 tòa nhà mặc định
        res_b = await ac.get("/api/v1/buildings/")
        assert res_b.status_code == 200
        buildings = res_b.json()
        codes = {b["code"] for b in buildings}
        assert {"A1", "A2", "B", "C", "D", "D2"}.issubset(codes)

        # 2. Login Admin
        res_admin = await ac.post(
            "/api/v1/auth/mock-login",
            json={
                "email": "admin_bldg@neu.edu.vn",
                "full_name": "Admin Building",
                "role": "ADMIN",
            },
        )
        admin_token = res_admin.json()["access_token"]
        admin_id = res_admin.json()["user"]["id"]
        headers_admin = {"Authorization": f"Bearer {admin_token}"}

        # 3. Tạo tòa nhà mới để test CRUD & EX-16
        unique_code = f"T{uuid.uuid4().hex[:4].upper()}"
        res_create = await ac.post(
            "/api/v1/buildings/",
            headers=headers_admin,
            json={
                "code": unique_code,
                "name": "Giảng đường Thử nghiệm",
                "latitude": 21.0002,
                "longitude": 105.8432,
                "radius_meters": 75,
            },
        )
        assert res_create.status_code == 201, res_create.text
        bldg_id = res_create.json()["id"]

        # 4. Gắn tòa nhà này vào 1 Course trong DB rồi thử xóa cứng -> Phải bị chặn EX-16 (HTTP 400)
        course_id = uuid.uuid4()
        async with AsyncSessionLocal() as db:
            db.add(
                Course(
                    id=course_id,
                    course_code="TEST101",
                    course_name="Môn kiểm thử EX-16",
                    building_id=uuid.UUID(bldg_id),
                    lecturer_id=uuid.UUID(admin_id),
                    total_sessions=15,
                )
            )
            db.add(
                AuditLog(
                    user_id=uuid.UUID(admin_id),
                    action="TEST_PHASE1_AUDIT",
                    details="Kiểm thử UC21 tra cứu AuditLog",
                    ip_address="127.0.0.1",
                )
            )
            await db.commit()

        res_del_blocked = await ac.delete(
            f"/api/v1/buildings/{bldg_id}", headers=headers_admin
        )
        assert res_del_blocked.status_code == 400
        assert "EX-16" in res_del_blocked.json()["detail"]

        # 5. Chuyển trạng thái is_active = False (Soft deactivate theo EX-16) -> Thành công
        res_deactivate = await ac.put(
            f"/api/v1/buildings/{bldg_id}",
            headers=headers_admin,
            json={"is_active": False, "radius_meters": 90},
        )
        assert res_deactivate.status_code == 200
        assert res_deactivate.json()["is_active"] is False
        assert res_deactivate.json()["radius_meters"] == 90

        # 6. Dọn Course thử nghiệm rồi xóa tòa nhà -> Thành công
        async with AsyncSessionLocal() as db:
            c_obj = await db.get(Course, course_id)
            if c_obj:
                await db.delete(c_obj)
                await db.commit()

        res_del_ok = await ac.delete(
            f"/api/v1/buildings/{bldg_id}", headers=headers_admin
        )
        assert res_del_ok.status_code == 200

        # 7. Kiểm tra UC21 (/api/v1/system/audit-logs)
        res_logs = await ac.get(
            "/api/v1/system/audit-logs?action=TEST_PHASE1_AUDIT",
            headers=headers_admin,
        )
        assert res_logs.status_code == 200
        logs = res_logs.json()
        assert len(logs) >= 1
        assert logs[0]["action"] == "TEST_PHASE1_AUDIT"
