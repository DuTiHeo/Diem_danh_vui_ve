"use client";

import { useState } from "react";

export default function LecturerDashboard() {
  const [courses, setCourses] = useState([
    { id: "1", name: "Phân tích tài chính", room: "B-301", students: 50 },
    { id: "2", name: "Kinh tế vi mô", room: "A2-205", students: 120 }
  ]);
  const [isUploading, setIsUploading] = useState(false);

  return (
    <div className="animate-in fade-in duration-500">
      <div className="flex justify-between items-end mb-8">
        <div>
          <h1 className="text-3xl font-bold text-neu-text mb-2">Quản lý lớp học phần</h1>
          <p className="text-neu-gray">Chào mừng bạn quay lại. Chọn lớp để bắt đầu điểm danh.</p>
        </div>
        
        {/* Nút Upload Clean */}
        <label className="bg-neu-primary hover:bg-neu-secondary text-white px-5 py-2.5 rounded-md font-medium cursor-pointer shadow-sm transition-colors">
          {isUploading ? "Đang xử lý..." : "Tải lên danh sách Excel"}
          <input type="file" className="hidden" accept=".xlsx" onChange={() => setIsUploading(true)} />
        </label>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {courses.map((course) => (
          <div key={course.id} className="bg-white border border-neu-border rounded-lg p-6 hover:shadow-md transition-shadow flex flex-col h-full">
            <div className="mb-4 flex-1">
              <h2 className="text-xl font-bold text-neu-primary mb-1 line-clamp-2" title={course.name}>
                {course.name}
              </h2>
              <div className="text-sm text-neu-gray mt-2 space-y-1">
                <p>Phòng học: <span className="font-medium text-neu-text">{course.room}</span></p>
                <p>Sĩ số: <span className="font-medium text-neu-text">{course.students} SV</span></p>
              </div>
            </div>
            
            <div className="pt-4 border-t border-neu-border mt-auto">
              <a 
                href={`/courses/${course.id}`}
                className="block w-full text-center bg-neu-bg hover:bg-gray-200 text-neu-text py-2 rounded font-medium transition-colors"
              >
                Vào lớp học
              </a>
            </div>
          </div>
        ))}

        {/* Card Thêm Lớp (Empty state) */}
        <div className="bg-transparent border-2 border-dashed border-neu-border rounded-lg p-6 flex flex-col items-center justify-center text-center min-h-[200px] hover:border-neu-primary hover:bg-blue-50 transition-colors cursor-pointer">
          <div className="text-neu-gray mb-2 text-4xl">+</div>
          <h3 className="font-medium text-neu-text">Tạo lớp học mới</h3>
          <p className="text-sm text-neu-gray mt-1">Upload danh sách sinh viên từ LMS</p>
        </div>
      </div>
    </div>
  );
}
