export type TrackCategory = "tech" | "data_ai" | "design" | "business";
export type TrackDifficulty = "beginner" | "intermediate" | "advanced";
export type TrackStage = 1 | 2 | 3;

export interface TrackCourse {
  id: string;
  position: number;
  stage: TrackStage;
  stage_display: string;
  is_required: boolean;
  notes: string;
  course_id: string;
  course_title: string;
  course_slug: string;
  course_level: string;
  course_price: string;
  course_thumbnail: string;
  is_enrolled: boolean;
  is_course_completed: boolean;
}

export interface CoursesByStage {
  stage: TrackStage;
  stage_name: string;
  courses: TrackCourse[];
}

export interface CareerTrack {
  id: string;
  title: string;
  slug: string;
  short_description: string;
  description?: string;
  category: TrackCategory;
  category_display: string;
  difficulty: TrackDifficulty;
  icon: string;
  color: string;
  target_job_titles: string[];
  skills_acquired: string[];
  duration_display: string;
  estimated_weeks_min: number;
  estimated_weeks_max: number;
  avg_salary_min: number;
  avg_salary_max: number;
  total_courses: number;
  required_courses_count: number;
  is_enrolled: boolean;
  position: number;
  courses_by_stage?: CoursesByStage[];
  user_enrollment?: UserTrackEnrollment | null;
}

export interface UserTrackEnrollment {
  id: string;
  track_title: string;
  track_slug: string;
  track_icon: string;
  track_color: string;
  current_stage: TrackStage;
  current_stage_display: string;
  courses_completed: number;
  total_required: number;
  progress_percentage: number;
  is_completed: boolean;
  completed_at: string | null;
  last_activity_at: string;
  created_at: string;
  next_course: {
    course_id: string;
    course_title: string;
    course_slug: string;
    stage: TrackStage;
    position: number;
  } | null;
}

export interface TrackCategory_ {
  value: TrackCategory;
  label: string;
  count: number;
}
