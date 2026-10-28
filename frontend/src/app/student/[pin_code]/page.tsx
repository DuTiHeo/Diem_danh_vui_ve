"use client";

import { useState, useEffect, Suspense } from "react";
import { useParams, useRouter } from "next/navigation";
import { fetchApi, getUser, getToken } from "@/lib/api";

interface SessionInfo {
  session_id: string;
  pin_code: string;
  course_name: string;
  session_number: number;
  room_name: string;
  building_name?: string | null;
  expires_in_seconds: number;
}

function StudentAttendanceContent() {
  const params = useParams<{ pin_code: string }>();
  const pinCode = params?.pin_code || "";
  const router = useRouter();

  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null);
  const [isLoggedInStudent, setIsLoggedInStudent] = useState(false);
  const [studentCode, setStudentCode] = useState("");
  const [fullName, setFullName] = useState("");
  const [location, setLocation] = useState<{ lat: number; lng: number; acc: number } | null>(null);
  const [isMockGeoActive, setIsMockGeoActive] = useState(false);
  const [geoError, setGeoError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string; student_name?: string } | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  // Hydrate user from localStorage on client only to prevent SSR hydration mismatch
  useEffect(() => {
    const token = getToken();
    const currentUser = getUser();
    if (token && currentUser && currentUser.role === "STUDENT") {
      setIsLoggedInStudent(true);
    }
    if (currentUser?.email) {
      const extracted = currentUser.email.split("@")[0].slice(0, 8);
      if (extracted.match(/^\d+$/)) {
        setStudentCode((prev) => prev || extracted);
      }
    }
    if (currentUser?.full_name) {
      setFullName((prev) => prev || currentUser.full_name || "");
    }
  }, []);

  // Load session from PIN
  useEffect(() => {
    if (!pinCode) return;

    fetchApi<SessionInfo>(`/sessions/qr/${pinCode}`)
      .then((data) => setSessionInfo(data))
      .catch((err: unknown) => {
        const msg = err instanceof Error ? err.message : "Mã PIN không hợp lệ hoặc đã hết hạn.";
        setLoadError(msg);
      });
  }, [pinCode]);

  // Request GPS
  useEffect(() => {
    if (typeof window !== "undefined") {
      if (!("geolocation" in navigator)) {
        setGeoError("Trình duyệt không hỗ trợ GPS hoặc đang chạy qua HTTP thông thường.");
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation({
            lat: position.coords.latitude,
            lng: position.coords.longitude,
            acc: position.coords.accuracy,
          });
          setGeoError(null);
        },
        (error) => {
          let errorMsg = "Lỗi xác định vị trí.";
          if (error.code === 1) errorMsg = "Quyền truy cập GPS bị từ chối hoặc yêu cầu HTTPS.";
          if (error.code === 2) errorMsg = "Không thể lấy được tọa độ GPS hiện tại.";
          if (error.code === 3) errorMsg = "Quá thời gian chờ định vị GPS.";
          setGeoError(errorMsg);
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
      );
    }
  }, []);

  const isGeofenceRequired = Boolean(sessionInfo?.building_name);

  const handleUseMockNeuGeo = (e?: React.SyntheticEvent) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    setLocation({
      lat: 20.99965,
      lng: 105.84315,
      acc: 5.0,
    });
    setIsMockGeoActive(true);
    setGeoError(null);
    setFormError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    const trimmedName = fullName.trim();
    const trimmedCode = studentCode.trim();

    if (trimmedName.length < 2) {
      setFormError("Vui lòng nhập đầy đủ Họ và tên sinh viên.");
      return;
    }

    if (trimmedCode.length < 6) {
      setFormError("Vui lòng nhập Mã số sinh viên (tối thiểu 6 chữ số).");
      return;
    }

    if (isGeofenceRequired && !location) {
      setFormError("Buổi học này yêu cầu vị trí GPS tại giảng đường. Vui lòng bấm 'Dùng tọa độ NEU (Thử nghiệm)' bên dưới để tiếp tục.");
      return;
    }

    const effectiveLat = location?.lat ?? 20.99965;
    const effectiveLng = location?.lng ?? 105.84315;
    const effectiveAcc = location?.acc ?? 5.0;

    setIsSubmitting(true);
    setResult(null);

    try {
      let res: { message?: string; student_name?: string };
      if (isLoggedInStudent) {
        res = await fetchApi<{ message?: string; student_name?: string }>("/attendance/qr", {
          method: "POST",
          body: JSON.stringify({
            pin_code: pinCode,
            latitude: effectiveLat,
            longitude: effectiveLng,
            accuracy: effectiveAcc,
          }),
        });
      } else {
        res = await fetchApi<{ message?: string; student_name?: string }>("/attendance/pin", {
          method: "POST",
          body: JSON.stringify({
            pin_code: pinCode,
            student_code: trimmedCode,
            full_name: trimmedName,
            latitude: effectiveLat,
            longitude: effectiveLng,
            accuracy: effectiveAcc,
          }),
        });
      }

      setResult({
        success: true,
        message: res.message || "Điểm danh thành công!",
        student_name: res.student_name || trimmedName,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Điểm danh thất bại.";
      setResult({
        success: false,
        message: msg,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loadError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[calc(100vh-12rem)] px-4">
        <div className="w-full max-w-sm bg-white border border-red-200 rounded-xl p-8 shadow-sm text-center">
          <div className="text-4xl text-neu-red mb-3">⚠️</div>
          <h2 className="text-xl font-bold text-neu-text mb-2">Mã PIN không khả dụng</h2>
          <p className="text-sm text-neu-gray mb-6">{loadError}</p>
          <button
            onClick={() => router.push("/student")}
            className="w-full py-3 bg-neu-primary text-white rounded-lg font-bold text-sm touch-manipulation cursor-pointer"
          >
            Nhập mã PIN khác
          </button>
        </div>
      </div>
    );
  }

  if (result) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[calc(100vh-12rem)] px-4 animate-in zoom-in duration-300">
        <div
          className={`w-full max-w-sm border rounded-2xl p-8 shadow-md text-center ${
            result.success ? "bg-emerald-50 border-emerald-200" : "bg-red-50 border-red-200"
          }`}
        >
          <div className={`text-6xl mb-4 ${result.success ? "text-emerald-500" : "text-neu-red"}`}>
            {result.success ? "✓" : "✕"}
          </div>
          <h2 className={`text-2xl font-black mb-2 ${result.success ? "text-emerald-900" : "text-red-900"}`}>
            {result.success ? "Điểm danh thành công!" : "Chưa thể điểm danh"}
          </h2>
          <p className="text-sm font-medium text-neu-text mt-1">{result.message}</p>
          {result.student_name && (
            <p className="text-xs font-bold text-neu-primary mt-2">
              Sinh viên: {result.student_name} ({studentCode})
            </p>
          )}

          {result.success ? (
            <div className="mt-6 pt-4 border-t border-emerald-200/60 flex flex-col gap-2">
              <button
                onClick={() => router.push("/")}
                className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-bold text-sm shadow-xs touch-manipulation cursor-pointer"
              >
                Về trang chủ
              </button>
            </div>
          ) : (
            <button
              onClick={() => setResult(null)}
              className="mt-6 w-full py-3 bg-neu-primary hover:bg-neu-secondary text-white rounded-lg font-bold text-sm shadow-xs touch-manipulation cursor-pointer"
            >
              Thử lại
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-12rem)] px-4">
      <div className="w-full max-w-sm bg-white border border-neu-border rounded-2xl p-6 shadow-sm">
        <div className="border-b border-neu-border pb-4 mb-6">
          <div className="inline-block bg-blue-50 text-neu-primary font-bold px-3 py-1 rounded-md mb-2 text-xs tracking-widest font-mono">
            MÃ PIN: {pinCode}
          </div>
          <h1 className="text-xl font-bold text-neu-text">
            {sessionInfo?.course_name || "Xác nhận có mặt"}
          </h1>
          <p className="text-neu-gray text-xs mt-1">
            Buổi {sessionInfo?.session_number || 1} • Phòng {sessionInfo?.room_name || "Phòng học"}
            {sessionInfo?.building_name ? ` (${sessionInfo.building_name})` : ""}
          </p>
        </div>

        {geoError && (
          <div className="bg-amber-50 border border-amber-200 text-amber-800 p-3 rounded-lg mb-4 text-xs">
            <span className="font-bold block mb-0.5">⚠️ Thông báo GPS:</span>
            {geoError}
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-neu-text mb-1 uppercase tracking-wider">
              Họ và tên sinh viên
            </label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => {
                setFullName(e.target.value);
                if (formError) setFormError(null);
              }}
              placeholder="VD: Bùi Phương Anh"
              className="w-full px-4 py-3 border border-neu-border rounded-lg focus:outline-none focus:border-neu-primary focus:ring-1 focus:ring-neu-primary text-neu-text text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-neu-text mb-1 uppercase tracking-wider">
              Mã số sinh viên (8 chữ số)
            </label>
            <input
              type="text"
              value={studentCode}
              onChange={(e) => {
                setStudentCode(e.target.value.replace(/[^0-9]/g, ""));
                if (formError) setFormError(null);
              }}
              placeholder="VD: 11242145"
              maxLength={10}
              className="w-full px-4 py-3 border border-neu-border rounded-lg focus:outline-none focus:border-neu-primary focus:ring-1 focus:ring-neu-primary text-neu-text tracking-widest font-mono text-sm"
            />
          </div>

          {/* GPS Status Indicator & Mock Location Action */}
          <div className="bg-neu-bg p-3.5 rounded-xl border border-neu-border flex flex-col gap-2.5 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-neu-gray font-medium">
                Vị trí GPS: <span className="font-semibold text-neu-text">{isGeofenceRequired ? "Bắt buộc" : "Không bắt buộc"}</span>
              </span>
              {location ? (
                <span className="text-emerald-700 font-bold flex items-center gap-1.5 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block"></span>
                  {isMockGeoActive ? "Tọa độ NEU" : `Chính xác (~${Math.round(location.acc)}m)`}
                </span>
              ) : isGeofenceRequired ? (
                <span className="text-amber-600 font-bold animate-pulse bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                  Đang lấy GPS...
                </span>
              ) : (
                <span className="text-blue-600 font-medium bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                  Đã tắt kiểm tra GPS
                </span>
              )}
            </div>

            <div className="pt-2 border-t border-gray-200">
              <button
                type="button"
                onClick={handleUseMockNeuGeo}
                className={`w-full py-2.5 px-3 rounded-lg font-bold text-xs border transition-all flex items-center justify-center gap-2 cursor-pointer touch-manipulation select-none active:scale-98 ${
                  isMockGeoActive
                    ? "bg-emerald-100 text-emerald-900 border-emerald-300 shadow-inner"
                    : "bg-white text-blue-700 hover:bg-blue-50 border-blue-300 shadow-xs active:bg-blue-100"
                }`}
              >
                <span>📍</span>
                <span>{isMockGeoActive ? "✓ Đang dùng tọa độ NEU (Thử nghiệm)" : "Dùng tọa độ NEU (Thử nghiệm)"}</span>
              </button>
            </div>
          </div>

          {formError && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-xs font-medium flex flex-col gap-1.5 animate-in fade-in">
              <div className="flex items-center gap-1.5 font-bold">
                <span>⚠️</span> {formError}
              </div>
              {isGeofenceRequired && !location && (
                <button
                  type="button"
                  onClick={handleUseMockNeuGeo}
                  className="mt-1 py-1.5 px-3 bg-red-600 text-white rounded font-bold text-xs self-start cursor-pointer touch-manipulation"
                >
                  📍 Dùng tọa độ NEU ngay
                </button>
              )}
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-neu-primary hover:bg-neu-secondary disabled:bg-gray-400 text-white font-bold py-3.5 rounded-xl transition-all shadow-md text-base mt-2 active:scale-98 cursor-pointer touch-manipulation select-none"
          >
            {isSubmitting ? "Đang xác thực vị trí..." : "Xác nhận có mặt ngay"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function StudentAttendancePage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-neu-gray">Đang tải thông tin điểm danh...</div>}>
      <StudentAttendanceContent />
    </Suspense>
  );
}
