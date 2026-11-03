export function getApiBaseUrl(): string {
  if (typeof window !== "undefined") {
    const envUrl = process.env.NEXT_PUBLIC_API_URL;
    if (
      envUrl &&
      !envUrl.includes("localhost") &&
      !envUrl.includes("127.0.0.1") &&
      !envUrl.includes("192.168.") &&
      !envUrl.includes("172.")
    ) {
      return envUrl;
    }

    const host = window.location.hostname;
    const protocol = window.location.protocol || "http:";
    const port = window.location.port;

    // Khi chạy qua Caddy Reverse Proxy (port 80 / 443 / rỗng), dùng cùng origin
    if (port === "" || port === "80" || port === "443") {
      return `${protocol}//${host}`;
    }

    // Khi chạy dev server Next.js (:3000), trỏ sang Backend (:8000)
    if (host) {
      return `${protocol}//${host}:8000`;
    }
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

export const API_BASE_URL =
  typeof window !== "undefined"
    ? getApiBaseUrl()
    : process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface UserProfile {
  id?: string;
  email: string;
  full_name?: string | null;
  role: "LECTURER" | "STUDENT" | "ADMIN" | string;
  student_code?: string | null;
  admin_class?: string | null;
  date_of_birth?: string | null;
}

export interface PinSessionInfo {
  session_id: string;
  pin_code: string;
  course_name: string;
  class_section?: string | null;
  session_number: number;
  room_name: string;
  building_name?: string | null;
  require_audio?: boolean;
  audio_freq_hz?: number | null;
  expires_in_seconds: number;
}

export interface StudentCourseAttendance {
  course_id: string;
  course_code?: string;
  course_name: string;
  class_section?: string;
  room_name?: string;
  semester?: string | null;
  attended_count: number;
  absent_count: number;
  pending_approval_count?: number;
  total_sessions: number;
  opened_sessions?: number;
}

export interface MyAttendanceResponse {
  student_code?: string | null;
  full_name?: string | null;
  admin_class?: string | null;
  date_of_birth?: string | null;
  student?: {
    id: string;
    student_code: string;
    full_name: string;
    last_name?: string | null;
    first_name?: string | null;
    date_of_birth?: string | null;
    admin_class?: string | null;
  } | null;
  courses: StudentCourseAttendance[];
}

export interface BuildingInfo {
  id: string;
  code: string;
  name: string;
  latitude: number;
  longitude: number;
  radius_meters: number;
  is_active?: boolean;
}

export interface UploadExcelResponse {
  id: string;
  course_name: string;
  room_name: string;
  total_students: number;
  total_sessions: number;
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("neu_access_token");
}

export function setToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem("neu_access_token", token);
  }
}

export function getUser(): UserProfile | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("neu_user");
  if (!raw) return null;
  try {
    return JSON.parse(raw) as UserProfile;
  } catch {
    return null;
  }
}

export function setUser(user: UserProfile): void {
  if (typeof window !== "undefined") {
    localStorage.setItem("neu_user", JSON.stringify(user));
  }
}

export function removeAuth(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem("neu_access_token");
    localStorage.removeItem("neu_user");
  }
}

export async function fetchApi<T = unknown>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };

  if (token && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}/api/v1${cleanEndpoint}`;

  let res: Response;
  try {
    res = await fetch(url, {
      ...options,
      headers,
    });
  } catch (err) {
    // Fallback sang cổng 80 (Caddy Reverse Proxy) nếu :8000 không mở trực tiếp
    if (typeof window !== "undefined" && baseUrl.endsWith(":8000")) {
      const fallbackBase = `${window.location.protocol || "http:"}//${window.location.hostname}`;
      res = await fetch(`${fallbackBase}/api/v1${cleanEndpoint}`, {
        ...options,
        headers,
      });
    } else {
      throw err;
    }
  }

  if (!res.ok) {
    let errorDetail = `Lỗi hệ thống (${res.status})`;
    try {
      const errJson = await res.json();
      if (typeof errJson.detail === "string") {
        errorDetail = errJson.detail;
      } else if (Array.isArray(errJson.detail) && errJson.detail[0]?.msg) {
        errorDetail = errJson.detail[0].msg;
      }
    } catch {
      // not json
    }
    throw new Error(errorDetail);
  }

  return res.json() as Promise<T>;
}

/**
 * UC15: Kiểm tra mã PIN 6 chữ số khả dụng (TTL 60s)
 */
export async function checkPinSession(pinCode: string): Promise<PinSessionInfo> {
  const cleanedPin = pinCode.trim();
  return fetchApi<PinSessionInfo>(`/sessions/qr/${cleanedPin}`);
}

/**
 * UC18: Lấy lịch sử chuyên cần cá nhân của Sinh viên đang đăng nhập
 */
export async function fetchMyAttendance(): Promise<MyAttendanceResponse> {
  const raw = await fetchApi<MyAttendanceResponse | StudentCourseAttendance[]>(
    "/auth/my-attendance"
  );
  if (Array.isArray(raw)) {
    const u = getUser();
    return {
      student_code: u?.student_code || null,
      full_name: u?.full_name || null,
      admin_class: u?.admin_class || null,
      date_of_birth: u?.date_of_birth || null,
      courses: raw,
    };
  }
  return {
    student_code: raw.student_code ?? raw.student?.student_code ?? null,
    full_name: raw.full_name ?? raw.student?.full_name ?? null,
    admin_class: raw.admin_class ?? raw.student?.admin_class ?? null,
    date_of_birth: raw.date_of_birth ?? raw.student?.date_of_birth ?? null,
    student: raw.student ?? null,
    courses: Array.isArray(raw.courses) ? raw.courses : [],
  };
}

/**
 * UC19: Lấy danh sách các Tòa nhà giảng đường NEU (Geofence Vòng 1)
 */
export async function fetchBuildings(): Promise<BuildingInfo[]> {
  return fetchApi<BuildingInfo[]>("/buildings/");
}

export async function uploadExcelFile(file: File): Promise<UploadExcelResponse> {
  const token = getToken();
  const formData = new FormData();
  formData.append("file", file);

  const headers: Record<string, string> = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const url = `${getApiBaseUrl()}/api/v1/courses/upload`;
  const res = await fetch(url, {
    method: "POST",
    headers,
    body: formData,
  });

  if (!res.ok) {
    let errorDetail = `Lỗi tải file (${res.status})`;
    try {
      const errJson = await res.json();
      if (errJson.detail) errorDetail = errJson.detail;
    } catch {}
    throw new Error(errorDetail);
  }

  return res.json();
}
