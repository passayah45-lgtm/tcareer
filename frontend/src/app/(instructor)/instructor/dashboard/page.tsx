"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Navbar } from "@/components/layout/Navbar";
import { InstructorGuard } from "@/components/shared/InstructorGuard";
import { getInstructorCourses } from "@/lib/api/courses.api";
import type { Course } from "@/types/course.types";

const statusColors: Record<string, string> = {
  draft: "bg-amber-50 text-amber-700 border border-amber-200",
  published: "bg-emerald-50 text-emerald-700 border border-emerald-200",
  archived: "bg-muted text-muted-foreground border border-border",
};

export default function InstructorDashboardPage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getInstructorCourses().then((d) => setCourses(d.results)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const published = courses.filter((c) => c.status === "published").length;
  const drafts = courses.filter((c) => c.status === "draft").length;
  const totalLessons = courses.reduce((sum, c) => sum + (c.total_lessons || 0), 0);

  return (
    <InstructorGuard>
      <Navbar />
      <main className="max-w-5xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight">Instructor dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1">Overview of your courses and activity.</p>
        </div>
        {loading ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="h-24 bg-muted rounded-xl animate-pulse" />)}</div>
            <div className="h-48 bg-muted rounded-xl animate-pulse" />
          </div>
        ) : (
          <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[{label:"Total courses",value:courses.length},{label:"Published",value:published},{label:"Drafts",value:drafts},{label:"Total lessons",value:totalLessons}].map((s) => (
                <div key={s.label} className="bg-card border border-border rounded-xl p-5">
                  <p className="text-2xl font-bold text-primary">{s.value}</p>
                  <p className="text-sm font-medium mt-0.5">{s.label}</p>
                </div>
              ))}
            </div>
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-5">
              <h2 className="font-semibold text-amber-900 mb-1 text-sm">Earnings coming soon</h2>
              <p className="text-xs text-amber-800 leading-relaxed">Instructor revenue sharing is in development. When it launches you will earn a percentage of every subscription from students enrolled in your courses.</p>
            </div>
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold">Your courses</h2>
                <Link href="/instructor/courses/new" className="h-9 px-4 inline-flex items-center text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary-600 transition-colors">Create course</Link>
              </div>
              {courses.length === 0 ? (
                <div className="border border-border rounded-xl p-10 text-center bg-card">
                  <p className="font-semibold mb-1">No courses yet</p>
                  <p className="text-sm text-muted-foreground mb-4">Create your first course to start teaching.</p>
                  <Link href="/instructor/courses/new" className="inline-flex items-center h-9 px-4 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary-600 transition-colors">Create your first course</Link>
                </div>
              ) : (
                <div className="space-y-2">
                  {courses.slice(0, 5).map((course) => (
                    <div key={course.id} className="border border-border rounded-xl p-4 flex items-center gap-4 bg-card hover:shadow-sm transition-all duration-200">
                      <div className="w-14 h-10 rounded-lg bg-muted flex-shrink-0 overflow-hidden">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        {course.thumbnail_url ? <img src={course.thumbnail_url} alt={course.title} className="w-full h-full object-cover" /> : <div className="w-full h-full flex items-center justify-center text-primary/20 text-lg font-bold">T</div>}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm truncate">{course.title}</p>
                        <p className="text-xs text-muted-foreground mt-0.5 capitalize">{course.level} � {course.total_lessons} lessons</p>
                      </div>
                      <div className="flex items-center gap-3 flex-shrink-0">
                        <span className={"text-xs px-2 py-0.5 rounded-full font-medium capitalize " + statusColors[course.status]}>{course.status}</span>
                        <Link href={"/instructor/courses/" + course.id} className="h-8 px-3 inline-flex items-center text-xs font-medium border border-border rounded-lg hover:bg-muted transition-colors">Edit</Link>
                      </div>
                    </div>
                  ))}
                  {courses.length > 5 && <Link href="/instructor/courses" className="block text-center text-sm text-primary hover:text-primary-600 py-2 transition-colors">View all {courses.length} courses</Link>}
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </InstructorGuard>
  );
}
