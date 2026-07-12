"use client";

import { FormEvent, useEffect, useState } from "react";
import { OrganizationShell, OrgEmptyState, useOrganizationContext } from "@/components/organization/OrganizationShell";
import { getEnterpriseSettings, updateEnterpriseSettings, updateOrganizationLifecycle } from "@/lib/api/organizations.api";
import type { EnterpriseSettings } from "@/types/organization.types";

export default function OrganizationSettingsPage() {
  const { organization } = useOrganizationContext();
  const [settings, setSettings] = useState<EnterpriseSettings | null>(null);
  const [name, setName] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [countryCode, setCountryCode] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!organization) return;
    getEnterpriseSettings(organization.id)
      .then((data) => {
        setSettings(data);
        setName(data.organization.name);
        setWebsiteUrl(data.organization.website_url || "");
        setCountryCode(data.organization.country_code || "");
      })
      .catch(() => setError("Unable to load organization settings."));
  }, [organization]);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!organization) return;
    setSaving(true);
    setError("");
    try {
      const data = await updateEnterpriseSettings(organization.id, { name, website_url: websiteUrl, country_code: countryCode });
      setSettings(data);
    } catch {
      setError("Unable to save organization settings.");
    } finally {
      setSaving(false);
    }
  }

  async function lifecycle(action: string) {
    if (!organization) return;
    setSaving(true);
    setError("");
    try {
      await updateOrganizationLifecycle(organization.id, action);
      const data = await getEnterpriseSettings(organization.id);
      setSettings(data);
    } catch {
      setError("Unable to update organization lifecycle.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <OrganizationShell title="Organization settings" description="Profile, members, pending invitations, and organization-level metadata.">
      {error && <p className="text-sm text-destructive mb-4">{error}</p>}
      {!settings ? <OrgEmptyState title="Loading settings" body="Organization settings are being loaded." /> : (
        <div className="grid gap-6 lg:grid-cols-[1fr_1.2fr]">
          <form onSubmit={save} className="rounded-xl border border-border bg-card p-5 space-y-4">
            <h2 className="font-semibold">Organization profile</h2>
            <label className="block text-sm">
              Name
              <input className="input mt-1" value={name} onChange={(event) => setName(event.target.value)} />
            </label>
            <label className="block text-sm">
              Website
              <input className="input mt-1" value={websiteUrl} onChange={(event) => setWebsiteUrl(event.target.value)} />
            </label>
            <label className="block text-sm">
              Country code
              <input className="input mt-1" value={countryCode} maxLength={2} onChange={(event) => setCountryCode(event.target.value.toUpperCase())} />
            </label>
            <button disabled={saving} className="btn-base btn-primary">{saving ? "Saving..." : "Save settings"}</button>
          </form>
          <div className="space-y-6">
            <section className="rounded-xl border border-border bg-card p-5">
              <h2 className="font-semibold mb-4">Lifecycle</h2>
              <p className="text-sm text-muted-foreground mb-4">Current status: {settings.organization.status}</p>
              <div className="flex flex-wrap gap-2">
                <button onClick={() => lifecycle("suspend")} className="btn-sm btn-secondary">Suspend</button>
                <button onClick={() => lifecycle("reactivate")} className="btn-sm btn-secondary">Reactivate</button>
                <button onClick={() => lifecycle("archive")} className="btn-sm btn-secondary">Archive</button>
                <button onClick={() => lifecycle("soft_delete")} className="btn-sm btn-secondary">Soft delete</button>
              </div>
            </section>
            <section className="rounded-xl border border-border bg-card p-5">
              <h2 className="font-semibold mb-4">Members</h2>
              <div className="divide-y divide-border">
                {settings.members.map((member) => (
                  <div key={member.id} className="py-3 text-sm flex flex-col gap-1 md:flex-row md:justify-between">
                    <span>{member.user_full_name || member.user_email}</span>
                    <span className="text-muted-foreground">{member.role.replaceAll("_", " ")} · {member.status}</span>
                  </div>
                ))}
              </div>
            </section>
            <section className="rounded-xl border border-border bg-card p-5">
              <h2 className="font-semibold mb-4">Pending invitations</h2>
              {settings.pending_invitations.length === 0 ? (
                <p className="text-sm text-muted-foreground">No pending invitations.</p>
              ) : settings.pending_invitations.map((invite) => (
                <div key={invite.id} className="py-2 text-sm flex justify-between">
                  <span>{invite.email}</span>
                  <span className="text-muted-foreground">{invite.role.replaceAll("_", " ")}</span>
                </div>
              ))}
            </section>
          </div>
        </div>
      )}
    </OrganizationShell>
  );
}
