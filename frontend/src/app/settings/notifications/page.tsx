"use client";

import { useEffect, useState } from "react";
import { Navbar } from "@/components/layout/Navbar";
import {
  getEmailDeliveryHistory,
  getNotificationPreferences,
  resubscribeCategory,
  unsubscribeCategory,
  updateNotificationPreferences,
  type EmailDeliveryHistory,
  type NotificationPreference,
} from "@/lib/api/notifications.api";
import { useAuthStore } from "@/stores/auth.store";

export default function NotificationSettingsPage() {
  const { isAuthenticated } = useAuthStore();
  const [preferences, setPreferences] = useState<NotificationPreference[]>([]);
  const [suppressed, setSuppressed] = useState<string[]>([]);
  const [history, setHistory] = useState<EmailDeliveryHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    try {
      const [prefData, historyData] = await Promise.all([
        getNotificationPreferences(),
        getEmailDeliveryHistory(),
      ]);
      setPreferences(prefData.preferences);
      setSuppressed(prefData.suppressed_categories);
      setHistory(historyData.deliveries);
      setError("");
    } catch {
      setError("Unable to load notification settings.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      if (isAuthenticated) void load();
      else setLoading(false);
    }, 0);
    return () => window.clearTimeout(timer);
  }, [isAuthenticated]);

  async function toggleEmail(pref: NotificationPreference) {
    if (pref.category === "security") return;
    const next = !pref.email_enabled;
    setPreferences((items) => items.map((item) => item.category === pref.category ? { ...item, email_enabled: next } : item));
    try {
      await updateNotificationPreferences([{ category: pref.category, email_enabled: next }]);
      if (next) await resubscribeCategory(pref.category);
      else await unsubscribeCategory(pref.category);
      await load();
    } catch {
      setError("Unable to update notification preference.");
      await load();
    }
  }

  async function toggleInApp(pref: NotificationPreference) {
    if (pref.category === "security") return;
    const next = !pref.in_app_enabled;
    setPreferences((items) => items.map((item) => item.category === pref.category ? { ...item, in_app_enabled: next } : item));
    try {
      await updateNotificationPreferences([{ category: pref.category, in_app_enabled: next }]);
      await load();
    } catch {
      setError("Unable to update notification preference.");
      await load();
    }
  }

  return (
    <>
      <Navbar />
      <main className="max-w-5xl mx-auto px-4 py-8 space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Notification settings</h1>
          <p className="text-sm text-muted-foreground mt-1">Manage email preferences, unsubscribe state, and delivery history.</p>
        </div>

        {!isAuthenticated && <div className="alert-error">Sign in to manage notification settings.</div>}
        {error && <div className="alert-error">{error}</div>}
        {loading ? (
          <div className="h-64 bg-muted rounded-xl animate-pulse" />
        ) : (
          <>
            <section className="border border-border rounded-xl bg-card p-5">
              <h2 className="font-semibold mb-4">Preferences</h2>
              <div className="divide-y divide-border">
                {preferences.map((pref) => (
                  <div key={pref.category} className="py-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                    <div>
                      <p className="font-medium text-sm">{pref.category_display}</p>
                      <p className="text-xs text-muted-foreground">
                        {pref.category === "security" ? "Always enabled for account protection." : suppressed.includes(pref.category) ? "Email is currently suppressed." : "Choose how T-Career contacts you."}
                      </p>
                    </div>
                    <div className="flex gap-4">
                      <label className="flex items-center gap-2 text-sm">
                        <input type="checkbox" checked={pref.in_app_enabled} disabled={pref.category === "security"} onChange={() => void toggleInApp(pref)} />
                        In-app
                      </label>
                      <label className="flex items-center gap-2 text-sm">
                        <input type="checkbox" checked={pref.email_enabled} disabled={pref.category === "security"} onChange={() => void toggleEmail(pref)} />
                        Email
                      </label>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="border border-border rounded-xl bg-card p-5">
              <h2 className="font-semibold mb-4">Email delivery history</h2>
              {history.length === 0 ? (
                <p className="text-sm text-muted-foreground">No email delivery records yet.</p>
              ) : (
                <div className="space-y-3">
                  {history.map((delivery) => (
                    <div key={delivery.id} className="rounded-lg border border-border p-4">
                      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                        <div>
                          <p className="text-sm font-medium">{delivery.subject}</p>
                          <p className="text-xs text-muted-foreground">{delivery.category_display} · {new Date(delivery.created_at).toLocaleString()}</p>
                        </div>
                        <span className="badge capitalize">{delivery.status}</span>
                      </div>
                      <p className="mt-2 text-xs text-muted-foreground">
                        Sent: {delivery.sent_at ? new Date(delivery.sent_at).toLocaleString() : "Not sent"} · Failed: {delivery.failed_at ? new Date(delivery.failed_at).toLocaleString() : "No"} · Retries: {delivery.retry_count}
                      </p>
                      {delivery.last_error && <p className="mt-2 text-xs text-destructive">{delivery.last_error}</p>}
                    </div>
                  ))}
                </div>
              )}
            </section>
          </>
        )}
      </main>
    </>
  );
}
