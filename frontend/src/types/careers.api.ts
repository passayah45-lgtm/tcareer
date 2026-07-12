

import api from "@/lib/api/client";
import type { ApiResponse } from "@/types/api.types";
import type {
  Portfolio,
  PortfolioUpdatePayload,
  PortfolioSkill,
  SkillCreatePayload,
  SkillSyncResult,
  PortfolioProject,
  PublicPortfolio,
  Resume,
  ResumeUpdatePayload,
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

// ── Skills ────────────────────────────────────────────────────────────────────

export async function getMySkills(): Promise<PortfolioSkill[]> {
  const res = await api.get<ApiResponse<PortfolioSkill[]>>(
    "/careers/portfolio/me/skills/"
  );
  return res.data.data;
}

export async function addSkill(
  payload: SkillCreatePayload
): Promise<PortfolioSkill> {
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

// ── Projects ──────────────────────────────────────────────────────────────────

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

// ── Public portfolio ──────────────────────────────────────────────────────────

export async function getPublicPortfolio(
  username: string
): Promise<PublicPortfolio> {
  const res = await api.get<ApiResponse<PublicPortfolio>>(
    `/careers/portfolio/${username}/`
  );
  return res.data.data;
}

// ── Resume ────────────────────────────────────────────────────────────────────

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

type PdfResponse = { pdf_url: string; generated_at: string };

export async function generateResumePdf(): Promise<PdfResponse> {
  const res = await api.post<ApiResponse<PdfResponse>>(
    "/careers/resume/me/generate-pdf/"
  );
  return res.data.data;
}