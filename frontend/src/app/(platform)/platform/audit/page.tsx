"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import { getDashboardPathForUser } from "@/lib/auth/role-redirects";
import { searchPlatformAudit } from "@/lib/api/platform.api";
import { useAuthStore } from "@/stores/auth.store";
import type { PlatformAuditLog, PlatformAuditSearchResponse } from "@/types/platform.types";
import type { UserRole } from "@/types/user.types";

const PLATFORM_ADMIN_ROLES = new Set<UserRole>(["admin", "platform_admin", "super_admin"]);

function metadataPreview(item: PlatformAuditLog) {
  const entries = Object.entries(item.metadata || {}).slice(0, 3);
  if (entries.length === 0) return "No metadata";
  return entries.map(([key, value]) => `${key}: ${String(value)}`).join(" | ");
}

export default function PlatformAuditPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading } = useAuthStore();
  const [filters, setFilters] = useState({ q: "", action: "", target_type: "", target_id: "" });
  const [audit, setAudit] = useState<PlatformAuditSearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const canAccessPlatform = Boolean(user?.role && PLATFORM_ADMIN_ROLES.has(user.role));

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      router.push("/login?next=/platform/audit");
      return;
    }
    if (!canAccessPlatform) router.push(getDashboardPathForUser(user));
  }, [canAccessPlatform, isAuthenticated, isLoading, router, user]);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const params = Object.fromEntries(Object.entries(filters).filter(([, value]) => value.trim()));
      const data = await searchPlatformAudit({ ...params, limit: "100" });
      setAudit(data);
    } catch {
      setError("Unable to load platform audit events.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!isLoading && isAuthenticated && canAccessPlatform) {
      const timer = window.setTimeout(() => void load(), 0);
      return () => window.clearTimeout(timer);
    }
    return undefined;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoading, isAuthenticated, canAccessPlatform]);

  if (isLoading || !isAuthenticated || !canAccessPlatform) {
    return (
      <>
        <Navbar />
        <main className="min-h-[60vh] flex items-center justify-center px-4">
          <div className="w-7 h-7 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </main>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 py-8 space-y-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-medium text-primary">Platform management</p>
            <h1 className="text-2xl md:text-3xl font-bold mt-1">Audit search</h1>
            <p className="text-sm text-muted-foreground mt-2 max-w-3xl">
              Search privileged actions, operational changes, security events, and platform-admin activity.
            </p>
          </div>
          <Link href="/platform/dashboard" className="btn-base btn-secondary">Back to dashboard</Link>
        </div>

        <section className="rounded-xl border border-border bg-card p-5">
          <div className="grid gap-3 md:grid-cols-4">
            <input className="input" value={filters.q} onChange={(event) => setFilters({ ...filters, q: event.target.value })} placeholder="Search all audit fields" />
            <input className="input" value={filters.action} onChange={(event) => setFilters({ ...filters, action: event.target.value })} placeholder="Action" />
            <input className="input" value={filters.target_type} onChange={(event) => setFilters({ ...filters, target_type: event.target.value })} placeholder="Target type" />
            <input className="input" value={filters.target_id} onChange={(event) => setFilters({ ...filters, target_id: event.target.value })} placeholder="Target ID" />
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <button type="button" className="btn-base btn-primary" onClick={() => void load()} disabled={loading}>
              {loading ? "Searching..." : "Search"}
            </button>
            <button
              type="button"
              className="btn-base btn-secondary"
              onClick={() => {
                setFilters({ q: "", action: "", target_type: "", target_id: "" });
                setTimeout(() => void load(), 0);
              }}
            >
              Reset
            </button>
          </div>
        </section>

        {error && <div className="rounded-xl border border-destructive/30 bg-card p-5 text-sm text-destructive">{error}</div>}

        <section className="rounded-xl border border-border bg-card p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-semibold">Audit events</h2>
            <span className="text-sm text-muted-foreground">{audit?.total ?? 0} results</span>
          </div>
          {!audit || loading ? (
            <div className="h-48 rounded-lg bg-muted animate-pulse" />
          ) : audit.results.length === 0 ? (
            <p className="text-sm text-muted-foreground">No audit events matched your filters.</p>
          ) : (
            <div className="divide-y divide-border">
              {audit.results.map((item) => (
                <div key={item.id} className="py-4">
                  <div className="flex flex-col gap-2 lg:flex-row lg:items-start lg:justify-between">
                    <div>
                      <p className="font-medium text-sm">{item.action.replaceAll("_", " ")}</p>
                      <p className="text-xs text-muted-foreground mt-1">{item.target_type}:{item.target_id}</p>
                    </div>
                    <p className="text-xs text-muted-foreground">{item.created_at ? new Date(item.created_at).toLocaleString() : ""}</p>
                  </div>
                  <div className="mt-2 grid gap-2 text-xs text-muted-foreground md:grid-cols-3">
                    <span>Actor: {item.actor_email || "system"}</span>
                    <span>IP: {item.ip_address || "-"}</span>
                    <span className="truncate">Metadata: {metadataPreview(item)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </>
  );
}
