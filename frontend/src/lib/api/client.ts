import axios, { AxiosInstance, AxiosError } from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
const AUTH_CSRF_COOKIE_NAME = "tcareer_csrf";

let accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

export function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const value = document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`))
    ?.split("=")
    .slice(1)
    .join("=");
  return value ? decodeURIComponent(value) : null;
}

export function getAuthCsrfHeader(): Record<string, string> {
  const csrfToken = getCookie(AUTH_CSRF_COOKIE_NAME);
  return csrfToken ? { "X-CSRFToken": csrfToken } : {};
}

const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

api.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: string) => void;
  reject: (error: unknown) => void;
}> = [];

function processQueue(error: unknown, token: string | null = null) {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else {
      resolve(token!);
    }
  });
  failedQueue = [];
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as typeof error.config & { _retry?: boolean };

    if (error.response?.status === 401 && !original?._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          original.headers!.Authorization = `Bearer ${token}`;
          return api(original);
        });
      }

      original._retry = true;
      isRefreshing = true;

      try {
        const response = await axios.post(
          `${API_URL}/auth/token/refresh/`,
          {},
          { withCredentials: true, headers: getAuthCsrfHeader() }
        );
        const newToken = response.data.data?.access || response.data.access;
        setAccessToken(newToken);
        processQueue(null, newToken);
        original.headers!.Authorization = `Bearer ${newToken}`;
        return api(original);
      } catch (refreshError) {
        processQueue(refreshError, null);
        setAccessToken(null);
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default api;
