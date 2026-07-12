export type OrganizationRole = "recruiter" | "company_admin" | "platform_admin" | "super_admin";

export interface Organization {
  id: string;
  name: string;
  slug: string;
  organization_type: string;
  status: string;
  website_url: string;
  country_code: string;
}

export interface OrganizationMember {
  id: string;
  organization: string;
  user: string;
  user_email: string;
  user_full_name: string;
  role: string;
  status: string;
}

export interface OrganizationInvitation {
  id: string;
  organization: string;
  email: string;
  role: string;
  invited_by: string | null;
  expires_at: string;
  accepted_at: string | null;
  revoked_at: string | null;
  created_at: string;
}

export interface RecruiterDashboard {
  total_jobs: number;
  published_jobs: number;
  draft_jobs: number;
  archived_jobs: number;
  applications_received: number;
  applications_by_stage: Record<string, number>;
  candidate_pipeline: Record<string, number>;
  upcoming_interviews: number;
  organization_recruiters: number;
  remaining_recruiter_seats: number;
  seat_usage: {
    active_recruiter_seats: number;
    max_recruiter_seats: number;
  };
  candidate_unlock_usage: {
    used: number;
    limit: number | null;
  };
  analytics_summary: Record<string, number | boolean | string | null>;
  recent_recruiter_activity: RecruiterActivity[];
}

export interface RecruiterSettings {
  organization: Organization;
  can_manage: boolean;
  members: OrganizationMember[];
  pending_invitations: OrganizationInvitation[];
  entitlement: {
    has_active_recruiter_entitlement: boolean;
    max_recruiter_seats: number;
    active_recruiter_seats: number;
    remaining_recruiter_seats: number;
    can_post_jobs: boolean;
    can_search_candidates: boolean;
    can_view_candidate_profiles: boolean;
  };
  candidate_unlock_usage: {
    used: number;
    limit: number | null;
  };
  recent_audit_activity: AuditHistoryEntry[];
}

export interface AuditHistoryEntry {
  id: string;
  action: string;
  target_type: string;
  target_id: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface RecruiterActivity {
  id: string;
  activity_type: string;
  created_at: string;
  actor__full_name?: string;
  application_id?: string;
}

export interface RecruiterJob {
  id: string;
  organization: string;
  title: string;
  company_name: string;
  company_logo_url: string;
  location: string;
  job_type: string;
  job_type_display: string;
  experience_level: string;
  experience_level_display: string;
  description: string;
  requirements: string[];
  salary_min: number | null;
  salary_max: number | null;
  salary_display: string;
  apply_url: string;
  required_track_title: string | null;
  required_track_slug: string | null;
  is_active: boolean;
  views_count: number;
  created_at: string;
}

export interface RecruiterJobPayload {
  title: string;
  company_name: string;
  company_logo_url?: string;
  description: string;
  requirements: string[];
  job_type?: string;
  experience_level?: string;
  location?: string;
  country_code?: string;
  city?: string;
  is_remote?: boolean;
  remote_regions?: string[];
  salary_min?: number | null;
  salary_max?: number | null;
  salary_currency?: string;
  salary_visible?: boolean;
  apply_url?: string;
  required_skills?: string[];
  preferred_skills?: string[];
  languages_required?: string[];
}

export type ApplicationStage =
  | "draft"
  | "applied"
  | "under_review"
  | "shortlisted"
  | "assessment"
  | "interview_scheduled"
  | "interview_completed"
  | "offer_sent"
  | "offer_accepted"
  | "offer_declined"
  | "rejected"
  | "withdrawn";

export interface JobApplication {
  id: string;
  job: string;
  job_title: string;
  company_name: string;
  candidate: string;
  candidate_name: string;
  candidate_email: string;
  organization: string;
  stage: ApplicationStage;
  stage_display: string;
  cover_letter: string;
  source: string;
  assigned_recruiter: string | null;
  hiring_manager: string | null;
  is_archived: boolean;
  withdrawn_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApplicationTimelineEntry {
  id: string;
  event_type: string;
  from_stage: string;
  to_stage: string;
  message: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface ApplicationAttachment {
  id: string;
  file_url: string;
  file_name: string;
  content_type: string;
  is_private: boolean;
  created_at: string;
}

export interface ApplicationAnswer {
  id: string;
  question: string;
  question_text: string;
  question_type: string;
  answer: { value: string | number | boolean };
  created_at: string;
  updated_at: string;
}

export type ApplicationQuestionType = "short_text" | "long_text" | "yes_no" | "multiple_choice" | "number" | "url";

export interface ApplicationQuestion {
  id: string;
  job: string;
  question_text: string;
  question_type: ApplicationQuestionType;
  is_required: boolean;
  choices: string[];
  position: number;
  is_active: boolean;
}

export interface ApplicationQuestionPayload {
  question_text: string;
  question_type: ApplicationQuestionType;
  is_required: boolean;
  choices?: string[];
  position?: number;
  is_active?: boolean;
}

export interface ApplicationActivity {
  id: string;
  actor: string | null;
  actor_name: string;
  activity_type: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface ApplicationNote {
  id: string;
  application: string;
  author: string;
  author_name: string;
  body: string;
  is_internal: boolean;
  created_at: string;
}

export interface PipelineResponse {
  data: JobApplication[];
  count: number;
  page: number;
  page_size: number;
  pipeline_statistics: Record<string, number>;
}

export interface CandidateSearchResult {
  candidate_id: string;
  full_name: string;
  headline: string;
  desired_role: string;
  experience_level: string;
  location: string;
  country: string;
  remote_preference: string;
  verified: boolean;
  portfolio_available: boolean;
  resume_available: boolean;
  skills: string[];
  is_saved: boolean;
  is_unlocked: boolean;
}

export interface SavedCandidate {
  id: string;
  candidate: string;
  candidate_name: string;
  candidate_email: string;
  talent_pool: string | null;
  talent_pool_name: string;
  labels: string[];
  private_notes: string;
  created_at: string;
  updated_at: string;
}

export interface TalentPool {
  id: string;
  name: string;
  description: string;
  created_at: string;
}

export interface Interview {
  id: string;
  application: string;
  organization: string;
  interview_type: "online" | "phone" | "onsite";
  status: "scheduled" | "rescheduled" | "completed" | "cancelled" | "no_show";
  scheduled_start: string;
  scheduled_end: string | null;
  timezone: string;
  meeting_link: string;
  location: string;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface InterviewFeedback {
  id: string;
  interview: string;
  author: string;
  rating: number;
  recommendation: string;
  feedback: string;
  created_at: string;
}

export interface InterviewScorecard {
  id: string;
  interview: string;
  author: string;
  criteria: Record<string, number>;
  total_score: string | number;
  recommendation: string;
  created_at: string;
}

export interface InterviewDetail extends Interview {
  feedback: InterviewFeedback[];
  scorecards: InterviewScorecard[];
}

export interface ApplicationDetail {
  application: JobApplication;
  candidate: {
    id: string;
    full_name: string;
    email: string;
    avatar_url: string;
    profile_headline: string;
    profile_location: string;
    username: string | null;
    is_verified: boolean;
  };
  job: RecruiterJob;
  timeline: ApplicationTimelineEntry[];
  notes: ApplicationNote[];
  attachments: ApplicationAttachment[];
  answers: ApplicationAnswer[];
  activity: ApplicationActivity[];
  interviews: InterviewDetail[];
  audit_history: AuditHistoryEntry[];
}
