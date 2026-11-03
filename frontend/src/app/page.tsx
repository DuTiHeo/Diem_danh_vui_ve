"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  checkPinSession,
  fetchMyAttendance,
  fetchApi,
  getToken,
  getUser,
  setToken,
  setUser,
  removeAuth,
  UserProfile,
  MyAttendanceResponse,
} from "@/lib/api";

export default function HomePage() {
  const router = useRouter();
  const [pinCode, setPinCode] = useState("");
  const [isCheckingPin, setIsCheckingPin] = useState(false);
  const [pinError, setPinError] = useState<string | null>(null);

  const [user, setUserState] = useState<UserProfile | null>(null);
  const [myAttendance, setMyAttendance] = useState<MyAttendanceResponse | null>(null);
  const [isLoadingAttendance, setIsLoadingAttendance] = useState(false);
  const [isQuickLoggingIn, setIsQuickLoggingIn] = useState(false);

  useEffect(() => {
    const currentUser = getUser();
    const token = getToken();
    setUserState(currentUser);

    if (token && currentUser?.role === "STUDENT") {
      setIsLoadingAttendance(true);
      fetchMyAttendance()
        .then((data) => setMyAttendance(data))
        .catch(() => {})
        .finally(() => setIsLoadingAttendance(false));
    }
  }, []);

  const handlePinSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPinError(null);

    const cleaned = pinCode.replace(/[^0-9]/g, "");
    if (cleaned.length !== 6) {
      setPinError("Vui lòng nhập đủ 6 chữ số của Mã PIN.");
      return;
    }

    setIsCheckingPin(true);
    try {
      await checkPinSession(cleaned);
      router.push(`/student/${cleaned}`);
    } catch {
      setPinError(
        "Mã PIN không khả dụng hoặc đã hết hạn 60s. Vui lòng nhìn lên màn chiếu để lấy mã mới nhất!"
      );
    } finally {
      setIsCheckingPin(false);
    }
  };

  const handleQuickMockLogin = async (
    email: string,
    role: "LECTURER" | "STUDENT",
    fullName: string
  ) => {
    setIsQuickLoggingIn(true);
    try {
      const res = await fetchApi<{
        access_token: string;
        role: string;
        user?: UserProfile;
      }>("/auth/mock-login", {
        method: "POST",
        body: JSON.stringify({
          email,
          role,
          full_name: fullName,
        }),
      });

      setToken(res.access_token);
      const profile: UserProfile = res.user || {
        email,
        role: res.role || role,
        full_name: fullName,
      };
      setUser(profile);
      setUserState(profile);

      if (profile.role === "LECTURER" || profile.role === "ADMIN") {
        router.push("/dashboard");
      } else {
        setIsLoadingAttendance(true);
        fetchMyAttendance()
          .then((data) => setMyAttendance(data))
          .catch(() => {})
          .finally(() => setIsLoadingAttendance(false));
      }
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Đăng nhập nhanh thất bại");
    } finally {
      setIsQuickLoggingIn(false);
    }
  };

  const handleLogout = () => {
    removeAuth();
    setUserState(null);
    setMyAttendance(null);
  };

  return (
    <div className="space-y-8 py-2 animate-in fade-in duration-300">
      {/* Banner Thương hiệu NEU */}
      <div className="bg-gradient-to-r from-[#003366] via-[#0b4b8a] to-[#0284c7] text-white rounded-2xl p-6 sm:p-8 shadow-md">
        <div className="max-w-3xl">
          <div className="inline-flex items-center gap-2 bg-white/15 backdrop-blur-xs px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider mb-3">
            <span>🎓</span> Trường Đại học Kinh tế Quốc dân (NEU)
          </div>
          <h1 className="text-2xl sm:text-4xl font-black text-white leading-tight mb-2">
            Hệ Thống Điểm Danh Thông Minh 2 Vòng
          </h1>
          <p className="text-sky-100 text-sm sm:text-base leading-relaxed">
            Xác thực hiện diện vật lý tại giảng đường bằng Mã QR/PIN động 60 giây kết hợp Định vị
            GPS nội khu NEU (Vòng 1) và Sóng âm thanh cận siêu âm 18.1–20.5 kHz (Vòng 2).
          </p>
        </div>
      </div>

      {/* 2 Khối Cổng Chức Năng Chính */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
        {/* KHỐI 1: CỔNG ĐIỂM DANH NHANH CHO SINH VIÊN (PUBLIC / STUDENT) */}
        <div className="bg-white border border-neu-border rounded-2xl p-6 sm:p-8 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between gap-2 mb-4">
              <span className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full bg-sky-50 text-neu-secondary border border-sky-200">
                📱 Cổng Sinh Viên (Public &amp; @st.neu.edu.vn)
              </span>
              {user?.role === "STUDENT" && (
                <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                  ✓ {user.full_name || user.email}
                </span>
              )}
            </div>

            <h2 className="text-2xl font-bold text-neu-primary mb-2">
              Điểm danh nhanh bằng Mã PIN 6 số
            </h2>
            <p className="text-sm text-neu-gray mb-6">
              Sử dụng ứng dụng <strong>Camera / Zalo</strong> trên điện thoại để quét mã QR trên màn
              chiếu, hoặc nhập trực tiếp <strong>Mã PIN 6 chữ số</strong> đang hiển thị trên bảng:
            </p>

            <form onSubmit={handlePinSubmit} className="space-y-4">
              <div>
                <label
                  htmlFor="home-pin-input"
                  className="block text-xs font-bold uppercase tracking-wider text-neu-text mb-2"
                >
                  Mã PIN Phiên Học (Đổi mới mỗi 60 giây)
                </label>
                <input
                  id="home-pin-input"
                  type="text"
                  inputMode="numeric"
                  maxLength={6}
                  value={pinCode}
                  onChange={(e) => {
                    setPinCode(e.target.value.replace(/[^0-9]/g, ""));
                    if (pinError) setPinError(null);
                  }}
                  placeholder="••••••"
                  className="w-full text-center text-4xl sm:text-5xl font-black tracking-[0.25em] px-4 py-4 border-2 border-neu-border rounded-xl focus:outline-none focus:border-neu-primary focus:ring-2 focus:ring-neu-primary/20 transition-all text-neu-primary font-mono bg-slate-50"
                />
              </div>

              {pinError && (
                <div
                  role="alert"
                  className="bg-red-50 border border-red-200 text-red-700 p-3.5 rounded-xl text-sm font-medium flex items-start gap-2.5 animate-in fade-in"
                >
                  <span className="text-lg leading-none">⚠️</span>
                  <span>{pinError}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={pinCode.length !== 6 || isCheckingPin}
                className="w-full bg-neu-primary hover:bg-neu-secondary disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-bold py-4 rounded-xl transition-all text-base shadow-sm cursor-pointer"
              >
                {isCheckingPin
                  ? "Đang kiểm tra mã PIN..."
                  : "Tiếp tục điểm danh →"}
              </button>
            </form>
          </div>

          <div className="mt-6 pt-5 border-t border-neu-border flex flex-wrap items-center justify-between gap-3 text-xs text-neu-gray">
            <span>
              Mẹo: Đăng nhập MS365 (<code>@st.neu.edu.vn</code>) để điểm danh 1 chạm không cần chờ duyệt.
            </span>
            {user?.role === "STUDENT" ? (
              <button
                type="button"
                onClick={handleLogout}
                className="text-red-600 font-bold hover:underline cursor-pointer"
              >
                Đăng xuất
              </button>
            ) : (
              <Link
                href="/login"
                className="text-neu-primary font-bold hover:underline"
              >
                Đăng nhập Sinh viên →
              </Link>
            )}
          </div>
        </div>

        {/* KHỐI 2: CỔNG QUẢN TRỊ LỚP HỌC CHO GIẢNG VIÊN (LECTURER / ADMIN) */}
        <div className="bg-white border border-neu-border rounded-2xl p-6 sm:p-8 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between gap-2 mb-4">
              <span className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full bg-blue-50 text-neu-primary border border-blue-200">
                👨‍🏫 Cổng Giảng Viên &amp; Quản Trị (@neu.edu.vn)
              </span>
              {(user?.role === "LECTURER" || user?.role === "ADMIN") && (
                <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                  ✓ Đã xác thực
                </span>
              )}
            </div>

            <h2 className="text-2xl font-bold text-neu-primary mb-2">
              Quản lý lớp học phần &amp; Trình chiếu QR
            </h2>
            <p className="text-sm text-neu-gray mb-6">
              Tải lên danh sách lớp từ LMS NEU (<code>.xls</code> / <code>.xlsx</code>), xem trước
              phôi điểm danh chuẩn Phòng QLĐT (Quick Look) và mở màn chiếu điểm danh dưới 60 giây.
            </p>

            {user && (user.role === "LECTURER" || user.role === "ADMIN") ? (
              <div className="space-y-4">
                <div className="bg-blue-50/70 border border-blue-200 rounded-xl p-4">
                  <div className="text-xs font-bold uppercase text-neu-gray mb-1">
                    Tài khoản đang đăng nhập
                  </div>
                  <div className="text-lg font-bold text-neu-primary">
                    {user.full_name || "Giảng viên NEU"}
                  </div>
                  <div className="text-xs text-neu-gray mt-0.5">
                    {user.email} • Vai trò: <strong>{user.role}</strong>
                  </div>
                </div>

                <Link
                  href="/dashboard"
                  className="block w-full text-center bg-neu-primary hover:bg-neu-secondary text-white font-bold py-4 rounded-xl shadow-sm transition-colors text-base"
                >
                  📂 Vào Bảng Điều Khiển Lớp Học (/dashboard)
                </Link>

                <button
                  type="button"
                  onClick={handleLogout}
                  className="w-full py-2.5 border border-neu-border hover:bg-slate-50 text-neu-gray hover:text-neu-text rounded-xl text-sm font-medium cursor-pointer"
                >
                  Đăng xuất tài khoản
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <Link
                  href="/login"
                  className="w-full flex items-center justify-center gap-3 bg-neu-primary hover:bg-neu-secondary text-white font-bold py-4 px-5 rounded-xl transition-colors shadow-sm text-base"
                >
                  <svg className="w-5 h-5 shrink-0" viewBox="0 0 21 21">
                    <path fill="#f25022" d="M1 1h9v9H1z" />
                    <path fill="#7fba00" d="M11 1h9v9h-9z" />
                    <path fill="#00a4ef" d="M1 11h9v9H1z" />
                    <path fill="#ffb900" d="M11 11h9v9h-9z" />
                  </svg>
                  <span>Đăng nhập Microsoft 365 (@neu.edu.vn)</span>
                </Link>

                <div className="pt-3 border-t border-neu-border">
                  <div className="text-xs font-bold uppercase tracking-wider text-neu-gray mb-2.5">
                    Chế độ thử nghiệm nhanh (1-Click Dev Mock Auth)
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                    <button
                      type="button"
                      disabled={isQuickLoggingIn}
                      onClick={() =>
                        handleQuickMockLogin(
                          "gv_test@neu.edu.vn",
                          "LECTURER",
                          "Nguyễn Trọng Hưng"
                        )
                      }
                      className="py-2.5 px-3 bg-blue-50 hover:bg-blue-100 text-neu-primary font-semibold rounded-lg border border-blue-200 text-xs transition-colors cursor-pointer"
                    >
                      👨‍🏫 Vào nhanh vai Giảng viên
                    </button>
                    <button
                      type="button"
                      disabled={isQuickLoggingIn}
                      onClick={() =>
                        handleQuickMockLogin(
                          "11242145@st.neu.edu.vn",
                          "STUDENT",
                          "Bùi Phương Anh"
                        )
                      }
                      className="py-2.5 px-3 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 font-semibold rounded-lg border border-emerald-200 text-xs transition-colors cursor-pointer"
                    >
                      🎓 Vào nhanh vai Sinh viên
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="mt-6 pt-5 border-t border-neu-border grid grid-cols-3 gap-2 text-center text-xs text-neu-gray">
            <div className="bg-slate-50 rounded-lg p-2">
              <div className="font-bold text-neu-primary">Quick Look</div>
              <div>Chuẩn phôi QLĐT</div>
            </div>
            <div className="bg-slate-50 rounded-lg p-2">
              <div className="font-bold text-neu-primary">QR + PIN 60s</div>
              <div>Chống chụp mã</div>
            </div>
            <div className="bg-slate-50 rounded-lg p-2">
              <div className="font-bold text-neu-primary">GPS + Audio</div>
              <div>Xác thực 2 vòng</div>
            </div>
          </div>
        </div>
      </div>

      {/* BẢNG LỊCH SỬ CHUYÊN CẦN CÁ NHÂN CỦA SINH VIÊN (UC18) */}
      {user?.role === "STUDENT" && (
        <div className="bg-white border border-neu-border rounded-2xl p-6 sm:p-8 shadow-sm animate-in fade-in">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-6">
            <div>
              <h2 className="text-xl font-bold text-neu-primary">
                📊 Lịch sử chuyên cần cá nhân
              </h2>
              <p className="text-xs text-neu-gray mt-0.5">
                Sinh viên: <strong>{myAttendance?.full_name || user.full_name || user.email}</strong>
                {myAttendance?.student_code ? ` • MSSV: ${myAttendance.student_code}` : ""}
                {myAttendance?.admin_class ? ` • Lớp: ${myAttendance.admin_class}` : ""}
              </p>
            </div>
            <span className="text-xs font-bold px-3 py-1 rounded-full bg-blue-50 text-neu-primary border border-blue-200">
              {myAttendance?.courses?.length || 0} lớp học phần
            </span>
          </div>

          {isLoadingAttendance ? (
            <div className="py-8 text-center text-sm text-neu-gray animate-pulse">
              Đang tải dữ liệu chuyên cần cá nhân...
            </div>
          ) : !myAttendance || myAttendance.courses.length === 0 ? (
            <div className="py-8 text-center text-sm text-neu-gray bg-slate-50 rounded-xl border border-dashed border-neu-border">
              Chưa có dữ liệu lớp học phần nào gắn với mã sinh viên của bạn.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-sm">
                <thead>
                  <tr className="bg-slate-50 text-xs font-bold uppercase text-neu-gray border-b border-neu-border">
                    <th className="p-3.5">Học phần</th>
                    <th className="p-3.5">Lớp học phần</th>
                    <th className="p-3.5">Phòng</th>
                    <th className="p-3.5 text-center">Có mặt</th>
                    <th className="p-3.5 text-center">Vắng mặt</th>
                    <th className="p-3.5 text-center">Tổng số buổi</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neu-border">
                  {myAttendance.courses.map((c) => (
                    <tr key={c.course_id} className="hover:bg-slate-50/80">
                      <td className="p-3.5 font-bold text-neu-primary">
                        {c.course_name}
                      </td>
                      <td className="p-3.5 text-neu-text font-medium">
                        {c.class_section || c.course_code || "—"}
                      </td>
                      <td className="p-3.5 text-neu-gray">{c.room_name || "—"}</td>
                      <td className="p-3.5 text-center">
                        <span className="inline-block px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800">
                          {c.attended_count} buổi
                        </span>
                      </td>
                      <td className="p-3.5 text-center">
                        <span className="inline-block px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-100 text-red-800">
                          {c.absent_count} buổi
                        </span>
                      </td>
                      <td className="p-3.5 text-center font-semibold text-neu-text">
                        {c.total_sessions} buổi
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
