import api from "./client";

export interface CourseReview {
  id: string;
  author_name: string;
  author_avatar: string;
  stars: number;
  title: string;
  body: string;
  helpful_count: number;
  instructor_reply: string;
  created_at: string;
}

export interface ReviewStats {
  average: number;
  total: number;
  distribution: Record<string, number>;
  reviews: CourseReview[];
}

export interface DiscussionReply {
  id: string;
  author_name: string;
  author_avatar: string;
  body: string;
  is_instructor_reply: boolean;
  deleted_at: string | null;
  created_at: string;
}

export interface DiscussionThread {
  id: string;
  author_name: string;
  title: string;
  body: string;
  is_pinned: boolean;
  is_resolved: boolean;
  reply_count: number;
  deleted_at: string | null;
  created_at: string;
  replies?: DiscussionReply[];
}

export async function getCourseReviews(courseId: string): Promise<ReviewStats> {
  const res = await api.get(`/community/courses/${courseId}/reviews/`);
  return res.data;
}

export async function createReview(
  courseId: string,
  stars: number,
  title: string,
  body: string
): Promise<CourseReview> {
  const res = await api.post(`/community/courses/${courseId}/reviews/create/`, {
    stars, title, body,
  });
  return res.data;
}

export async function getLessonDiscussions(lessonId: string): Promise<DiscussionThread[]> {
  const res = await api.get(`/community/lessons/${lessonId}/discussions/`);
  return res.data;
}

export async function createThread(
  lessonId: string,
  title: string,
  body: string
): Promise<DiscussionThread> {
  const res = await api.post(`/community/lessons/${lessonId}/discussions/create/`, {
    title, body,
  });
  return res.data;
}

export async function createReply(
  threadId: string,
  body: string
): Promise<DiscussionReply> {
  const res = await api.post(`/community/threads/${threadId}/replies/`, { body });
  return res.data;
}
