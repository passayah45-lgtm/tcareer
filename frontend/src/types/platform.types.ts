export interface PlatformManagementDashboard {
  summary: Record<string, number>;
  learning: Record<string, number>;
  career: Record<string, number | Record<string, number>>;
  organizations: Record<string, number>;
  trust: Record<string, number>;
  ai: Record<string, number | string>;
  notifications: Record<string, number>;
  revenue: Record<string, number>;
  sections: PlatformManagementSection[];
  recent_activity: PlatformActivity[];
}

export interface PlatformManagementSection {
  label: string;
  href: string;
  description: string;
}

export interface PlatformActivity {
  id: string;
  action: string;
  target_type: string;
  target_id: string;
  created_at: string;
}

export interface PlatformOperationItem {
  id: string;
  label: string;
  subtitle: string;
  status: string;
  metadata: Record<string, string | number | boolean>;
  created_at: string;
}

export interface PlatformOperationQueue {
  label: string;
  description: string;
  items: PlatformOperationItem[];
}

export interface PlatformOperations {
  counts: Record<string, number>;
  queues: Record<string, PlatformOperationQueue>;
}

export interface PlatformAuditLog {
  id: string;
  actor_email: string;
  action: string;
  target_type: string;
  target_id: string;
  organization_id: string;
  ip_address: string;
  user_agent: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface PlatformAuditSearchResponse {
  total: number;
  results: PlatformAuditLog[];
}

export interface PlatformVerificationRequest {
  id: string;
  label: string;
  subtitle: string;
  status: string;
  metadata: Record<string, string | number | boolean>;
  created_at: string;
}

export interface PlatformVerificationDocument {
  id: string;
  owner_type: string;
  owner_id: string;
  document_type: string;
  file_name: string;
  file_size: number;
  mime_type: string;
  is_encrypted: boolean;
  created_at: string;
  expires_at: string | null;
  verified_until: string | null;
  is_active: boolean;
  staff_notes: string;
}

export interface PlatformVerificationRequestDetail {
  id: string;
  subject_type: string;
  subject_id: string;
  status: string;
  priority: string;
  priority_reason: string;
  assigned_to: string | null;
  applicant_notes: string;
  reviewer_notes: string;
  internal_notes: string;
  submitted_at: string;
  reviewed_at: string | null;
  documents: PlatformVerificationDocument[];
}

export interface PlatformVerificationAction {
  id: string;
  actor: string | null;
  actor_email: string | null;
  target_type: string;
  target_id: string;
  action: string;
  previous_status: string;
  new_status: string;
  reason: string;
  notes: string;
  ip_address: string;
  device: string;
  browser: string;
  country: string;
  city: string;
  performed_at: string;
}

export interface PlatformVerificationListResponse {
  total: number;
  counts: Record<string, number>;
  results: PlatformVerificationRequest[];
}

export interface PlatformVerificationDetailResponse {
  request: PlatformVerificationRequestDetail;
  actions: PlatformVerificationAction[];
}
