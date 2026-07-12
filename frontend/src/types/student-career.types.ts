import type { Portfolio, Resume } from "@/types/careers.types";
import type { CareerResume } from "@/types/careers.types";

export interface StudentJob {
  id: string;
  organization: string | null;
  organization_name: string;
  organization_type: string;
  title: string;
  company_name: string;
  company_logo_url: string;
  location: string;
  country_code: string;
  city: string;
  is_remote: boolean;
  remote_regions: string[];
  job_type: string;
  job_type_display: string;
  experience_level: string;
  experience_level_display: string;
  description: string;
  requirements: string[];
  required_skills: string[];
  preferred_skills: string[];
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string;
  salary_display: string;
  salary_visible: boolean;
  apply_url: string;
  required_track_title: string | null;
  required_track_slug: string | null;
  is_active: boolean;
  views_count: number;
  expires_at: string | null;
  posted_by_name: string;
  recommendation_score?: number;
  recommendation_reasons?: string[];
  application_questions: ApplicationQuestion[];
  created_at: string;
}

export interface ApplicationQuestion {
  id: string;
  question_text: string;
  question_type: "short_text" | "long_text" | "yes_no" | "multiple_choice" | "number" | "url";
  is_required: boolean;
  choices: string[];
  position: number;
  is_active: boolean;
}

export interface ApplicationAnswer {
  id?: string;
  question: string;
  question_text?: string;
  question_type?: string;
  answer: { value: string | number | boolean };
}

export type StudentApplicationStage =
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

export interface StudentApplication {
  id: string;
  job: string;
  job_title: string;
  company_name: string;
  candidate: string;
  candidate_name: string;
  candidate_email: string;
  organization: string;
  stage: StudentApplicationStage;
  stage_display: string;
  cover_letter: string;
  source: string;
  assigned_recruiter: string | null;
  hiring_manager: string | null;
  is_archived: boolean;
  selected_resume: string | null;
  answers: ApplicationAnswer[];
  withdrawn_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface StudentTimelineEntry {
  id: string;
  event_type: string;
  from_stage: string;
  to_stage: string;
  message: string;
  created_at: string;
}

export interface StudentInterview {
  id: string;
  application: string;
  organization: string;
  interview_type: string;
  status: string;
  scheduled_start: string;
  scheduled_end: string | null;
  timezone: string;
  meeting_link: string;
  location: string;
}

export interface SavedJobCollection {
  id: string;
  name: string;
  description: string;
  saved_count: number;
  created_at: string;
}

export interface SavedJob {
  id: string;
  job: StudentJob;
  collection: string | null;
  collection_name: string;
  notes: string;
  is_favorite_company: boolean;
  created_at: string;
}

export interface StudentDashboard {
  profile_completion: number;
  resume_completion: number;
  portfolio_completion: number;
  skills_summary: string[];
  certificates_earned: number;
  courses_in_progress: Array<{ id: string; course__title: string; course__slug: string; status: string }>;
  applications_submitted: number;
  applications: StudentApplication[];
  application_status_timeline: StudentTimelineEntry[];
  upcoming_interviews: StudentInterview[];
  saved_jobs: SavedJob[];
  recommended_jobs: StudentJob[];
  career_goals: { desired_role: string; open_to_work: boolean; remote_preference: string };
  recent_recruiter_activity: Array<{ id: string; name: string; metadata: Record<string, unknown>; occurred_at: string }>;
  ai_usage_summary: { ai_tutor_used: number; resume_analysis_available: boolean; portfolio_analysis_available: boolean };
  student_analytics: {
    profile_views: number;
    recruiter_views: number;
    resume_downloads: number;
    portfolio_views: number;
    applications_by_status: Record<string, number>;
    saved_jobs: number;
    job_alert_matches: number;
    recommended_job_clicks: number;
  };
}

export interface StudentApplicationDetail {
  application: StudentApplication;
  job: StudentJob;
  timeline: StudentTimelineEntry[];
  interviews: StudentInterview[];
  attachments: Array<{ id: string; file_url: string; file_name: string; content_type: string; is_private: boolean; created_at: string }>;
  answers: ApplicationAnswer[];
}

export interface CareerProfileBundle {
  portfolio: Portfolio;
  resume: Resume;
}

export interface ApplicationPreview {
  job: StudentJob;
  company: string;
  selected_resume: Pick<CareerResume, "id" | "title" | "target_role" | "summary"> & { file_count: number } | null;
  portfolio: { id: string; headline: string; public_url: string | null; visibility: string; skills: string[] } | null;
  cover_letter: string;
  answers: Array<{ question: string; question_text: string; question_type: string; answer: { value: string | number | boolean } }>;
  profile_summary: {
    name: string;
    email: string;
    profile_completion: number;
    resume_completion: number;
    portfolio_completion: number;
  };
  can_submit: boolean;
}
