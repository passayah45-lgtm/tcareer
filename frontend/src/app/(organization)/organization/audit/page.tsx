"use client";

import { useCallback, useEffect, useState } from "react";
import { OrganizationShell, OrgEmptyState, useOrganizationContext } from "@/components/organization/OrganizationShell";
import { getEnterpriseAudit } from "@/lib/api/organizations.api";
import type { EnterpriseAuditResponse } from "@/types/organization.types";

export default function OrganizationAuditPage() {
  const { organization } = useOrganizationContext();
  const [audit, setAudit] = useState<EnterpriseAuditResponse | null>(null);
  const [query, setQuery] = useState("");
  const [action, setAction] = useState("");
  const [actionPrefix, setActionPrefix] = useState("");
  const [targetType, setTargetType] = useState("");
  const [targetId, setTargetId] = useState("");
  const [severity, setSeverity] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!organization) return;
    setAudit(await getEnterpriseAudit(organization.id, {
      q: query || undefined,
      action: action || undefined,
      action_prefix: actionPrefix || undefined,
      target_type: targetType || undefined,
      target_id: targetId || undefined,
      severity: severity || undefined,
    }));
  }, [organization, query, action, actionPrefix, targetType, targetId, severity]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      load().catch(() => setError("Unable to load audit center."));
    }, 250);
    return () => window.clearTimeout(timer);
  }, [load]);

  return (
    <OrganizationShell title="Audit center" description="Filter organization audit events across roles, lifecycle, exports, imports, and hierarchy changes.">
      {error && <p className="text-sm text-destructive mb-4">{error}</p>}
      <section className="rounded-xl border border-border bg-card p-5 mb-6 grid gap-3 md:grid-cols-3">
        <input className="input" placeholder="Search target/action" value={query} onChange={(event) => setQuery(event.target.value)} />
        <input className="input" placeholder="Action filter" value={action} onChange={(event) => setAction(event.target.value)} />
        <input className="input" placeholder="Action prefix" value={actionPrefix} onChange={(event) => setActionPrefix(event.target.value)} />
        <input className="input" placeholder="Target type" value={targetType} onChange={(event) => setTargetType(event.target.value)} />
        <input className="input" placeholder="Target id" value={targetId} onChange={(event) => setTargetId(event.target.value)} />
        <select className="input" value={severity} onChange={(event) => setSeverity(event.target.value)}>
          <option value="">Any severity</option>
          <option value="info">Info</option>
          <option value="warning">Warning</option>
          <option value="critical">Critical</option>
        </select>
      </section>
      {!audit ? <OrgEmptyState title="Loading audit events" body="Audit events are being loaded." /> : (
        <section className="rounded-xl border border-border bg-card p-5">
          <p className="text-sm text-muted-foreground mb-4">{audit.total} matching events</p>
          <div className="divide-y divide-border">
            {audit.events.map((item) => (
              <div key={item.id} className="py-3 text-sm grid gap-1 md:grid-cols-[1fr_160px_1fr_120px_180px]">
                <span>{item.action.replaceAll("_", " ")}</span>
                <span>{item.target_type}</span>
                <span className="text-muted-foreground truncate">{item.target_id}</span>
                <span className="text-muted-foreground">{String(item.metadata.severity ?? "info")}</span>
                <span className="text-muted-foreground">{new Date(item.created_at).toLocaleString()}</span>
              </div>
            ))}
          </div>
        </section>
      )}
    </OrganizationShell>
  );
}
