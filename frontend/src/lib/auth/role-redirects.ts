import type { User, UserRole } from "@/types/user.types";

const STUDENT_HOME = "/dashboard";

const ROLE_HOME: Record<UserRole, string> = {
  student: STUDENT_HOME,
  instructor: "/instructor/dashboard",
  mentor: STUDENT_HOME,
  recruiter: "/recruiter/dashboard",
  company_admin: "/organization/dashboard",
  university_admin: "/organization/dashboard",
  content_moderator: "/organization/dashboard",
  finance_admin: "/organization/dashboard",
  platform_admin: "/platform/dashboard",
  super_admin: "/platform/dashboard",
  admin: "/platform/dashboard",
  report_viewer: "/organization/dashboard",
  department_manager: "/organization/dashboard",
  cohort_manager: "/organization/dashboard",
  team_manager: "/organization/dashboard",
  export_manager: "/organization/dashboard",
};

export function getDashboardPathForRole(role?: UserRole | null): string {
  return role ? ROLE_HOME[role] || STUDENT_HOME : STUDENT_HOME;
}

export function getDashboardPathForUser(user?: Pick<User, "role"> | null): string {
  return getDashboardPathForRole(user?.role);
}

export function isSafeInternalPath(path?: string | null): path is string {
  return Boolean(path && path.startsWith("/") && !path.startsWith("//"));
}

export function getPostAuthRedirect(user: Pick<User, "role">, next?: string | null): string {
  if (isSafeInternalPath(next)) return next;
  return getDashboardPathForUser(user);
}
