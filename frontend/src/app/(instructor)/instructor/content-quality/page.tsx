"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Navbar } from "@/components/layout/Navbar";
import { InstructorGuard } from "@/components/shared/InstructorGuard";
import { getAuthorAnalytics, getContentQualityDashboard, submitCourseForReview } from "@/lib/api/courses.api";
import type { CourseQualityDashboard, InstructorAnalytics } from "@/types/course.types";

const scoreColor = (score: number) => {
  if (score >= 85) return "text-emerald-700";
  if (score >= 60) return "text-amber-700";
  return "text-red-700";
};

export default function InstructorContentQualityPage() {
  const [dashboard, setDashboard] = useState<CourseQualityDashboard | null>(null);
  const [analytics, setAnalytics] = useState<InstructorAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [submittingCourseId, setSubmittingCourseId] = useState<string | null>(null);

  async function load() {
    try {
      const [quality, authorAnalytics] = await Promise.all([
        getContentQualityDashboard(),
        getAuthorAnalytics(),
      ]);
      setDashboard(quality);
      setAnalytics(authorAnalytics);
    } catch {
      setError("Could not load content quality data.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  const weakestCourses = useMemo(() => {
    return [...(dashboard?.courses ?? [])].sort((a, b) => a.quality_score - b.quality_score).slice(0, 3);
  }, [dashboard]);

  async function handleSubmitReview(courseId: string) {
    setSubmittingCourseId(courseId);
    setError("");
    try {
      await submitCourseForReview(courseId, "Submitted from content quality dashboard.");
      await load();
    } catch {
      setError("Could not submit this course for review.");
    } finally {
      setSubmittingCourseId(null);
    }
  }

  return (
    <InstructorGuard>
      <Navbar />
      <main className="max-w-6xl mx-auto px-4 py-8">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between mb-8">
          <div>
            <p className="text-sm font-semibold text-primary">Academic readiness</p>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight">Content quality</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Review course completeness, lesson approval, assessments, projects, and resource readiness before publishing.
            </p>
          </div>
          <Link
            href="/instructor/courses"
            className="h-10 px-4 inline-flex items-center justify-center text-sm font-medium border border-border rounded-lg hover:bg-muted transition-colors"
          >
            Course workspace
          </Link>
        </div>

        {loading ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[...Array(4)].map((_, index) => (
                <div key={index} className="h-24 rounded-xl bg-muted animate-pulse" />
              ))}
            </div>
            <div className="h-72 rounded-xl bg-muted animate-pulse" />
          </div>
        ) : error ? (
          <div className="border border-red-200 bg-red-50 rounded-xl p-5 text-sm text-red-700">{error}</div>
        ) : dashboard ? (
          <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-card border border-border rounded-xl p-5">
                <p className="text-2xl font-bold text-primary">{dashboard.summary.total_courses}</p>
                <p className="text-sm font-medium mt-0.5">Courses reviewed</p>
              </div>
              <div className="bg-card border border-border rounded-xl p-5">
                <p className="text-2xl font-bold text-emerald-700">{dashboard.summary.publish_ready}</p>
                <p className="text-sm font-medium mt-0.5">Publish ready</p>
              </div>
              <div className="bg-card border border-border rounded-xl p-5">
                <p className={"text-2xl font-bold " + scoreColor(dashboard.summary.average_score)}>
                  {dashboard.summary.average_score}%
                </p>
                <p className="text-sm font-medium mt-0.5">Average score</p>
              </div>
              <div className="bg-card border border-border rounded-xl p-5">
                <p className="text-2xl font-bold text-primary">{analytics?.reviews_completed ?? 0}</p>
                <p className="text-sm font-medium mt-0.5">Reviews completed</p>
              </div>
            </div>

            {weakestCourses.length > 0 && (
              <section className="border border-border bg-card rounded-xl p-5">
                <h2 className="text-lg font-semibold mb-1">Priority fixes</h2>
                <p className="text-sm text-muted-foreground mb-4">Courses with the lowest readiness scores should be reviewed first.</p>
                <div className="grid gap-3 md:grid-cols-3">
                  {weakestCourses.map((course) => (
                    <Link
                      href={`/instructor/courses/${course.course_id}`}
                      key={course.course_id}
                      className="border border-border rounded-lg p-4 hover:bg-muted/50 transition-colors"
                    >
                      <p className="font-semibold text-sm truncate">{course.title}</p>
                      <p className={"text-2xl font-bold mt-2 " + scoreColor(course.quality_score)}>{course.quality_score}%</p>
                      <p className="text-xs text-muted-foreground mt-1">{course.blockers[0] || "Ready for academic review."}</p>
                    </Link>
                  ))}
                </div>
              </section>
            )}

            <section className="border border-border bg-card rounded-xl overflow-hidden">
              <div className="p-5 border-b border-border">
                <h2 className="text-lg font-semibold">Course checklist</h2>
                <p className="text-sm text-muted-foreground">Each course must clear content, assessment, project, resource, and review gates.</p>
              </div>
              <div className="divide-y divide-border">
                {dashboard.courses.length === 0 ? (
                  <div className="p-8 text-center">
                    <p className="font-semibold">No instructor courses yet</p>
                    <p className="text-sm text-muted-foreground mt-1">Create a course before using academic quality review.</p>
                  </div>
                ) : (
                  dashboard.courses.map((course) => (
                    <article key={course.course_id} className="p-5">
                      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <h3 className="font-semibold truncate">{course.title}</h3>
                            <span className="text-xs px-2 py-0.5 rounded-full border border-border capitalize">{course.status}</span>
                            {course.publish_ready && (
                              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                                Ready
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-muted-foreground mt-1">
                            {course.metrics.lesson_count} lessons, {course.metrics.approved_lessons} approved, {course.metrics.approved_certificate_questions} approved certificate questions
                          </p>
                        </div>
                        <div className="flex flex-wrap items-center gap-2">
                          <span className={"text-xl font-bold " + scoreColor(course.quality_score)}>{course.quality_score}%</span>
                          <button
                            type="button"
                            disabled={submittingCourseId === course.course_id}
                            onClick={() => void handleSubmitReview(course.course_id)}
                            className="h-9 px-3 text-xs font-medium rounded-lg bg-primary text-primary-foreground hover:bg-primary-600 disabled:opacity-60 transition-colors"
                          >
                            {submittingCourseId === course.course_id ? "Submitting" : "Submit review"}
                          </button>
                          <Link
                            href={`/instructor/courses/${course.course_id}`}
                            className="h-9 px-3 inline-flex items-center text-xs font-medium border border-border rounded-lg hover:bg-muted transition-colors"
                          >
                            Open
                          </Link>
                          <Link
                            href={`/instructor/courses/${course.course_id}/review`}
                            className="h-9 px-3 inline-flex items-center text-xs font-medium border border-border rounded-lg hover:bg-muted transition-colors"
                          >
                            Review
                          </Link>
                          <Link
                            href={`/instructor/courses/${course.course_id}/versions`}
                            className="h-9 px-3 inline-flex items-center text-xs font-medium border border-border rounded-lg hover:bg-muted transition-colors"
                          >
                            Versions
                          </Link>
                        </div>
                      </div>

                      <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-3 mt-4">
                        {course.checks.map((check) => (
                          <div
                            key={check.key}
                            className={
                              "rounded-lg border p-3 " +
                              (check.passed ? "border-emerald-200 bg-emerald-50" : "border-amber-200 bg-amber-50")
                            }
                          >
                            <p className={check.passed ? "text-sm font-semibold text-emerald-800" : "text-sm font-semibold text-amber-900"}>
                              {check.passed ? "Passed" : "Needs work"}: {check.label}
                            </p>
                            <p className={check.passed ? "text-xs text-emerald-700 mt-1" : "text-xs text-amber-800 mt-1"}>{check.detail}</p>
                          </div>
                        ))}
                      </div>
                    </article>
                  ))
                )}
              </div>
            </section>
          </div>
        ) : null}
      </main>
    </InstructorGuard>
  );
}
