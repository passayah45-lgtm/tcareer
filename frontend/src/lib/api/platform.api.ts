import api from "@/lib/api/client";
import type { ApiResponse } from "@/types/api.types";
import type {
  PlatformAuditSearchResponse,
  PlatformManagementDashboard,
  PlatformOperations,
  PlatformVerificationDetailResponse,
  PlatformVerificationListResponse,
} from "@/types/platform.types";

export async function getPlatformManagementDashboard(): Promise<PlatformManagementDashboard> {
  const response = await api.get<ApiResponse<PlatformManagementDashboard>>("/platform/management/dashboard/");
  return response.data.data;
}

export async function getPlatformOperations(): Promise<PlatformOperations> {
  const response = await api.get<ApiResponse<PlatformOperations>>("/platform/operations/");
  return response.data.data;
}

export async function runPlatformOperation(resource: string, id: string, action: string, payload: Record<string, unknown> = {}): Promise<void> {
  await api.post(`/platform/operations/${resource}/${id}/${action}/`, payload);
}

export async function searchPlatformAudit(params: Record<string, string>): Promise<PlatformAuditSearchResponse> {
  const response = await api.get<ApiResponse<PlatformAuditSearchResponse>>("/platform/audit/", { params });
  return response.data.data;
}

export async function listPlatformVerification(params: Record<string, string>): Promise<PlatformVerificationListResponse> {
  const response = await api.get<ApiResponse<PlatformVerificationListResponse>>("/platform/verification/", { params });
  return response.data.data;
}

export async function getPlatformVerificationDetail(id: string): Promise<PlatformVerificationDetailResponse> {
  const response = await api.get<ApiResponse<PlatformVerificationDetailResponse>>(`/platform/verification/${id}/`);
  return response.data.data;
}

export async function runPlatformVerificationAction(id: string, action: string, payload: Record<string, unknown> = {}): Promise<void> {
  await api.post(`/platform/verification/${id}/${action}/`, payload);
}
