"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { fetchApi, setToken, setUser, UserProfile } from "@/lib/api";

function LoginContent() {
  const [role, setRole] = useState<"LECTURER" | "STUDENT" | "ADMIN">("LECTURER");
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectUrl = searchParams?.get("redirect") || null;

  const validateNeuDomain = (inputEmail: string): string | null => {
    const cleaned = inputEmail.trim().toLowerCase();
    if (!cleaned.endsWith("@neu.edu.vn") && !cleaned.endsWith("@st.neu.edu.vn")) {
      return "EX-01: Hệ thống chỉ cho phép đăng nhập bằng tài khoản email thuộc tên miền @neu.edu.vn (Giảng viên/Quản trị) hoặc @st.neu.edu.vn (Sinh viên).";
    }
    return null;
  };

  const handleLogin = async (
    loginEmail: string,
    loginRole: "LECTURER" | "STUDENT" | "ADMIN",
    name?: string
  ) => {
    setErrorMsg(null);
    const domainErr = validateNeuDomain(loginEmail);
    if (domainErr) {
      setErrorMsg(domainErr);
      return;
    }

    setIsLoading(true);
    try {
      const data = await fetchApi<{
        access_token: string;
        role?: string;
        user?: UserProfile;
      }>("/auth/mock-login", {
        method: "POST",
        body: JSON.stringify({
          email: loginEmail.trim(),
          role: loginRole,
          full_name: name?.trim() || loginEmail.split("@")[0],
        }),
      });

      setToken(data.access_token);

      const finalRole = data.user?.role || data.role || loginRole;
      const userObj: UserProfile = data.user || {
        email: loginEmail.trim(),
        role: finalRole,
        full_name: name?.trim() || loginEmail.split("@")[0],
      };

      // Đồng bộ thêm từ /auth/me nếu có
      try {
        const me = await fetchApi<UserProfile>("/auth/me");
        Object.assign(userObj, me);
      } catch {
        // Bỏ qua nếu không cần thiết
      }

      setUser(userObj);

      if (redirectUrl) {
        router.push(redirectUrl);
      } else if (finalRole === "LECTURER" || finalRole === "ADMIN") {
        router.push("/dashboard");
      } else {
        router.push("/");
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
    <div className="flex items-center justify-center min-h-[calc(100vh-12rem)] py-6">
      <div className="w-full max-w-md bg-white border border-neu-border rounded-2xl p-8 shadow-sm">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-neu-primary text-white font-black text-lg mb-3 shadow-xs">
            NEU
          </div>
          <h1 className="text-2xl font-bold text-neu-primary mb-1">
            Đăng nhập Hệ thống
          </h1>
          <p className="text-sm text-neu-gray">
            Sử dụng tài khoản Microsoft 365 trường Đại học Kinh tế Quốc dân
          </p>
        </div>

        {errorMsg && (
          <div
            role="alert"
            className="bg-red-50 border border-red-200 text-red-700 p-3.5 rounded-xl text-xs font-medium mb-5 flex items-start gap-2"
          >
            <span className="text-base leading-none">⚠️</span>
            <span>{errorMsg}</span>
          </div>
        )}

        <button
          type="button"
          onClick={() =>
            handleLogin("lecturer.neu@neu.edu.vn", "LECTURER", "Giảng viên NEU")
          }
          disabled={isLoading}
          className="w-full flex items-center justify-center gap-3 bg-neu-primary hover:bg-neu-secondary text-white font-bold py-3.5 px-4 rounded-xl transition-colors mb-6 shadow-xs cursor-pointer"
        >
          <svg className="w-5 h-5" viewBox="0 0 21 21">
            <path fill="#f25022" d="M1 1h9v9H1z" />
            <path fill="#7fba00" d="M11 1h9v9h-9z" />
            <path fill="#00a4ef" d="M1 11h9v9H1z" />
            <path fill="#ffb900" d="M11 11h9v9h-9z" />
          </svg>
          <span>Đăng nhập với Microsoft 365 (Entra ID)</span>
        </button>

        <div className="relative flex items-center py-3 mb-4">
          <div className="flex-grow border-t border-neu-border"></div>
          <span className="flex-shrink-0 mx-3 text-neu-gray text-[11px] uppercase tracking-wider font-bold">
            Chế độ Thử nghiệm (Dev Mock Auth)
          </span>
          <div className="flex-grow border-t border-neu-border"></div>
        </div>

        {/* 3 Nút đăng nhập nhanh 1-click */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 mb-6">
          <button
            type="button"
            disabled={isLoading}
            onClick={() =>
              handleLogin("gv_test@neu.edu.vn", "LECTURER", "Nguyễn Trọng Hưng")
            }
            className="text-xs py-2.5 px-2 bg-blue-50 hover:bg-blue-100 text-neu-primary font-bold rounded-lg border border-blue-200 transition-colors cursor-pointer"
          >
            👨‍🏫 Giảng viên
            <span className="block text-[10px] font-normal text-neu-gray truncate">
              gv_test@neu.edu.vn
            </span>
          </button>

          <button
            type="button"
            disabled={isLoading}
            onClick={() =>
              handleLogin(
                "11242145@st.neu.edu.vn",
                "STUDENT",
                "Bùi Phương Anh"
              )
            }
            className="text-xs py-2.5 px-2 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 font-bold rounded-lg border border-emerald-200 transition-colors cursor-pointer"
          >
            🎓 Sinh viên
            <span className="block text-[10px] font-normal text-emerald-700 truncate">
              11242145@st.neu.edu.vn
            </span>
          </button>

          <button
            type="button"
            disabled={isLoading}
            onClick={() =>
              handleLogin("admin@neu.edu.vn", "ADMIN", "Quản trị viên NEU")
            }
            className="text-xs py-2.5 px-2 bg-amber-50 hover:bg-amber-100 text-amber-900 font-bold rounded-lg border border-amber-200 transition-colors cursor-pointer"
          >
            🛡️ Quản trị
            <span className="block text-[10px] font-normal text-amber-800 truncate">
              admin@neu.edu.vn
            </span>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-neu-text mb-1">
              Email trường (@neu.edu.vn / @st.neu.edu.vn)
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                if (errorMsg) setErrorMsg(null);
              }}
              placeholder="gv_test@neu.edu.vn hoặc 11242145@st.neu.edu.vn"
              className="w-full px-3.5 py-2.5 border border-neu-border rounded-lg text-sm focus:outline-none focus:border-neu-primary focus:ring-1 focus:ring-neu-primary"
            />
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-neu-text mb-1">
              Họ và tên
            </label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Nguyễn Văn A"
              className="w-full px-3.5 py-2.5 border border-neu-border rounded-lg text-sm focus:outline-none focus:border-neu-primary focus:ring-1 focus:ring-neu-primary"
            />
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-neu-text mb-1">
              Vai trò
            </label>
            <select
              value={role}
              onChange={(e) =>
                setRole(e.target.value as "LECTURER" | "STUDENT" | "ADMIN")
              }
              className="w-full px-3.5 py-2.5 border border-neu-border rounded-lg text-sm focus:outline-none focus:border-neu-primary focus:ring-1 focus:ring-neu-primary bg-white"
            >
              <option value="LECTURER">Giảng viên (@neu.edu.vn)</option>
              <option value="STUDENT">Sinh viên (@st.neu.edu.vn)</option>
              <option value="ADMIN">Quản trị viên (@neu.edu.vn)</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={isLoading || !email}
            className="w-full bg-neu-primary hover:bg-neu-secondary disabled:bg-slate-300 text-white font-bold py-3 rounded-xl transition-colors mt-2 cursor-pointer"
          >
            {isLoading ? "Đang xác thực..." : "Đăng nhập giả lập"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="p-8 text-center text-neu-gray">
          Đang tải trang đăng nhập...
        </div>
      }
    >
      <LoginContent />
    </Suspense>
  );
}
