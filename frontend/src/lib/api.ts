export function getApiBaseUrl(): string {
  if (typeof window !== "undefined") {
    const host = window.location.hostname;
    if (host) {
      if (host === "localhost" || host === "127.0.0.1") {
        return process.env.NEXT_PUBLIC_API_URL || "http://192.168.1.131:8000";
      }
      return `http://${host}:8000`;
    }
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://192.168.1.131:8000";
}

export const API_BASE_URL = typeof window !== "undefined" && window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1"
  ? `http://${window.location.hostname}:8000`
  : (process.env.NEXT_PUBLIC_API_URL || "http://192.168.1.131:8000");

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("neu_access_token");
}

export function setToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem("neu_access_token", token);
  }
}

export function getUser(): { email: string; role: string; full_name?: string } | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("neu_user");
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function setUser(user: { email: string; role: string; full_name?: string }): void {
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

export interface UploadExcelResponse {
  id: string;
  course_name: string;
  room_name: string;
  total_students: number;
  total_sessions: number;
}

export async function fetchApi<T = unknown>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> || {}),
  };

  if (token && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}/api/v1${cleanEndpoint}`;

  const res = await fetch(url, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let errorDetail = `Lỗi hệ thống (${res.status})`;
    try {
      const errJson = await res.json();
      if (errJson.detail) {
        errorDetail = errJson.detail;
      }
    } catch {
      // not json
    }
    throw new Error(errorDetail);
  }

  return res.json() as Promise<T>;
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
