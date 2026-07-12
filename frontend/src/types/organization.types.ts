import type { Organization, OrganizationInvitation, OrganizationMember, AuditHistoryEntry } from "@/types/recruiter.types";

export interface OrganizationProfile {
  id: string;
  logo_url: string;
  banner_url: string;
  favicon_url: string;
  primary_color: string;
  secondary_color: string;
  support_email: string;
  support_phone: string;
  time_zone: string;
  default_language: string;
  email_branding: Record<string, unknown>;
  certificate_branding: Record<string, unknown>;
  landing_page_branding: Record<string, unknown>;
  logo_file_url: string;
  banner_file_url: string;
  favicon_file_url: string;
  certificate_logo_file_url: string;
  email_header_image_file_url: string;
  settings: Record<string, unknown>;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface OrganizationPolicy {
  id: string;
  password_min_length: number;
  mfa_required: boolean;
  profile_visibility_default: boolean;
  resume_visibility_default: boolean;
  portfolio_visibility_default: boolean;
  invitation_expiration_days: number;
  session_timeout_minutes: number;
  allowed_email_domains: string[];
  recruiter_permissions: Record<string, unknown>;
  student_permissions: Record<string, unknown>;
  notification_defaults: Record<string, unknown>;
  digest_frequency: string;
  quiet_hours: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface EnterpriseAnalytics {
  active_learners: number;
  active_recruiters: number;
  student_activation_rate: number;
  course_completion: { completed: number; total: number; rate: number };
  course_progress_by_cohort: Array<{ cohort_id: string; name: string; completed: number; total: number; rate: number }>;
  certificates_issued: number;
  certificate_completion_rate: number;
  jobs_posted: number;
  applications_received: number;
  applications_by_status: Record<string, number>;
  interviews: number;
  interviews_by_status: Record<string, number>;
  hiring_success: number;
  placement_rate: number;
  recruiter_activity: Record<string, number>;
  department_breakdown: Array<{ id: string; name: string; status: string; member_count: number }>;
  cohort_breakdown: Array<{ id: string; name: string; status: string; program: string; graduation_year: number | null; member_count: number }>;
  student_engagement: { active_members: number; enrollments: number };
  ai_usage: { events: number };
  monthly_trend_summary: Record<string, number>;
  revenue: { placeholder: boolean; amount: number };
  organization_health_score: number;
}

export interface OrganizationHierarchySummary {
  departments: number;
  teams: number;
  cohorts: number;
  members: number;
}

export interface EnterpriseDashboard {
  organization: Organization;
  profile: OrganizationProfile;
  policy: OrganizationPolicy;
  hierarchy: OrganizationHierarchySummary;
  analytics: EnterpriseAnalytics;
  recent_audit_activity: AuditHistoryEntry[];
  recent_imports: BulkImportJob[];
  recent_exports: DataExportJob[];
  can_manage: boolean;
}

export interface EnterpriseSettings {
  organization: Organization;
  profile: OrganizationProfile;
  policy: OrganizationPolicy;
  members: OrganizationMember[];
  pending_invitations: OrganizationInvitation[];
}

export interface EnterpriseMemberAssignment {
  id: string;
  membership: string;
  user_email: string;
  user_full_name: string;
  role: string;
  created_at: string;
}

export interface Department {
  id: string;
  name: string;
  description: string;
  status: string;
  metadata: Record<string, unknown>;
  member_count: number;
  members: EnterpriseMemberAssignment[];
  created_at: string;
  updated_at: string;
}

export interface OrganizationTeam {
  id: string;
  name: string;
  team_type: string;
  manager: string | null;
  manager_email: string;
  status: string;
  permissions: Record<string, unknown>;
  metadata: Record<string, unknown>;
  member_count: number;
  members: EnterpriseMemberAssignment[];
  created_at: string;
  updated_at: string;
}

export interface Cohort {
  id: string;
  name: string;
  academic_year: string;
  semester: string;
  batch: string;
  program: string;
  graduation_year: number | null;
  status: string;
  enrollment_starts_at: string | null;
  enrollment_ends_at: string | null;
  assigned_course_ids: string[];
  metadata: Record<string, unknown>;
  member_count: number;
  progress_summary?: Record<string, unknown>;
  members: EnterpriseMemberAssignment[];
  created_at: string;
  updated_at: string;
}

export interface BulkImportJob {
  id: string;
  import_type: string;
  status: string;
  source_filename: string;
  preview_rows: Array<{ row_number: number; data: Record<string, string> }>;
  validation_errors: Array<{ row: number; field: string; message: string }>;
  required_columns: string[];
  error_report: Array<{ row: number; field: string; message: string }>;
  partial_success_report: Array<Record<string, number>>;
  success_count: number;
  error_count: number;
  progress_percentage: number;
  started_at: string | null;
  completed_at: string | null;
  failed_at: string | null;
  duration_seconds: number;
  retry_count: number;
  failure_reason: string;
  summary_file_url: string;
  error_file_url: string;
  created_at: string;
}

export interface DataExportJob {
  id: string;
  export_type: string;
  file_format: string;
  row_count: number;
  status: string;
  file_name: string;
  file_url: string;
  content_type: string;
  file_size: number;
  completed_at: string | null;
  failed_at: string | null;
  expires_at: string | null;
  deleted_at: string | null;
  duration_seconds: number;
  retry_count: number;
  download_count: number;
  last_downloaded_at: string | null;
  last_error: string;
  failure_reason: string;
  retention_days: number;
  legal_hold: boolean;
  file_deleted_at: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface ImportTemplate {
  import_type: string;
  required_columns: string[];
  columns: string[];
  sample_rows: Array<Record<string, string>>;
}

export interface EnterpriseReportJob {
  id: string;
  report_type: string;
  status: string;
  progress_percentage: number;
  started_at: string | null;
  completed_at: string | null;
  failed_at: string | null;
  duration_seconds: number;
  retry_count: number;
  failure_reason: string;
  metadata: Record<string, unknown>;
  export: DataExportJob | null;
  created_at: string;
}

export interface EnterpriseRoleResponse {
  memberships: OrganizationMember[];
  permission_summary: Record<string, string>;
}

export interface EnterpriseAuditResponse {
  total: number;
  events: Array<{
    id: string;
    action: string;
    target_type: string;
    target_id: string;
    actor_id: string | null;
    metadata: Record<string, unknown>;
    ip_address: string;
    created_at: string;
  }>;
}

export interface EnterpriseWorkerStatus {
  id: string;
  worker_key: string;
  last_heartbeat_at: string | null;
  last_successful_run_at: string | null;
  last_failed_run_at: string | null;
  average_duration_seconds: number;
  failure_count: number;
  retry_count: number;
  stuck_job_count: number;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface EnterpriseWorkerJobs {
  exports: DataExportJob[];
  imports: BulkImportJob[];
  reports: EnterpriseReportJob[];
  worker_statuses: EnterpriseWorkerStatus[];
  stuck_counts: Record<string, number>;
}
