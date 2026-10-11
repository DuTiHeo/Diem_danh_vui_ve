"use client";

import { useState } from "react";

export default function LoginPage() {
  const [role, setRole] = useState("LECTURER");
  const [email, setEmail] = useState("");

  const handleMockLogin = (e: React.FormEvent) => {
    e.preventDefault();
    alert(`Mock login as ${role} with email ${email}`);
    if (role === "LECTURER") {
      window.location.href = "/";
    } else {
      window.location.href = "/student";
    }
  };

  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-12rem)]">
      <div className="w-full max-w-md bg-white border border-neu-border rounded-xl p-8 shadow-sm">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-neu-primary mb-2">Đăng nhập hệ thống</h1>
          <p className="text-neu-gray">Sử dụng tài khoản Microsoft 365 của trường</p>
        </div>

        <button className="w-full flex items-center justify-center gap-3 bg-white border border-neu-border text-neu-text font-medium py-3 px-4 rounded hover:bg-gray-50 transition-colors mb-8">
          <svg className="w-5 h-5" viewBox="0 0 21 21">
            <path fill="#f25022" d="M1 1h9v9H1z"/>
            <path fill="#7fba00" d="M11 1h9v9h-9z"/>
            <path fill="#00a4ef" d="M1 11h9v9H1z"/>
            <path fill="#ffb900" d="M11 11h9v9h-9z"/>
          </svg>
          Đăng nhập với Microsoft
        </button>

        <div className="relative flex items-center py-5">
          <div className="flex-grow border-t border-neu-border"></div>
          <span className="flex-shrink-0 mx-4 text-neu-gray text-xs uppercase tracking-wider font-bold">Chế độ Thử nghiệm (Mock Auth)</span>
          <div className="flex-grow border-t border-neu-border"></div>
        </div>

        <form onSubmit={handleMockLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-neu-text mb-1">Email thử nghiệm</label>
            <input 
              type="email" 
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="11243929@st.neu.edu.vn" 
              className="w-full px-4 py-2 border border-neu-border rounded focus:outline-none focus:border-neu-primary focus:ring-1 focus:ring-neu-primary"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-neu-text mb-1">Vai trò</label>
            <select 
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full px-4 py-2 border border-neu-border rounded focus:outline-none focus:border-neu-primary focus:ring-1 focus:ring-neu-primary bg-white"
            >
              <option value="LECTURER">Giảng viên (@neu.edu.vn)</option>
              <option value="STUDENT">Sinh viên (@st.neu.edu.vn)</option>
            </select>
          </div>
          <button type="submit" className="w-full bg-neu-primary hover:bg-neu-secondary text-white font-medium py-2.5 rounded transition-colors mt-2">
            Đăng nhập giả lập
          </button>
        </form>
      </div>
    </div>
  );
}

