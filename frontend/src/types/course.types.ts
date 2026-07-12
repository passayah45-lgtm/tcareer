export type CourseLevel = "beginner" | "intermediate" | "advanced";
export type CourseStatus = "draft" | "published" | "archived";
export type LessonType = "video" | "text" | "quiz";
export type TranscodingStatus = "pending" | "processing" | "complete" | "failed";
export type EnrollmentStatus = "active" | "completed" | "refunded" | "expired";

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
