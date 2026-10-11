"use client";

import { useState, useEffect } from "react";

export default function StudentAttendancePage({ params }: { params: { pin_code: string } }) {
  const [studentCode, setStudentCode] = useState("");
  const [fullName, setFullName] = useState("");
  const [location, setLocation] = useState<{ lat: number; lng: number; acc: number } | null>(null);
  const [geoError, setGeoError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);

  useEffect(() => {
    // Yêu cầu quyền GPS ngay khi vào trang
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation({
            lat: position.coords.latitude,
            lng: position.coords.longitude,
            acc: position.coords.accuracy
          });
          setGeoError(null);
        },
        (error) => {
          let errorMsg = "Lỗi xác định vị trí.";
          if (error.code === 1) errorMsg = "Vui lòng cho phép trình duyệt truy cập Vị trí (GPS) để điểm danh.";
          if (error.code === 2) errorMsg = "Không thể lấy được tọa độ GPS hiện tại.";
          setGeoError(errorMsg);
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
      );
    } else {
      setGeoError("Trình duyệt của bạn không hỗ trợ định vị GPS.");
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!location) {
      alert("Vui lòng đợi hệ thống lấy tọa độ GPS hoặc cấp quyền vị trí.");
      return;
    }

    setIsSubmitting(true);
    // Giả lập call API
    setTimeout(() => {
      setIsSubmitting(false);
      // Giả lập thành công
      setResult({ success: true, message: "Điểm danh thành công! Bạn có thể đóng trình duyệt." });
    }, 1500);
  };

  if (result) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[calc(100vh-12rem)] px-4 animate-in zoom-in duration-300">
        <div className={`w-full max-w-sm border rounded-xl p-8 shadow-sm text-center ${result.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
          <div className={`text-5xl mb-4 ${result.success ? 'text-green-500' : 'text-red-500'}`}>
            {result.success ? "✓" : "✕"}
          </div>
          <h2 className={`text-xl font-bold mb-2 ${result.success ? 'text-green-800' : 'text-red-800'}`}>
            {result.message}
          </h2>
          <p className="text-sm text-neu-gray mt-4">Phiên bản lưu trữ: {new Date().toLocaleTimeString()}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-12rem)] px-4">
      <div className="w-full max-w-sm bg-white border border-neu-border rounded-xl p-6 shadow-sm">
        <div className="border-b border-neu-border pb-4 mb-6">
          <div className="inline-block bg-neu-bg text-neu-primary font-bold px-3 py-1 rounded mb-2 text-sm tracking-widest">
            MÃ LỚP: {params.pin_code}
          </div>
          <h1 className="text-xl font-bold text-neu-text">Xác nhận có mặt</h1>
          <p className="text-neu-gray text-sm mt-1">Buổi học đang diễn ra. Vui lòng điền thông tin.</p>
        </div>

        {geoError && (
          <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg mb-6 text-sm">
            <span className="font-bold block mb-1">Cảnh báo GPS:</span>
            {geoError}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-bold text-neu-text mb-1 uppercase text-xs tracking-wider">Họ và tên chuẩn</label>
            <input 
              type="text" 
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="VD: Nguyễn Văn A" 
              className="w-full px-4 py-3 border border-neu-border rounded focus:outline-none focus:border-neu-primary focus:ring-1 focus:ring-neu-primary text-neu-text"
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-neu-text mb-1 uppercase text-xs tracking-wider">Mã sinh viên</label>
            <input 
              type="text" 
              required
              value={studentCode}
              onChange={(e) => setStudentCode(e.target.value.replace(/[^0-9]/g, ""))}
              placeholder="VD: 11243929" 
              maxLength={8}
              className="w-full px-4 py-3 border border-neu-border rounded focus:outline-none focus:border-neu-primary focus:ring-1 focus:ring-neu-primary text-neu-text tracking-widest"
            />
          </div>

          <div className="bg-neu-bg p-3 rounded border border-neu-border flex justify-between items-center text-sm">
            <span className="text-neu-gray">Trạng thái GPS</span>
            {location ? (
              <span className="text-green-600 font-bold">Đã lấy tọa độ ({Math.round(location.acc)}m)</span>
            ) : (
              <span className="text-yellow-600 font-bold animate-pulse">Đang định vị...</span>
            )}
          </div>

          <button 
            type="submit" 
            disabled={!location || isSubmitting || studentCode.length < 8 || fullName.length < 3}
            className="w-full bg-neu-primary hover:bg-neu-secondary disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-bold py-3.5 rounded-lg transition-colors shadow-sm"
          >
            {isSubmitting ? "Đang gửi..." : "Điểm danh ngay"}
          </button>
        </form>
      </div>
    </div>
  );
}

