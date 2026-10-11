from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.api import deps
from app.db.session import get_db
from app.models.users import User
from app.models.courses import Course, Enrollment
from app.models.students import Student
from app.schemas.api_models import CourseCreateResponse
from app.services.excel_service import ExcelService

router = APIRouter()

@router.post("/upload", response_model=CourseCreateResponse)
async def upload_course_excel(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_lecturer)
):
    """
    Tải lên file Excel LMS, parse và lưu vào Database.
    """
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ file .xlsx")
        
    contents = await file.read()
    
    # 1. Parse Excel
    try:
        parsed_data = ExcelService.parse_lms_excel(contents)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Lỗi đọc file: {str(e)}")
        
    course_id = uuid.uuid4()
    
    # 2. Lưu phôi template
    template_path = ExcelService.save_template(contents, str(course_id))
    
    # 3. Tạo Course record
    course = Course(
        id=course_id,
        course_code="TBD", # Mở rộng parser nếu cần lấy từ tên file/header
        course_name=parsed_data["course_name"],
        class_section=parsed_data["class_section"],
        room_name=parsed_data["room_name"],
        lecturer_id=current_user.id,
        excel_template_path=template_path,
        total_sessions=parsed_data["total_sessions"]
    )
    db.add(course)
    
    # 4. Lưu Students & Enrollments
    for st_data in parsed_data["students"]:
        # Tồn tại sinh viên chưa?
        result_st = await db.execute(select(Student).where(Student.student_code == st_data["student_code"]))
        student = result_st.scalar_one_or_none()
        if not student:
            student = Student(student_code=st_data["student_code"], full_name=st_data["full_name"])
            db.add(student)
            await db.flush() # Lấy ID tạm
            
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
        room_name=course.room_name or "Unknown",
        total_students=len(parsed_data["students"]),
        total_sessions=course.total_sessions
    )

@router.get("/")
async def get_my_courses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_lecturer)
):
    result = await db.execute(select(Course).where(Course.lecturer_id == current_user.id))
    courses = result.scalars().all()
    return [{"id": str(c.id), "name": c.course_name, "room": c.room_name} for c in courses]

