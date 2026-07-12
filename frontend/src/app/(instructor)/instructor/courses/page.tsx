"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Navbar } from "@/components/layout/Navbar";
import { InstructorGuard } from "@/components/shared/InstructorGuard";
import { getInstructorCourses, publishCourse } from "@/lib/api/courses.api";
import { toast } from "@/components/shared/Toast";
import { formatPrice } from "@/lib/utils";
import type { Course } from "@/types/course.types";

const statusColors: Record<string, string> = {
  draft: "bg-amber-50 text-amber-700 border border-amber-200",
  published: "bg-emerald-50 text-emerald-700 border border-emerald-200",
  archived: "bg-muted text-muted-foreground border border-border",
};

export default function InstructorCoursesPage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [publishing, setPublishing] = useState<string | null>(null);

  useEffect(() => {
    getInstructorCourses().then((d) => setCourses(d.results)).catch(() => toast("Failed to load courses.", "error")).finally(() => setLoading(false));
  }, []);

  async function handlePublish(courseId: string) {
    setPublishing(courseId);
    try {
      const updated = await publishCourse(courseId);
      setCourses((prev) => prev.map((c) => (c.id === courseId ? updated : c)));
      toast("Course published.");
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      toast(e?.response?.data?.detail || "Could not publish course.", "error");
    } finally { setPublishing(null); }
  }

  return (
    <InstructorGuard>
      <Navbar />
      <main className="max-w-5xl mx-auto px-4 py-8">
        <div className="flex items-start justify-between mb-8 gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight">My courses</h1>
            <p className="text-sm text-muted-foreground mt-1">{courses.length} course{courses.length !== 1 ? "s" : ""} total</p>
          </div>
          <Link href="/instructor/courses/new" className="flex-shrink-0 h-9 px-4 inline-flex items-center gap-2 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary-600 transition-colors">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" /></svg>
            New course
          </Link>
        </div>
        {loading ? (
          <div className="space-y-3">{[...Array(4)].map((_, i) => <div key={i} className="h-20 bg-muted rounded-xl animate-pulse" />)}</div>
        ) : courses.length === 0 ? (
          <div className="border border-border rounded-xl p-12 text-center bg-card">
            <p className="font-semibold mb-1">No courses yet</p>
            <p className="text-sm text-muted-foreground mb-4">Create your first course to start teaching on T-Career.</p>
            <Link href="/instructor/courses/new" className="inline-flex items-center h-9 px-4 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary-600 transition-colors">Create your first course</Link>
          </div>
        ) : (
          <div className="space-y-2">
            {courses.map((course) => (
              <div key={course.id} className="border border-border rounded-xl p-4 flex items-center gap-4 bg-card hover:shadow-sm transition-all duration-200">
                <div className="w-16 h-12 rounded-lg bg-muted flex-shrink-0 overflow-hidden">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  {course.thumbnail_url ? <img src={course.thumbnail_url} alt={course.title} className="w-full h-full object-cover" /> : <div className="w-full h-full flex items-center justify-center text-primary/20 text-lg font-bold">T</div>}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-sm truncate">{course.title}</h3>
                  <p className="text-xs text-muted-foreground mt-0.5 capitalize">{course.level} � {course.total_lessons} lessons � {formatPrice(course.price)}</p>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <span className={"text-xs px-2 py-0.5 rounded-full font-medium capitalize " + statusColors[course.status]}>{course.status}</span>
                  <Link href={"/instructor/courses/" + course.id} className="h-8 px-3 inline-flex items-center text-xs font-medium border border-border rounded-lg hover:bg-muted transition-colors">Edit</Link>
                  {course.status === "draft" && <button onClick={() => handlePublish(course.id)} disabled={publishing === course.id} className="h-8 px-3 inline-flex items-center text-xs font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary-600 disabled:opacity-50 transition-colors">{publishing === course.id ? "Publishing..." : "Publish"}</button>}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </InstructorGuard>
  );
}
