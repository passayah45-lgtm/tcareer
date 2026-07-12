import api from "./client";
import type { ApiResponse } from "@/types/api.types";

export interface SubscriptionStatus {
  has_subscription: boolean;
  is_active?: boolean;
  status?: string;
  plan?: string;
  current_period_end?: string;
}

export async function createCheckoutSession(): Promise<{ checkout_url: string }> {
  const res = await api.post<ApiResponse<{ checkout_url: string }>>("/payments/checkout/");
  return res.data.data;
}

export async function createBillingPortal(): Promise<{ portal_url: string }> {
  const res = await api.post<ApiResponse<{ portal_url: string }>>("/payments/billing-portal/");
  return res.data.data;
}

export async function getSubscriptionStatus(): Promise<SubscriptionStatus> {
  const res = await api.get<ApiResponse<SubscriptionStatus>>("/payments/subscription/");
  return res.data.data;
}
