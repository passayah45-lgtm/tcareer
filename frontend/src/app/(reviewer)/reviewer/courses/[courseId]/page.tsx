"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import { decideCourseReview, getCoursePublishBlockers, getCourseQuality, getLessons } from "@/lib/api/courses.api";
import type { CourseQualityReadiness, Lesson, PublishBlockerResponse } from "@/types/course.types";

export default function ReviewerCoursePage() {
  const params = useParams<{ courseId: string }>();
  const [quality, setQuality] = useState<CourseQualityReadiness | null>(null);
  const [blockers, setBlockers] = useState<PublishBlockerResponse | null>(null);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const [q, b, l] = await Promise.all([
        getCourseQuality(params.courseId),
        getCoursePublishBlockers(params.courseId),
        getLessons(params.courseId),
      ]);
      setQuality(q);
      setBlockers(b);
      setLessons(l);
      setError("");
    } catch {
      setError("Unable to load course review workspace.");
    } finally {
      setLoading(false);
    }
  }, [params.courseId]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function decide(status: "approved" | "changes_requested" | "rejected") {
    await decideCourseReview(params.courseId, { status, comments: `Reviewer decision: ${status}` });
    await load();
  }

  return (
    <>
      <Navbar />
      <main className="max-w-6xl mx-auto px-4 py-8 space-y-6">
        <Link href="/reviewer/queue" className="text-sm text-primary">Back to queue</Link>
        {loading ? <div className="h-48 rounded-xl bg-muted animate-pulse" /> : error ? <div className="rounded-xl border border-red-200 bg-red-50 p-5 text-sm text-red-700">{error}</div> : (
          <>
            <div>
              <p className="text-sm font-semibold text-primary">Course review</p>
              <h1 className="text-2xl md:text-3xl font-bold">{quality?.title}</h1>
              <p className="text-sm text-muted-foreground mt-1">Readiness score {quality?.quality_score}%</p>
            </div>
            <section className="rounded-xl border border-border bg-card p-5">
              <h2 className="font-semibold mb-3">Publishing blockers</h2>
              {blockers?.publish_ready ? <p className="text-sm text-emerald-700">No blockers detected.</p> : (
                <ul className="space-y-2 text-sm text-muted-foreground">
                  {blockers?.blockers.map((item) => <li key={item.code}>{item.message}</li>)}
                </ul>
              )}
            </section>
            <section className="rounded-xl border border-border bg-card p-5">
              <h2 className="font-semibold mb-3">Lessons</h2>
              <div className="grid gap-2 md:grid-cols-2">
                {lessons.map((lesson) => (
                  <Link key={lesson.id} href={`/reviewer/lessons/${lesson.id}?course=${params.courseId}`} className="rounded-lg border border-border p-3 hover:bg-muted/50">
                    <p className="font-medium">{lesson.title}</p>
                    <p className="text-xs text-muted-foreground mt-1">Review: {lesson.review_status || "draft"}</p>
                  </Link>
                ))}
              </div>
            </section>
            <div className="flex flex-wrap gap-2">
              <button className="btn-base btn-primary" onClick={() => void decide("approved")} type="button">Approve course</button>
              <button className="btn-base btn-secondary" onClick={() => void decide("changes_requested")} type="button">Request changes</button>
              <button className="btn-base btn-secondary" onClick={() => void decide("rejected")} type="button">Reject</button>
            </div>
          </>
        )}
      </main>
    </>
  );
}
