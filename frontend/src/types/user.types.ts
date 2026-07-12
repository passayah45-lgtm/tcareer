export type UserRole =
  | "student"
  | "instructor"
  | "mentor"
  | "recruiter"
  | "company_admin"
  | "university_admin"
  | "content_moderator"
  | "finance_admin"
  | "platform_admin"
  | "super_admin"
  | "admin"
  | "report_viewer"
  | "department_manager"
  | "cohort_manager"
  | "team_manager"
  | "export_manager";

export interface User {
  id: string;
  email: string;
  full_name: string;
  avatar_url: string;
  role: UserRole;
  is_verified: boolean;
  created_at: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface AuthResponse {
  user: User;
  access: string;
  refresh: string;
  created?: boolean;
}
