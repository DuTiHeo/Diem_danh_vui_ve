import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "NEU Attendance System",
  description: "Hệ thống điểm danh thông minh bằng QR & GPS",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi">
      <body className="antialiased min-h-screen flex flex-col bg-neu-bg text-neu-text">
        <header className="bg-white border-b border-neu-border px-6 py-4 flex justify-between items-center sticky top-0 z-10 shadow-sm">
          <div className="flex items-center gap-4">
            {/* Logo Text Instead of Icon for clean UI */}
            <div className="font-bold text-xl text-neu-primary tracking-tight">
              NEU <span className="font-normal text-neu-gray">Attendance</span>
            </div>
          </div>
          <nav className="text-sm font-medium text-neu-gray flex gap-4">
            <Link href="/" className="hover:text-neu-primary transition-colors">Bảng điều khiển</Link>
            <Link href="/student" className="hover:text-neu-primary transition-colors">Sinh viên điểm danh</Link>
            <Link href="/login" className="hover:text-neu-primary transition-colors">Đăng nhập</Link>
          </nav>
        </header>
        <main className="flex-1 max-w-7xl w-full mx-auto p-6">
          {children}
        </main>
        <footer className="py-6 text-center text-xs text-neu-gray border-t border-neu-border mt-auto">
          &copy; 2026 Đại học Kinh tế Quốc Dân. Hệ thống điểm danh nội bộ.
        </footer>
      </body>
    </html>
  );
}
