"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import { getDashboardPathForUser } from "@/lib/auth/role-redirects";
import { getPlatformOperations, runPlatformOperation } from "@/lib/api/platform.api";
import { useAuthStore } from "@/stores/auth.store";
import type { PlatformOperationItem, PlatformOperations } from "@/types/platform.types";
import type { UserRole } from "@/types/user.types";

const PLATFORM_ADMIN_ROLES = new Set<UserRole>(["admin", "platform_admin", "super_admin"]);
const QUEUE_ORDER = ["users", "organizations", "courses", "verification", "email", "audit"];

const QUEUE_ACTIONS: Record<string, Array<{ action: string; label: string; tone?: "primary" | "secondary" | "danger" }>> = {
  users: [
    { action: "activate", label: "Activate", tone: "secondary" },
    { action: "deactivate", label: "Deactivate", tone: "danger" },
  ],
  organizations: [
    { action: "activate", label: "Activate", tone: "secondary" },
    { action: "suspend", label: "Suspend", tone: "danger" },
    { action: "archive", label: "Archive", tone: "secondary" },
  ],
  courses: [{ action: "archive", label: "Archive", tone: "danger" }],
  verification: [
    { action: "assign", label: "Assign", tone: "secondary" },
    { action: "approve", label: "Approve", tone: "primary" },
    { action: "more_info", label: "More info", tone: "secondary" },
    { action: "reject", label: "Reject", tone: "danger" },
  ],
  email: [
    { action: "retry", label: "Retry", tone: "primary" },
    { action: "cancel", label: "Cancel", tone: "danger" },
  ],
};

const REASON_REQUIRED_ACTIONS = new Set([
  "users:deactivate",
  "organizations:suspend",
  "organizations:archive",
  "courses:archive",
  "verification:reject",
  "verification:more_info",
  "email:cancel",
]);

function OperationCard({
  queueKey,
  item,
  busy,
  onRun,
}: {
  queueKey: string;
  item: PlatformOperationItem;
  busy: boolean;
  onRun: (queueKey: string, item: PlatformOperationItem, action: string) => void;
}) {
  const actions = QUEUE_ACTIONS[queueKey] || [];
  return (
    <div className="rounded-lg border border-border bg-background p-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <p className="font-medium text-sm truncate">{item.label}</p>
            <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">{item.status}</span>
          </div>
          <p className="text-xs text-muted-foreground mt-1 truncate">{item.subtitle}</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {Object.entries(item.metadata || {}).slice(0, 4).map(([key, value]) => (
              <span key={key} className="rounded-md bg-muted/70 px-2 py-1 text-xs text-muted-foreground">
                {key.replaceAll("_", " ")}: {String(value || "-")}
              </span>
            ))}
          </div>
        </div>
        {actions.length > 0 && (
          <div className="flex flex-wrap gap-2 lg:justify-end">
            {actions.map((operation) => (
              <button
                key={operation.action}
                type="button"
                disabled={busy}
                onClick={() => onRun(queueKey, item, operation.action)}
                className={
                  operation.tone === "danger"
                    ? "btn-sm border border-destructive/30 text-destructive hover:bg-destructive/10"
                    : operation.tone === "primary"
                      ? "btn-sm btn-primary"
                      : "btn-sm btn-secondary"
                }
              >
                {busy ? "Working..." : operation.label}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function PlatformOperationsPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading } = useAuthStore();
  const [operations, setOperations] = useState<PlatformOperations | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [operationError, setOperationError] = useState("");
  const [busyOperation, setBusyOperation] = useState("");
  const [pendingOperation, setPendingOperation] = useState<{ queueKey: string; item: PlatformOperationItem; action: string } | null>(null);
  const [reason, setReason] = useState("");
  const canAccessPlatform = Boolean(user?.role && PLATFORM_ADMIN_ROLES.has(user.role));

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      router.push("/login?next=/platform/operations");
      return;
    }
    if (!canAccessPlatform) {
      router.push(getDashboardPathForUser(user));
    }
  }, [canAccessPlatform, isAuthenticated, isLoading, router, user]);

  async function refreshOperations() {
    const data = await getPlatformOperations();
    setOperations(data);
  }

  useEffect(() => {
    if (isLoading || !isAuthenticated || !canAccessPlatform) return;
    const timer = window.setTimeout(() => {
      setLoading(true);
      refreshOperations()
        .then(() => setError(""))
        .catch(() => setError("Unable to load platform operation queues."))
        .finally(() => setLoading(false));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [canAccessPlatform, isAuthenticated, isLoading]);

  async function handleOperation(queueKey: string, item: PlatformOperationItem, action: string) {
    if (REASON_REQUIRED_ACTIONS.has(`${queueKey}:${action}`) && !pendingOperation) {
      setPendingOperation({ queueKey, item, action });
      setReason("");
      setOperationError("");
      return;
    }
    const busyKey = `${queueKey}:${item.id}:${action}`;
    setBusyOperation(busyKey);
    setOperationError("");
    try {
      await runPlatformOperation(queueKey, item.id, action, reason.trim() ? { reason: reason.trim() } : {});
      await refreshOperations();
      setPendingOperation(null);
      setReason("");
    } catch {
      setOperationError(`Unable to ${action.replaceAll("_", " ")} ${item.label}.`);
    } finally {
      setBusyOperation("");
    }
  }

  if (isLoading || (!isAuthenticated || !canAccessPlatform)) {
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
        {pendingOperation && (
          <div className="fixed inset-0 z-[80] flex items-center justify-center bg-black/40 px-4">
            <div className="w-full max-w-lg rounded-xl border border-border bg-background p-5 shadow-xl">
              <h2 className="font-semibold">Reason required</h2>
              <p className="mt-2 text-sm text-muted-foreground">
                {pendingOperation.action.replaceAll("_", " ")}: {pendingOperation.item.label}
              </p>
              <textarea
                className="input mt-4 min-h-28 w-full"
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                placeholder="Explain why this admin action is necessary."
              />
              <div className="mt-4 flex flex-wrap justify-end gap-2">
                <button type="button" className="btn-base btn-secondary" onClick={() => { setPendingOperation(null); setReason(""); }}>
                  Cancel
                </button>
                <button
                  type="button"
                  className="btn-base btn-primary"
                  disabled={reason.trim().length < 10 || Boolean(busyOperation)}
                  onClick={() => void handleOperation(pendingOperation.queueKey, pendingOperation.item, pendingOperation.action)}
                >
                  Confirm action
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-medium text-primary">Platform management</p>
            <h1 className="text-2xl md:text-3xl font-bold mt-1">Operations queues</h1>
            <p className="text-sm text-muted-foreground mt-2 max-w-3xl">
              Focused production queues for access, organizations, course moderation, verification, email delivery, and audit review.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link href="/platform/dashboard" className="btn-base btn-secondary">Back to dashboard</Link>
            <Link href="/platform/verification" className="btn-base btn-secondary">Verification workbench</Link>
            <Link href="/platform/audit" className="btn-base btn-secondary">Audit search</Link>
          </div>
        </div>

        {error && <div className="rounded-xl border border-destructive/30 bg-card p-5 text-sm text-destructive">{error}</div>}
        {operationError && <div className="rounded-xl border border-destructive/30 bg-card p-5 text-sm text-destructive">{operationError}</div>}

        {!operations || loading ? (
          <div className="h-72 rounded-xl bg-muted animate-pulse" />
        ) : (
          <>
            <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
              {Object.entries(operations.counts).map(([key, value]) => (
                <div key={key} className="rounded-xl border border-border bg-card p-4">
                  <p className="text-2xl font-bold text-primary">{value}</p>
                  <p className="text-xs text-muted-foreground leading-4">{key.replaceAll("_", " ")}</p>
                </div>
              ))}
            </section>
            <section className="grid gap-4 xl:grid-cols-2">
              {QUEUE_ORDER.map((queueKey) => {
                const queue = operations.queues[queueKey];
                if (!queue) return null;
                return (
                  <div key={queueKey} className="rounded-xl border border-border bg-card p-5">
                    <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                      <div>
                        <h2 className="font-semibold">{queue.label}</h2>
                        <p className="text-xs text-muted-foreground mt-1">{queue.description}</p>
                      </div>
                      {queueKey === "verification" && <Link href="/platform/verification" className="btn-sm btn-secondary">Open workbench</Link>}
                      {queueKey === "audit" && <Link href="/platform/audit" className="btn-sm btn-secondary">Open search</Link>}
                    </div>
                    <div className="mt-4 space-y-3">
                      {queue.items.length === 0 ? (
                        <p className="rounded-lg border border-border bg-background p-4 text-sm text-muted-foreground">No items need attention.</p>
                      ) : (
                        queue.items.map((item) => (
                          <OperationCard
                            key={item.id}
                            queueKey={queueKey}
                            item={item}
                            busy={busyOperation.startsWith(`${queueKey}:${item.id}:`)}
                            onRun={handleOperation}
                          />
                        ))
                      )}
                    </div>
                  </div>
                );
              })}
            </section>
          </>
        )}
      </main>
    </>
  );
}
