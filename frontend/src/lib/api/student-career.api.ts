import api from "@/lib/api/client";
import type { ApiResponse } from "@/types/api.types";
import type {
  SavedJob,
  SavedJobCollection,
  ApplicationAnswer,
  ApplicationPreview,
  StudentApplication,
  StudentApplicationDetail,
  StudentDashboard,
  StudentJob,
} from "@/types/student-career.types";

function dataOrRaw<T>(payload: ApiResponse<T> | T): T {
  if (payload && typeof payload === "object" && "data" in payload) {
    return (payload as ApiResponse<T>).data;
  }
  return payload as T;
}

function query(params: Record<string, string | number | boolean | undefined | null>) {
  const out = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") out.set(key, String(value));
  });
  return out.toString();
}

export async function getStudentDashboard(): Promise<StudentDashboard> {
  const res = await api.get<ApiResponse<StudentDashboard>>("/jobs/student/dashboard/");
  return res.data.data;
}

export async function browseJobs(params: Record<string, string | number | boolean | undefined | null>) {
  const res = await api.get(`/jobs/${query(params) ? `?${query(params)}` : ""}`);
  const payload = dataOrRaw<{ count: number; results: StudentJob[]; meta?: { page: number; page_size: number } }>(res.data);
  return { count: payload.count ?? payload.results?.length ?? 0, results: payload.results ?? [], meta: payload.meta };
}

export async function getJob(jobId: string): Promise<StudentJob> {
  const res = await api.get<ApiResponse<StudentJob> | StudentJob>(`/jobs/${jobId}/`);
  return dataOrRaw<StudentJob>(res.data);
}

export async function applyToJob(jobId: string, payload: { cover_letter: string; resume_id?: string; portfolio_id?: string; answers?: ApplicationAnswer[] }): Promise<StudentApplication> {
  const res = await api.post<ApiResponse<StudentApplication>>(`/jobs/${jobId}/apply/`, payload);
  return res.data.data;
}

export async function saveApplicationDraft(jobId: string, payload: { cover_letter: string; resume_id?: string; portfolio_id?: string; answers?: ApplicationAnswer[] }): Promise<StudentApplication> {
  const res = await api.post<ApiResponse<StudentApplication>>(`/jobs/${jobId}/draft/`, payload);
  return res.data.data;
}

export async function previewApplication(jobId: string, payload: { cover_letter: string; resume_id?: string; portfolio_id?: string; answers?: ApplicationAnswer[] }): Promise<ApplicationPreview> {
  const res = await api.post<ApiResponse<ApplicationPreview>>(`/jobs/${jobId}/preview/`, payload);
  return res.data.data;
}

export async function trackRecommendedJobClick(jobId: string): Promise<void> {
  await api.post(`/jobs/${jobId}/recommended-click/`);
}

export async function submitApplication(applicationId: string): Promise<StudentApplication> {
  const res = await api.post<ApiResponse<StudentApplication>>(`/jobs/student/applications/${applicationId}/submit/`);
  return res.data.data;
}

export async function withdrawApplication(applicationId: string): Promise<StudentApplication> {
  const res = await api.post<ApiResponse<StudentApplication>>(`/jobs/applications/${applicationId}/withdraw/`);
  return res.data.data;
}

export async function getMyApplications(): Promise<StudentApplication[]> {
  const res = await api.get<ApiResponse<StudentApplication[]>>("/jobs/student/applications/");
  return res.data.data;
}

export async function getApplicationDetail(applicationId: string): Promise<StudentApplicationDetail> {
  const res = await api.get<ApiResponse<StudentApplicationDetail>>(`/jobs/student/applications/${applicationId}/`);
  return res.data.data;
}

export async function getSavedJobs(): Promise<SavedJob[]> {
  const res = await api.get<ApiResponse<SavedJob[]>>("/jobs/student/saved/");
  return res.data.data;
}

export async function saveJob(payload: { job_id: string; collection?: string | null; notes?: string; is_favorite_company?: boolean }): Promise<SavedJob> {
  const res = await api.post<ApiResponse<SavedJob>>("/jobs/student/saved/", payload);
  return res.data.data;
}

export async function removeSavedJob(jobId: string): Promise<void> {
  await api.delete(`/jobs/student/saved/${jobId}/`);
}

export async function getSavedJobCollections(): Promise<SavedJobCollection[]> {
  const res = await api.get<ApiResponse<SavedJobCollection[]>>("/jobs/student/collections/");
  return res.data.data;
}

export async function createSavedJobCollection(payload: { name: string; description?: string }): Promise<SavedJobCollection> {
  const res = await api.post<ApiResponse<SavedJobCollection>>("/jobs/student/collections/", payload);
  return res.data.data;
}
