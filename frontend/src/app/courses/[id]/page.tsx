"use client";

import { useState, useEffect, use, Suspense } from "react";
import { useRouter } from "next/navigation";
import { fetchApi, API_BASE_URL, getToken } from "@/lib/api";

interface StudentInfo {
  id: string;
  ordinal: number;
  student_code: string;
  full_name: string;
  attended_count: number;
  total_sessions: number;
}

interface SessionInfo {
  id: string;
  session_number: number;
  status: "OPEN" | "CLOSED";
  started_at: string | null;
  attended_count: number;
  building_id: string | null;
}

interface CourseDetail {
  id: string;
  name: string;
  course_code: string;
  class_section: string;
  room: string;
  building_id: string | null;
  total_sessions: number;
  students: StudentInfo[];
  sessions: SessionInfo[];
}

interface BuildingItem {
  id: string;
  code: string;
  name: string;
}

function CourseDetailContent({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const courseId = resolvedParams.id;
  const router = useRouter();

  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [buildings, setBuildings] = useState<BuildingItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Modal State
  const [showModal, setShowModal] = useState(false);
  const [sessionNumber, setSessionNumber] = useState(1);
  const [selectedBuilding, setSelectedBuilding] = useState<string>("");
  const [durationSeconds, setDurationSeconds] = useState(60);
  const [isStartingSession, setIsStartingSession] = useState(false);

  useEffect(() => {
    if (!courseId) return;
    let ignore = false;

    fetchApi<CourseDetail>(`/courses/${courseId}`)
      .then((data) => {
        if (ignore) return;
        setCourse(data);
        setSessionNumber((data.sessions?.length || 0) + 1);
        if (data.building_id) setSelectedBuilding(data.building_id);
        setIsLoading(false);
      })
      .catch((err: unknown) => {
        if (ignore) return;
        const msg = err instanceof Error ? err.message : "Không thể tải thông tin môn học";
        setErrorMessage(msg);
        setIsLoading(false);
      });

    fetchApi<BuildingItem[]>("/buildings/")
      .then((bList) => {
        if (!ignore) setBuildings(bList);
      })
      .catch(() => {});

    return () => {
      ignore = true;
    };
  }, [courseId]);

  const handleStartSession = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsStartingSession(true);
    try {
      const res = await fetchApi<{ session_id: string }>(`/sessions/${courseId}/open`, {
        method: "POST",
        body: JSON.stringify({
          session_number: Number(sessionNumber),
          building_id: selectedBuilding || null,
          duration_seconds: Number(durationSeconds),
        }),
      });

      setShowModal(false);
      router.push(`/projector/${res.session_id}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Lỗi mở phiên";
      alert("Lỗi mở phiên điểm danh: " + msg);
    } finally {
      setIsStartingSession(false);
    }
  };

  const handleExport = () => {
    const token = getToken();
    const url = `${API_BASE_URL}/api/v1/courses/${courseId}/export`;
    
    // Download via fetch with auth header
    fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((res) => {
        if (!res.ok) throw new Error("Xuất báo cáo thất bại");
        return res.blob();
      })
      .then((blob) => {
        const blobUrl = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = blobUrl;
        a.download = `DiemDanh_${course?.name || "Lop"}.xlsx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
      })
      .catch((err: unknown) => {
        const msg = err instanceof Error ? err.message : "Lỗi tải file";
        alert(msg);
      });
  };

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-24 bg-white rounded-lg border border-neu-border p-6"></div>
        <div className="h-64 bg-white rounded-lg border border-neu-border p-6"></div>
      </div>
    );
  }

  if (errorMessage || !course) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 p-6 rounded-lg text-center my-8">
        <h2 className="text-xl font-bold mb-2">Đã có lỗi xảy ra</h2>
        <p className="mb-4">{errorMessage || "Không tìm thấy dữ liệu môn học"}</p>
        <button
          onClick={() => router.push("/")}
          className="bg-neu-primary text-white px-4 py-2 rounded font-medium hover:bg-neu-secondary"
        >
          Quay lại Bảng điều khiển
        </button>
      </div>
    );
  }

  const filteredStudents = course.students.filter(
    (s) =>
      s.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.student_code.includes(searchTerm)
  );

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Header */}
      <div className="bg-white border border-neu-border rounded-xl p-6 shadow-xs flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="text-xs uppercase tracking-wider font-bold text-neu-gray mb-1">
            {course.class_section} • Mã HP: {course.course_code}
          </div>
          <h1 className="text-2xl md:text-3xl font-black text-neu-primary mb-2">
            {course.name}
          </h1>
          <div className="flex flex-wrap items-center gap-4 text-sm text-neu-gray">
            <span>Phòng: <strong className="text-neu-text">{course.room}</strong></span>
            <span>•</span>
            <span>Sĩ số: <strong className="text-neu-text">{course.students.length} sinh viên</strong></span>
            <span>•</span>
            <span>Đã học: <strong className="text-neu-text">{course.sessions.length} / {course.total_sessions} buổi</strong></span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={handleExport}
            className="px-4 py-2.5 bg-white border border-neu-border hover:bg-gray-50 text-neu-text rounded-lg font-medium transition-colors shadow-xs flex items-center gap-2"
          >
            <span>📊</span> Xuất Excel
          </button>
          <button
            onClick={() => setShowModal(true)}
            className="px-5 py-2.5 bg-neu-primary hover:bg-neu-secondary text-white rounded-lg font-bold shadow-sm transition-colors flex items-center gap-2"
          >
            <span>⚡</span> Bắt đầu điểm danh
          </button>
        </div>
      </div>

      {/* Grid: Sessions & Students */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Sessions History */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-white border border-neu-border rounded-xl p-6 shadow-xs">
            <h2 className="text-lg font-bold text-neu-text mb-4 flex items-center justify-between">
              <span>Lịch sử các buổi học</span>
              <span className="text-xs font-semibold text-neu-gray bg-neu-bg px-2.5 py-1 rounded-full">
                {course.sessions.length} buổi
              </span>
            </h2>

            {course.sessions.length === 0 ? (
              <div className="text-center py-8 text-neu-gray text-sm">
                Chưa có buổi học nào được mở. Bấm &quot;Bắt đầu điểm danh&quot; để tạo buổi 1.
              </div>
            ) : (
              <div className="space-y-3">
                {course.sessions.map((sess) => (
                  <div
                    key={sess.id}
                    className={`border rounded-lg p-4 transition-all ${
                      sess.status === "OPEN"
                        ? "border-emerald-300 bg-emerald-50/50 shadow-xs"
                        : "border-neu-border bg-white hover:bg-gray-50"
                    }`}
                  >
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-bold text-neu-text">Buổi {sess.session_number}</span>
                      <span
                        className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${
                          sess.status === "OPEN"
                            ? "bg-emerald-100 text-emerald-800 animate-pulse"
                            : "bg-gray-100 text-neu-gray"
                        }`}
                      >
                        {sess.status === "OPEN" ? "ĐANG MỞ" : "ĐÃ ĐÓNG"}
                      </span>
                    </div>

                    <div className="text-xs text-neu-gray space-y-1 mb-3">
                      <div>Có mặt: <strong className="text-neu-text">{sess.attended_count} / {course.students.length}</strong></div>
                      {sess.started_at && (
                        <div>Thời gian: {new Date(sess.started_at).toLocaleTimeString("vi-VN")} - {new Date(sess.started_at).toLocaleDateString("vi-VN")}</div>
                      )}
                    </div>

                    <div className="pt-2 border-t border-neu-border flex gap-2">
                      <a
                        href={`/projector/${sess.id}`}
                        className={`text-xs text-center flex-1 py-1.5 rounded font-bold transition-colors ${
                          sess.status === "OPEN"
                            ? "bg-emerald-600 hover:bg-emerald-700 text-white"
                            : "bg-neu-bg hover:bg-gray-200 text-neu-text"
                        }`}
                      >
                        {sess.status === "OPEN" ? "🖥 Màn hình máy chiếu" : "Xem chi tiết buổi"}
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Student Roster */}
        <div className="lg:col-span-2">
          <div className="bg-white border border-neu-border rounded-xl shadow-xs overflow-hidden">
            <div className="p-6 border-b border-neu-border flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <div>
                <h2 className="text-lg font-bold text-neu-text">Danh sách sinh viên lớp</h2>
                <p className="text-xs text-neu-gray mt-0.5">Tổng số {course.students.length} sinh viên được nạp từ Excel LMS</p>
              </div>

              <input
                type="text"
                placeholder="Tìm mã SV hoặc tên..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="px-3.5 py-2 border border-neu-border rounded-lg text-sm focus:outline-none focus:border-neu-primary focus:ring-1 focus:ring-neu-primary w-full sm:w-64"
              />
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-neu-bg text-xs font-bold text-neu-gray uppercase tracking-wider border-b border-neu-border">
                    <th className="p-4 text-center w-14">STT</th>
                    <th className="p-4">Mã sinh viên</th>
                    <th className="p-4">Họ và tên</th>
                    <th className="p-4 text-center">Đã có mặt</th>
                    <th className="p-4 text-center">Tỷ lệ</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neu-border text-sm">
                  {filteredStudents.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="p-8 text-center text-neu-gray">
                        Không tìm thấy sinh viên phù hợp
                      </td>
                    </tr>
                  ) : (
                    filteredStudents.map((st) => {
                      const totalSess = course.sessions.length;
                      const pct = totalSess > 0 ? Math.round((st.attended_count / totalSess) * 100) : 100;
                      return (
                        <tr key={st.id} className="hover:bg-gray-50 transition-colors">
                          <td className="p-4 text-center font-medium text-neu-gray">{st.ordinal}</td>
                          <td className="p-4 font-mono font-bold text-neu-primary">{st.student_code}</td>
                          <td className="p-4 font-medium text-neu-text">{st.full_name}</td>
                          <td className="p-4 text-center">
                            <span className="font-bold text-neu-text">{st.attended_count}</span>
                            <span className="text-neu-gray text-xs"> / {totalSess}</span>
                          </td>
                          <td className="p-4 text-center">
                            <span
                              className={`inline-block px-2 py-0.5 rounded text-xs font-bold ${
                                pct >= 80
                                  ? "bg-green-100 text-green-800"
                                  : pct >= 50
                                  ? "bg-amber-100 text-amber-800"
                                  : "bg-red-100 text-red-800"
                              }`}
                            >
                              {pct}%
                            </span>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {/* Modal: Bắt đầu Buổi Điểm Danh */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl border border-neu-border shadow-xl max-w-md w-full p-6 animate-in zoom-in-95 duration-200">
            <div className="flex justify-between items-center mb-4 border-b border-neu-border pb-3">
              <h3 className="text-xl font-bold text-neu-primary">Bắt đầu phiên điểm danh</h3>
              <button
                onClick={() => setShowModal(false)}
                className="text-neu-gray hover:text-neu-text font-bold text-xl"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleStartSession} className="space-y-4">
              <div>
                <label className="block text-sm font-bold text-neu-text mb-1">Buổi số</label>
                <input
                  type="number"
                  min={1}
                  max={course.total_sessions || 20}
                  required
                  value={sessionNumber}
                  onChange={(e) => setSessionNumber(Number(e.target.value))}
                  className="w-full px-4 py-2 border border-neu-border rounded-lg focus:outline-none focus:border-neu-primary"
                />
              </div>

              <div>
                <label className="block text-sm font-bold text-neu-text mb-1">
                  Giảng đường (Kiểm tra vị trí GPS)
                </label>
                <select
                  value={selectedBuilding}
                  onChange={(e) => setSelectedBuilding(e.target.value)}
                  className="w-full px-4 py-2 border border-neu-border rounded-lg focus:outline-none focus:border-neu-primary bg-white"
                >
                  <option value="">-- Không bắt buộc (Tắt Geofence) --</option>
                  {buildings.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.name} ({b.code})
                    </option>
                  ))}
                </select>
                <p className="text-xs text-neu-gray mt-1">
                  Sinh viên phải có mặt trong bán kính khu vực giảng đường để điểm danh thành công.
                </p>
              </div>

              <div>
                <label className="block text-sm font-bold text-neu-text mb-1">Thời gian hiệu lực mỗi mã (Giây)</label>
                <select
                  value={durationSeconds}
                  onChange={(e) => setDurationSeconds(Number(e.target.value))}
                  className="w-full px-4 py-2 border border-neu-border rounded-lg focus:outline-none focus:border-neu-primary bg-white"
                >
                  <option value={30}>30 giây (Rất nhanh)</option>
                  <option value={60}>60 giây (Khuyến nghị chuẩn NEU)</option>
                  <option value={120}>120 giây (2 phút)</option>
                  <option value={300}>300 giây (5 phút)</option>
                </select>
              </div>

              <div className="pt-4 border-t border-neu-border flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 py-2.5 border border-neu-border rounded-lg text-neu-text font-medium hover:bg-gray-50"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={isStartingSession}
                  className="flex-1 py-2.5 bg-neu-primary hover:bg-neu-secondary text-white rounded-lg font-bold shadow-sm"
                >
                  {isStartingSession ? "Đang mở..." : "Khởi động ngay"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default function CourseDetailPage(props: { params: Promise<{ id: string }> }) {
  return (
    <Suspense fallback={<div className="p-8 text-center text-neu-gray">Đang tải thông tin lớp học...</div>}>
      <CourseDetailContent {...props} />
    </Suspense>
  );
}
