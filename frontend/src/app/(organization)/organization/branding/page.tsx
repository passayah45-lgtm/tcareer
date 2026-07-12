"use client";

import { FormEvent, useEffect, useState } from "react";
import { OrganizationShell, OrgEmptyState, useOrganizationContext } from "@/components/organization/OrganizationShell";
import { getOrganizationBranding, updateOrganizationBranding, uploadOrganizationBrandingAsset } from "@/lib/api/organizations.api";
import type { OrganizationProfile } from "@/types/organization.types";

export default function OrganizationBrandingPage() {
  const { organization } = useOrganizationContext();
  const [profile, setProfile] = useState<OrganizationProfile | null>(null);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState("");

  useEffect(() => {
    if (!organization) return;
    getOrganizationBranding(organization.id).then(setProfile).catch(() => setError("Unable to load branding."));
  }, [organization]);

  function updateField(field: keyof OrganizationProfile, value: string) {
    setProfile((current) => current ? { ...current, [field]: value } : current);
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!organization || !profile) return;
    setSaving(true);
    setError("");
    try {
      setProfile(await updateOrganizationBranding(organization.id, profile));
    } catch {
      setError("Unable to save branding.");
    } finally {
      setSaving(false);
    }
  }

  async function uploadAsset(assetType: string, file?: File) {
    if (!organization || !file) return;
    setUploading(assetType);
    setError("");
    try {
      setProfile(await uploadOrganizationBrandingAsset(organization.id, assetType, file));
    } catch {
      setError("Unable to upload branding asset. Use PNG, JPG, WEBP, or ICO under 5MB.");
    } finally {
      setUploading("");
    }
  }

  return (
    <OrganizationShell title="Branding" description="Configure organization branding for pages, emails, certificates, and support metadata.">
      {error && <p className="text-sm text-destructive mb-4">{error}</p>}
      {!profile ? <OrgEmptyState title="Loading branding" body="Brand settings are being loaded." /> : (
        <form onSubmit={save} className="grid gap-6 lg:grid-cols-[1fr_340px]">
          <section className="rounded-xl border border-border bg-card p-5 space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              {[
                ["logo", "Logo", profile.logo_file_url],
                ["banner", "Banner", profile.banner_file_url],
                ["favicon", "Favicon", profile.favicon_file_url],
                ["certificate_logo", "Certificate logo", profile.certificate_logo_file_url],
                ["email_header_image", "Email header", profile.email_header_image_file_url],
              ].map(([assetType, label, url]) => (
                <label key={assetType} className="block text-sm rounded-lg border border-border p-3">
                  <span className="font-medium">{label}</span>
                  {url && <span className="block text-xs text-muted-foreground truncate mt-1">{url}</span>}
                  <input className="mt-3 text-xs" type="file" accept="image/png,image/jpeg,image/webp,image/x-icon" onChange={(event) => uploadAsset(assetType, event.target.files?.[0])} />
                  {uploading === assetType && <span className="block text-xs text-muted-foreground mt-1">Uploading...</span>}
                </label>
              ))}
            </div>
            <label className="block text-sm">Logo URL<input className="input mt-1" value={profile.logo_url} onChange={(event) => updateField("logo_url", event.target.value)} /></label>
            <label className="block text-sm">Banner URL<input className="input mt-1" value={profile.banner_url} onChange={(event) => updateField("banner_url", event.target.value)} /></label>
            <div className="grid gap-4 md:grid-cols-2">
              <label className="block text-sm">Primary color<input className="input mt-1" value={profile.primary_color} onChange={(event) => updateField("primary_color", event.target.value)} /></label>
              <label className="block text-sm">Secondary color<input className="input mt-1" value={profile.secondary_color} onChange={(event) => updateField("secondary_color", event.target.value)} /></label>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <label className="block text-sm">Support email<input className="input mt-1" value={profile.support_email} onChange={(event) => updateField("support_email", event.target.value)} /></label>
              <label className="block text-sm">Support phone<input className="input mt-1" value={profile.support_phone} onChange={(event) => updateField("support_phone", event.target.value)} /></label>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <label className="block text-sm">Time zone<input className="input mt-1" value={profile.time_zone} onChange={(event) => updateField("time_zone", event.target.value)} /></label>
              <label className="block text-sm">Default language<input className="input mt-1" value={profile.default_language} onChange={(event) => updateField("default_language", event.target.value)} /></label>
            </div>
            <button disabled={saving} className="btn-base btn-primary">{saving ? "Saving..." : "Save branding"}</button>
          </section>
          <aside className="rounded-xl border border-border bg-card p-5">
            <p className="text-sm text-muted-foreground mb-4">Preview</p>
            <div className="rounded-lg border border-border overflow-hidden">
              <div className="h-24 bg-muted" style={{ backgroundColor: profile.secondary_color || undefined }} />
              <div className="p-4">
                <div className="h-12 w-12 rounded-lg bg-primary mb-3" style={{ backgroundColor: profile.primary_color || undefined }} />
                <h2 className="font-semibold">{organization?.name}</h2>
                <p className="text-sm text-muted-foreground">{profile.support_email || "support@example.com"}</p>
              </div>
            </div>
          </aside>
        </form>
      )}
    </OrganizationShell>
  );
}
