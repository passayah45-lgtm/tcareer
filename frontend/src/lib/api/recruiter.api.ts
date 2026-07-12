import api from "./client";
import type { ApiResponse } from "@/types/api.types";
import type {
  ApplicationNote,
  ApplicationQuestion,
  ApplicationQuestionPayload,
  ApplicationStage,
  ApplicationTimelineEntry,
  ApplicationDetail,
  CandidateSearchResult,
  Interview,
  JobApplication,
  Organization,
  OrganizationMember,
  PipelineResponse,
  RecruiterDashboard,
  RecruiterSettings,
  RecruiterJob,
  RecruiterJobPayload,
  SavedCandidate,
  TalentPool,
} from "@/types/recruiter.types";

function dataOrRaw<T>(payload: ApiResponse<T> | T): T {
  if (payload && typeof payload === "object" && "data" in payload) {
    return (payload as ApiResponse<T>).data;
  }
  return payload as T;
}

function toQuery(params: Record<string, string | number | boolean | undefined | null>) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") query.append(key, String(value));
  });
  return query.toString();
}

export async function getOrganizations(): Promise<Organization[]> {
  const res = await api.get<ApiResponse<Organization[]> | Organization[]>("/organizations/");
  return dataOrRaw<Organization[]>(res.data);
}

export async function getOrganizationMembers(organizationId: string): Promise<OrganizationMember[]> {
  const res = await api.get<ApiResponse<OrganizationMember[]> | OrganizationMember[]>(`/organizations/${organizationId}/members/`);
  return dataOrRaw<OrganizationMember[]>(res.data);
}

export async function getRecruiterSettings(organizationId: string): Promise<RecruiterSettings> {
  const res = await api.get<ApiResponse<RecruiterSettings>>(`/organizations/${organizationId}/recruiter-settings/`);
  return res.data.data;
}

export async function inviteRecruiter(organizationId: string, email: string): Promise<void> {
  await api.post(`/organizations/${organizationId}/invitations/`, { email, role: "recruiter" });
}

export async function changeOrganizationMemberRole(organizationId: string, membershipId: string, role: string): Promise<void> {
  await api.patch(`/organizations/${organizationId}/members/${membershipId}/role/`, { role });
}

export async function removeOrganizationMember(organizationId: string, membershipId: string): Promise<void> {
  await api.delete(`/organizations/${organizationId}/members/${membershipId}/`);
}

export async function getRecruiterDashboard(organizationId: string): Promise<RecruiterDashboard> {
  const res = await api.get<ApiResponse<RecruiterDashboard>>(`/jobs/organizations/${organizationId}/dashboard/`);
  return res.data.data;
}

export async function getOrganizationJobs(organizationId: string): Promise<RecruiterJob[]> {
  const res = await api.get<ApiResponse<RecruiterJob[]> | RecruiterJob[]>(`/jobs/organizations/${organizationId}/`);
  return dataOrRaw<RecruiterJob[]>(res.data);
}

export async function createOrganizationJob(organizationId: string, payload: RecruiterJobPayload): Promise<RecruiterJob> {
  const res = await api.post<ApiResponse<RecruiterJob> | RecruiterJob>(`/jobs/organizations/${organizationId}/`, payload);
  return dataOrRaw<RecruiterJob>(res.data);
}

export async function updateOrganizationJob(organizationId: string, jobId: string, payload: Partial<RecruiterJobPayload>): Promise<RecruiterJob> {
  const res = await api.patch<ApiResponse<RecruiterJob> | RecruiterJob>(`/jobs/organizations/${organizationId}/${jobId}/`, payload);
  return dataOrRaw<RecruiterJob>(res.data);
}

export async function publishOrganizationJob(organizationId: string, jobId: string): Promise<RecruiterJob> {
  const res = await api.post<ApiResponse<RecruiterJob> | RecruiterJob>(`/jobs/organizations/${organizationId}/${jobId}/publish/`);
  return dataOrRaw<RecruiterJob>(res.data);
}

export async function archiveOrganizationJob(organizationId: string, jobId: string): Promise<RecruiterJob> {
  const res = await api.post<ApiResponse<RecruiterJob> | RecruiterJob>(`/jobs/organizations/${organizationId}/${jobId}/archive/`);
  return dataOrRaw<RecruiterJob>(res.data);
}

export async function getJobApplicationQuestions(organizationId: string, jobId: string): Promise<ApplicationQuestion[]> {
  const res = await api.get<ApiResponse<ApplicationQuestion[]> | ApplicationQuestion[]>(`/jobs/organizations/${organizationId}/${jobId}/questions/`);
  return dataOrRaw<ApplicationQuestion[]>(res.data);
}

export async function createJobApplicationQuestion(
  organizationId: string,
  jobId: string,
  payload: ApplicationQuestionPayload,
): Promise<ApplicationQuestion> {
  const res = await api.post<ApiResponse<ApplicationQuestion> | ApplicationQuestion>(`/jobs/organizations/${organizationId}/${jobId}/questions/`, payload);
  return dataOrRaw<ApplicationQuestion>(res.data);
}

export async function updateJobApplicationQuestion(
  organizationId: string,
  jobId: string,
  questionId: string,
  payload: Partial<ApplicationQuestionPayload>,
): Promise<ApplicationQuestion> {
  const res = await api.patch<ApiResponse<ApplicationQuestion> | ApplicationQuestion>(
    `/jobs/organizations/${organizationId}/${jobId}/questions/${questionId}/`,
    payload,
  );
  return dataOrRaw<ApplicationQuestion>(res.data);
}

export async function deleteJobApplicationQuestion(organizationId: string, jobId: string, questionId: string): Promise<ApplicationQuestion> {
  const res = await api.delete<ApiResponse<ApplicationQuestion> | ApplicationQuestion>(`/jobs/organizations/${organizationId}/${jobId}/questions/${questionId}/`);
  return dataOrRaw<ApplicationQuestion>(res.data);
}

export async function getPipelineApplications(
  organizationId: string,
  params: Record<string, string | number | boolean | undefined | null> = {},
): Promise<PipelineResponse> {
  const query = toQuery(params);
  const res = await api.get<ApiResponse<JobApplication[]>>(`/jobs/organizations/${organizationId}/pipeline/${query ? `?${query}` : ""}`);
  return {
    data: res.data.data,
    count: res.data.meta.count ?? 0,
    page: Number(res.data.meta.page ?? 1),
    page_size: Number(res.data.meta.page_size ?? 20),
    pipeline_statistics: (res.data.meta.pipeline_statistics as Record<string, number> | undefined) ?? {},
  };
}

export async function getApplicationTimeline(organizationId: string, applicationId: string): Promise<ApplicationTimelineEntry[]> {
  const res = await api.get<ApiResponse<ApplicationTimelineEntry[]>>(`/jobs/organizations/${organizationId}/applications/${applicationId}/timeline/`);
  return res.data.data;
}

export async function getApplicationDetail(organizationId: string, applicationId: string): Promise<ApplicationDetail> {
  const res = await api.get<ApiResponse<ApplicationDetail>>(`/jobs/organizations/${organizationId}/applications/${applicationId}/`);
  return res.data.data;
}

export async function changeApplicationStage(
  organizationId: string,
  applicationId: string,
  stage: ApplicationStage,
  message = "",
): Promise<JobApplication> {
  const res = await api.post<ApiResponse<JobApplication>>(`/jobs/organizations/${organizationId}/applications/${applicationId}/stage/`, { stage, message });
  return res.data.data;
}

export async function assignApplication(
  organizationId: string,
  applicationId: string,
  payload: { assigned_recruiter?: string | null; hiring_manager?: string | null },
): Promise<JobApplication> {
  const res = await api.post<ApiResponse<JobApplication>>(`/jobs/organizations/${organizationId}/applications/${applicationId}/assign/`, payload);
  return res.data.data;
}

export async function getApplicationNotes(organizationId: string, applicationId: string): Promise<ApplicationNote[]> {
  const res = await api.get<ApiResponse<ApplicationNote[]>>(`/jobs/organizations/${organizationId}/applications/${applicationId}/notes/`);
  return res.data.data;
}

export async function addApplicationNote(
  organizationId: string,
  applicationId: string,
  payload: { body: string; is_internal: boolean },
): Promise<ApplicationNote> {
  const res = await api.post<ApiResponse<ApplicationNote>>(`/jobs/organizations/${organizationId}/applications/${applicationId}/notes/`, payload);
  return res.data.data;
}

export async function bulkRejectApplications(organizationId: string, applicationIds: string[], message = ""): Promise<JobApplication[]> {
  const res = await api.post<ApiResponse<JobApplication[]>>(`/jobs/organizations/${organizationId}/applications/bulk-reject/`, {
    application_ids: applicationIds,
    message,
  });
  return res.data.data;
}

export async function bulkArchiveApplications(organizationId: string, applicationIds: string[]): Promise<JobApplication[]> {
  const res = await api.post<ApiResponse<JobApplication[]>>(`/jobs/organizations/${organizationId}/applications/bulk-archive/`, {
    application_ids: applicationIds,
  });
  return res.data.data;
}

export async function searchCandidates(
  organizationId: string,
  params: Record<string, string | number | boolean | undefined | null>,
): Promise<{ data: CandidateSearchResult[]; count: number }> {
  const query = toQuery(params);
  const res = await api.get<ApiResponse<CandidateSearchResult[]>>(`/jobs/organizations/${organizationId}/candidates/${query ? `?${query}` : ""}`);
  return { data: res.data.data, count: res.data.meta.count ?? 0 };
}

export async function unlockCandidate(organizationId: string, candidateId: string): Promise<{ candidate_id: string; is_unlocked: boolean; created: boolean }> {
  const res = await api.post<ApiResponse<{ candidate_id: string; is_unlocked: boolean; created: boolean }>>(
    `/jobs/organizations/${organizationId}/candidates/${candidateId}/unlock/`,
  );
  return res.data.data;
}

export async function getSavedCandidates(organizationId: string): Promise<SavedCandidate[]> {
  const res = await api.get<ApiResponse<SavedCandidate[]>>(`/jobs/organizations/${organizationId}/saved-candidates/`);
  return res.data.data;
}

export async function saveCandidate(
  organizationId: string,
  payload: { candidate_id: string; labels?: string[]; private_notes?: string; talent_pool?: string | null },
): Promise<SavedCandidate> {
  const res = await api.post<ApiResponse<SavedCandidate>>(`/jobs/organizations/${organizationId}/saved-candidates/`, payload);
  return res.data.data;
}

export async function removeSavedCandidate(organizationId: string, candidateId: string): Promise<void> {
  await api.delete(`/jobs/organizations/${organizationId}/saved-candidates/${candidateId}/`);
}

export async function getTalentPools(organizationId: string): Promise<TalentPool[]> {
  const res = await api.get<ApiResponse<TalentPool[]>>(`/jobs/organizations/${organizationId}/talent-pools/`);
  return res.data.data;
}

export async function createTalentPool(organizationId: string, payload: { name: string; description?: string }): Promise<TalentPool> {
  const res = await api.post<ApiResponse<TalentPool>>(`/jobs/organizations/${organizationId}/talent-pools/`, payload);
  return res.data.data;
}

export async function getInterviews(organizationId: string, status?: string): Promise<Interview[]> {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  const res = await api.get<ApiResponse<Interview[]>>(`/jobs/organizations/${organizationId}/interviews/${query}`);
  return res.data.data;
}

export async function scheduleInterview(
  organizationId: string,
  payload: {
    application_id: string;
    interview_type: string;
    scheduled_start: string;
    scheduled_end?: string | null;
    timezone?: string;
    meeting_link?: string;
    location?: string;
    participant_ids?: string[];
  },
): Promise<Interview> {
  const res = await api.post<ApiResponse<Interview>>(`/jobs/organizations/${organizationId}/interviews/`, payload);
  return res.data.data;
}

export async function updateInterview(organizationId: string, interviewId: string, payload: Partial<Interview>): Promise<Interview> {
  const res = await api.patch<ApiResponse<Interview>>(`/jobs/organizations/${organizationId}/interviews/${interviewId}/`, payload);
  return res.data.data;
}

export async function addInterviewFeedback(
  organizationId: string,
  interviewId: string,
  payload: { rating: number; recommendation: string; feedback: string },
): Promise<void> {
  await api.post(`/jobs/organizations/${organizationId}/interviews/${interviewId}/feedback/`, payload);
}

export async function addInterviewScorecard(
  organizationId: string,
  interviewId: string,
  payload: { criteria: Record<string, number>; total_score: number; recommendation: string },
): Promise<void> {
  await api.post(`/jobs/organizations/${organizationId}/interviews/${interviewId}/scorecard/`, payload);
}
