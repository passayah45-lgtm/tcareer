import api, { getAuthCsrfHeader } from "./client";
import type { AuthResponse, User, UserRole } from "@/types/user.types";
import type { ApiResponse } from "@/types/api.types";

export type PublicRegistrationRole = Extract<UserRole, "student" | "instructor" | "mentor" | "recruiter">;

export interface RegisterPayload {
  email: string;
  password: string;
  password_confirm: string;
  full_name: string;
  role?: PublicRegistrationRole;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export async function register(payload: RegisterPayload): Promise<AuthResponse> {
  const res = await api.post<ApiResponse<AuthResponse>>("/auth/register/", payload);
  return res.data.data;
}

export async function login(payload: LoginPayload): Promise<AuthResponse> {
  const res = await api.post<ApiResponse<AuthResponse>>("/auth/login/", payload);
  return res.data.data;
}

export async function logout(refreshToken: string): Promise<void> {
  await api.post("/auth/logout/", { refresh: refreshToken }, { headers: getAuthCsrfHeader() });
}

export async function getMe(): Promise<User> {
  const res = await api.get<ApiResponse<User>>("/auth/me/");
  return res.data.data;
}

export async function googleAuth(idToken: string): Promise<AuthResponse> {
  const res = await api.post<ApiResponse<AuthResponse>>("/auth/google/", {
    id_token: idToken,
  });
  return res.data.data;
}

export async function refreshToken(): Promise<{ access: string }> {
  try {
    const res = await api.post("/auth/token/refresh/", {}, { headers: getAuthCsrfHeader() });
    const access = res.data.data?.access || res.data.access;
    if (!access) throw new Error("No access token in response");
    return { access };
  } catch {
    throw new Error("Token refresh failed");
  }
}
