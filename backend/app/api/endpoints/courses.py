from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import uuid
import urllib.parse

from app.api import deps
from app.db.session import get_db
from app.models.users import User
from app.models.courses import Course, Enrollment
from app.models.students import Student
from app.models.buildings import Building
from app.models.attendance import AttendanceSession, AttendanceRecord, AttendanceStatus
from app.schemas.api_models import CourseCreateResponse
from app.services.excel_service import ExcelService
from app.api.endpoints.buildings import ensure_buildings_seeded

router = APIRouter()

@router.post("/upload", response_model=CourseCreateResponse)
async def upload_course_excel(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_lecturer)
):
    """
    Tải lên file Excel LMS (.xlsx hoặc .xls), parse và lưu vào Database.
    """
    filename_lower = file.filename.lower() if file.filename else ""
    if not (filename_lower.endswith('.xlsx') or filename_lower.endswith('.xls')):
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ file Excel định dạng .xlsx hoặc .xls")
        
    contents = await file.read()
    
    # 1. Parse Excel
    try:
        parsed_data = ExcelService.parse_lms_excel(contents, filename=file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Lỗi đọc file: {str(e)}")
        
    course_id = uuid.uuid4()
    
    # 2. Lưu phôi template
    template_path = ExcelService.save_template(contents, str(course_id))

    # Auto detect building from room name
    await ensure_buildings_seeded(db)
    building_id = None
    room = parsed_data["room_name"]
    res_b = await db.execute(select(Building))
    for b in res_b.scalars().all():
        if b.code.lower() in room.lower() or b.name.lower() in room.lower():
            building_id = b.id
            break
    
    # 3. Tạo Course record
    course = Course(
        id=course_id,
        course_code=parsed_data.get("class_section", "TBD")[:50],
        course_name=parsed_data["course_name"],
        class_section=parsed_data["class_section"],
        room_name=parsed_data["room_name"],
        building_id=building_id,
        lecturer_id=current_user.id,
        excel_template_path=template_path,
        total_sessions=parsed_data["total_sessions"]
    )
    db.add(course)
    
    # 4. Lưu Students & Enrollments
    for st_data in parsed_data["students"]:
        result_st = await db.execute(select(Student).where(Student.student_code == st_data["student_code"]))
        student = result_st.scalar_one_or_none()
        if not student:
            student = Student(student_code=st_data["student_code"], full_name=st_data["full_name"])
            db.add(student)
            await db.flush()
            
        enrollment = Enrollment(
            course_id=course.id,
            student_id=student.id,
            ordinal_number=st_data["ordinal"]
        )
        db.add(enrollment)
        
    await db.commit()
    
    return CourseCreateResponse(
        id=str(course.id),
        course_name=course.course_name,
        room_name=course.room_name or "Chưa rõ phòng",
        total_students=len(parsed_data["students"]),
        total_sessions=course.total_sessions
    )

@router.get("/")
async def get_my_courses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_lecturer)
):
    result = await db.execute(select(Course).where(Course.lecturer_id == current_user.id).order_by(Course.created_at.desc()))
    courses = result.scalars().all()
    
    response = []
    for c in courses:
        res_cnt = await db.execute(select(func.count(Enrollment.id)).where(Enrollment.course_id == c.id))
        st_count = res_cnt.scalar() or 0
        response.append({
            "id": str(c.id),
            "name": c.course_name,
            "room": c.room_name or "Chưa rõ",
            "class_section": c.class_section or "",
            "students": st_count,
            "total_sessions": c.total_sessions or 10,
            "building_id": str(c.building_id) if c.building_id else None
        })
    return response

@router.get("/{course_id}")
async def get_course_detail(
    course_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_lecturer)
):
    res_c = await db.execute(select(Course).where(Course.id == course_id, Course.lecturer_id == current_user.id))
    course = res_c.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Không tìm thấy môn học")

    # Enrolled students
    query = (
        select(Student, Enrollment.ordinal_number)
        .join(Enrollment, Enrollment.student_id == Student.id)
        .where(Enrollment.course_id == course.id)
        .order_by(Enrollment.ordinal_number)
    )
    res_st = await db.execute(query)
    students_raw = res_st.all()

    # Sessions
    res_s = await db.execute(
        select(AttendanceSession)
        .where(AttendanceSession.course_id == course.id)
        .order_by(AttendanceSession.session_number)
    )
    sessions = res_s.scalars().all()

    # Calculate attendance counts per student
    res_rec = await db.execute(
        select(AttendanceRecord.student_id, AttendanceRecord.status)
        .join(AttendanceSession, AttendanceSession.id == AttendanceRecord.session_id)
        .where(AttendanceSession.course_id == course.id)
    )
    records = res_rec.all()
    att_count_by_student = {}
    for st_id, status in records:
        if status == AttendanceStatus.ATTENDED:
            att_count_by_student[str(st_id)] = att_count_by_student.get(str(st_id), 0) + 1

    student_list = []
    for st, ordinal in students_raw:
        student_list.append({
            "id": str(st.id),
            "ordinal": ordinal,
            "student_code": st.student_code,
            "full_name": st.full_name,
            "attended_count": att_count_by_student.get(str(st.id), 0),
            "total_sessions": len(sessions)
        })

    session_list = []
    for s in sessions:
        res_att = await db.execute(
            select(func.count(AttendanceRecord.id))
            .where(AttendanceRecord.session_id == s.id, AttendanceRecord.status == AttendanceStatus.ATTENDED)
        )
        attended_count = res_att.scalar() or 0
        session_list.append({
            "id": str(s.id),
            "session_number": s.session_number,
            "status": s.status.value,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "attended_count": attended_count,
            "building_id": str(s.building_id) if s.building_id else None
        })

    return {
        "id": str(course.id),
        "name": course.course_name,
        "course_code": course.course_code,
        "class_section": course.class_section,
        "room": course.room_name,
        "building_id": str(course.building_id) if course.building_id else None,
        "total_sessions": course.total_sessions or 10,
        "students": student_list,
        "sessions": session_list
    }

@router.get("/{course_id}/sessions")
async def get_course_sessions(
    course_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_lecturer)
):
    res_s = await db.execute(
        select(AttendanceSession)
        .where(AttendanceSession.course_id == course_id)
        .order_by(AttendanceSession.session_number)
    )
    sessions = res_s.scalars().all()
    
    result = []
    for s in sessions:
        res_att = await db.execute(
            select(func.count(AttendanceRecord.id))
            .where(AttendanceRecord.session_id == s.id, AttendanceRecord.status == AttendanceStatus.ATTENDED)
        )
        result.append({
            "id": str(s.id),
            "session_number": s.session_number,
            "status": s.status.value,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "attended_count": res_att.scalar() or 0
        })
    return result

@router.get("/{course_id}/export")
async def export_attendance_excel(
    course_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_lecturer)
):
    res_c = await db.execute(select(Course).where(Course.id == course_id, Course.lecturer_id == current_user.id))
    course = res_c.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Không tìm thấy môn học")

    # Students
    query_st = (
        select(Student, Enrollment.ordinal_number)
        .join(Enrollment, Enrollment.student_id == Student.id)
        .where(Enrollment.course_id == course.id)
        .order_by(Enrollment.ordinal_number)
    )
    res_st = await db.execute(query_st)
    students = [
        {"id": str(st.id), "ordinal": ord_num, "student_code": st.student_code, "full_name": st.full_name}
        for st, ord_num in res_st.all()
    ]

    # Sessions
    res_s = await db.execute(
        select(AttendanceSession)
        .where(AttendanceSession.course_id == course.id)
        .order_by(AttendanceSession.session_number)
    )
    sessions = [
        {"id": str(s.id), "session_number": s.session_number, "status": s.status.value}
        for s in res_s.scalars().all()
    ]

    # Records map
    res_rec = await db.execute(
        select(AttendanceRecord.student_id, AttendanceRecord.session_id, AttendanceRecord.status)
        .join(AttendanceSession, AttendanceSession.id == AttendanceRecord.session_id)
        .where(AttendanceSession.course_id == course.id)
    )
    att_map = {}
    for st_id, s_id, status in res_rec.all():
        att_map[(str(st_id), str(s_id))] = status.value

    excel_file = ExcelService.generate_attendance_report(
        course_name=course.course_name,
        class_section=course.class_section or "",
        room_name=course.room_name or "",
        students=students,
        sessions=sessions,
        attendance_map=att_map
    )

    filename = f"DiemDanh_{course.course_name.replace(' ', '_')}.xlsx"
    encoded_filename = urllib.parse.quote(filename)

    return Response(
        content=excel_file.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )

