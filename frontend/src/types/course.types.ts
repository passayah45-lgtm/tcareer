export type CourseLevel = "beginner" | "intermediate" | "advanced";
export type CourseStatus = "draft" | "published" | "archived";
export type LessonType = "video" | "text" | "quiz";
export type TranscodingStatus = "pending" | "processing" | "complete" | "failed";
export type EnrollmentStatus = "active" | "completed" | "refunded" | "expired";
export type ContentReviewStatus =
  | "draft"
  | "needs_review"
  | "under_review"
  | "changes_requested"
  | "approved"
  | "rejected"
  | "published"
  | "archived";

export interface VideoLesson {
  id: string;
  hls_url: string;
  thumbnail_url: string;
  duration_seconds: number;
  transcoding_status: TranscodingStatus;
  file_size_bytes: number;
}

export interface Lesson {
  id: string;
  title: string;
  lesson_type: LessonType;
  content: string;
  position: number;
  is_published: boolean;
  is_free_preview: boolean;
  review_status?: ContentReviewStatus;
  published_version?: number;
  draft_version?: number;
  video: VideoLesson | null;
  is_accessible: boolean;
}

export interface CourseInstructor {
  id: string;
  full_name: string;
  avatar_url: string;
  email: string;
}

export interface Course {
  id: string;
  title: string;
  slug: string;
  short_description: string;
  description: string;
  thumbnail_url: string;
  preview_video_url: string;
  level: CourseLevel;
  status: CourseStatus;
  price: string;
  language: string;
  tags: string[];
  requirements: string[];
  what_you_learn: string[];
  pass_threshold: number;
  instructor: CourseInstructor;
  instructor_name?: string;
  lessons: Lesson[];
  total_lessons: number;
  is_enrolled: boolean;
  created_at: string;
  updated_at: string;
}

export interface Enrollment {
  id: string;
  course: Course;
  status: EnrollmentStatus;
  amount_paid: string;
  completed_at: string | null;
  last_accessed_at: string | null;
  created_at: string;
  first_lesson_id: string | null;
}

export interface LessonProgress {
  id: string;
  lesson_id: string;
  lesson_title: string;
  is_completed: boolean;
  watch_percentage: number;
  last_position_seconds: number;
  completed_at: string | null;
}

export interface CourseProgress {
  total_lessons: number;
  completed_lessons: number;
  percentage: number;
  lessons: LessonProgress[];
}

export interface UploadUrlResponse {
  upload_url: string;
  file_url: string;
  key: string;
  content_type: string;
  expires_in: number;
}

export interface CourseQualityCheck {
  key: string;
  label: string;
  passed: boolean;
  detail: string;
}

export interface CourseQualityReadiness {
  course_id: string;
  title: string;
  status: CourseStatus;
  quality_score: number;
  publish_ready: boolean;
  blockers: string[];
  checks: CourseQualityCheck[];
  metrics: Record<string, number>;
}

export interface CourseQualityDashboard {
  summary: {
    total_courses: number;
    publish_ready: number;
    average_score: number;
  };
  courses: CourseQualityReadiness[];
}

export interface InstructorAnalytics {
  courses_authored: number;
  lessons_created: number;
  lessons_approved: number;
  reviews_completed: number;
  courses_published: number;
  resources_created: number;
}

export interface CourseReview {
  id: string;
  course: string;
  status: ContentReviewStatus;
  reviewer_email: string | null;
  submitted_by_email: string | null;
  comments: string;
  required_fixes: string[];
  reviewed_at: string | null;
  created_at: string;
}

export interface LessonVersion {
  id: string;
  lesson: string;
  version_number: number;
  editor_email: string | null;
  title: string;
  lesson_type: LessonType;
  content: string;
  summary_of_changes: string;
  is_published_version: boolean;
  created_at: string;
}

export interface CourseProject {
  id: string;
  course: string;
  instructions: string;
  required_deliverables: string[];
  rubric: Array<Record<string, unknown>>;
  evaluation_criteria: string[];
  passing_score: number;
  reviewer_notes: string;
  example_solution: string;
  resources: string[];
  version: number;
  approval_state: ContentReviewStatus;
  reviewed_by_email: string | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ResourceLibraryItem {
  id: string;
  owner_email: string;
  course: string | null;
  course_title: string | null;
  title: string;
  resource_type: string;
  file_url: string;
  storage_key: string;
  file_name: string;
  content_type: string;
  file_size_bytes: number;
  checksum: string;
  description: string;
  version: number;
  visibility: "private" | "course" | "public";
  review_status: ContentReviewStatus;
  review_notes: string;
  download_count: number;
  malware_scan_status: string;
  malware_scanner: string;
  malware_scanned_at: string | null;
  malware_scan_result: Record<string, unknown>;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ReviewAssignment {
  id: string;
  target_type: "course" | "lesson" | "assessment" | "project" | "resource";
  target_id: string;
  course: string | null;
  course_title: string | null;
  lesson: string | null;
  lesson_title: string | null;
  assigned_reviewer: string;
  reviewer_email: string;
  assigned_by_email: string | null;
  organization: string | null;
  subject: string;
  priority: "low" | "normal" | "high" | "urgent";
  review_status: ContentReviewStatus;
  due_date: string | null;
  reassignment_history: Array<Record<string, unknown>>;
  escalation_level: number;
  escalated_to: string | null;
  escalation_reason: string;
  escalated_at: string | null;
  completed_at: string | null;
  is_overdue: boolean;
  created_at: string;
  updated_at: string;
}

export interface ReviewerDashboard {
  metrics: {
    total: number;
    assigned: number;
    completed: number;
    overdue: number;
    due_soon: number;
    high_priority: number;
    average_review_time_hours: number;
    approval_rate: number;
    changes_requested: number;
    rejected: number;
    subject_distribution: Array<{ subject: string; count: number }>;
    organization_distribution: Array<{ organization_id: string | null; count: number }>;
  };
  profile: {
    id: string;
    reviewer_role: string;
    subject_tags: string[];
    max_active_assignments: number;
    automatic_assignment_enabled: boolean;
    is_active: boolean;
  } | null;
}

export interface PublishBlocker {
  code: string;
  message: string;
  severity: string;
}

export interface PublishBlockerResponse {
  blockers: PublishBlocker[];
  publish_ready: boolean;
}

export interface AcademicAuditRow {
  id: string;
  timestamp: string;
  actor_email: string;
  action: string;
  target_type: string;
  target_id: string;
  metadata: Record<string, unknown>;
}
