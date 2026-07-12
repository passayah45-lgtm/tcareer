import api, { getAccessToken } from "@/lib/api/client";
import type { ApiResponse } from "@/types/api.types";
import type {
  AIAdminOverview,
  AIAuditExport,
  AICareerAnalytics,
  AICareerAssessment,
  AICareerCoachingSummary,
  AICareerGoal,
  AICareerHistory,
  AICareerRoadmap,
  AICareerSkillGap,
  AIChatResponse,
  AIComparisonReport,
  AICostSummary,
  AIEvaluationRunResponse,
  AIEvaluationReview,
  AIEvaluationSummary,
  AIFeatureFlag,
  AIFeedback,
  AIInterviewAnalytics,
  AIInterviewEvaluation,
  AIInterviewQuestion,
  AIInterviewSession,
  AIInterviewStartPayload,
  AIInterviewTemplate,
  AIKnowledgeEmbeddingStatus,
  AIKnowledgeIndexStatus,
  AIKnowledgeSearchResult,
  AIGeneratedQuiz,
  AILearningAnalytics,
  AILearningHistory,
  AILearningTutorSession,
  AILessonIntelligence,
  AIQuizFeedback,
  AIOverview,
  AIProviderStatus,
  AIQualityDashboard,
  AIReleaseGate,
  AIReleaseGovernanceSummary,
  AIRecruiterAnalytics,
  AIRecruiterReport,
  AIReviewerQueue,
  AIRedTeamSuite,
  AIRequest,
  AIStudyPlan,
  AISettings,
  AIStreamEvent,
} from "@/types/ai.types";

function unwrap<T>(payload: ApiResponse<T> | T): T {
  return (payload as ApiResponse<T>).data ?? (payload as T);
}

export async function getAIOverview(): Promise<AIOverview> {
  const response = await api.get<ApiResponse<AIOverview>>("/ai/");
  return unwrap(response.data);
}

export async function sendAIChat(inputText: string, feature = "chat"): Promise<AIChatResponse> {
  const response = await api.post<ApiResponse<AIChatResponse>>("/ai/chat/", { input_text: inputText, feature });
  return unwrap(response.data);
}

export async function getCareerGoals(): Promise<AICareerGoal[]> {
  const response = await api.get<ApiResponse<AICareerGoal[]>>("/ai/career/goals/");
  return unwrap(response.data);
}

export async function createCareerGoal(payload: { title?: string; target_role: string; target_industry?: string; target_country?: string; milestones?: Array<Record<string, unknown>> }): Promise<AICareerGoal> {
  const response = await api.post<ApiResponse<AICareerGoal>>("/ai/career/goals/", payload);
  return unwrap(response.data);
}

export async function updateCareerGoal(goalId: string, payload: Partial<Pick<AICareerGoal, "title" | "target_role" | "target_industry" | "target_country" | "status" | "progress_percentage" | "milestones" | "completed_milestones">>): Promise<AICareerGoal> {
  const response = await api.patch<ApiResponse<AICareerGoal>>(`/ai/career/goals/${goalId}/`, payload);
  return unwrap(response.data);
}

export async function runCareerAssessment(payload: { goal_id?: string; current_skills?: string[]; education?: string; experience?: string; career_interests?: string[]; preferred_industries?: string[]; preferred_countries?: string[]; preferred_work_style?: string }): Promise<AICareerAssessment> {
  const response = await api.post<ApiResponse<AICareerAssessment>>("/ai/career/assessment/", payload);
  return unwrap(response.data);
}

export async function generateCareerRoadmap(payload: { goal_id?: string; horizon?: "3_months" | "6_months" | "12_months" | "24_months"; target_role?: string; skills?: string[] }): Promise<AICareerRoadmap> {
  const response = await api.post<ApiResponse<AICareerRoadmap>>("/ai/career/roadmap/", payload);
  return unwrap(response.data);
}

export async function runCareerSkillGap(payload: { goal_id?: string; comparison_type?: string; target?: string; desired_skills?: string[] }): Promise<AICareerSkillGap> {
  const response = await api.post<ApiResponse<AICareerSkillGap>>("/ai/career/skill-gap/", payload);
  return unwrap(response.data);
}

export async function getCareerLearningRecommendations(payload: { goal_id?: string; comparison_type?: string; target?: string; desired_skills?: string[] }): Promise<Record<string, unknown>> {
  const response = await api.post<ApiResponse<Record<string, unknown>>>("/ai/career/learning-recommendations/", payload);
  return unwrap(response.data);
}

export async function generateWeeklyCareerCoaching(payload: { goal_id?: string; achievements?: string[]; missed_goals?: string[] }): Promise<AICareerCoachingSummary> {
  const response = await api.post<ApiResponse<AICareerCoachingSummary>>("/ai/career/weekly-coaching/", payload);
  return unwrap(response.data);
}

export async function getCareerHistory(): Promise<AICareerHistory> {
  const response = await api.get<ApiResponse<AICareerHistory>>("/ai/career/history/");
  return unwrap(response.data);
}

export async function getCareerAnalytics(): Promise<AICareerAnalytics> {
  const response = await api.get<ApiResponse<AICareerAnalytics>>("/ai/career/analytics/");
  return unwrap(response.data);
}

export async function analyzeRecruiterCandidate(payload: { candidate_id: string; organization_id?: string; job_id?: string }): Promise<AIRecruiterReport> {
  const response = await api.post<ApiResponse<AIRecruiterReport>>("/ai/recruiter/candidate-analysis/", payload);
  return unwrap(response.data);
}

export async function rankRecruiterCandidates(payload: { job_id: string; candidate_ids: string[]; sort_by?: "best_fit" | "highest_confidence" | "highest_growth_potential" | "highest_learning_activity" }): Promise<AIRecruiterReport> {
  const response = await api.post<ApiResponse<AIRecruiterReport>>("/ai/recruiter/candidate-ranking/", payload);
  return unwrap(response.data);
}

export async function compareRecruiterCandidates(payload: { candidate_ids: string[]; organization_id?: string; job_id?: string }): Promise<AIRecruiterReport> {
  const response = await api.post<ApiResponse<AIRecruiterReport>>("/ai/recruiter/candidate-comparison/", payload);
  return unwrap(response.data);
}

export async function analyzeRecruiterJob(payload: { job_id?: string; title?: string; description?: string }): Promise<AIRecruiterReport> {
  const response = await api.post<ApiResponse<AIRecruiterReport>>("/ai/recruiter/job-analysis/", payload);
  return unwrap(response.data);
}

export async function createRecruiterInterviewPlan(payload: { candidate_id: string; organization_id?: string; job_id?: string }): Promise<AIRecruiterReport> {
  const response = await api.post<ApiResponse<AIRecruiterReport>>("/ai/recruiter/interview-plan/", payload);
  return unwrap(response.data);
}

export async function generateRecruiterPipelineInsights(payload: { organization_id: string; job_id?: string }): Promise<AIRecruiterReport> {
  const response = await api.post<ApiResponse<AIRecruiterReport>>("/ai/recruiter/pipeline-insights/", payload);
  return unwrap(response.data);
}

export async function getRecruiterAIHistory(): Promise<AIRecruiterReport[]> {
  const response = await api.get<ApiResponse<AIRecruiterReport[]>>("/ai/recruiter/history/");
  return unwrap(response.data);
}

export async function getRecruiterAIAnalytics(): Promise<AIRecruiterAnalytics> {
  const response = await api.get<ApiResponse<AIRecruiterAnalytics>>("/ai/recruiter/analytics/");
  return unwrap(response.data);
}

export async function askLearningTutor(payload: { course_id: string; lesson_id?: string; question?: string; mode?: string }): Promise<AILearningTutorSession> {
  const response = await api.post<ApiResponse<AILearningTutorSession>>("/ai/learning/course-tutor/", payload);
  return unwrap(response.data);
}

export async function generateLessonIntelligence(payload: { course_id: string; lesson_id: string; regenerate?: boolean }): Promise<AILessonIntelligence> {
  const response = await api.post<ApiResponse<AILessonIntelligence>>("/ai/learning/lesson-summary/", payload);
  return unwrap(response.data);
}

export async function generateStudyPlan(payload: { cadence?: "daily" | "weekly" | "monthly"; pace?: "relaxed" | "balanced" | "intensive"; available_minutes_per_day?: number; deadline?: string; career_goal_id?: string }): Promise<AIStudyPlan> {
  const response = await api.post<ApiResponse<AIStudyPlan>>("/ai/learning/study-plan/", payload);
  return unwrap(response.data);
}

export async function generateLearningQuiz(payload: { course_id: string; lesson_id?: string; difficulty?: "beginner" | "intermediate" | "advanced"; number_of_questions?: number; learning_objectives?: string[]; include_coding_foundation?: boolean }): Promise<AIGeneratedQuiz> {
  const response = await api.post<ApiResponse<AIGeneratedQuiz>>("/ai/learning/quiz-generation/", payload);
  return unwrap(response.data);
}

export async function generateQuizFeedback(payload: { course_id: string; attempt_id?: string }): Promise<AIQuizFeedback> {
  const response = await api.post<ApiResponse<AIQuizFeedback>>("/ai/learning/quiz-feedback/", payload);
  return unwrap(response.data);
}

export async function runInstructorLearningTool(payload: { course_id: string; lesson_id?: string; tool?: string; difficulty?: "beginner" | "intermediate" | "advanced"; number_of_questions?: number }): Promise<Record<string, unknown>> {
  const response = await api.post<ApiResponse<Record<string, unknown>>>("/ai/learning/instructor-tools/", payload);
  return unwrap(response.data);
}

export async function getLearningHistory(): Promise<AILearningHistory> {
  const response = await api.get<ApiResponse<AILearningHistory>>("/ai/learning/history/");
  return unwrap(response.data);
}

export async function getLearningAnalytics(): Promise<AILearningAnalytics> {
  const response = await api.get<ApiResponse<AILearningAnalytics>>("/ai/learning/analytics/");
  return unwrap(response.data);
}

export async function getAIHistory(): Promise<AIRequest[]> {
  const response = await api.get<ApiResponse<AIRequest[]>>("/ai/history/");
  return unwrap(response.data);
}

export async function getAISettings(): Promise<AISettings> {
  const response = await api.get<ApiResponse<AISettings>>("/ai/settings/");
  return unwrap(response.data);
}

export async function getAIAdminOverview(): Promise<AIAdminOverview> {
  const response = await api.get<ApiResponse<AIAdminOverview>>("/ai/admin/");
  return unwrap(response.data);
}

export async function getKnowledgeIndexStatus(): Promise<AIKnowledgeIndexStatus> {
  const response = await api.get<ApiResponse<AIKnowledgeIndexStatus>>("/ai/knowledge/index-status/");
  return unwrap(response.data);
}

export async function getKnowledgeEmbeddingStatus(): Promise<AIKnowledgeEmbeddingStatus> {
  const response = await api.get<ApiResponse<AIKnowledgeEmbeddingStatus>>("/ai/knowledge/embedding-status/");
  return unwrap(response.data);
}

export async function searchKnowledge(payload: { query: string; feature?: string; collection_types?: string[]; search_type?: "semantic" | "hybrid" | "keyword"; limit?: number; include_private?: boolean }): Promise<AIKnowledgeSearchResult> {
  const response = await api.post<ApiResponse<AIKnowledgeSearchResult>>("/ai/knowledge/search/", payload);
  return unwrap(response.data);
}

export async function reindexKnowledge(payload: { source_type: string; source_id?: string; collection_type?: string; title?: string; text?: string; visibility?: "public" | "organization" | "private"; metadata?: Record<string, unknown> }): Promise<{ indexed: Array<Record<string, unknown>> }> {
  const response = await api.post<ApiResponse<{ indexed: Array<Record<string, unknown>> }>>("/ai/knowledge/reindex/", payload);
  return unwrap(response.data);
}

export async function getAIProviderStatus(): Promise<AIProviderStatus> {
  const response = await api.get<ApiResponse<AIProviderStatus>>("/ai/providers/status/");
  return unwrap(response.data);
}

export async function getAICostSummary(): Promise<AICostSummary> {
  const response = await api.get<ApiResponse<AICostSummary>>("/ai/costs/");
  return unwrap(response.data);
}

export async function getAIEvaluations(): Promise<AIEvaluationSummary> {
  const response = await api.get<ApiResponse<AIEvaluationSummary>>("/ai/evaluations/");
  return unwrap(response.data);
}

export async function getAIFeatureFlags(): Promise<AIFeatureFlag[]> {
  const response = await api.get<ApiResponse<AIFeatureFlag[]>>("/ai/feature-flags/");
  return unwrap(response.data);
}

export async function getAIQualityDashboard(): Promise<AIQualityDashboard> {
  const response = await api.get<ApiResponse<AIQualityDashboard>>("/ai/quality/");
  return unwrap(response.data);
}

export async function submitAIFeedback(payload: { request_id?: string; feature: string; rating: AIFeedback["rating"]; comment?: string }): Promise<AIFeedback> {
  const response = await api.post<ApiResponse<AIFeedback>>("/ai/feedback/", payload);
  return unwrap(response.data);
}

export async function runFilteredEvaluations(payload: { dataset_type?: string; feature?: string; provider?: string; prompt_version?: string; limit?: number; dry_run?: boolean; budget?: Record<string, unknown> }): Promise<AIEvaluationRunResponse> {
  const response = await api.post<ApiResponse<AIEvaluationRunResponse>>("/ai/evaluations/run-filtered/", payload);
  return unwrap(response.data);
}

export async function getAIReviewerQueue(params?: { feature?: string; dataset_type?: string; risk_tag?: string; status?: string }): Promise<AIReviewerQueue> {
  const response = await api.get<ApiResponse<AIReviewerQueue>>("/ai/evaluations/reviewer-queue/", { params });
  return unwrap(response.data);
}

export async function reviewAIResult(resultId: string, payload: { status: string; manual_score?: string; hallucination_flag?: boolean; bias_flag?: boolean; unsafe_flag?: boolean; request_prompt_revision?: boolean; notes?: string }): Promise<AIEvaluationReview> {
  const response = await api.post<ApiResponse<AIEvaluationReview>>(`/ai/evaluations/results/${resultId}/review/`, payload);
  return unwrap(response.data);
}

export async function bulkAssignAIReviews(reviewIds: string[], assignedTo: string): Promise<AIEvaluationReview[]> {
  const response = await api.post<ApiResponse<AIEvaluationReview[]>>("/ai/evaluations/reviewer-queue/bulk-assign/", { review_ids: reviewIds, assigned_to: assignedTo });
  return unwrap(response.data);
}

export async function bulkApproveAIReviews(reviewIds: string[], notes = ""): Promise<AIEvaluationReview[]> {
  const response = await api.post<ApiResponse<AIEvaluationReview[]>>("/ai/evaluations/reviewer-queue/bulk-approve/", { review_ids: reviewIds, notes });
  return unwrap(response.data);
}

export async function getRedTeamSuites(): Promise<AIRedTeamSuite[]> {
  const response = await api.get<ApiResponse<AIRedTeamSuite[]>>("/ai/red-team/suites/");
  return unwrap(response.data);
}

export async function runRedTeamSuite(suiteId: string): Promise<Array<Record<string, unknown>>> {
  const response = await api.post<ApiResponse<Array<Record<string, unknown>>>>("/ai/red-team/run/", { suite_id: suiteId });
  return unwrap(response.data);
}

export async function createAIComparison(payload: { comparison_type: string; feature: string; left_label: string; right_label: string }): Promise<AIComparisonReport> {
  const response = await api.post<ApiResponse<AIComparisonReport>>("/ai/comparisons/", payload);
  return unwrap(response.data);
}

export async function createAIAuditExport(payload: { export_type: string; file_format: "csv" | "xlsx" }): Promise<AIAuditExport> {
  const response = await api.post<ApiResponse<AIAuditExport>>("/ai/audit-exports/", payload);
  return unwrap(response.data);
}

export async function getAIReleaseGates(): Promise<AIReleaseGate[]> {
  const response = await api.get<ApiResponse<AIReleaseGate[]>>("/ai/release-gates/");
  return unwrap(response.data);
}

export async function createAIReleaseGate(payload: { change_type: string; target_id: string; feature: string; previous_version?: Record<string, unknown>; new_version?: Record<string, unknown>; evaluation_run_id?: string; thresholds?: Record<string, unknown> }): Promise<AIReleaseGate> {
  const response = await api.post<ApiResponse<AIReleaseGate>>("/ai/release-gates/", payload);
  return unwrap(response.data);
}

export async function actOnAIReleaseGate(gateId: string, action: "promote" | "rollback", reason = ""): Promise<AIReleaseGate> {
  const response = await api.post<ApiResponse<AIReleaseGate>>(`/ai/release-gates/${gateId}/action/`, { action, reason });
  return unwrap(response.data);
}

export async function getAILaunchChecklist(): Promise<AIReleaseGovernanceSummary["launch_checklist"]> {
  const response = await api.get<ApiResponse<AIReleaseGovernanceSummary["launch_checklist"]>>("/ai/launch-checklist/");
  return unwrap(response.data);
}

export async function cancelAIRequest(requestId: string): Promise<AIRequest> {
  const response = await api.post<ApiResponse<AIRequest>>(`/ai/requests/${requestId}/cancel/`);
  return unwrap(response.data);
}

export async function getInterviewSessions(): Promise<AIInterviewSession[]> {
  const response = await api.get<ApiResponse<AIInterviewSession[]>>("/ai/interview/sessions/");
  return unwrap(response.data);
}

export async function startInterviewSession(payload: AIInterviewStartPayload): Promise<AIInterviewSession> {
  const response = await api.post<ApiResponse<AIInterviewSession>>("/ai/interview/sessions/", payload);
  return unwrap(response.data);
}

export async function getInterviewSession(sessionId: string): Promise<AIInterviewSession> {
  const response = await api.get<ApiResponse<AIInterviewSession>>(`/ai/interview/sessions/${sessionId}/`);
  return unwrap(response.data);
}

export async function generateInterviewQuestion(sessionId: string): Promise<AIInterviewQuestion> {
  const response = await api.post<ApiResponse<AIInterviewQuestion>>(`/ai/interview/sessions/${sessionId}/next-question/`);
  return unwrap(response.data);
}

export async function submitInterviewAnswer(sessionId: string, questionId: string, answerText: string): Promise<AIInterviewEvaluation> {
  const response = await api.post<ApiResponse<AIInterviewEvaluation>>(`/ai/interview/sessions/${sessionId}/submit-answer/`, {
    question_id: questionId,
    answer_text: answerText,
  });
  return unwrap(response.data);
}

export async function finishInterviewSession(sessionId: string): Promise<AIInterviewSession> {
  const response = await api.post<ApiResponse<AIInterviewSession>>(`/ai/interview/sessions/${sessionId}/finish/`);
  return unwrap(response.data);
}

export async function pauseInterviewSession(sessionId: string): Promise<AIInterviewSession> {
  const response = await api.post<ApiResponse<AIInterviewSession>>(`/ai/interview/sessions/${sessionId}/pause/`);
  return unwrap(response.data);
}

export async function resumeInterviewSession(sessionId: string): Promise<AIInterviewSession> {
  const response = await api.post<ApiResponse<AIInterviewSession>>(`/ai/interview/sessions/${sessionId}/resume/`);
  return unwrap(response.data);
}

export async function cancelInterviewSession(sessionId: string): Promise<AIInterviewSession> {
  const response = await api.post<ApiResponse<AIInterviewSession>>(`/ai/interview/sessions/${sessionId}/cancel/`);
  return unwrap(response.data);
}

export async function getInterviewAnalytics(): Promise<AIInterviewAnalytics> {
  const response = await api.get<ApiResponse<AIInterviewAnalytics>>("/ai/interview/analytics/");
  return unwrap(response.data);
}

export async function getInterviewTemplates(organizationId?: string): Promise<AIInterviewTemplate[]> {
  const response = await api.get<ApiResponse<AIInterviewTemplate[]>>("/ai/interview/templates/", {
    params: organizationId ? { organization_id: organizationId } : undefined,
  });
  return unwrap(response.data);
}

export async function streamAIChat(
  inputText: string,
  feature: string,
  onEvent: (event: AIStreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  const response = await fetch(`${apiUrl}/ai/chat/`, {
    method: "POST",
    credentials: "include",
    signal,
    headers: {
      "Content-Type": "application/json",
      ...(getAccessToken() ? { Authorization: `Bearer ${getAccessToken()}` } : {}),
    },
    body: JSON.stringify({ input_text: inputText, feature, stream: true }),
  });
  if (!response.ok || !response.body) {
    throw new Error("AI stream failed.");
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      const line = part.split("\n").find((item) => item.startsWith("data: "));
      if (!line) continue;
      onEvent(JSON.parse(line.slice(6)) as AIStreamEvent);
    }
  }
}
