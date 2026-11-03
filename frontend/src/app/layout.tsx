import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "NEU Attendance - Hệ Thống Điểm Danh Thông Minh",
  description:
    "Nền tảng quản lý lớp học phần & điểm danh xác thực 2 vòng (GPS + Sóng siêu âm) trường Đại học Kinh tế Quốc dân (NEU)",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi">
      <body className="antialiased min-h-screen flex flex-col bg-neu-bg text-neu-text">
        <header className="bg-neu-primary text-white border-b border-blue-900 px-6 py-3.5 flex flex-wrap justify-between items-center gap-4 sticky top-0 z-20 shadow-md">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 rounded-lg bg-white text-neu-primary font-black flex items-center justify-center text-sm shadow-xs group-hover:scale-105 transition-transform">
              NEU
            </div>
            <div>
              <div className="font-bold text-lg tracking-tight leading-none text-white">
                NEU <span className="font-normal text-sky-200">Attendance</span>
              </div>
              <div className="text-[11px] text-sky-200/90 hidden sm:block mt-0.5">
                Đại học Kinh tế Quốc dân • Smart Classroom
              </div>
            </div>
          </Link>

          <nav className="text-sm font-medium flex items-center gap-2 sm:gap-5">
            <Link
              href="/"
              className="px-3 py-1.5 rounded-md text-sky-100 hover:text-white hover:bg-white/10 transition-colors"
            >
              Trang chủ
            </Link>
            <Link
              href="/dashboard"
              className="px-3 py-1.5 rounded-md text-sky-100 hover:text-white hover:bg-white/10 transition-colors"
            >
              Quản lý lớp học
            </Link>
            <Link
              href="/student"
              className="px-3 py-1.5 rounded-md text-sky-100 hover:text-white hover:bg-white/10 transition-colors"
            >
              Điểm danh PIN
            </Link>
            <Link
              href="/login"
              className="px-3.5 py-1.5 rounded-md bg-white text-neu-primary font-bold hover:bg-sky-50 transition-colors shadow-xs"
            >
              Đăng nhập
            </Link>
          </nav>
        </header>

        <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6">
          {children}
        </main>

        <footer className="py-5 text-center text-xs text-neu-gray border-t border-neu-border bg-white mt-auto">
          &copy; 2026 Trường Đại học Kinh tế Quốc dân (NEU) • Hệ thống Điểm danh Lớp học Thông minh 2 Vòng (GPS &amp; Cận Siêu Âm).
        </footer>
      </body>
    </html>
  );
}
