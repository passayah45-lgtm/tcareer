import api from "@/lib/api/client";
import type { ApiResponse } from "@/types/api.types";
import type { Organization, OrganizationMember } from "@/types/recruiter.types";
import type {
  BulkImportJob,
  Cohort,
  DataExportJob,
  Department,
  EnterpriseDashboard,
  EnterpriseAuditResponse,
  EnterpriseSettings,
  EnterpriseReportJob,
  EnterpriseRoleResponse,
  EnterpriseWorkerJobs,
  OrganizationPolicy,
  OrganizationProfile,
  OrganizationTeam,
  ImportTemplate,
} from "@/types/organization.types";

function unwrap<T>(payload: ApiResponse<T> | T): T {
  return (payload as ApiResponse<T>).data ?? (payload as T);
}

export async function getOrganizations(): Promise<Organization[]> {
  const response = await api.get<ApiResponse<Organization[]> | Organization[]>("/organizations/");
  return unwrap(response.data);
}

export async function getEnterpriseDashboard(organizationId: string): Promise<EnterpriseDashboard> {
  const response = await api.get<ApiResponse<EnterpriseDashboard>>(`/organizations/${organizationId}/enterprise/dashboard/`);
  return unwrap(response.data);
}

export async function getEnterpriseSettings(organizationId: string): Promise<EnterpriseSettings> {
  const response = await api.get<ApiResponse<EnterpriseSettings>>(`/organizations/${organizationId}/enterprise/settings/`);
  return unwrap(response.data);
}

export async function updateOrganizationLifecycle(organizationId: string, action: string, ownerId?: string): Promise<Organization> {
  const response = await api.post<ApiResponse<Organization>>(`/organizations/${organizationId}/enterprise/lifecycle/`, {
    action,
    owner_id: ownerId,
  });
  return unwrap(response.data);
}

export async function getEnterpriseRoles(organizationId: string): Promise<EnterpriseRoleResponse> {
  const response = await api.get<ApiResponse<EnterpriseRoleResponse>>(`/organizations/${organizationId}/enterprise/roles/`);
  return unwrap(response.data);
}

export async function assignEnterpriseRole(organizationId: string, membershipId: string, role: string): Promise<OrganizationMember> {
  const response = await api.post<ApiResponse<OrganizationMember>>(`/organizations/${organizationId}/enterprise/roles/`, {
    membership_id: membershipId,
    role,
  });
  return unwrap(response.data);
}

export async function getEnterpriseAudit(
  organizationId: string,
  params?: { action?: string; action_prefix?: string; q?: string; severity?: string; actor?: string; target_type?: string; target_id?: string; start_date?: string; end_date?: string },
): Promise<EnterpriseAuditResponse> {
  const response = await api.get<ApiResponse<EnterpriseAuditResponse>>(`/organizations/${organizationId}/enterprise/audit/`, { params });
  return unwrap(response.data);
}

export async function getEnterpriseWorkerJobs(organizationId: string): Promise<EnterpriseWorkerJobs> {
  const response = await api.get<ApiResponse<EnterpriseWorkerJobs>>(`/organizations/${organizationId}/enterprise/worker-jobs/`);
  return unwrap(response.data);
}

export async function updateEnterpriseSettings(organizationId: string, payload: Partial<Organization>): Promise<EnterpriseSettings> {
  const response = await api.patch<ApiResponse<EnterpriseSettings>>(`/organizations/${organizationId}/enterprise/settings/`, payload);
  return unwrap(response.data);
}

export async function getOrganizationBranding(organizationId: string): Promise<OrganizationProfile> {
  const response = await api.get<ApiResponse<OrganizationProfile>>(`/organizations/${organizationId}/enterprise/branding/`);
  return unwrap(response.data);
}

export async function updateOrganizationBranding(organizationId: string, payload: Partial<OrganizationProfile>): Promise<OrganizationProfile> {
  const response = await api.patch<ApiResponse<OrganizationProfile>>(`/organizations/${organizationId}/enterprise/branding/`, payload);
  return unwrap(response.data);
}

export async function uploadOrganizationBrandingAsset(organizationId: string, assetType: string, file: File): Promise<OrganizationProfile> {
  const formData = new FormData();
  formData.append("asset_type", assetType);
  formData.append("file", file);
  const response = await api.post<ApiResponse<OrganizationProfile>>(
    `/organizations/${organizationId}/enterprise/branding/upload/`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } },
  );
  return unwrap(response.data);
}

export async function getOrganizationPolicies(organizationId: string): Promise<OrganizationPolicy> {
  const response = await api.get<ApiResponse<OrganizationPolicy>>(`/organizations/${organizationId}/enterprise/policies/`);
  return unwrap(response.data);
}

export async function updateOrganizationPolicies(organizationId: string, payload: Partial<OrganizationPolicy>): Promise<OrganizationPolicy> {
  const response = await api.patch<ApiResponse<OrganizationPolicy>>(`/organizations/${organizationId}/enterprise/policies/`, payload);
  return unwrap(response.data);
}

export async function getDepartments(organizationId: string): Promise<Department[]> {
  const response = await api.get<ApiResponse<Department[]>>(`/organizations/${organizationId}/enterprise/departments/`);
  return unwrap(response.data);
}

export async function createDepartment(organizationId: string, payload: Partial<Department>): Promise<Department> {
  const response = await api.post<ApiResponse<Department>>(`/organizations/${organizationId}/enterprise/departments/`, payload);
  return unwrap(response.data);
}

export async function archiveDepartment(organizationId: string, departmentId: string): Promise<void> {
  await api.delete(`/organizations/${organizationId}/enterprise/departments/${departmentId}/`);
}

export async function assignDepartmentMember(organizationId: string, departmentId: string, membershipId: string, role = "member"): Promise<Department> {
  const response = await api.post<ApiResponse<Department>>(
    `/organizations/${organizationId}/enterprise/departments/${departmentId}/members/`,
    { membership_id: membershipId, role },
  );
  return unwrap(response.data);
}

export async function getTeams(organizationId: string): Promise<OrganizationTeam[]> {
  const response = await api.get<ApiResponse<OrganizationTeam[]>>(`/organizations/${organizationId}/enterprise/teams/`);
  return unwrap(response.data);
}

export async function createTeam(organizationId: string, payload: Partial<OrganizationTeam>): Promise<OrganizationTeam> {
  const response = await api.post<ApiResponse<OrganizationTeam>>(`/organizations/${organizationId}/enterprise/teams/`, payload);
  return unwrap(response.data);
}

export async function archiveTeam(organizationId: string, teamId: string): Promise<void> {
  await api.delete(`/organizations/${organizationId}/enterprise/teams/${teamId}/`);
}

export async function assignTeamMember(organizationId: string, teamId: string, membershipId: string, role = "member"): Promise<OrganizationTeam> {
  const response = await api.post<ApiResponse<OrganizationTeam>>(
    `/organizations/${organizationId}/enterprise/teams/${teamId}/members/`,
    { membership_id: membershipId, role },
  );
  return unwrap(response.data);
}

export async function getCohorts(organizationId: string): Promise<Cohort[]> {
  const response = await api.get<ApiResponse<Cohort[]>>(`/organizations/${organizationId}/enterprise/cohorts/`);
  return unwrap(response.data);
}

export async function createCohort(organizationId: string, payload: Partial<Cohort>): Promise<Cohort> {
  const response = await api.post<ApiResponse<Cohort>>(`/organizations/${organizationId}/enterprise/cohorts/`, payload);
  return unwrap(response.data);
}

export async function archiveCohort(organizationId: string, cohortId: string): Promise<void> {
  await api.delete(`/organizations/${organizationId}/enterprise/cohorts/${cohortId}/`);
}

export async function assignCohortMember(organizationId: string, cohortId: string, membershipId: string, role = "member"): Promise<Cohort> {
  const response = await api.post<ApiResponse<Cohort>>(
    `/organizations/${organizationId}/enterprise/cohorts/${cohortId}/members/`,
    { membership_id: membershipId, role },
  );
  return unwrap(response.data);
}

export async function bulkImport(
  organizationId: string,
  payload: { import_type: string; csv_content: string; source_filename?: string; commit: boolean },
): Promise<BulkImportJob> {
  const response = await api.post<ApiResponse<BulkImportJob>>(`/organizations/${organizationId}/enterprise/imports/`, payload);
  return unwrap(response.data);
}

export async function getImportTemplate(organizationId: string, importType: string): Promise<ImportTemplate> {
  const response = await api.get<ApiResponse<ImportTemplate>>(`/organizations/${organizationId}/enterprise/imports/template/`, { params: { import_type: importType } });
  return unwrap(response.data);
}

export async function downloadImportTemplate(organizationId: string, importType: string): Promise<Blob> {
  const response = await api.get(`/organizations/${organizationId}/enterprise/imports/template/`, {
    params: { import_type: importType, download: "1" },
    responseType: "blob",
  });
  return response.data as Blob;
}

export async function getImportJobs(organizationId: string): Promise<BulkImportJob[]> {
  const response = await api.get<ApiResponse<BulkImportJob[]>>(`/organizations/${organizationId}/enterprise/imports/jobs/`);
  return unwrap(response.data);
}

export async function downloadImportFile(organizationId: string, importId: string, fileKind: "summary" | "errors"): Promise<Blob> {
  const response = await api.get(`/organizations/${organizationId}/enterprise/imports/${importId}/${fileKind}/download/`, { responseType: "blob" });
  return response.data as Blob;
}

export async function getExports(organizationId: string): Promise<DataExportJob[]> {
  const response = await api.get<ApiResponse<DataExportJob[]>>(`/organizations/${organizationId}/enterprise/exports/`);
  return unwrap(response.data);
}

export async function deleteExport(organizationId: string, exportId: string): Promise<void> {
  await api.delete(`/organizations/${organizationId}/enterprise/exports/${exportId}/`);
}

export async function createExport(organizationId: string, exportType: string, fileFormat: string): Promise<DataExportJob> {
  const response = await api.post<ApiResponse<DataExportJob>>(
    `/organizations/${organizationId}/enterprise/exports/`,
    { export_type: exportType, file_format: fileFormat },
  );
  return unwrap(response.data);
}

export async function downloadExport(organizationId: string, exportId: string): Promise<Blob> {
  const response = await api.get(`/organizations/${organizationId}/enterprise/exports/${exportId}/download/`, { responseType: "blob" });
  return response.data as Blob;
}

export async function getOrganizationMembers(organizationId: string): Promise<OrganizationMember[]> {
  const response = await api.get<ApiResponse<OrganizationMember[]>>(`/organizations/${organizationId}/members/`);
  return unwrap(response.data);
}

export async function getEnterpriseReports(organizationId: string): Promise<EnterpriseReportJob[]> {
  const response = await api.get<ApiResponse<EnterpriseReportJob[]>>(`/organizations/${organizationId}/enterprise/reports/`);
  return unwrap(response.data);
}

export async function createEnterpriseReport(organizationId: string, reportType: string, fileFormat = "xlsx"): Promise<EnterpriseReportJob> {
  const response = await api.post<ApiResponse<EnterpriseReportJob>>(`/organizations/${organizationId}/enterprise/reports/`, { report_type: reportType, file_format: fileFormat });
  return unwrap(response.data);
}
