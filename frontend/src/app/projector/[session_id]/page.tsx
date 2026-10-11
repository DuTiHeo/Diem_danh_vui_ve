"use client";

import { useState, useEffect } from "react";

export default function ProjectorScreen({ params }: { params: { session_id: string } }) {
  const [timeLeft, setTimeLeft] = useState(60);
  const [pinCode, setPinCode] = useState("123456");
  const [students, setStudents] = useState([
    { id: "11243929", name: "Dương Tiến Hào", status: "PENDING", time: null },
    { id: "11230001", name: "Nguyễn Văn A", status: "ATTENDED", time: "08:15:22" },
  ]);

  // Giả lập đếm ngược
  useEffect(() => {
    if (timeLeft > 0) {
      const timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [timeLeft]);

  const progressPercentage = (timeLeft / 60) * 100;
  const isWarning = timeLeft <= 15;

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Header Buổi học */}
      <div className="flex justify-between items-end mb-6 border-b border-neu-border pb-4">
        <div>
          <h1 className="text-3xl font-bold text-neu-primary">Phân tích tài chính - Buổi 1</h1>
          <p className="text-neu-gray text-lg mt-1">Phòng B-301 • Giảng viên: Nguyễn Trọng Hưng</p>
        </div>
        <div className="flex gap-4">
          <button className="px-6 py-2 bg-neu-bg hover:bg-gray-200 text-neu-text rounded font-medium border border-neu-border">
            Can thiệp thủ công
          </button>
          <button className="px-6 py-2 bg-neu-red hover:bg-red-600 text-white rounded font-bold shadow-sm">
            Kết thúc phiên
          </button>
        </div>
      </div>

      {/* Layout 2 cột */}
      <div className="flex-1 flex gap-8">
        
        {/* Cột trái: QR Code & Mã PIN (Máy chiếu) */}
        <div className="flex-1 bg-white border border-neu-border rounded-xl flex flex-col items-center justify-center p-8 shadow-sm relative overflow-hidden">
          {/* Thanh tiến trình thời gian ở trên cùng */}
          <div className="absolute top-0 left-0 w-full h-2 bg-gray-100">
            <div 
              className={`h-full transition-all duration-1000 ease-linear ${isWarning ? 'bg-neu-red' : 'bg-neu-secondary'}`}
              style={{ width: `${progressPercentage}%` }}
            ></div>
          </div>

          <h2 className="text-2xl font-bold text-neu-text mb-6">Quét mã để điểm danh</h2>
          
          <div className={`p-4 rounded-xl border-4 ${isWarning ? 'border-neu-red' : 'border-neu-primary'} mb-8`}>
            {/* Giả lập hình QR */}
            <div className="w-64 h-64 bg-gray-200 flex items-center justify-center">
              [MÃ QR CODE]
            </div>
          </div>

          <div className="text-center">
            <p className="text-neu-gray uppercase tracking-widest text-sm font-bold mb-2">Hoặc nhập mã PIN tại trang chủ</p>
            <div className="text-6xl font-black text-neu-text tracking-[0.2em]">{pinCode}</div>
          </div>

          {timeLeft === 0 && (
            <div className="absolute inset-0 bg-white/90 backdrop-blur-sm flex flex-col items-center justify-center">
              <p className="text-2xl font-bold text-neu-red mb-4">Mã đã hết hạn!</p>
              <button 
                onClick={() => { setTimeLeft(60); setPinCode("654321"); }}
                className="px-8 py-3 bg-neu-primary text-white rounded-lg text-lg font-bold shadow-md hover:bg-neu-secondary"
              >
                Tạo mã mới ngay
              </button>
            </div>
          )}
          
          <div className="absolute bottom-6 right-6">
            <div className={`text-3xl font-bold ${isWarning ? 'text-neu-red animate-pulse' : 'text-neu-gray'}`}>
              {timeLeft}s
            </div>
          </div>
        </div>

        {/* Cột phải: Danh sách Realtime */}
        <div className="w-[450px] bg-white border border-neu-border rounded-xl flex flex-col shadow-sm">
          <div className="p-4 border-b border-neu-border bg-neu-bg rounded-t-xl flex justify-between items-center">
            <h3 className="font-bold text-neu-text text-lg">Trạng thái lớp học</h3>
            <div className="text-neu-primary font-bold bg-blue-50 px-3 py-1 rounded-full">
              1 / 50 Có mặt
            </div>
          </div>
          
          <div className="flex-1 overflow-y-auto p-2">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="text-xs text-neu-gray uppercase tracking-wider border-b border-neu-border">
                  <th className="p-3 font-medium">Sinh viên</th>
                  <th className="p-3 font-medium text-right">Trạng thái</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neu-bg">
                {students.map((st) => (
                  <tr key={st.id} className="hover:bg-gray-50 transition-colors">
                    <td className="p-3">
                      <div className="font-medium text-neu-text">{st.name}</div>
                      <div className="text-xs text-neu-gray">{st.id}</div>
                    </td>
                    <td className="p-3 text-right">
                      {st.status === "ATTENDED" ? (
                        <div>
                          <span className="inline-block px-2 py-1 bg-green-100 text-green-700 text-xs font-bold rounded">CÓ MẶT</span>
                          <div className="text-[10px] text-neu-gray mt-1">{st.time}</div>
                        </div>
                      ) : (
                        <span className="inline-block px-2 py-1 bg-gray-100 text-neu-gray text-xs font-medium rounded">CHỜ QUÉT</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

