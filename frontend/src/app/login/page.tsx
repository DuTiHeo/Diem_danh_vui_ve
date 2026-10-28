"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { fetchApi, setToken, setUser } from "@/lib/api";

export default function LoginPage() {
  const [role, setRole] = useState("LECTURER");
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const router = useRouter();

  const handleLogin = async (loginEmail: string, loginRole: string, name?: string) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const data = await fetchApi<{ access_token: string }>("/auth/mock-login", {
        method: "POST",
        body: JSON.stringify({
          email: loginEmail,
          role: loginRole,
          full_name: name || loginEmail.split("@")[0],
        }),
      });

      setToken(data.access_token);
      setUser({ email: loginEmail, role: loginRole, full_name: name });

      if (loginRole === "LECTURER") {
        router.push("/");
      } else {
        router.push("/student");
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Đăng nhập thất bại";
      setErrorMsg(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleLogin(email, role, fullName);
  };

  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-12rem)]">
      <div className="w-full max-w-md bg-white border border-neu-border rounded-xl p-8 shadow-sm">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-neu-primary mb-2">Đăng nhập hệ thống</h1>
          <p className="text-neu-gray">Sử dụng tài khoản Microsoft 365 của trường</p>
        </div>

        {errorMsg && (
          <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg text-sm mb-4">
            {errorMsg}
          </div>
        )}

        <button 
          onClick={() => handleLogin("lecturer.neu@neu.edu.vn", "LECTURER", "Giảng viên NEU")}
          disabled={isLoading}
          className="w-full flex items-center justify-center gap-3 bg-white border border-neu-border text-neu-text font-medium py-3 px-4 rounded hover:bg-gray-50 transition-colors mb-6 shadow-xs"
        >
          <svg className="w-5 h-5" viewBox="0 0 21 21">
            <path fill="#f25022" d="M1 1h9v9H1z"/>
            <path fill="#7fba00" d="M11 1h9v9h-9z"/>
            <path fill="#00a4ef" d="M1 11h9v9H1z"/>
            <path fill="#ffb900" d="M11 11h9v9h-9z"/>
          </svg>
          Đăng nhập với Microsoft (Entra ID)
        </button>

        <div className="relative flex items-center py-4">
          <div className="flex-grow border-t border-neu-border"></div>
          <span className="flex-shrink-0 mx-4 text-neu-gray text-xs uppercase tracking-wider font-bold">Chế độ Thử nghiệm (Mock Auth)</span>
          <div className="flex-grow border-t border-neu-border"></div>
        </div>

        {/* Quick login shortcut buttons */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          <button
            type="button"
            disabled={isLoading}
            onClick={() => handleLogin("gv_test@neu.edu.vn", "LECTURER", "Nguyễn Trọng Hưng")}
            className="text-xs py-2 px-3 bg-blue-50 hover:bg-blue-100 text-neu-primary font-medium rounded border border-blue-200 transition-colors"
          >
            👨‍🏫 Vào vai Giảng viên
          </button>
          <button
            type="button"
            disabled={isLoading}
            onClick={() => handleLogin("11242145@st.neu.edu.vn", "STUDENT", "Bùi Phương Anh")}
            className="text-xs py-2 px-3 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 font-medium rounded border border-emerald-200 transition-colors"
          >
            🎓 Vào vai Sinh viên
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-neu-text mb-1">Email thử nghiệm</label>
            <input 
              type="email" 
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="nhap_email@neu.edu.vn" 
              className="w-full px-4 py-2 border border-neu-border rounded focus:outline-none focus:border-neu-primary focus:ring-1 focus:ring-neu-primary"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-neu-text mb-1">Họ và tên</label>
            <input 
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Nguyễn Văn A" 
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
          <button 
            type="submit" 
            disabled={isLoading || !email}
            className="w-full bg-neu-primary hover:bg-neu-secondary disabled:bg-gray-300 text-white font-medium py-2.5 rounded transition-colors mt-2"
          >
            {isLoading ? "Đang xử lý..." : "Đăng nhập giả lập"}
          </button>
        </form>
      </div>
    </div>
  );
}

