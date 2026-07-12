"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Navbar } from "@/components/layout/Navbar";
import { getOrganizations } from "@/lib/api/recruiter.api";
import { useAuthStore } from "@/stores/auth.store";
import type { Organization } from "@/types/recruiter.types";

const RECRUITER_ROLES = new Set(["recruiter", "company_admin", "platform_admin", "super_admin", "admin"]);

const NAV_ITEMS = [
  { href: "/recruiter/dashboard", label: "Dashboard" },
  { href: "/recruiter/jobs", label: "Jobs" },
  { href: "/recruiter/pipeline", label: "Pipeline" },
  { href: "/recruiter/candidates", label: "Candidates" },
  { href: "/recruiter/saved-candidates", label: "Saved" },
  { href: "/recruiter/interviews", label: "Interviews" },
  { href: "/recruiter/settings", label: "Settings" },
];

const SELECTED_ORG_KEY = "tcareer_recruiter_org_id";

export function isRecruiterRole(role?: string) {
  return RECRUITER_ROLES.has(role || "");
}

export function useRecruiterContext() {
  const { user, isAuthenticated, isLoading } = useAuthStore();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [loadingOrg, setLoadingOrg] = useState(true);
  const [error, setError] = useState("");

  const loadOrganizations = useCallback(async (mounted: { current: boolean }) => {
    if (isLoading) return;
    if (!isAuthenticated || !isRecruiterRole(user?.role)) {
      setLoadingOrg(false);
      return;
    }

    setLoadingOrg(true);
    try {
      const items = await getOrganizations();
      if (!mounted.current) return;
      const requestedOrgId = typeof window !== "undefined" ? new URLSearchParams(window.location.search).get("org") : null;
      const storedOrgId = typeof window !== "undefined" ? window.localStorage.getItem(SELECTED_ORG_KEY) : null;
      const selected = items.find((item) => item.id === requestedOrgId)
        || items.find((item) => item.id === storedOrgId)
        || items[0]
        || null;
      if (selected && typeof window !== "undefined") window.localStorage.setItem(SELECTED_ORG_KEY, selected.id);
      setOrganizations(items);
      setOrganization(selected);
      setError("");
    } catch {
      if (mounted.current) setError("Unable to load recruiter organization.");
    } finally {
      if (mounted.current) setLoadingOrg(false);
    }
  }, [isAuthenticated, isLoading, user?.role]);

  useEffect(() => {
    const mounted = { current: true };
    const timer = window.setTimeout(() => {
      void loadOrganizations(mounted);
    }, 0);
    return () => {
      window.clearTimeout(timer);
      mounted.current = false;
    };
  }, [loadOrganizations]);

  return {
    user,
    isAuthenticated,
    isLoading: isLoading || loadingOrg,
    organization,
    organizations,
    error,
    allowed: isAuthenticated && isRecruiterRole(user?.role),
  };
}

export function RecruiterShell({
  children,
  title,
  description,
}: {
  children: React.ReactNode;
  title: string;
  description?: string;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated, isLoading, allowed, organization, organizations, error } = useRecruiterContext();

  const orgQuery = useMemo(() => (organization ? `?org=${organization.id}` : ""), [organization]);

  function switchOrganization(organizationId: string) {
    if (typeof window !== "undefined") window.localStorage.setItem(SELECTED_ORG_KEY, organizationId);
    router.push(`${pathname}?org=${organizationId}`);
  }

  if (isLoading) {
    return (
      <>
        <Navbar />
        <main className="max-w-7xl mx-auto px-4 py-8">
          <div className="space-y-4 animate-pulse">
            <div className="h-8 w-56 bg-muted rounded" />
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[...Array(4)].map((_, index) => <div key={index} className="h-28 bg-muted rounded-xl" />)}
            </div>
          </div>
        </main>
      </>
    );
  }

  if (!isAuthenticated) {
    return (
      <>
        <Navbar />
        <main className="max-w-3xl mx-auto px-4 py-16 text-center">
          <h1 className="text-2xl font-bold mb-2">Sign in required</h1>
          <p className="text-sm text-muted-foreground mb-6">Recruiter tools are available after sign in.</p>
          <button onClick={() => router.push("/login")} className="btn-base btn-primary">Sign in</button>
        </main>
      </>
    );
  }

  if (!allowed) {
    return (
      <>
        <Navbar />
        <main className="max-w-3xl mx-auto px-4 py-16 text-center">
          <h1 className="text-2xl font-bold mb-2">Recruiter access required</h1>
          <p className="text-sm text-muted-foreground">Your account does not currently have recruiter or company admin access.</p>
        </main>
      </>
    );
  }

  if (!organization) {
    return (
      <>
        <Navbar />
        <main className="max-w-3xl mx-auto px-4 py-16 text-center">
          <h1 className="text-2xl font-bold mb-2">No organization found</h1>
          <p className="text-sm text-muted-foreground">Ask a company admin to invite you, or accept your organization invitation first.</p>
        </main>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex flex-col gap-4 mb-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs text-muted-foreground mb-1">{organization.name}</p>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight">{title}</h1>
            {description && <p className="text-sm text-muted-foreground mt-1">{description}</p>}
            {error && <p className="text-xs text-destructive mt-2">{error}</p>}
          </div>
          {organizations.length > 1 && (
            <select
              value={organization.id}
              onChange={(event) => switchOrganization(event.target.value)}
              className="input max-w-xs"
            >
              {organizations.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
          )}
        </div>

        <div className="flex gap-2 overflow-x-auto border-b border-border mb-6 pb-2">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={`${item.href}${orgQuery}`}
              className={`px-3 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                pathname === item.href ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </div>

        {children}
      </main>
    </>
  );
}

export function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <div className="border border-border rounded-xl p-10 text-center bg-card">
      <p className="font-semibold mb-1">{title}</p>
      <p className="text-sm text-muted-foreground">{body}</p>
    </div>
  );
}
