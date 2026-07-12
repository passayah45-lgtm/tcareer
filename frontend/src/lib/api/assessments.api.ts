import api from "./client";
import type { ApiResponse } from "@/types/api.types";

export interface QuizQuestion { id: string; question_text: string; options: string[]; correct_index?: number; explanation?: string; position: number; }
export interface QuizResult { id: string; score: number; total_questions: number; percentage: number; passed: boolean; attempt_number: number; pass_threshold: number; question_results: { question_id: string; question_text: string; options: string[]; selected_index: number | null; correct_index: number; is_correct: boolean; explanation: string; }[]; created_at: string; }
export interface QuizMeta { questions: QuizQuestion[]; total: number; pass_threshold: number; }
export interface CanAttempt { can_attempt: boolean; reason: string; }
export interface BulkQuestionItem { question_text: string; options: string[]; correct_index: number; explanation?: string; position?: number; }
export interface BulkCreatePayload { questions: BulkQuestionItem[]; replace: boolean; }
export interface BulkCreateResponse { questions: QuizQuestion[]; total: number; course_id: string; }

export async function getQuizQuestions(courseId: string): Promise<QuizMeta> {
  const res = await api.get<ApiResponse<QuizMeta>>(`/assessments/${courseId}/questions/`);
  return res.data.data;
}

export async function getInstructorQuizQuestions(courseId: string): Promise<QuizQuestion[]> {
  const res = await api.get<ApiResponse<QuizMeta> | QuizMeta>(`/assessments/${courseId}/questions/`);
  const data = "data" in res.data ? res.data.data : res.data;
  return data.questions || [];
}

export async function canAttemptQuiz(courseId: string): Promise<CanAttempt> {
  const res = await api.get<ApiResponse<CanAttempt>>(`/assessments/${courseId}/can-attempt/`);
  return res.data.data;
}

export async function submitQuiz(courseId: string, answers: Record<string, number>): Promise<QuizResult> {
  const res = await api.post<ApiResponse<QuizResult>>(`/assessments/${courseId}/submit/`, { answers });
  return res.data.data;
}

export async function getAttemptHistory(courseId: string): Promise<QuizResult[]> {
  const res = await api.get<ApiResponse<QuizResult[]>>(`/assessments/${courseId}/attempts/`);
  return res.data.data as QuizResult[];
}

export async function submitRating(courseId: string, stars: number, review: string): Promise<void> {
  await api.post(`/assessments/${courseId}/rate/`, { stars, review });
}

export async function bulkCreateQuestions(courseId: string, payload: BulkCreatePayload): Promise<BulkCreateResponse> {
  const res = await api.post<ApiResponse<BulkCreateResponse>>(`/assessments/${courseId}/questions/bulk/`, payload);
  return res.data.data;
}

export async function reorderQuestions(courseId: string, questions: { id: string; position: number }[]): Promise<QuizQuestion[]> {
  const res = await api.post<ApiResponse<{ questions: QuizQuestion[]; total: number }>>(`/assessments/${courseId}/questions/reorder/`, { questions });
  return res.data.data.questions;
}

export async function deleteQuestion(courseId: string, questionId: string): Promise<void> {
  await api.delete(`/assessments/${courseId}/questions/${questionId}/`);
}

export async function updateQuestion(courseId: string, questionId: string, payload: Partial<BulkQuestionItem>): Promise<QuizQuestion> {
  const res = await api.patch<ApiResponse<QuizQuestion>>(`/assessments/${courseId}/questions/${questionId}/`, payload);
  return res.data.data;
}
