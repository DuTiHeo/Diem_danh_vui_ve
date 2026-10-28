"use client";

import { useState, useEffect, use, Suspense } from "react";
import { useRouter } from "next/navigation";
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

function StudentAttendanceContent({ params }: { params: Promise<{ pin_code: string }> }) {
  const resolvedParams = use(params);
  const pinCode = resolvedParams.pin_code;
  const router = useRouter();

  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null);
  
  const [isLoggedInStudent] = useState(() => {
    if (typeof window === "undefined") return false;
    const token = getToken();
    const currentUser = getUser();
    return Boolean(token && currentUser && currentUser.role === "STUDENT");
  });

  const [studentCode, setStudentCode] = useState(() => {
    if (typeof window === "undefined") return "";
    const currentUser = getUser();
    if (currentUser?.email) {
      const extracted = currentUser.email.split("@")[0].slice(0, 8);
      if (extracted.match(/^\d+$/)) return extracted;
    }
    return "";
  });

  const [fullName, setFullName] = useState(() => {
    if (typeof window === "undefined") return "";
    const currentUser = getUser();
    return currentUser?.full_name || "";
  });

  const [location, setLocation] = useState<{ lat: number; lng: number; acc: number } | null>(null);
  const [geoError, setGeoError] = useState<string | null>(() => {
    if (typeof window !== "undefined" && !("geolocation" in navigator)) {
      return "Trình duyệt của bạn không hỗ trợ định vị GPS.";
    }
    return null;
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string; student_name?: string } | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

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
    if (typeof window !== "undefined" && "geolocation" in navigator) {
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
          if (error.code === 1) errorMsg = "Vui lòng cho phép quyền truy cập Vị trí (GPS) để điểm danh.";
          if (error.code === 2) errorMsg = "Không thể lấy được tọa độ GPS hiện tại. Hãy bật dịch vụ định vị.";
          if (error.code === 3) errorMsg = "Quá thời gian chờ định vị GPS.";
          setGeoError(errorMsg);
        },
        { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
      );
    }
  }, []);

  const isGeofenceRequired = Boolean(sessionInfo?.building_name);

  const handleUseMockNeuGeo = () => {
    setLocation({
      lat: 20.99965,
      lng: 105.84315,
      acc: 5.0,
    });
    setGeoError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isGeofenceRequired && !location) {
      alert("Buổi học này yêu cầu kiểm tra vị trí GPS tại giảng đường. Vui lòng cấp quyền định vị hoặc bấm 'Dùng tọa độ NEU (Thử nghiệm)' để kiểm tra.");
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
            student_code: studentCode.trim(),
            full_name: fullName.trim(),
            latitude: effectiveLat,
            longitude: effectiveLng,
            accuracy: effectiveAcc,
          }),
        });
      }

      setResult({
        success: true,
        message: res.message || "Điểm danh thành công!",
        student_name: res.student_name || fullName,
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
            className="w-full py-2.5 bg-neu-primary text-white rounded-lg font-bold"
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
            <div className="mt-6 pt-4 border-t border-emerald-200 text-xs text-neu-gray">
              Buổi {sessionInfo?.session_number || 1} • {sessionInfo?.course_name}
              <p className="mt-1 font-mono">{new Date().toLocaleTimeString("vi-VN")}</p>
            </div>
          ) : (
            <div className="mt-6">
              <button
                onClick={() => setResult(null)}
                className="w-full py-2.5 bg-neu-red text-white rounded-lg font-bold text-sm shadow-xs"
              >
                Thử lại
              </button>
            </div>
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
          <div className="bg-red-50 border border-red-200 text-red-700 p-3.5 rounded-lg mb-5 text-xs">
            <span className="font-bold block mb-0.5">⚠️ Yêu cầu vị trí GPS:</span>
            {geoError}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-neu-text mb-1 uppercase tracking-wider">
              Họ và tên sinh viên
            </label>
            <input
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="VD: Bùi Phương Anh"
              className="w-full px-4 py-2.5 border border-neu-border rounded-lg focus:outline-none focus:border-neu-primary focus:ring-1 focus:ring-neu-primary text-neu-text text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-neu-text mb-1 uppercase tracking-wider">
              Mã số sinh viên (8 chữ số)
            </label>
            <input
              type="text"
              required
              value={studentCode}
              onChange={(e) => setStudentCode(e.target.value.replace(/[^0-9]/g, ""))}
              placeholder="VD: 11242145"
              maxLength={10}
              className="w-full px-4 py-2.5 border border-neu-border rounded-lg focus:outline-none focus:border-neu-primary focus:ring-1 focus:ring-neu-primary text-neu-text tracking-widest font-mono text-sm"
            />
          </div>

          {/* GPS Status Indicator */}
          <div className="bg-neu-bg p-3 rounded-lg border border-neu-border flex flex-col gap-1.5 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-neu-gray">
                Vị trí GPS {isGeofenceRequired ? "(Bắt buộc)" : "(Không bắt buộc)"}
              </span>
              {location ? (
                <span className="text-emerald-700 font-bold flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block"></span>
                  Chính xác (~{Math.round(location.acc)}m)
                </span>
              ) : isGeofenceRequired ? (
                <span className="text-amber-600 font-bold animate-pulse">
                  Đang lấy tọa độ GPS...
                </span>
              ) : (
                <span className="text-blue-600 font-medium">
                  Đã tắt kiểm tra GPS
                </span>
              )}
            </div>

            {(!location || geoError) && (
              <div className="flex items-center justify-between pt-1.5 border-t border-gray-200 mt-1">
                <span className="text-[11px] text-neu-gray">Không ở trường hoặc lỗi GPS?</span>
                <button
                  type="button"
                  onClick={handleUseMockNeuGeo}
                  className="text-[11px] text-blue-600 hover:text-blue-800 font-bold underline"
                >
                  📍 Dùng tọa độ NEU (Thử nghiệm)
                </button>
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={
              (isGeofenceRequired && !location) ||
              isSubmitting ||
              studentCode.length < 6 ||
              fullName.length < 2
            }
            className="w-full bg-neu-primary hover:bg-neu-secondary disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-bold py-3 rounded-xl transition-all shadow-sm text-base mt-2"
          >
            {isSubmitting ? "Đang xác thực vị trí..." : "Xác nhận có mặt ngay"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function StudentAttendancePage(props: { params: Promise<{ pin_code: string }> }) {
  return (
    <Suspense fallback={<div className="p-8 text-center text-neu-gray">Đang tải thông tin điểm danh...</div>}>
      <StudentAttendanceContent {...props} />
    </Suspense>
  );
}


