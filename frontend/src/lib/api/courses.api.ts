import api from "./client";
import type { Course, Lesson, Enrollment, CourseProgress, UploadUrlResponse } from "@/types/course.types";
import type { ApiResponse } from "@/types/api.types";

export interface CourseFilters { level?: string; search?: string; is_free?: boolean; page?: number; }
export interface PaginatedCourses { count: number; next: string | null; previous: string | null; results: Course[]; }
export interface ReorderItem { id: string; position: number; }

export async function getCourses(filters?: CourseFilters): Promise<PaginatedCourses> {
  const params = new URLSearchParams();
  if (filters?.level) params.append("level", filters.level);
  if (filters?.search) params.append("search", filters.search);
  if (filters?.is_free) params.append("is_free", "true");
  if (filters?.page) params.append("page", String(filters.page));
  const res = await api.get<ApiResponse<Course[]>>(`/courses/?${params.toString()}`);
  return { count: res.data.meta.count || 0, next: res.data.meta.next || null, previous: res.data.meta.previous || null, results: res.data.data as Course[] };
}

export async function getCourse(slug: string): Promise<Course> {
  const res = await api.get<ApiResponse<Course>>(`/courses/${slug}/`);
  return res.data.data;
}

export async function getCourseById(courseId: string): Promise<Course> {
  const all = await getInstructorCourses();
  const course = all.results.find((c) => c.id === courseId);
  if (!course) throw new Error("Course not found");
  return course;
}

export async function createCourse(payload: Partial<Course>): Promise<Course> {
  const res = await api.post<ApiResponse<Course>>("/courses/create/", payload);
  return res.data.data;
}

export async function updateCourse(courseId: string, payload: Partial<Course> | Record<string, unknown>): Promise<Course> {
  const res = await api.patch<ApiResponse<Course>>(`/courses/${courseId}/update/`, payload);
  return res.data.data;
}

export async function publishCourse(courseId: string): Promise<Course> {
  const res = await api.post<ApiResponse<Course>>(`/courses/${courseId}/publish/`);
  return res.data.data;
}

export async function deleteCourse(courseId: string): Promise<void> {
  await api.delete(`/courses/${courseId}/delete/`);
}

export async function getInstructorCourses(): Promise<PaginatedCourses> {
  const res = await api.get<ApiResponse<Course[]>>("/courses/mine/");
  return { count: res.data.meta.count || 0, next: res.data.meta.next || null, previous: res.data.meta.previous || null, results: res.data.data as Course[] };
}

export async function getLessons(courseId: string): Promise<Lesson[]> {
  const res = await api.get<ApiResponse<Lesson[]>>(`/courses/${courseId}/lessons/`);
  return res.data.data as Lesson[];
}

export async function getLesson(courseId: string, lessonId: string): Promise<Lesson> {
  const res = await api.get<ApiResponse<Lesson>>(`/courses/${courseId}/lessons/${lessonId}/`);
  return res.data.data;
}

export async function createLesson(courseId: string, payload: Partial<Lesson>): Promise<Lesson> {
  const res = await api.post<ApiResponse<Lesson>>(`/courses/${courseId}/lessons/create/`, payload);
  return res.data.data;
}

export async function updateLesson(courseId: string, lessonId: string, payload: Partial<Lesson>): Promise<Lesson> {
  const res = await api.patch<ApiResponse<Lesson>>(`/courses/${courseId}/lessons/${lessonId}/update/`, payload);
  return res.data.data;
}

export async function inlineUpdateLesson(lessonId: string, payload: Partial<Lesson>): Promise<Lesson> {
  const res = await api.patch<ApiResponse<Lesson>>(`/courses/lessons/${lessonId}/`, payload);
  return res.data.data;
}

export async function reorderLessons(courseId: string, lessons: ReorderItem[]): Promise<Lesson[]> {
  const res = await api.post<ApiResponse<Lesson[]>>(`/courses/${courseId}/lessons/reorder/`, { lessons });
  return res.data.data as Lesson[];
}

export async function getUploadUrl(courseId: string, lessonId: string, fileName: string, contentType = "video/mp4"): Promise<UploadUrlResponse> {
  const res = await api.post<ApiResponse<UploadUrlResponse>>(`/courses/${courseId}/lessons/${lessonId}/upload-url/`, { file_name: fileName, content_type: contentType });
  return res.data.data;
}

export async function confirmUpload(courseId: string, lessonId: string, s3Key: string, fileSizeBytes: number): Promise<{ transcoding_status: string }> {
  const res = await api.post<ApiResponse<{ transcoding_status: string }>>(`/courses/${courseId}/lessons/${lessonId}/confirm-upload/`, { s3_key: s3Key, file_size_bytes: fileSizeBytes });
  return res.data.data;
}

export async function enroll(courseId: string): Promise<Enrollment> {
  const res = await api.post<ApiResponse<Enrollment>>(`/courses/${courseId}/enroll/`);
  return res.data.data;
}

export async function getMyEnrollments(): Promise<PaginatedCourses> {
  const res = await api.get<ApiResponse<Enrollment[]>>("/courses/enrollments/");
  return { count: res.data.meta.count || 0, next: res.data.meta.next || null, previous: res.data.meta.previous || null, results: res.data.data as unknown as Course[] };
}

export async function updateProgress(courseId: string, lessonId: string, watchPercentage: number, lastPositionSeconds?: number): Promise<void> {
  await api.post(`/courses/${courseId}/lessons/${lessonId}/progress/`, { watch_percentage: watchPercentage, last_position_seconds: lastPositionSeconds ?? 0 });
}

export async function completeTextLesson(courseId: string, lessonId: string): Promise<void> {
  await api.post(`/courses/${courseId}/lessons/${lessonId}/complete/`);
}

export async function getCourseProgress(courseId: string): Promise<CourseProgress> {
  const res = await api.get<ApiResponse<CourseProgress>>(`/courses/${courseId}/progress/`);
  return res.data.data;
}

export async function uploadVideoToS3(uploadUrl: string, file: File, onProgress?: (percentage: number) => void): Promise<void> {
  await new Promise<void>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    if (onProgress) {
      xhr.upload.addEventListener("progress", (event) => {
        if (event.lengthComputable) onProgress(Math.round((event.loaded / event.total) * 100));
      });
    }
    xhr.addEventListener("load", () => { if (xhr.status >= 200 && xhr.status < 300) resolve(); else reject(new Error(`Upload failed: ${xhr.status}`)); });
    xhr.addEventListener("error", () => reject(new Error("Network error")));
    xhr.open("PUT", uploadUrl);
    xhr.setRequestHeader("Content-Type", file.type);
    xhr.send(file);
  });
}
