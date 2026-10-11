import openpyxl
from io import BytesIO
import shutil
import os

class ExcelService:
    @staticmethod
    def parse_lms_excel(file_bytes: bytes) -> dict:
        """
        Reads an Excel file from NEU LMS and extracts metadata and students.
        We expect the file to be converted to .xlsx
        """
        wb = openpyxl.load_workbook(filename=BytesIO(file_bytes), data_only=True)
        sheet = wb.active
        
        # NOTE: Exact cell references (A1, B5, etc.) depend on the NEU template.
        # Here we do a basic search or heuristic. 
        # For a robust implementation, we scan rows for keywords like "Môn học", "Phòng", "Mã SV".
        
        course_name = "Unknown Course"
        room_name = "Unknown"
        class_section = "Unknown"
        
        students = []
        header_row_idx = None
        
        for row_idx, row in enumerate(sheet.iter_rows(values_only=True), start=1):
            row_str = [str(cell).strip() if cell else "" for cell in row]
            
            # Look for Metadata
            for cell_val in row_str:
                if "Môn học:" in cell_val or "Học phần:" in cell_val:
                    course_name = cell_val.split(":")[-1].strip()
                if "Phòng:" in cell_val or "Địa điểm:" in cell_val:
                    room_name = cell_val.split(":")[-1].strip()
                if "Lớp học phần:" in cell_val:
                    class_section = cell_val.split(":")[-1].strip()
            
            # Find the header row for the student table
            if "Mã SV" in row_str or "Mã sinh viên" in row_str:
                header_row_idx = row_idx
                # Find column indices
                try:
                    ma_sv_col = row_str.index("Mã SV") if "Mã SV" in row_str else row_str.index("Mã sinh viên")
                    ho_ten_col = row_str.index("Họ và tên") if "Họ và tên" in row_str else (row_str.index("Họ đệm") if "Họ đệm" in row_str else -1)
                except ValueError:
                    continue
                continue
                
            # If we passed the header, read students
            if header_row_idx and row_idx > header_row_idx:
                # Stop if we hit an empty row or summary row
                if not row_str[0] and not row_str[1]:
                    continue
                
                try:
                    student_code = str(row[ma_sv_col]).strip()
                    if student_code and student_code.isdigit():
                        # If name is split in 2 columns (Họ đệm, Tên)
                        if "Họ đệm" in sheet[header_row_idx][ho_ten_col].value:
                            full_name = f"{row[ho_ten_col]} {row[ho_ten_col+1]}".strip()
                        else:
                            full_name = str(row[ho_ten_col]).strip()
                            
                        students.append({
                            "ordinal": len(students) + 1,
                            "student_code": student_code,
                            "full_name": full_name
                        })
                except Exception:
                    pass

        return {
            "course_name": course_name,
            "room_name": room_name,
            "class_section": class_section,
            "students": students,
            "total_sessions": 10 # Default fallback, can be calculated based on columns
        }

    @staticmethod
    def save_template(file_bytes: bytes, course_id: str, upload_dir: str = "uploads") -> str:
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, f"{course_id}_template.xlsx")
        with open(file_path, "wb") as f:
            f.write(file_bytes)
        return file_path

    @staticmethod
    def generate_attendance_report(template_path: str, records: list[dict], total_sessions: int) -> BytesIO:
        """
        Reads the template and writes '1' for attended students.
        records: list of dicts: [{"student_code": "...", "session_number": 1, "status": "ATTENDED"}]
        """
        wb = openpyxl.load_workbook(filename=template_path)
        sheet = wb.active
        
        # Strategy: find the row for each student by matching student_code
        # Find the column for each session_number.
        # This requires knowing where the session columns start.
        # Usually it's after the "Ghi chú" or right after Name.
        
        # For a production ready parser, you'd map these exact coordinates during parse_lms_excel 
        # and store them. Here we use a generic approach.
        
        # ... Implementation of writing to openpyxl ...
        
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output

