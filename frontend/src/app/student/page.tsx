"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function StudentHomePage() {
  const [pinCode, setPinCode] = useState("");
  const router = useRouter();

  const handlePinSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (pinCode.length === 6) {
      router.push(`/student/${pinCode}`);
    } else {
      alert("Mã PIN phải bao gồm 6 chữ số");
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-12rem)] px-4">
      <div className="w-full max-w-sm bg-white border border-neu-border rounded-xl p-8 shadow-sm text-center">
        <h1 className="text-2xl font-bold text-neu-primary mb-2">Điểm danh Sinh viên</h1>
        <p className="text-neu-gray text-sm mb-8">
          Sử dụng ứng dụng Camera để quét mã QR trên màn chiếu, hoặc nhập mã PIN 6 số thủ công bên dưới.
        </p>

        <form onSubmit={handlePinSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-bold text-neu-text mb-2 text-left uppercase tracking-wider">
              Nhập mã PIN
            </label>
            <input 
              type="text" 
              maxLength={6}
              value={pinCode}
              onChange={(e) => setPinCode(e.target.value.replace(/[^0-9]/g, ""))}
              placeholder="123456" 
              className="w-full text-center text-4xl font-black tracking-[0.2em] px-4 py-4 border-2 border-neu-border rounded-lg focus:outline-none focus:border-neu-primary transition-colors text-neu-text"
            />
          </div>
          
          <button 
            type="submit" 
            disabled={pinCode.length !== 6}
            className="w-full bg-neu-primary hover:bg-neu-secondary disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-bold py-4 rounded-lg transition-colors text-lg shadow-sm"
          >
            Tiếp tục
          </button>
        </form>

        <div className="mt-8 pt-6 border-t border-neu-border">
          <p className="text-sm text-neu-gray mb-3">Dành cho thiết bị cá nhân của bạn</p>
          <a href="/login" className="text-neu-primary font-medium hover:underline">
            Đăng nhập bằng Microsoft 365
          </a>
        </div>
      </div>
    </div>
  );
}

