"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  checkPinSession,
  fetchMyAttendance,
  getToken,
  getUser,
  UserProfile,
  MyAttendanceResponse,
} from "@/lib/api";

export default function StudentHomePage() {
  const [pinCode, setPinCode] = useState("");
  const [isChecking, setIsChecking] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [myAttendance, setMyAttendance] = useState<MyAttendanceResponse | null>(null);
  const router = useRouter();

  useEffect(() => {
    const u = getUser();
    const token = getToken();
    setUser(u);
    if (token && u?.role === "STUDENT") {
      fetchMyAttendance()
        .then((res) => setMyAttendance(res))
        .catch(() => {});
    }
  }, []);

  const handlePinSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (pinCode.length !== 6) {
      setErrorMsg("Mã PIN phải bao gồm đúng 6 chữ số.");
      return;
    }

    setIsChecking(true);
    try {
      await checkPinSession(pinCode);
      router.push(`/student/${pinCode}`);
    } catch {
      setErrorMsg(
        "Mã PIN không khả dụng hoặc đã hết hạn 60s. Vui lòng nhìn lên màn chiếu để lấy mã mới nhất!"
      );
    } finally {
      setIsChecking(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto py-8 px-4 space-y-8">
      <div className="bg-white border border-neu-border rounded-2xl p-8 shadow-sm text-center">
        <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full bg-sky-50 text-neu-secondary border border-sky-200 mb-3">
          🎓 Cổng Điểm Danh Sinh Viên
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold text-neu-primary mb-2">
          Nhập Mã PIN Phiên Học (60s)
        </h1>
        <p className="text-neu-gray text-sm max-w-lg mx-auto mb-6">
          Sử dụng ứng dụng <strong>Camera</strong> trên điện thoại để quét mã QR trên màn chiếu, hoặc nhập trực tiếp <strong>Mã PIN 6 chữ số</strong> bên dưới:
        </p>

        <form onSubmit={handlePinSubmit} className="max-w-sm mx-auto space-y-5">
          <div>
            <label className="block text-xs font-bold text-neu-text mb-2 uppercase tracking-wider">
              Mã PIN 6 chữ số
            </label>
            <input
              type="text"
              inputMode="numeric"
              maxLength={6}
              value={pinCode}
              onChange={(e) => {
                setPinCode(e.target.value.replace(/[^0-9]/g, ""));
                if (errorMsg) setErrorMsg(null);
              }}
              placeholder="••••••"
              className="w-full text-center text-4xl font-black tracking-[0.25em] px-4 py-4 border-2 border-neu-border rounded-xl focus:outline-none focus:border-neu-primary transition-colors text-neu-primary font-mono bg-slate-50"
            />
          </div>

          {errorMsg && (
            <div
              role="alert"
              className="bg-red-50 border border-red-200 text-red-700 p-3.5 rounded-xl text-xs font-medium text-left flex items-start gap-2"
            >
              <span>⚠️</span>
              <span>{errorMsg}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={pinCode.length !== 6 || isChecking}
            className="w-full bg-neu-primary hover:bg-neu-secondary disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-bold py-4 rounded-xl transition-colors text-base shadow-sm cursor-pointer"
          >
            {isChecking ? "Đang kiểm tra mã PIN..." : "Tiếp tục điểm danh →"}
          </button>
        </form>

        <div className="mt-8 pt-6 border-t border-neu-border flex flex-col sm:flex-row items-center justify-center gap-3 text-sm">
          {user?.role === "STUDENT" ? (
            <span className="text-emerald-700 font-semibold">
              ✓ Đang đăng nhập: {user.full_name || user.email}
              {user.student_code ? ` (${user.student_code})` : ""}
            </span>
          ) : (
            <>
              <span className="text-neu-gray">
                Dành cho thiết bị cá nhân của bạn:
              </span>
              <Link
                href="/login"
                className="text-neu-primary font-bold hover:underline"
              >
                Đăng nhập bằng Microsoft 365 (@st.neu.edu.vn)
              </Link>
            </>
          )}
        </div>
      </div>

      {user?.role === "STUDENT" && myAttendance && (
        <div className="bg-white border border-neu-border rounded-2xl p-6 shadow-sm">
          <h2 className="text-lg font-bold text-neu-primary mb-4">
            📊 Lịch sử chuyên cần cá nhân ({myAttendance.courses.length} môn)
          </h2>
          {myAttendance.courses.length === 0 ? (
            <p className="text-sm text-neu-gray">
              Chưa có lớp học phần nào được ghi nhận cho mã sinh viên của bạn.
            </p>
          ) : (
            <div className="space-y-3">
              {myAttendance.courses.map((c) => (
                <div
                  key={c.course_id}
                  className="p-4 rounded-xl border border-neu-border flex flex-wrap justify-between items-center gap-3"
                >
                  <div>
                    <div className="font-bold text-neu-primary">{c.course_name}</div>
                    <div className="text-xs text-neu-gray">
                      Lớp: {c.class_section || c.course_code} • Phòng: {c.room_name || "—"}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-xs font-bold">
                    <span className="px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800">
                      Có mặt: {c.attended_count}/{c.total_sessions}
                    </span>
                    <span className="px-2.5 py-1 rounded-full bg-red-100 text-red-800">
                      Vắng: {c.absent_count}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
