import re
import urllib.parse
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.db.session import get_db
from app.models.users import User, UserRole
from app.models.students import Student
from app.models.courses import Course, Enrollment
from app.models.attendance import (
    AttendanceSession,
    AttendanceRecord,
    AttendanceStatus,
    SessionStatus,
)
from app.schemas.auth import MockLoginRequest, Token, UserResponse
from app.core.security import create_access_token
from app.api import deps

router = APIRouter()


def validate_and_classify_neu_email(
    email: str | None, requested_role: UserRole | None = None
) -> tuple[str, str, UserRole]:
    """
    BR-01, BR-02 & EX-01:
    - Chỉ chấp nhận @neu.edu.vn và @st.neu.edu.vn.
    - @st.neu.edu.vn -> STUDENT.
    - @neu.edu.vn -> LECTURER (hoặc ADMIN nếu được yêu cầu).
    """
    email_clean = (email or "").strip().lower()
    if "@" not in email_clean:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản không thuộc tên miền @neu.edu.vn hoặc @st.neu.edu.vn. Vui lòng sử dụng tài khoản Microsoft 365 của trường NEU (EX-01).",
        )
    local_part, domain = email_clean.rsplit("@", 1)
    if not local_part or domain not in ("neu.edu.vn", "st.neu.edu.vn"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản không thuộc tên miền @neu.edu.vn hoặc @st.neu.edu.vn. Vui lòng sử dụng tài khoản Microsoft 365 của trường NEU (EX-01).",
        )

    if domain == "st.neu.edu.vn":
        resolved_role = UserRole.STUDENT
    else:
        resolved_role = (
            UserRole.ADMIN if requested_role == UserRole.ADMIN else UserRole.LECTURER
        )

    return email_clean, local_part, resolved_role


def extract_student_code(local_part: str) -> str:
    """
    BR-03: Tự động tách 8 chữ số đầu tiên từ email [Mã_SV]@st.neu.edu.vn làm student_code.
    """
    match = re.match(r"^(\d{8})", local_part)
    if match:
        return match.group(1)
    digits = "".join(ch for ch in local_part if ch.isdigit())
    if len(digits) >= 8:
        return digits[:8]
    return local_part[:8]


def split_vietnamese_name(full_name: str) -> tuple[str, str]:
    cleaned = " ".join((full_name or "").strip().split())
    if not cleaned:
        return "", ""
    parts = cleaned.split(" ")
    if len(parts) == 1:
        return "", parts[0]
    return " ".join(parts[:-1]), parts[-1]


async def _build_user_response(db: AsyncSession, user: User) -> UserResponse:
    student = None
    if user.role == UserRole.STUDENT:
        res_st = await db.execute(select(Student).where(Student.user_id == user.id))
        student = res_st.scalar_one_or_none()
        if not student and "@" in (user.email or ""):
            st_code = extract_student_code(user.email.split("@")[0])
            res_st = await db.execute(
                select(Student).where(Student.student_code == st_code)
            )
            student = res_st.scalar_one_or_none()

    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=bool(user.is_active),
        student_code=student.student_code if student else None,
        last_name=student.last_name if student else None,
        first_name=student.first_name if student else None,
        date_of_birth=student.date_of_birth if student else None,
        admin_class=student.admin_class if student else None,
    )


async def _authenticate_neu_account(
    db: AsyncSession,
    email: str,
    requested_role: UserRole | None = None,
    full_name: str | None = None,
) -> Token:
    email_clean, local_part, resolved_role = validate_and_classify_neu_email(
        email, requested_role
    )

    result = await db.execute(select(User).where(User.email == email_clean))
    user = result.scalar_one_or_none()

    provided_name = (full_name or "").strip()

    if not user:
        user = User(
            email=email_clean,
            full_name=provided_name or local_part,
            role=resolved_role,
            is_active=True,
        )
        db.add(user)
        await db.flush()
    else:
        user.role = resolved_role
        if provided_name:
            user.full_name = provided_name

    # BR-03: Nếu là sinh viên (@st.neu.edu.vn), tự động trích xuất 8 chữ số đầu và liên kết bảng students
    if resolved_role == UserRole.STUDENT:
        student_code = extract_student_code(local_part)
        result_st = await db.execute(
            select(Student).where(Student.student_code == student_code)
        )
        student = result_st.scalar_one_or_none()

        if student:
            student.user_id = user.id
            if not provided_name and student.full_name:
                user.full_name = student.full_name
            elif provided_name and not student.full_name:
                student.full_name = provided_name
            if not student.last_name and not student.first_name and student.full_name:
                student.last_name, student.first_name = split_vietnamese_name(
                    student.full_name
                )
        else:
            effective_name = provided_name or user.full_name or student_code
            last_name, first_name = split_vietnamese_name(effective_name)
            student = Student(
                student_code=student_code,
                last_name=last_name,
                first_name=first_name,
                full_name=effective_name,
                user_id=user.id,
            )
            db.add(student)

    await db.commit()
    await db.refresh(user)

    user_resp = await _build_user_response(db, user)
    access_token = create_access_token(subject=user.id, role=user.role.value)

    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role.value,
        user=user_resp,
    )


@router.post("/mock-login", response_model=Token)
async def mock_login(
    req: MockLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    UC01: Giả lập đăng nhập Microsoft 365 (khi DEV_MOCK_AUTH = True).
    Áp dụng chặt chẽ BR-01, BR-02, BR-03 và EX-01.
    """
    if not settings.DEV_MOCK_AUTH:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chế độ Mock Auth đã bị tắt trên môi trường này.",
        )

    return await _authenticate_neu_account(
        db=db,
        email=req.email,
        requested_role=req.role,
        full_name=req.full_name,
    )


@router.get("/microsoft")
async def login_microsoft():
    """
    UC01: Trả về URL điều hướng đăng nhập Microsoft Entra ID (OAuth2).
    """
    params = {
        "client_id": settings.MICROSOFT_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": settings.MICROSOFT_REDIRECT_URI,
        "response_mode": "query",
        "scope": "openid profile email User.Read",
    }
    authorize_url = (
        f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/oauth2/v2.0/authorize?"
        + urllib.parse.urlencode(params)
    )
    return {
        "auth_url": authorize_url,
        "dev_mock_auth": settings.DEV_MOCK_AUTH,
        "allowed_domains": ["@neu.edu.vn", "@st.neu.edu.vn"],
    }


@router.get("/callback", response_model=Token)
async def microsoft_callback(
    code: str | None = Query(default=None),
    email: str | None = Query(default=None),
    full_name: str | None = Query(default=None),
    role: UserRole | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """
    UC01: Xử lý OAuth2 Callback từ Microsoft Entra ID (hoặc mock callback trong môi trường Dev).
    """
    candidate_email = email
    if not candidate_email and code and "@" in code:
        candidate_email = code

    if not candidate_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Thiếu mã xác thực hoặc thông tin email từ Microsoft Entra ID (EX-01).",
        )

    return await _authenticate_neu_account(
        db=db,
        email=candidate_email,
        requested_role=role,
        full_name=full_name,
    )


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    UC02: Xem hồ sơ người dùng hiện tại.
    """
    return await _build_user_response(db, current_user)


@router.get("/my-attendance")
async def get_my_attendance_history(
    current_user: User = Depends(deps.get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """
    UC18: Sinh viên xem lịch sử chuyên cần cá nhân theo từng môn học đang tham gia.
    """
    res_st = await db.execute(
        select(Student).where(Student.user_id == current_user.id)
    )
    student = res_st.scalar_one_or_none()
    if not student and "@" in (current_user.email or ""):
        st_code = extract_student_code(current_user.email.split("@")[0])
        res_st = await db.execute(
            select(Student).where(Student.student_code == st_code)
        )
        student = res_st.scalar_one_or_none()

    if not student:
        return {
            "student_code": None,
            "full_name": current_user.full_name,
            "admin_class": None,
            "date_of_birth": None,
            "student": None,
            "courses": [],
        }

    res_enroll = await db.execute(
        select(Enrollment, Course)
        .join(Course, Course.id == Enrollment.course_id)
        .where(Enrollment.student_id == student.id)
        .order_by(Course.created_at.desc())
    )
    enrolled_rows = res_enroll.all()

    courses_summary = []
    for enrollment, course in enrolled_rows:
        res_sessions = await db.execute(
            select(AttendanceSession)
            .where(AttendanceSession.course_id == course.id)
            .order_by(AttendanceSession.session_number)
        )
        sessions = res_sessions.scalars().all()

        res_records = await db.execute(
            select(AttendanceRecord)
            .join(
                AttendanceSession,
                AttendanceSession.id == AttendanceRecord.session_id,
            )
            .where(
                AttendanceSession.course_id == course.id,
                AttendanceRecord.student_id == student.id,
            )
        )
        records_by_session = {
            str(r.session_id): r for r in res_records.scalars().all()
        }

        attended_count = 0
        absent_count = 0
        pending_approval_count = 0
        session_details = []

        for s in sessions:
            rec = records_by_session.get(str(s.id))
            att_status = rec.status.value if rec else None
            if rec:
                if rec.status == AttendanceStatus.ATTENDED:
                    attended_count += 1
                elif rec.status == AttendanceStatus.ABSENT:
                    absent_count += 1
                elif rec.status == AttendanceStatus.PENDING_APPROVAL:
                    pending_approval_count += 1
            elif s.status == SessionStatus.CLOSED:
                att_status = AttendanceStatus.ABSENT.value
                absent_count += 1

            session_details.append(
                {
                    "session_id": str(s.id),
                    "session_number": s.session_number,
                    "session_status": s.status.value,
                    "attendance_status": att_status or "NOT_YET",
                    "method": rec.method.value if (rec and rec.method) else None,
                    "marked_at": (
                        rec.marked_at.isoformat() if (rec and rec.marked_at) else None
                    ),
                    "distance_meters": rec.distance_meters if rec else None,
                    "audio_verified": rec.audio_verified if rec else False,
                }
            )

        courses_summary.append(
            {
                "course_id": str(course.id),
                "course_code": course.course_code,
                "course_name": course.course_name,
                "class_section": course.class_section,
                "room_name": course.room_name,
                "ordinal_number": enrollment.ordinal_number,
                "total_sessions": course.total_sessions or 15,
                "attended_count": attended_count,
                "absent_count": absent_count,
                "pending_approval_count": pending_approval_count,
                "sessions": session_details,
            }
        )

    return {
        "student_code": student.student_code,
        "full_name": student.full_name,
        "admin_class": student.admin_class,
        "date_of_birth": student.date_of_birth,
        "student": {
            "id": str(student.id),
            "student_code": student.student_code,
            "full_name": student.full_name,
            "last_name": student.last_name,
            "first_name": student.first_name,
            "date_of_birth": student.date_of_birth,
            "admin_class": student.admin_class,
        },
        "courses": courses_summary,
    }
