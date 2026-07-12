// Types for the careers domain (Portfolio, Resume, Skills, Projects)

export type VisibilityChoice = "public" | "unlisted" | "private";
export type ExperienceLevel = "student" | "entry" | "mid" | "senior" | "lead";
export type SkillSource = "manual" | "track" | "course";

export interface PortfolioSkill {
  id: string;
  name: string;
  category: string;
  source: SkillSource;
  position: number;
  created_at: string;
}

export interface SkillCreatePayload {
  name: string;
  category?: string;
  position?: number;
}

export interface PortfolioProject {
  id: string;
  title: string;
  description: string;
  tech_stack: string[];
  project_url: string;
  github_url: string;
  demo_video_url: string;
  thumbnail_url: string;
  gallery_urls: string[];
  media: PortfolioProjectMedia[];
  is_featured: boolean;
  position: number;
  visibility?: VisibilityChoice;
  start_date: string | null;
  end_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface PortfolioProjectMedia {
  id: string;
  media_type: "image" | "video" | "document";
  url: string;
  file_name: string;
  content_type: string;
  file_size: number;
  title: string;
  description: string;
  visibility: VisibilityChoice;
  position: number;
  is_featured: boolean;
  created_at: string;
}

export interface Portfolio {
  id: string;
  username: string | null;
  full_name: string;
  avatar_url: string | null;
  headline: string;
  bio: string;
  location: string;
  desired_role: string;
  experience_level: ExperienceLevel;
  linkedin_url: string;
  github_url: string;
  website_url: string;
  visibility: VisibilityChoice;
  profile_views: number;
  public_url: string | null;
  skills: PortfolioSkill[];
  projects: PortfolioProject[];
  created_at: string;
  updated_at: string;
}

export interface PortfolioUpdatePayload {
  headline?: string;
  bio?: string;
  location?: string;
  desired_role?: string;
  experience_level?: ExperienceLevel;
  linkedin_url?: string;
  github_url?: string;
  website_url?: string;
  visibility?: VisibilityChoice;
}

export interface SkillSyncResult {
  from_courses: { added: number; skipped: number };
  from_tracks: { added: number; skipped: number };
  total_added: number;
}

// Resume types
export interface EducationEntry {
  id: string;
  institution: string;
  degree: string;
  field: string;
  start_year: number;
  end_year?: number | null;
  grade: string;
  description: string;
}

export interface ExperienceEntry {
  id: string;
  company: string;
  title: string;
  location: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
  description: string;
}

export interface ResumeCertificate {
  cert_number: string;
  course_title: string;
  course_slug: string;
  issued_at: string;
  verify_url: string;
}

export interface Resume {
  id: string;
  title: string;
  summary: string;
  target_role: string;
  education: EducationEntry[];
  experience: ExperienceEntry[];
  certificates: ResumeCertificate[];
  skills: PortfolioSkill[];
  pdf_url: string;
  last_generated_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ResumeUpdatePayload {
  title?: string;
  summary?: string;
  target_role?: string;
  education?: EducationEntry[];
  experience?: ExperienceEntry[];
}

export interface CareerResumeFile {
  id: string;
  file_url: string;
  file_name: string;
  content_type: string;
  file_size: number;
  is_private: boolean;
  created_at: string;
}

export interface CareerResumeVersion {
  id: string;
  version_number: number;
  snapshot: Record<string, unknown>;
  change_summary: string;
  created_at: string;
}

export interface CareerResumeAnalytics {
  id: string;
  event_type: "viewed_by_recruiter" | "downloaded" | "used_for_application";
  metadata: Record<string, unknown>;
  created_at: string;
}

export type ResumeAIReviewType = "review" | "skill_extraction" | "ats" | "job_match" | "comparison";

export interface ResumeAIReview {
  id: string;
  resume: string;
  review_type: ResumeAIReviewType;
  job: string | null;
  job_title: string;
  comparison_resume: string | null;
  comparison_resume_title: string;
  prompt_version: string;
  model_name: string;
  estimated_cost: string;
  overall_score: number;
  ats_score: number;
  match_score: number;
  confidence: number;
  extracted_skills: {
    normalized?: string[];
    technical_skills?: string[];
    soft_skills?: string[];
    languages?: string[];
    tools?: string[];
    frameworks?: string[];
    platforms?: string[];
    cloud_providers?: string[];
    databases?: string[];
    certificates?: string[];
    [key: string]: string[] | undefined;
  };
  missing_skills: string[];
  strengths: string[];
  weaknesses: string[];
  suggestions: string[];
  action_items: { priority: "high" | "medium" | "low"; action: string }[];
  report: Record<string, unknown>;
  summary: string;
  created_at: string;
}

export interface ResumeAIAnalytics {
  average_score: number;
  best_score: number;
  review_count: number;
  top_weaknesses: { label: string; count: number }[];
  top_strengths: { label: string; count: number }[];
  score_history: { score: number; review_type: ResumeAIReviewType; created_at: string }[];
  ats_trend: { score: number; created_at: string }[];
  job_match_trend: { score: number; created_at: string }[];
  skill_growth: { count: number; created_at: string }[];
}

export type PortfolioAIReviewType = "portfolio_review" | "project_review" | "github_review" | "skill_extraction" | "job_match";

export interface PortfolioAIReview {
  id: string;
  portfolio: string;
  review_type: PortfolioAIReviewType;
  project: string | null;
  project_title: string;
  job: string | null;
  job_title: string;
  prompt_version: string;
  model_name: string;
  estimated_cost: string;
  overall_score: number;
  project_score: number;
  github_score: number;
  match_score: number;
  confidence: number;
  extracted_skills: {
    normalized?: string[];
    project_technologies?: string[];
    duplicate_skills?: string[];
    emerging_skills?: string[];
    [key: string]: string[] | undefined;
  };
  missing_skills: string[];
  technology_stack: string[];
  strengths: string[];
  weaknesses: string[];
  suggestions: string[];
  action_items: { priority: "high" | "medium" | "low"; action: string }[];
  report: Record<string, unknown>;
  summary: string;
  created_at: string;
}

export interface PortfolioAIAnalytics {
  average_score: number;
  best_score: number;
  review_count: number;
  top_strengths: { label: string; count: number }[];
  top_weaknesses: { label: string; count: number }[];
  score_history: { score: number; review_type: PortfolioAIReviewType; created_at: string }[];
  project_quality_trend: { score: number; created_at: string }[];
  skill_growth: { count: number; created_at: string }[];
  technology_diversity: { count: number; created_at: string }[];
  job_match_trend: { score: number; created_at: string }[];
}

export interface CareerResume {
  id: string;
  title: string;
  summary: string;
  target_role: string;
  education: EducationEntry[];
  experience: ExperienceEntry[];
  skills: string[];
  is_default: boolean;
  is_archived: boolean;
  files: CareerResumeFile[];
  versions: CareerResumeVersion[];
  analytics?: CareerResumeAnalytics[];
  ai_reviews?: ResumeAIReview[];
  created_at: string;
  updated_at: string;
}

export interface CareerResumePayload {
  title: string;
  summary?: string;
  target_role?: string;
  education?: EducationEntry[];
  experience?: ExperienceEntry[];
  skills?: string[];
  is_default?: boolean;
}

// Public portfolio types
export interface PublicPortfolio {
  username: string;
  full_name: string;
  avatar_url: string | null;
  headline: string;
  bio: string;
  location: string;
  desired_role: string;
  experience_level: ExperienceLevel;
  preferred_work_country: string;
  relocation_willingness: string;
  remote_preference: string;
  availability: { remote_preference: string; relocation_willingness: string; preferred_work_country: string };
  open_to_work: boolean;
  is_verified: boolean;
  linkedin_url: string;
  github_url: string;
  website_url: string;
  skills: PortfolioSkill[];
  projects: PortfolioProject[];
  education: EducationEntry[];
  experience: ExperienceEntry[];
  certificates: ResumeCertificate[];
  completed_courses: {
    title: string;
    slug: string;
    thumbnail_url: string;
    level: string;
    completed_at: string;
  }[];
  career_tracks: {
    track_title: string;
    track_slug: string;
    track_color: string;
    progress_percentage: number;
    is_completed: boolean;
  }[];
}
