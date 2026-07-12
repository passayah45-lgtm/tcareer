import api from "./client";
import type { ApiResponse } from "@/types/api.types";
import type {
  Portfolio,
  PortfolioUpdatePayload,
  PortfolioSkill,
  PortfolioProject,
  PortfolioProjectMedia,
  PortfolioAIAnalytics,
  PortfolioAIReview,
  SkillSyncResult,
  Resume,
  ResumeUpdatePayload,
  CareerResume,
  CareerResumeFile,
  CareerResumePayload,
  PublicPortfolio,
  ResumeAIAnalytics,
  ResumeAIReview,
} from "@/types/careers.types";

// ── Portfolio ─────────────────────────────────────────────────────────────────

export async function getMyPortfolio(): Promise<Portfolio> {
  const res = await api.get<ApiResponse<Portfolio>>("/careers/portfolio/me/");
  return res.data.data;
}

export async function updateMyPortfolio(
  payload: PortfolioUpdatePayload
): Promise<Portfolio> {
  const res = await api.patch<ApiResponse<Portfolio>>(
    "/careers/portfolio/me/",
    payload
  );
  return res.data.data;
}

// ── Skills ─────────────────────────────────────────────────────────────────────

export async function getMySkills(): Promise<PortfolioSkill[]> {
  const res = await api.get<ApiResponse<PortfolioSkill[]>>(
    "/careers/portfolio/me/skills/"
  );
  return res.data.data;
}

export async function addSkill(payload: {
  name: string;
  category?: string;
}): Promise<PortfolioSkill> {
  const res = await api.post<ApiResponse<PortfolioSkill>>(
    "/careers/portfolio/me/skills/",
    payload
  );
  return res.data.data;
}

export async function deleteSkill(skillId: string): Promise<void> {
  await api.delete(`/careers/portfolio/me/skills/${skillId}/`);
}

export async function syncSkills(): Promise<SkillSyncResult> {
  const res = await api.post<ApiResponse<SkillSyncResult>>(
    "/careers/portfolio/me/skills/sync/"
  );
  return res.data.data;
}

// ── Projects ───────────────────────────────────────────────────────────────────

export async function getMyProjects(): Promise<PortfolioProject[]> {
  const res = await api.get<ApiResponse<PortfolioProject[]>>(
    "/careers/portfolio/me/projects/"
  );
  return res.data.data;
}

export async function createProject(
  payload: Partial<PortfolioProject>
): Promise<PortfolioProject> {
  const res = await api.post<ApiResponse<PortfolioProject>>(
    "/careers/portfolio/me/projects/",
    payload
  );
  return res.data.data;
}

export async function updateProject(
  projectId: string,
  payload: Partial<PortfolioProject>
): Promise<PortfolioProject> {
  const res = await api.patch<ApiResponse<PortfolioProject>>(
    `/careers/portfolio/me/projects/${projectId}/`,
    payload
  );
  return res.data.data;
}

export async function deleteProject(projectId: string): Promise<void> {
  await api.delete(`/careers/portfolio/me/projects/${projectId}/`);
}

export async function addProjectMedia(
  projectId: string,
  payload: Partial<PortfolioProjectMedia>
): Promise<PortfolioProjectMedia> {
  const res = await api.post<ApiResponse<PortfolioProjectMedia>>(
    `/careers/portfolio/me/projects/${projectId}/media/`,
    payload
  );
  return res.data.data;
}

export async function uploadProjectMedia(
  projectId: string,
  payload: { file: File; title?: string; description?: string; visibility?: string; position?: number; is_featured?: boolean }
): Promise<PortfolioProjectMedia> {
  const form = new FormData();
  form.append("file", payload.file);
  form.append("title", payload.title || payload.file.name);
  form.append("description", payload.description || "");
  form.append("visibility", payload.visibility || "public");
  form.append("position", String(payload.position ?? 0));
  form.append("is_featured", String(Boolean(payload.is_featured)));
  const res = await api.post<ApiResponse<PortfolioProjectMedia>>(
    `/careers/portfolio/me/projects/${projectId}/media/`,
    form,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return res.data.data;
}

export async function updateProjectMedia(
  projectId: string,
  mediaId: string,
  payload: Partial<PortfolioProjectMedia>
): Promise<PortfolioProjectMedia> {
  const res = await api.patch<ApiResponse<PortfolioProjectMedia>>(
    `/careers/portfolio/me/projects/${projectId}/media/${mediaId}/`,
    payload
  );
  return res.data.data;
}

export async function deleteProjectMedia(
  projectId: string,
  mediaId: string
): Promise<void> {
  await api.delete(`/careers/portfolio/me/projects/${projectId}/media/${mediaId}/`);
}

export async function runPortfolioAIReview(): Promise<PortfolioAIReview> {
  const res = await api.post<ApiResponse<PortfolioAIReview>>("/careers/portfolio/me/ai/review/");
  return res.data.data;
}

export async function runPortfolioAIProjectReview(projectId: string): Promise<PortfolioAIReview> {
  const res = await api.post<ApiResponse<PortfolioAIReview>>("/careers/portfolio/me/ai/project-review/", { project_id: projectId });
  return res.data.data;
}

export async function runPortfolioAIGitHubReview(projectId?: string): Promise<PortfolioAIReview> {
  const res = await api.post<ApiResponse<PortfolioAIReview>>("/careers/portfolio/me/ai/github/", projectId ? { project_id: projectId } : {});
  return res.data.data;
}

export async function runPortfolioAISkillExtraction(): Promise<PortfolioAIReview> {
  const res = await api.post<ApiResponse<PortfolioAIReview>>("/careers/portfolio/me/ai/skills/");
  return res.data.data;
}

export async function runPortfolioAIJobMatch(jobId: string): Promise<PortfolioAIReview> {
  const res = await api.post<ApiResponse<PortfolioAIReview>>("/careers/portfolio/me/ai/job-match/", { job_id: jobId });
  return res.data.data;
}

export async function getPortfolioAIHistory(): Promise<PortfolioAIReview[]> {
  const res = await api.get<ApiResponse<PortfolioAIReview[]>>("/careers/portfolio/me/ai/history/");
  return res.data.data;
}

export async function getPortfolioAIAnalytics(): Promise<PortfolioAIAnalytics> {
  const res = await api.get<ApiResponse<PortfolioAIAnalytics>>("/careers/portfolio/me/ai/analytics/");
  return res.data.data;
}

// ── Public portfolio ───────────────────────────────────────────────────────────

export async function getPublicPortfolio(
  username: string
): Promise<PublicPortfolio> {
  const res = await api.get<ApiResponse<PublicPortfolio>>(
    `/careers/portfolio/${username}/`
  );
  return res.data.data;
}

// ── Resume ─────────────────────────────────────────────────────────────────────

export async function getMyResume(): Promise<Resume> {
  const res = await api.get<ApiResponse<Resume>>("/careers/resume/me/");
  return res.data.data;
}

export async function updateMyResume(
  payload: ResumeUpdatePayload
): Promise<Resume> {
  const res = await api.patch<ApiResponse<Resume>>(
    "/careers/resume/me/",
    payload
  );
  return res.data.data;
}

export async function generateResumePdf(): Promise<{
  pdf_url: string;
  generated_at: string;
}> {
  const res = await api.post<ApiResponse<{ pdf_url: string; generated_at: string }>>(
    "/careers/resume/me/generate-pdf/"
  );
  return res.data.data;
}

export async function getCareerResumes(): Promise<CareerResume[]> {
  const res = await api.get<ApiResponse<CareerResume[]>>("/careers/resumes/");
  return res.data.data;
}

export async function createCareerResume(
  payload: CareerResumePayload
): Promise<CareerResume> {
  const res = await api.post<ApiResponse<CareerResume>>("/careers/resumes/", payload);
  return res.data.data;
}

export async function getCareerResume(resumeId: string): Promise<CareerResume> {
  const res = await api.get<ApiResponse<CareerResume>>(`/careers/resumes/${resumeId}/`);
  return res.data.data;
}

export async function updateCareerResume(
  resumeId: string,
  payload: Partial<CareerResumePayload>
): Promise<CareerResume> {
  const res = await api.patch<ApiResponse<CareerResume>>(
    `/careers/resumes/${resumeId}/`,
    payload
  );
  return res.data.data;
}

export async function duplicateCareerResume(resumeId: string): Promise<CareerResume> {
  const res = await api.post<ApiResponse<CareerResume>>(
    `/careers/resumes/${resumeId}/duplicate/`
  );
  return res.data.data;
}

export async function setDefaultCareerResume(resumeId: string): Promise<CareerResume> {
  const res = await api.post<ApiResponse<CareerResume>>(
    `/careers/resumes/${resumeId}/default/`
  );
  return res.data.data;
}

export async function archiveCareerResume(resumeId: string): Promise<CareerResume> {
  const res = await api.post<ApiResponse<CareerResume>>(
    `/careers/resumes/${resumeId}/archive/`
  );
  return res.data.data;
}

export async function uploadCareerResumeFile(
  resumeId: string,
  payload: { file_url: string; file_name: string; content_type?: string; is_private?: boolean }
): Promise<CareerResume> {
  const res = await api.post<ApiResponse<CareerResume>>(
    `/careers/resumes/${resumeId}/files/`,
    payload
  );
  return res.data.data;
}

export async function uploadCareerResumeBinary(
  resumeId: string,
  file: File
): Promise<CareerResumeFile> {
  const form = new FormData();
  form.append("file", file);
  const res = await api.post<ApiResponse<CareerResumeFile>>(
    `/careers/resumes/${resumeId}/files/`,
    form,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return res.data.data;
}

export async function downloadCareerResume(
  resumeId: string
): Promise<{ download_url: string; file_name: string; tracked_at: string }> {
  const res = await api.post<ApiResponse<{ download_url: string; file_name: string; tracked_at: string }>>(
    `/careers/resumes/${resumeId}/download/`
  );
  return res.data.data;
}

export async function runResumeAIReview(resumeId: string): Promise<ResumeAIReview> {
  const res = await api.post<ApiResponse<ResumeAIReview>>(`/careers/resumes/${resumeId}/ai/review/`);
  return res.data.data;
}

export async function runResumeAISkillExtraction(resumeId: string): Promise<ResumeAIReview> {
  const res = await api.post<ApiResponse<ResumeAIReview>>(`/careers/resumes/${resumeId}/ai/skills/`);
  return res.data.data;
}

export async function runResumeAIATS(resumeId: string): Promise<ResumeAIReview> {
  const res = await api.post<ApiResponse<ResumeAIReview>>(`/careers/resumes/${resumeId}/ai/ats/`);
  return res.data.data;
}

export async function runResumeAIJobMatch(resumeId: string, jobId: string): Promise<ResumeAIReview> {
  const res = await api.post<ApiResponse<ResumeAIReview>>(`/careers/resumes/${resumeId}/ai/job-match/`, { job_id: jobId });
  return res.data.data;
}

export async function runResumeAIComparison(resumeId: string, comparisonResumeId: string): Promise<ResumeAIReview> {
  const res = await api.post<ApiResponse<ResumeAIReview>>(`/careers/resumes/${resumeId}/ai/compare/`, { comparison_resume_id: comparisonResumeId });
  return res.data.data;
}

export async function getResumeAIHistory(resumeId: string): Promise<ResumeAIReview[]> {
  const res = await api.get<ApiResponse<ResumeAIReview[]>>(`/careers/resumes/${resumeId}/ai/history/`);
  return res.data.data;
}

export async function getResumeAIAnalytics(resumeId: string): Promise<ResumeAIAnalytics> {
  const res = await api.get<ApiResponse<ResumeAIAnalytics>>(`/careers/resumes/${resumeId}/ai/analytics/`);
  return res.data.data;
}
