"use client";

import { useState, useEffect, useRef } from "react";
import { fetchApi, uploadExcelFile, getToken, getUser } from "@/lib/api";

interface CourseItem {
  id: string;
  name: string;
  room: string;
  class_section?: string;
  students: number;
  total_sessions?: number;
}

export default function LecturerDashboard() {
  const [courses, setCourses] = useState<CourseItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [user, setUser] = useState<{ email: string; role: string; full_name?: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadCourses = async () => {
    try {
      const data = await fetchApi<CourseItem[]>("/courses/");
      setCourses(data);
    } catch {
      setErrorMessage("Chưa đăng nhập hoặc phiên làm việc đã hết hạn. Vui lòng đăng nhập.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const currentUser = getUser();
    setUser(currentUser);
    const token = getToken();
    if (!token) {
      setErrorMessage("Vui lòng đăng nhập với vai trò Giảng viên để quản lý lớp học.");
      setIsLoading(false);
      return;
    }

    fetchApi<CourseItem[]>("/courses/")
      .then((data) => {
        setCourses(data);
        setIsLoading(false);
      })
      .catch(() => {
        setErrorMessage("Chưa đăng nhập hoặc phiên làm việc đã hết hạn. Vui lòng đăng nhập.");
        setIsLoading(false);
      });
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const res = await uploadExcelFile(file);
      setSuccessMessage(`Đã tải lên lớp "${res.course_name}" với ${res.total_students} sinh viên thành công!`);
      await loadCourses();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Không thể tải lên file Excel.";
      setErrorMessage(msg);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <div className="animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-neu-primary mb-2">Quản lý lớp học phần</h1>
          <p className="text-neu-gray">
            {user ? `Xin chào ${user.full_name || user.email}. Chọn lớp để bắt đầu điểm danh.` : "Chào mừng bạn. Vui lòng đăng nhập để bắt đầu."}
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <input 
            ref={fileInputRef}
            type="file" 
            className="hidden" 
            accept=".xlsx,.xls" 
            onChange={handleFileUpload} 
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="bg-neu-primary hover:bg-neu-secondary disabled:bg-gray-400 text-white px-5 py-2.5 rounded-md font-medium cursor-pointer shadow-sm transition-colors flex items-center gap-2"
          >
            <span>📄</span>
            {isUploading ? "Đang xử lý Excel..." : "Tải lên danh sách Excel (LMS)"}
          </button>
        </div>
      </div>

      {successMessage && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-4 rounded-lg mb-6 flex justify-between items-center">
          <span>✓ {successMessage}</span>
          <button onClick={() => setSuccessMessage(null)} className="text-emerald-600 hover:text-emerald-900 font-bold">✕</button>
        </div>
      )}

      {errorMessage && (
        <div className="bg-amber-50 border border-amber-200 text-amber-800 p-4 rounded-lg mb-6 flex justify-between items-center">
          <div>
            <span>⚠️ {errorMessage}</span>
            {!getToken() && (
              <a href="/login" className="ml-3 underline font-bold text-neu-primary">
                Đăng nhập ngay
              </a>
            )}
          </div>
          <button onClick={() => setErrorMessage(null)} className="text-amber-600 hover:text-amber-900 font-bold">✕</button>
        </div>
      )}

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white border border-neu-border rounded-lg p-6 animate-pulse h-48"></div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {courses.map((course) => (
            <div key={course.id} className="bg-white border border-neu-border rounded-lg p-6 hover:shadow-md transition-shadow flex flex-col h-full">
              <div className="mb-4 flex-1">
                <div className="text-xs uppercase tracking-wider font-semibold text-neu-gray mb-1">
                  {course.class_section || "Lớp học phần"}
                </div>
                <h2 className="text-xl font-bold text-neu-primary mb-2 line-clamp-2" title={course.name}>
                  {course.name}
                </h2>
                <div className="text-sm text-neu-gray mt-3 space-y-1.5">
                  <p>Phòng học: <span className="font-medium text-neu-text">{course.room}</span></p>
                  <p>Sĩ số: <span className="font-medium text-neu-text">{course.students} sinh viên</span></p>
                </div>
              </div>
              
              <div className="pt-4 border-t border-neu-border mt-auto">
                <a 
                  href={`/courses/${course.id}`}
                  className="block w-full text-center bg-neu-primary hover:bg-neu-secondary text-white py-2 rounded font-medium transition-colors shadow-xs"
                >
                  Vào lớp học & Điểm danh
                </a>
              </div>
            </div>
          ))}

          {/* Card Thêm Lớp */}
          <div 
            onClick={() => fileInputRef.current?.click()}
            className="bg-transparent border-2 border-dashed border-neu-border rounded-lg p-6 flex flex-col items-center justify-center text-center min-h-[200px] hover:border-neu-primary hover:bg-blue-50/50 transition-colors cursor-pointer group"
          >
            <div className="text-neu-gray group-hover:text-neu-primary mb-2 text-4xl transition-colors">+</div>
            <h3 className="font-medium text-neu-text group-hover:text-neu-primary transition-colors">Thêm lớp học mới</h3>
            <p className="text-xs text-neu-gray mt-1">Hỗ trợ file .xlsx và .xls từ LMS NEU</p>
          </div>
        </div>
      )}
    </div>
  );
}
