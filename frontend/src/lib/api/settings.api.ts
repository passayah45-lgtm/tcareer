import api from "./client";

function unwrap<T>(payload: { data?: T } | T): T {
  if (payload && typeof payload === "object" && "data" in payload) {
    return (payload as { data: T }).data;
  }
  return payload as T;
}

export interface PrivacySettings {
  public_profile: boolean;
  recruiter_resume_visibility: boolean;
  recruiter_portfolio_visibility: boolean;
  open_to_work: boolean;
  allow_recruiter_contact: boolean;
  allow_analytics: boolean;
  allow_ai_analysis: boolean;
}

export async function getPrivacySettings(): Promise<PrivacySettings> {
  const res = await api.get<PrivacySettings>("/auth/privacy/");
  return unwrap<PrivacySettings>(res.data);
}

export async function updatePrivacySettings(payload: Partial<PrivacySettings>): Promise<PrivacySettings> {
  const res = await api.patch<PrivacySettings>("/auth/privacy/", payload);
  return unwrap<PrivacySettings>(res.data);
}
