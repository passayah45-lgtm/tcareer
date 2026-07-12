import api from "./client";

function unwrap<T>(payload: { data?: T } | T): T {
  if (payload && typeof payload === "object" && "data" in payload) {
    return (payload as { data: T }).data;
  }
  return payload as T;
}

export interface Notification {
  id: string;
  notification_type: string;
  category: string;
  title: string;
  body: string;
  action_url: string;
  is_read: boolean;
  created_at: string;
}

export interface NotificationsResponse {
  unread_count: number;
  notifications: Notification[];
}

export async function getNotifications(): Promise<NotificationsResponse> {
  const res = await api.get("/notifications/");
  return unwrap<NotificationsResponse>(res.data);
}

export async function markRead(notificationId: string): Promise<void> {
  await api.post(`/notifications/${notificationId}/read/`);
}

export async function markAllRead(): Promise<void> {
  await api.post("/notifications/read-all/");
}

export interface NotificationPreference {
  category: string;
  category_display: string;
  in_app_enabled: boolean;
  email_enabled: boolean;
}

export interface EmailDeliveryHistory {
  id: string;
  category: string;
  category_display: string;
  subject: string;
  status: string;
  created_at: string;
  sent_at: string | null;
  failed_at: string | null;
  retry_count: number;
  last_error: string;
}

export async function getNotificationPreferences(): Promise<{
  preferences: NotificationPreference[];
  suppressed_categories: string[];
}> {
  const res = await api.get("/notifications/preferences/");
  return unwrap<{ preferences: NotificationPreference[]; suppressed_categories: string[] }>(res.data);
}

export async function updateNotificationPreferences(preferences: Partial<NotificationPreference>[]): Promise<{
  preferences: NotificationPreference[];
}> {
  const res = await api.patch("/notifications/preferences/", { preferences });
  return unwrap<{ preferences: NotificationPreference[] }>(res.data);
}

export async function getEmailDeliveryHistory(): Promise<{ deliveries: EmailDeliveryHistory[] }> {
  const res = await api.get("/notifications/delivery-history/");
  return unwrap<{ deliveries: EmailDeliveryHistory[] }>(res.data);
}

export async function unsubscribeCategory(category: string): Promise<void> {
  await api.post("/notifications/unsubscribe/", { category });
}

export async function resubscribeCategory(category: string): Promise<void> {
  await api.post("/notifications/resubscribe/", { category });
}
