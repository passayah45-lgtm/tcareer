"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import { getDashboardPathForUser } from "@/lib/auth/role-redirects";
import {
  getPlatformVerificationDetail,
  listPlatformVerification,
  runPlatformVerificationAction,
} from "@/lib/api/platform.api";
import { useAuthStore } from "@/stores/auth.store";
import type {
  PlatformVerificationDetailResponse,
  PlatformVerificationListResponse,
  PlatformVerificationRequest,
} from "@/types/platform.types";
import type { UserRole } from "@/types/user.types";

const PLATFORM_ADMIN_ROLES = new Set<UserRole>(["admin", "platform_admin", "super_admin"]);

const STATUS_OPTIONS = [
  { value: "", label: "Active review" },
  { value: "submitted", label: "Submitted" },
  { value: "under_review", label: "Under review" },
  { value: "more_info_required", label: "More info required" },
  { value: "approved", label: "Approved" },
  { value: "rejected", label: "Rejected" },
];

const SUBJECT_OPTIONS = [
  { value: "", label: "All subjects" },
  { value: "instructor", label: "Instructor" },
  { value: "recruiter", label: "Recruiter" },
  { value: "organization", label: "Organization" },
];

const PRIORITY_OPTIONS = [
  { value: "", label: "All priorities" },
  { value: "high", label: "High" },
  { value: "normal", label: "Normal" },
  { value: "low", label: "Low" },
];

const ASSIGNED_OPTIONS = [
  { value: "", label: "All assignments" },
  { value: "me", label: "Assigned to me" },
  { value: "unassigned", label: "Unassigned" },
];

function labelize(value: string) {
  return value.replaceAll("_", " ");
}

function StatusPill({ status }: { status: string }) {
  const tone =
    status === "approved"
      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
      : status === "rejected"
        ? "bg-red-50 text-red-700 border-red-200"
        : status === "under_review"
          ? "bg-blue-50 text-blue-700 border-blue-200"
          : "bg-amber-50 text-amber-700 border-amber-200";
  return <span className={`rounded-full border px-2 py-0.5 text-xs capitalize ${tone}`}>{labelize(status)}</span>;
}

function QueueItem({
  item,
  selected,
  onSelect,
}: {
  item: PlatformVerificationRequest;
  selected: boolean;
  onSelect: (id: string) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onSelect(item.id)}
      className={`w-full rounded-xl border p-4 text-left transition ${
        selected ? "border-primary bg-primary/5" : "border-border bg-card hover:border-primary/40"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="font-semibold text-sm capitalize">{labelize(item.label)}</p>
          <p className="mt-1 truncate text-xs text-muted-foreground">{item.subtitle}</p>
        </div>
        <StatusPill status={item.status} />
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {Object.entries(item.metadata).slice(0, 3).map(([key, value]) => (
          <span key={key} className="rounded-md bg-muted px-2 py-1 text-xs text-muted-foreground">
            {labelize(key)}: {String(value || "-")}
          </span>
        ))}
      </div>
    </button>
  );
}

export default function PlatformVerificationPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading } = useAuthStore();
  const [filters, setFilters] = useState({ status: "", subject_type: "", priority: "", assigned: "", q: "" });
  const [queue, setQueue] = useState<PlatformVerificationListResponse | null>(null);
  const [detail, setDetail] = useState<PlatformVerificationDetailResponse | null>(null);
  const [selectedId, setSelectedId] = useState("");
  const [loadingQueue, setLoadingQueue] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");
  const [busyAction, setBusyAction] = useState("");
  const [pendingAction, setPendingAction] = useState<"reject" | "more_info" | null>(null);
  const [reason, setReason] = useState("");
  const canAccessPlatform = Boolean(user?.role && PLATFORM_ADMIN_ROLES.has(user.role));

  const loadQueue = useCallback(async () => {
    setLoadingQueue(true);
    setError("");
    try {
      const params = Object.fromEntries(Object.entries(filters).filter(([, value]) => value.trim()));
      const data = await listPlatformVerification(params);
      setQueue(data);
      setSelectedId((current) => current || data.results[0]?.id || "");
    } catch {
      setError("Unable to load verification queue.");
    } finally {
      setLoadingQueue(false);
    }
  }, [filters]);

  const loadDetail = useCallback(async (id: string) => {
    if (!id) {
      setDetail(null);
      return;
    }
    setLoadingDetail(true);
    setActionError("");
    try {
      setDetail(await getPlatformVerificationDetail(id));
    } catch {
      setActionError("Unable to load verification detail.");
    } finally {
      setLoadingDetail(false);
    }
  }, []);

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      router.push("/login?next=/platform/verification");
      return;
    }
    if (!canAccessPlatform) {
      router.push(getDashboardPathForUser(user));
    }
  }, [canAccessPlatform, isAuthenticated, isLoading, router, user]);

  useEffect(() => {
    if (isLoading || !isAuthenticated || !canAccessPlatform) return;
    const timer = window.setTimeout(() => {
      void loadQueue();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [canAccessPlatform, isAuthenticated, isLoading, loadQueue]);

  useEffect(() => {
    if (isLoading || !isAuthenticated || !canAccessPlatform) return;
    const timer = window.setTimeout(() => {
      void loadDetail(selectedId);
    }, 0);
    return () => window.clearTimeout(timer);
  }, [canAccessPlatform, isAuthenticated, isLoading, loadDetail, selectedId]);

  const selectedRequest = useMemo(
    () => queue?.results.find((item) => item.id === selectedId) || null,
    [queue?.results, selectedId],
  );

  async function runAction(action: "assign" | "approve" | "reject" | "more_info") {
    if (!selectedId) return;
    if ((action === "reject" || action === "more_info") && !pendingAction) {
      setPendingAction(action);
      setReason("");
      setActionError("");
      return;
    }
    setBusyAction(action);
    setActionError("");
    try {
      await runPlatformVerificationAction(selectedId, action, reason.trim() ? { reason: reason.trim() } : {});
      await loadQueue();
      await loadDetail(selectedId);
      setPendingAction(null);
      setReason("");
    } catch {
      setActionError(`Unable to ${labelize(action)} this verification request.`);
    } finally {
      setBusyAction("");
    }
  }

  if (isLoading || (!isAuthenticated || !canAccessPlatform)) {
    return (
      <>
        <Navbar />
        <main className="flex min-h-[60vh] items-center justify-center px-4">
          <div className="h-7 w-7 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </main>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-7xl px-4 py-8">
        {pendingAction && (
          <div className="fixed inset-0 z-[80] flex items-center justify-center bg-black/40 px-4">
            <div className="w-full max-w-lg rounded-xl border border-border bg-background p-5 shadow-xl">
              <h2 className="font-semibold">{pendingAction === "reject" ? "Reject verification" : "Request more information"}</h2>
              <p className="mt-2 text-sm text-muted-foreground">A clear reviewer reason is required and will be stored in the audit trail.</p>
              <textarea
                className="input mt-4 min-h-28 w-full"
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                placeholder="Explain what needs to happen next."
              />
              <div className="mt-4 flex flex-wrap justify-end gap-2">
                <button type="button" className="btn-base btn-secondary" onClick={() => setPendingAction(null)}>
                  Cancel
                </button>
                <button
                  type="button"
                  className="btn-base btn-primary"
                  disabled={reason.trim().length < 10 || Boolean(busyAction)}
                  onClick={() => void runAction(pendingAction)}
                >
                  Confirm
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="mb-6 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-medium text-primary">Trust operations</p>
            <h1 className="mt-1 text-2xl font-bold md:text-3xl">Verification workbench</h1>
            <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
              Review instructor, recruiter, and organization verification requests with assignment, approval, rejection, and more-info workflows.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link href="/platform/dashboard" className="btn-base btn-secondary">Platform dashboard</Link>
            <Link href="/platform/audit" className="btn-base btn-secondary">Audit search</Link>
          </div>
        </div>

        {error && <div className="mb-4 rounded-xl border border-destructive/30 bg-card p-4 text-sm text-destructive">{error}</div>}

        <section className="mb-5 rounded-xl border border-border bg-card p-4">
          <div className="grid gap-3 md:grid-cols-5">
            <input
              className="input md:col-span-2"
              value={filters.q}
              onChange={(event) => setFilters((current) => ({ ...current, q: event.target.value }))}
              placeholder="Search reviewer, status, priority..."
            />
            <select className="input" value={filters.status} onChange={(event) => setFilters((current) => ({ ...current, status: event.target.value }))}>
              {STATUS_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
            <select className="input" value={filters.subject_type} onChange={(event) => setFilters((current) => ({ ...current, subject_type: event.target.value }))}>
              {SUBJECT_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
            <select className="input" value={filters.priority} onChange={(event) => setFilters((current) => ({ ...current, priority: event.target.value }))}>
              {PRIORITY_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
            <select className="input md:col-span-2" value={filters.assigned} onChange={(event) => setFilters((current) => ({ ...current, assigned: event.target.value }))}>
              {ASSIGNED_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
            <button type="button" className="btn-base btn-primary md:col-span-3" onClick={() => void loadQueue()}>
              Refresh queue
            </button>
          </div>
        </section>

        <div className="grid gap-5 lg:grid-cols-[0.9fr_1.4fr]">
          <section className="rounded-xl border border-border bg-muted/20 p-4">
            <div className="mb-4 flex items-start justify-between gap-3">
              <div>
                <h2 className="font-semibold">Review queue</h2>
                <p className="text-xs text-muted-foreground">{queue ? `${queue.total} matching requests` : "Loading requests"}</p>
              </div>
              {queue && (
                <div className="flex flex-wrap justify-end gap-1">
                  {Object.entries(queue.counts).slice(0, 4).map(([key, value]) => (
                    <span key={key} className="rounded-md bg-background px-2 py-1 text-xs text-muted-foreground">
                      {labelize(key)} {value}
                    </span>
                  ))}
                </div>
              )}
            </div>
            {loadingQueue ? (
              <div className="h-72 animate-pulse rounded-xl bg-muted" />
            ) : queue?.results.length ? (
              <div className="space-y-3">
                {queue.results.map((item) => (
                  <QueueItem key={item.id} item={item} selected={item.id === selectedId} onSelect={setSelectedId} />
                ))}
              </div>
            ) : (
              <div className="rounded-xl border border-border bg-card p-6 text-sm text-muted-foreground">
                No verification requests match these filters.
              </div>
            )}
          </section>

          <section className="rounded-xl border border-border bg-card p-5">
            {!selectedRequest && !loadingDetail ? (
              <div className="py-16 text-center text-sm text-muted-foreground">Select a verification request to review.</div>
            ) : loadingDetail ? (
              <div className="h-96 animate-pulse rounded-xl bg-muted" />
            ) : detail ? (
              <div className="space-y-6">
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h2 className="text-xl font-bold capitalize">{labelize(detail.request.subject_type)} verification</h2>
                      <StatusPill status={detail.request.status} />
                    </div>
                    <p className="mt-1 text-sm text-muted-foreground">Subject ID: {detail.request.subject_id}</p>
                    <p className="mt-1 text-sm text-muted-foreground">Priority: {detail.request.priority || "normal"}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button type="button" className="btn-sm btn-secondary" disabled={Boolean(busyAction)} onClick={() => void runAction("assign")}>
                      {busyAction === "assign" ? "Assigning..." : "Assign to me"}
                    </button>
                    <button type="button" className="btn-sm btn-primary" disabled={Boolean(busyAction)} onClick={() => void runAction("approve")}>
                      {busyAction === "approve" ? "Approving..." : "Approve"}
                    </button>
                    <button type="button" className="btn-sm btn-secondary" disabled={Boolean(busyAction)} onClick={() => void runAction("more_info")}>
                      More info
                    </button>
                    <button type="button" className="btn-sm border border-destructive/30 text-destructive hover:bg-destructive/10" disabled={Boolean(busyAction)} onClick={() => void runAction("reject")}>
                      Reject
                    </button>
                  </div>
                </div>

                {actionError && <div className="rounded-lg border border-destructive/30 bg-card p-3 text-sm text-destructive">{actionError}</div>}

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="rounded-xl border border-border bg-background p-4">
                    <h3 className="font-semibold text-sm">Applicant notes</h3>
                    <p className="mt-2 whitespace-pre-wrap text-sm text-muted-foreground">{detail.request.applicant_notes || "No applicant notes."}</p>
                  </div>
                  <div className="rounded-xl border border-border bg-background p-4">
                    <h3 className="font-semibold text-sm">Reviewer notes</h3>
                    <p className="mt-2 whitespace-pre-wrap text-sm text-muted-foreground">{detail.request.reviewer_notes || "No reviewer notes yet."}</p>
                  </div>
                </div>

                <div>
                  <h3 className="mb-3 font-semibold">Documents</h3>
                  {detail.request.documents.length === 0 ? (
                    <p className="rounded-xl border border-border bg-background p-4 text-sm text-muted-foreground">No active documents are attached.</p>
                  ) : (
                    <div className="grid gap-3 md:grid-cols-2">
                      {detail.request.documents.map((document) => (
                        <div key={document.id} className="rounded-xl border border-border bg-background p-4">
                          <p className="font-medium text-sm capitalize">{labelize(document.document_type)}</p>
                          <p className="mt-1 text-xs text-muted-foreground">{document.file_name}</p>
                          <div className="mt-3 flex flex-wrap gap-2">
                            <span className="rounded-md bg-muted px-2 py-1 text-xs text-muted-foreground">{document.mime_type}</span>
                            <span className="rounded-md bg-muted px-2 py-1 text-xs text-muted-foreground">{Math.round(document.file_size / 1024)} KB</span>
                            <span className="rounded-md bg-muted px-2 py-1 text-xs text-muted-foreground">{document.is_encrypted ? "encrypted" : "not encrypted"}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div>
                  <h3 className="mb-3 font-semibold">Action history</h3>
                  {detail.actions.length === 0 ? (
                    <p className="rounded-xl border border-border bg-background p-4 text-sm text-muted-foreground">No verification actions have been recorded yet.</p>
                  ) : (
                    <div className="divide-y divide-border rounded-xl border border-border bg-background">
                      {detail.actions.map((action) => (
                        <div key={action.id} className="p-4 text-sm">
                          <div className="flex flex-col gap-1 md:flex-row md:items-center md:justify-between">
                            <strong className="capitalize">{labelize(action.action)}</strong>
                            <span className="text-xs text-muted-foreground">{new Date(action.performed_at).toLocaleString()}</span>
                          </div>
                          <p className="mt-1 text-xs text-muted-foreground">
                            {action.actor_email || "System"} changed {action.previous_status || "-"} to {action.new_status || "-"}
                          </p>
                          {(action.reason || action.notes) && (
                            <p className="mt-2 whitespace-pre-wrap text-sm text-muted-foreground">{action.reason || action.notes}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : null}
          </section>
        </div>
      </main>
    </>
  );
}
