"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Navbar } from "@/components/layout/Navbar";
import { getReviewerQueue } from "@/lib/api/courses.api";
import type { ReviewAssignment } from "@/types/course.types";

function targetHref(item: ReviewAssignment) {
  if (item.target_type === "lesson") return `/reviewer/lessons/${item.target_id}`;
  if (item.target_type === "assessment") return `/reviewer/questions/${item.target_id}?course=${item.course || ""}`;
  if (item.target_type === "project") return `/reviewer/projects/${item.target_id}?course=${item.course || ""}`;
  return `/reviewer/courses/${item.course || item.target_id}`;
}

export default function ReviewerQueuePage() {
  const [assignments, setAssignments] = useState<ReviewAssignment[]>([]);
  const [filter, setFilter] = useState("me");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setLoading(true);
      getReviewerQueue(filter === "me" ? { assigned: "me" } : filter === "overdue" ? { overdue: "true" } : {})
        .then((data) => {
          setAssignments(data.results);
          setError("");
        })
        .catch(() => setError("Unable to load reviewer queue."))
        .finally(() => setLoading(false));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [filter]);

  return (
    <>
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 py-8 space-y-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-semibold text-primary">Academic review</p>
            <h1 className="text-2xl md:text-3xl font-bold">Review queue</h1>
            <p className="text-sm text-muted-foreground mt-1">Assigned, overdue, high-priority, and completed academic review work.</p>
          </div>
          <Link href="/reviewer/dashboard" className="btn-base btn-secondary">Dashboard</Link>
        </div>

        <div className="flex flex-wrap gap-2">
          {["me", "all", "overdue"].map((value) => (
            <button key={value} type="button" className={filter === value ? "btn-base btn-primary" : "btn-base btn-secondary"} onClick={() => setFilter(value)}>
              {value === "me" ? "Assigned to me" : value}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="h-52 rounded-xl bg-muted animate-pulse" />
        ) : error ? (
          <div className="rounded-xl border border-red-200 bg-red-50 p-5 text-sm text-red-700">{error}</div>
        ) : assignments.length === 0 ? (
          <div className="rounded-xl border border-border bg-card p-8 text-center">
            <p className="font-semibold">No review assignments</p>
            <p className="text-sm text-muted-foreground mt-1">Your queue is clear for this filter.</p>
          </div>
        ) : (
          <div className="divide-y divide-border rounded-xl border border-border bg-card">
            {assignments.map((item) => (
              <Link key={item.id} href={targetHref(item)} className="block p-5 hover:bg-muted/50">
                <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                  <div>
                    <p className="font-semibold capitalize">{item.target_type} review</p>
                    <p className="text-sm text-muted-foreground">{item.course_title || item.lesson_title || item.target_id}</p>
                  </div>
                  <div className="flex flex-wrap gap-2 text-xs">
                    <span className="rounded-full border border-border px-2 py-1 capitalize">{item.review_status}</span>
                    <span className="rounded-full border border-border px-2 py-1 capitalize">{item.priority}</span>
                    {item.is_overdue && <span className="rounded-full border border-red-200 bg-red-50 px-2 py-1 text-red-700">Overdue</span>}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>
    </>
  );
}
