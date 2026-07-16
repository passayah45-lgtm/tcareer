"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Navbar } from "@/components/layout/Navbar";
import { getAcademicAudit } from "@/lib/api/courses.api";
import type { AcademicAuditRow } from "@/types/course.types";

export default function AcademicAuditPage() {
  const [rows, setRows] = useState<AcademicAuditRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const timer = window.setTimeout(() => {
      getAcademicAudit()
        .then((data) => {
          setRows(data);
          setError("");
        })
        .catch(() => setError("Unable to load academic audit events."))
        .finally(() => setLoading(false));
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  return (
    <>
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 py-8 space-y-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-semibold text-primary">Academic governance</p>
            <h1 className="text-2xl md:text-3xl font-bold">Academic audit</h1>
            <p className="text-sm text-muted-foreground mt-1">Review assignments, approvals, rejections, version rollbacks, publication blocks, and resource actions.</p>
          </div>
          <Link className="btn-base btn-secondary" href="/platform/dashboard">Back to platform</Link>
        </div>
        {loading ? <div className="h-60 rounded-xl bg-muted animate-pulse" /> : error ? <div className="rounded-xl border border-red-200 bg-red-50 p-5 text-sm text-red-700">{error}</div> : rows.length === 0 ? (
          <div className="rounded-xl border border-border bg-card p-8 text-center">No academic audit events yet.</div>
        ) : (
          <div className="overflow-hidden rounded-xl border border-border bg-card">
            <div className="grid grid-cols-4 gap-3 border-b border-border px-4 py-3 text-xs font-semibold uppercase text-muted-foreground">
              <span>Time</span><span>Actor</span><span>Action</span><span>Target</span>
            </div>
            {rows.map((row) => (
              <div key={row.id} className="grid grid-cols-4 gap-3 border-b border-border px-4 py-3 text-sm last:border-b-0">
                <span>{new Date(row.timestamp).toLocaleString()}</span>
                <span>{row.actor_email || "System"}</span>
                <span>{row.action}</span>
                <span>{row.target_type}</span>
              </div>
            ))}
          </div>
        )}
      </main>
    </>
  );
}
