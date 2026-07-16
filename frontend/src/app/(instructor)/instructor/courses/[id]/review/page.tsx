"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import { InstructorGuard } from "@/components/shared/InstructorGuard";
import { getCoursePublishBlockers, getCourseQuality, getCourseReviews, submitCourseForReview } from "@/lib/api/courses.api";
import type { CourseQualityReadiness, CourseReview, PublishBlockerResponse } from "@/types/course.types";

export default function InstructorCourseReviewPage() {
  const params = useParams<{ id: string }>();
  const [quality, setQuality] = useState<CourseQualityReadiness | null>(null);
  const [blockers, setBlockers] = useState<PublishBlockerResponse | null>(null);
  const [reviews, setReviews] = useState<CourseReview[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    const [q, b, r] = await Promise.all([
      getCourseQuality(params.id),
      getCoursePublishBlockers(params.id),
      getCourseReviews(params.id),
    ]);
    setQuality(q);
    setBlockers(b);
    setReviews(r);
    setLoading(false);
  }, [params.id]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function submit() {
    await submitCourseForReview(params.id, "Ready for academic review.");
    setMessage("Course submitted for academic review.");
    await load();
  }

  return (
    <InstructorGuard>
      <Navbar />
      <main className="max-w-6xl mx-auto px-4 py-8 space-y-6">
        <Link href={`/instructor/courses/${params.id}`} className="text-sm text-primary">Back to course editor</Link>
        {loading ? <div className="h-52 rounded-xl bg-muted animate-pulse" /> : (
          <>
            <div>
              <p className="text-sm font-semibold text-primary">Instructor workflow</p>
              <h1 className="text-2xl md:text-3xl font-bold">{quality?.title} review</h1>
              <p className="text-sm text-muted-foreground mt-1">Quality score {quality?.quality_score}%</p>
            </div>
            <section className="rounded-xl border border-border bg-card p-5">
              <h2 className="font-semibold mb-3">Readiness blockers</h2>
              {blockers?.publish_ready ? <p className="text-sm text-emerald-700">No publication blockers detected.</p> : (
                <ul className="space-y-2 text-sm text-muted-foreground">
                  {blockers?.blockers.map((item) => <li key={item.code}>{item.message}</li>)}
                </ul>
              )}
            </section>
            <section className="rounded-xl border border-border bg-card p-5">
              <h2 className="font-semibold mb-3">Approval history</h2>
              {reviews.length === 0 ? <p className="text-sm text-muted-foreground">No course review decisions yet.</p> : reviews.map((review) => (
                <div key={review.id} className="border-b border-border py-3 last:border-b-0">
                  <p className="font-medium capitalize">{review.status}</p>
                  <p className="text-sm text-muted-foreground">{review.comments || "No comments"}</p>
                </div>
              ))}
            </section>
            <button type="button" className="btn-base btn-primary" onClick={() => void submit()}>Submit or resubmit for review</button>
            {message && <p className="text-sm text-emerald-700">{message}</p>}
          </>
        )}
      </main>
    </InstructorGuard>
  );
}
