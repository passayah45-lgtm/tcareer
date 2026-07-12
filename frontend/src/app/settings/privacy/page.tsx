"use client";

import { useEffect, useState } from "react";
import { Navbar } from "@/components/layout/Navbar";
import { getPrivacySettings, updatePrivacySettings, type PrivacySettings } from "@/lib/api/settings.api";
import { useAuthStore } from "@/stores/auth.store";

const CONTROLS: { key: keyof PrivacySettings; label: string; description: string }[] = [
  { key: "public_profile", label: "Public profile", description: "Allow your profile to appear publicly and in recruiter discovery." },
  { key: "recruiter_resume_visibility", label: "Recruiter resume visibility", description: "Allow authorized recruiters to access your resume after visibility checks." },
  { key: "recruiter_portfolio_visibility", label: "Recruiter portfolio visibility", description: "Allow authorized recruiters to view your portfolio details." },
  { key: "open_to_work", label: "Open to work", description: "Show recruiters that you are actively considering opportunities." },
  { key: "allow_recruiter_contact", label: "Recruiter contact", description: "Allow recruiter-facing screens to show your contact email." },
  { key: "allow_analytics", label: "Analytics", description: "Allow T-Career to use your activity for product and career insights." },
  { key: "allow_ai_analysis", label: "AI analysis", description: "Allow AI-powered resume and portfolio analysis features." },
];

export default function PrivacySettingsPage() {
  const { isAuthenticated } = useAuthStore();
  const [settings, setSettings] = useState<PrivacySettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<keyof PrivacySettings | null>(null);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    try {
      setSettings(await getPrivacySettings());
      setError("");
    } catch {
      setError("Unable to load privacy settings.");
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

  async function toggle(key: keyof PrivacySettings) {
    if (!settings) return;
    const next = { ...settings, [key]: !settings[key] };
    setSettings(next);
    setSaving(key);
    try {
      setSettings(await updatePrivacySettings({ [key]: next[key] }));
      setError("");
    } catch {
      setError("Unable to update privacy setting.");
      await load();
    } finally {
      setSaving(null);
    }
  }

  return (
    <>
      <Navbar />
      <main className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Privacy settings</h1>
          <p className="text-sm text-muted-foreground mt-1">Control what recruiters can see and how T-Career may use your data.</p>
        </div>

        {!isAuthenticated && <div className="alert-error">Sign in to manage privacy settings.</div>}
        {error && <div className="alert-error">{error}</div>}
        {loading ? (
          <div className="h-64 bg-muted rounded-xl animate-pulse" />
        ) : settings ? (
          <section className="border border-border rounded-xl bg-card p-5 divide-y divide-border">
            {CONTROLS.map((control) => (
              <div key={control.key} className="py-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <p className="font-medium text-sm">{control.label}</p>
                  <p className="text-xs text-muted-foreground">{control.description}</p>
                </div>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={settings[control.key]}
                    disabled={saving === control.key}
                    onChange={() => void toggle(control.key)}
                  />
                  {settings[control.key] ? "Enabled" : "Disabled"}
                </label>
              </div>
            ))}
          </section>
        ) : (
          <div className="rounded-xl border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
            Privacy settings are unavailable.
          </div>
        )}
      </main>
    </>
  );
}
