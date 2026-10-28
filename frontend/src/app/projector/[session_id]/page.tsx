"use client";

import { useState, useEffect, useRef, use, Suspense, useCallback } from "react";
import { useRouter } from "next/navigation";
import QRCode from "qrcode";
import { fetchApi, getApiBaseUrl } from "@/lib/api";

interface StudentAttendee {
  id: string;
  ordinal: number;
  student_code: string;
  name: string;
  status: "ATTENDED" | "ABSENT" | "PENDING";
  time: string | null;
  method?: string | null;
  distance_meters?: number | null;
}

interface SessionData {
  id: string;
  course_id: string;
  course_name: string;
  room_name: string;
  session_number: number;
  status: "OPEN" | "CLOSED";
  pin_code: string | null;
  remaining_seconds: number;
  building: { name: string; code: string } | null;
  total_students: number;
  attended_count: number;
  students: StudentAttendee[];
}

function ProjectorContent({ params }: { params: Promise<{ session_id: string }> }) {
  const resolvedParams = use(params);
  const sessionId = resolvedParams.session_id;
  const router = useRouter();

  const [session, setSession] = useState<SessionData | null>(null);
  const [timeLeft, setTimeLeft] = useState(60);
  const [pinCode, setPinCode] = useState("000000");
  const [lanIp, setLanIp] = useState("192.168.1.131");
  const [isEditingIp, setIsEditingIp] = useState(false);
  const [customIpInput, setCustomIpInput] = useState("192.168.1.131");
  const [copiedLink, setCopiedLink] = useState(false);
  const [qrDataUrl, setQrDataUrl] = useState<string>("");
  const [students, setStudents] = useState<StudentAttendee[]>([]);
  const [attendedCount, setAttendedCount] = useState(0);
  const [showManualModal, setShowManualModal] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isClosing, setIsClosing] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  // Generate QR Code data URL with LAN IP
  const generateQR = useCallback(async (code: string, ipOverride?: string) => {
    try {
      let targetIp = ipOverride || lanIp || "192.168.1.131";
      if (typeof window !== "undefined") {
        const curHost = window.location.hostname;
        if (curHost && curHost !== "localhost" && curHost !== "127.0.0.1" && !ipOverride) {
          targetIp = curHost;
        }
      }
      const port = typeof window !== "undefined" && window.location.port ? `:${window.location.port}` : ":3000";
      const checkInUrl = `http://${targetIp}${port}/student/${code}`;
      const url = await QRCode.toDataURL(checkInUrl, {
        width: 320,
        margin: 2,
        color: {
          dark: "#1E3A8A",
          light: "#FFFFFF",
        },
      });
      setQrDataUrl(url);
    } catch (e) {
      console.error("QR Code Error:", e);
    }
  }, [lanIp]);

  // Load system network info
  useEffect(() => {
    fetchApi<{ lan_ip: string }>("/system/network-info")
      .then((net) => {
        if (net?.lan_ip) {
          setLanIp(net.lan_ip);
          setCustomIpInput(net.lan_ip);
        }
      })
      .catch(() => {});
  }, []);

  // Load Session Data
  const loadSession = useCallback(async () => {
    if (!sessionId) return;
    try {
      const data = await fetchApi<SessionData>(`/sessions/${sessionId}`);
      setSession(data);
      setStudents(data.students || []);
      setAttendedCount(data.attended_count || 0);
      if (data.pin_code) {
        setPinCode(data.pin_code);
        generateQR(data.pin_code);
      }
      setTimeLeft(data.remaining_seconds || 60);
    } catch (err: unknown) {
      console.error("Lỗi tải thông tin session:", err);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, generateQR]);

  useEffect(() => {
    if (!sessionId) return;
    let ignore = false;

    fetchApi<SessionData>(`/sessions/${sessionId}`)
      .then((data) => {
        if (ignore) return;
        setSession(data);
        setStudents(data.students || []);
        setAttendedCount(data.attended_count || 0);
        if (data.pin_code) {
          setPinCode(data.pin_code);
          generateQR(data.pin_code);
        }
        setTimeLeft(data.remaining_seconds || 60);
        setIsLoading(false);
      })
      .catch((err: unknown) => {
        if (!ignore) {
          console.error("Lỗi tải session:", err);
          setIsLoading(false);
        }
      });

    return () => {
      ignore = true;
    };
  }, [sessionId, generateQR]);

  // Connect WebSocket for live updates
  useEffect(() => {
    if (!sessionId) return;

    let wsUrl: string;
    try {
      const baseUrl = getApiBaseUrl();
      const base = new URL(baseUrl);
      const proto = base.protocol === "https:" ? "wss:" : "ws:";
      wsUrl = `${proto}//${base.host}/api/v1/sessions/ws/${sessionId}`;
    } catch {
      const host = lanIp || "192.168.1.131";
      wsUrl = `ws://${host}:8000/api/v1/sessions/ws/${sessionId}`;
    }

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.event === "ATTENDANCE_MARKED") {
          setStudents((prev) =>
            prev.map((st) =>
              st.id === data.student_id || st.student_code === data.student_code
                ? {
                    ...st,
                    status: "ATTENDED",
                    time: data.time || new Date().toLocaleTimeString("vi-VN"),
                    method: data.method || "QR",
                    distance_meters: data.distance_meters,
                  }
                : st
            )
          );
          setAttendedCount((prev) => prev + 1);
        } else if (data.event === "QR_REFRESHED") {
          setPinCode(data.pin_code);
          generateQR(data.pin_code);
          setTimeLeft(data.expires_in_seconds || 60);
        } else if (data.event === "ATTENDANCE_MANUAL_OVERRIDE") {
          setStudents((prev) =>
            prev.map((st) =>
              st.id === data.student_id
                ? {
                    ...st,
                    status: data.status,
                    time: data.status === "ATTENDED" ? data.time : null,
                  }
                : st
            )
          );
        } else if (data.event === "SESSION_CLOSED") {
          setSession((prev) => (prev ? { ...prev, status: "CLOSED" } : null));
        }
      } catch (err) {
        console.error("WS Parse error:", err);
      }
    };

    return () => {
      ws.close();
    };
  }, [sessionId, generateQR, lanIp]);

  // Countdown timer
  useEffect(() => {
    if (session?.status !== "OPEN") return;
    if (timeLeft > 0) {
      const timer = setTimeout(() => setTimeLeft((prev) => prev - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [timeLeft, session?.status]);

  // Refresh QR
  const handleRefreshQr = async () => {
    setIsRefreshing(true);
    try {
      const res = await fetchApi<{ pin_code: string; expires_in_seconds: number }>(`/sessions/${sessionId}/refresh-qr`, { method: "POST" });
      setPinCode(res.pin_code);
      generateQR(res.pin_code);
      setTimeLeft(res.expires_in_seconds || 60);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Lỗi làm mới mã";
      alert("Lỗi làm mới mã: " + msg);
    } finally {
      setIsRefreshing(false);
    }
  };

  // Close Session
  const handleCloseSession = async () => {
    if (!confirm("Bạn có chắc chắn muốn kết thúc phiên điểm danh? Những sinh viên chưa quét sẽ được ghi nhận là VẮNG.")) {
      return;
    }
    setIsClosing(true);
    try {
      await fetchApi(`/sessions/${sessionId}/close`, { method: "POST" });
      await loadSession();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Lỗi kết thúc phiên";
      alert("Lỗi kết thúc phiên: " + msg);
    } finally {
      setIsClosing(false);
    }
  };

  // Manual Override
  const handleManualToggle = async (studentId: string, currentStatus: string) => {
    const newStatus = currentStatus === "ATTENDED" ? "ABSENT" : "ATTENDED";
    try {
      await fetchApi("/attendance/manual", {
        method: "POST",
        body: JSON.stringify({
          session_id: sessionId,
          student_id: studentId,
          status: newStatus,
        }),
      });
      setStudents((prev) =>
        prev.map((st) =>
          st.id === studentId
            ? {
                ...st,
                status: newStatus,
                time: newStatus === "ATTENDED" ? new Date().toLocaleTimeString("vi-VN") : null,
              }
            : st
        )
      );
      setAttendedCount((prev) => (newStatus === "ATTENDED" ? prev + 1 : Math.max(0, prev - 1)));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Lỗi can thiệp";
      alert("Lỗi can thiệp: " + msg);
    }
  };

  const progressPercentage = (timeLeft / 60) * 100;
  const isWarning = timeLeft <= 15;
  const totalStudents = students.length;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-12rem)] text-neu-gray">
        Đang khởi động màn hình máy chiếu...
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-[calc(100vh-8rem)]">
      {/* Header Buổi học */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4 mb-6 border-b border-neu-border pb-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl md:text-3xl font-black text-neu-primary">
              {session?.course_name || "Buổi học"} - Buổi {session?.session_number || 1}
            </h1>
            <span
              className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                session?.status === "OPEN"
                  ? "bg-emerald-100 text-emerald-800 animate-pulse"
                  : "bg-gray-200 text-neu-gray"
              }`}
            >
              {session?.status === "OPEN" ? "ĐANG ĐIỂM DANH" : "ĐÃ KẾT THÚC"}
            </span>
          </div>
          <p className="text-neu-gray text-base mt-1">
            Phòng {session?.room_name || "B-301"}
            {session?.building ? ` • Giảng đường ${session.building.name} (${session.building.code})` : ""}
          </p>
        </div>
        
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => setShowManualModal(true)}
            className="px-4 py-2 bg-white hover:bg-gray-100 text-neu-text rounded-lg font-medium border border-neu-border shadow-xs text-sm"
          >
            ✏️ Can thiệp thủ công
          </button>
          {session?.status === "OPEN" ? (
            <button
              onClick={handleCloseSession}
              disabled={isClosing}
              className="px-5 py-2 bg-neu-red hover:bg-red-600 text-white rounded-lg font-bold shadow-xs text-sm transition-colors"
            >
              {isClosing ? "Đang đóng..." : "⏹ Kết thúc phiên"}
            </button>
          ) : (
            <button
              onClick={handleRefreshQr}
              className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-bold shadow-xs text-sm"
            >
              🔄 Mở lại phiên điểm danh
            </button>
          )}
          <button
            onClick={() => router.push(`/courses/${session?.course_id}`)}
            className="px-4 py-2 bg-neu-bg hover:bg-gray-200 text-neu-text rounded-lg font-medium text-sm"
          >
            ← Về lớp học
          </button>
        </div>
      </div>

      {/* Layout 2 cột: Màn hình trình chiếu & Danh sách realtime */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
        
        {/* Cột trái: QR Code & Mã PIN (Máy chiếu) */}
        <div className="lg:col-span-7 bg-white border border-neu-border rounded-2xl flex flex-col items-center justify-center p-8 shadow-sm relative overflow-hidden min-h-[460px]">
          {/* Thanh tiến trình thời gian ở trên cùng */}
          {session?.status === "OPEN" && (
            <div className="absolute top-0 left-0 w-full h-2.5 bg-gray-100">
              <div
                className={`h-full transition-all duration-1000 ease-linear ${
                  isWarning ? "bg-neu-red" : "bg-neu-primary"
                }`}
                style={{ width: `${progressPercentage}%` }}
              ></div>
            </div>
          )}

          <h2 className="text-2xl font-bold text-neu-text mb-6">Quét mã QR bằng Camera điện thoại</h2>
          
          <div className={`p-4 rounded-2xl border-4 ${isWarning ? "border-neu-red" : "border-neu-primary"} mb-6 bg-white shadow-md`}>
            {qrDataUrl ? (
              /* eslint-disable-next-line @next/next/no-img-element */
              <img src={qrDataUrl} alt="Mã QR Điểm Danh" className="w-64 h-64 md:w-72 md:h-72 object-contain" />
            ) : (
              <div className="w-64 h-64 bg-gray-100 flex items-center justify-center text-neu-gray font-bold">
                Đang tạo mã QR...
              </div>
            )}
          </div>

          <div className="text-center">
            <p className="text-neu-gray uppercase tracking-widest text-xs font-bold mb-2">
              Hoặc nhập mã PIN tại trang sinh viên
            </p>
            <div className="text-5xl md:text-6xl font-black text-neu-text tracking-[0.25em] font-mono">
              {pinCode}
            </div>
          </div>

          {/* Link truy cập trực tiếp từ điện thoại & Điều khiển IP mạng */}
          <div className="mt-5 p-3.5 bg-blue-50/80 border border-blue-200 rounded-xl text-center max-w-sm w-full">
            <div className="text-xs text-neu-gray font-medium mb-1">
              📱 Link điểm danh trực tiếp trên điện thoại:
            </div>
            <div className="text-xs font-mono font-bold text-neu-primary break-all select-all bg-white px-2.5 py-1.5 rounded border border-blue-100">
              http://{lanIp}:3000/student/{pinCode}
            </div>
            <div className="flex items-center justify-center gap-2 mt-2">
              <button
                type="button"
                onClick={() => {
                  if (typeof navigator !== "undefined" && navigator.clipboard) {
                    navigator.clipboard.writeText(`http://${lanIp}:3000/student/${pinCode}`);
                    setCopiedLink(true);
                    setTimeout(() => setCopiedLink(false), 2000);
                  }
                }}
                className="text-xs px-2.5 py-1 bg-white border border-blue-300 rounded text-blue-700 hover:bg-blue-100 font-semibold transition-colors"
              >
                {copiedLink ? "✓ Đã copy link" : "📋 Sao chép link gửi lớp"}
              </button>
              <button
                type="button"
                onClick={() => setIsEditingIp(!isEditingIp)}
                className="text-xs px-2.5 py-1 bg-white border border-gray-300 rounded text-gray-700 hover:bg-gray-100 font-semibold transition-colors"
              >
                ⚙️ {isEditingIp ? "Đóng" : `IP: ${lanIp}`}
              </button>
            </div>

            {isEditingIp && (
              <div className="mt-2.5 pt-2.5 border-t border-blue-200 flex gap-2 items-center justify-center">
                <input
                  type="text"
                  value={customIpInput}
                  onChange={(e) => setCustomIpInput(e.target.value)}
                  placeholder="Ví dụ: 192.168.1.131"
                  className="px-2.5 py-1 text-xs border border-blue-300 rounded bg-white text-neu-text w-36 font-mono"
                />
                <button
                  type="button"
                  onClick={() => {
                    const clean = customIpInput.trim();
                    if (clean) {
                      setLanIp(clean);
                      generateQR(pinCode, clean);
                      setIsEditingIp(false);
                    }
                  }}
                  className="px-3 py-1 bg-neu-primary text-white rounded text-xs font-bold hover:bg-neu-secondary"
                >
                  Áp dụng
                </button>
              </div>
            )}
          </div>

          {/* Hết hạn Overlay */}
          {session?.status === "OPEN" && timeLeft === 0 && (
            <div className="absolute inset-0 bg-white/95 backdrop-blur-xs flex flex-col items-center justify-center z-20 animate-in fade-in duration-200">
              <div className="text-4xl mb-2">⏱️</div>
              <p className="text-2xl font-bold text-neu-red mb-2">Mã QR đã hết hạn!</p>
              <p className="text-sm text-neu-gray mb-6">Nhấn nút bên dưới để cấp mã mới bảo mật chống gian lận.</p>
              <button
                onClick={handleRefreshQr}
                disabled={isRefreshing}
                className="px-8 py-3.5 bg-neu-primary text-white rounded-xl text-lg font-bold shadow-lg hover:bg-neu-secondary transition-all transform hover:scale-105"
              >
                {isRefreshing ? "Đang tạo mã..." : "⚡ Tạo mã mới ngay (60s)"}
              </button>
            </div>
          )}

          {session?.status === "CLOSED" && (
            <div className="absolute inset-0 bg-gray-50/95 backdrop-blur-xs flex flex-col items-center justify-center z-20">
              <div className="text-5xl mb-3">✓</div>
              <p className="text-2xl font-bold text-neu-text mb-2">Phiên điểm danh đã kết thúc</p>
              <p className="text-sm text-neu-gray mb-6">
                Đã ghi nhận {attendedCount} / {totalStudents} sinh viên có mặt.
              </p>
              <button
                onClick={() => router.push(`/courses/${session?.course_id}`)}
                className="px-6 py-2.5 bg-neu-primary text-white rounded-lg font-bold"
              >
                Quay lại lớp học & Xem báo cáo
              </button>
            </div>
          )}
          
          {session?.status === "OPEN" && (
            <div className="absolute bottom-6 right-6">
              <div className={`text-3xl font-black ${isWarning ? "text-neu-red animate-pulse" : "text-neu-gray"}`}>
                {timeLeft}s
              </div>
            </div>
          )}
        </div>

        {/* Cột phải: Danh sách Realtime */}
        <div className="lg:col-span-5 bg-white border border-neu-border rounded-2xl flex flex-col shadow-sm max-h-[640px]">
          <div className="p-4 border-b border-neu-border bg-neu-bg rounded-t-2xl flex justify-between items-center">
            <h3 className="font-bold text-neu-text text-lg">Trạng thái lớp học</h3>
            <div className="text-emerald-700 font-bold bg-emerald-100 px-3.5 py-1 rounded-full text-sm">
              {attendedCount} / {totalStudents} Có mặt
            </div>
          </div>
          
          <div className="flex-1 overflow-y-auto p-2">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="text-xs text-neu-gray uppercase tracking-wider border-b border-neu-border">
                  <th className="p-3 font-semibold">Sinh viên</th>
                  <th className="p-3 font-semibold text-right">Trạng thái</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neu-bg text-sm">
                {students.map((st) => (
                  <tr key={st.id} className="hover:bg-gray-50 transition-colors">
                    <td className="p-3">
                      <div className="font-bold text-neu-text">{st.name}</div>
                      <div className="text-xs font-mono text-neu-gray">{st.student_code}</div>
                    </td>
                    <td className="p-3 text-right">
                      {st.status === "ATTENDED" ? (
                        <div className="inline-flex flex-col items-end">
                          <span className="inline-block px-2.5 py-1 bg-green-100 text-green-700 text-xs font-bold rounded">
                            CÓ MẶT {st.method ? `(${st.method})` : ""}
                          </span>
                          {st.time && (
                            <span className="text-[11px] text-neu-gray mt-0.5">{st.time}</span>
                          )}
                        </div>
                      ) : (
                        <span className="inline-block px-2.5 py-1 bg-gray-100 text-neu-gray text-xs font-medium rounded">
                          {session?.status === "CLOSED" ? "VẮNG" : "CHỜ QUÉT"}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Modal: Can thiệp thủ công */}
      {showManualModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl border border-neu-border shadow-2xl max-w-lg w-full p-6 max-h-[85vh] flex flex-col">
            <div className="flex justify-between items-center mb-4 border-b border-neu-border pb-3">
              <div>
                <h3 className="text-lg font-bold text-neu-primary">Can thiệp điểm danh thủ công</h3>
                <p className="text-xs text-neu-gray">Bấm vào trạng thái sinh viên để chuyển đổi Có mặt / Vắng</p>
              </div>
              <button
                onClick={() => setShowManualModal(false)}
                className="text-neu-gray hover:text-neu-text font-bold text-xl"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-y-auto divide-y divide-neu-border">
              {students.map((st) => (
                <div key={st.id} className="py-3 flex justify-between items-center">
                  <div>
                    <div className="font-bold text-neu-text text-sm">{st.name}</div>
                    <div className="text-xs text-neu-gray font-mono">{st.student_code}</div>
                  </div>
                  <button
                    onClick={() => handleManualToggle(st.id, st.status)}
                    className={`px-3 py-1.5 rounded text-xs font-bold transition-all ${
                      st.status === "ATTENDED"
                        ? "bg-green-600 text-white hover:bg-green-700"
                        : "bg-gray-200 text-neu-text hover:bg-gray-300"
                    }`}
                  >
                    {st.status === "ATTENDED" ? "✓ CÓ MẶT" : "○ VẮNG (Bấm điểm danh)"}
                  </button>
                </div>
              ))}
            </div>

            <div className="pt-4 border-t border-neu-border text-right">
              <button
                onClick={() => setShowManualModal(false)}
                className="px-5 py-2 bg-neu-primary text-white rounded-lg font-bold text-sm"
              >
                Hoàn tất
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ProjectorScreen(props: { params: Promise<{ session_id: string }> }) {
  return (
    <Suspense fallback={<div className="p-8 text-center text-neu-gray">Đang khởi động màn hình máy chiếu...</div>}>
      <ProjectorContent {...props} />
    </Suspense>
  );
}


