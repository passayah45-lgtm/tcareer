"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import { InstructorGuard } from "@/components/shared/InstructorGuard";
import { getLessons, getLessonVersions } from "@/lib/api/courses.api";
import type { Lesson, LessonVersion } from "@/types/course.types";

export default function InstructorCourseVersionsPage() {
  const params = useParams<{ id: string }>();
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [versions, setVersions] = useState<Record<string, LessonVersion[]>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timer = window.setTimeout(async () => {
      const loadedLessons = await getLessons(params.id);
      setLessons(loadedLessons);
      const entries = await Promise.all(loadedLessons.map(async (lesson) => [lesson.id, await getLessonVersions(params.id, lesson.id)] as const));
      setVersions(Object.fromEntries(entries));
      setLoading(false);
    }, 0);
    return () => window.clearTimeout(timer);
  }, [params.id]);

  return (
    <InstructorGuard>
      <Navbar />
      <main className="max-w-6xl mx-auto px-4 py-8 space-y-6">
        <Link href={`/instructor/courses/${params.id}`} className="text-sm text-primary">Back to course editor</Link>
        <div>
          <p className="text-sm font-semibold text-primary">Version safety</p>
          <h1 className="text-2xl md:text-3xl font-bold">Lesson versions</h1>
          <p className="text-sm text-muted-foreground mt-1">Published versions remain separate from draft revisions and rollback history.</p>
        </div>
        {loading ? <div className="h-56 rounded-xl bg-muted animate-pulse" /> : lessons.length === 0 ? <div className="rounded-xl border border-border bg-card p-8 text-center">No lessons yet.</div> : (
          <div className="space-y-4">
            {lessons.map((lesson) => (
              <section key={lesson.id} className="rounded-xl border border-border bg-card p-5">
                <h2 className="font-semibold">{lesson.title}</h2>
                <p className="text-sm text-muted-foreground">Draft v{lesson.draft_version ?? 1} | Published v{lesson.published_version ?? 0}</p>
                <div className="mt-3 grid gap-2">
                  {(versions[lesson.id] || []).map((version) => (
                    <div key={version.id} className="rounded-lg border border-border p-3 text-sm">
                      Version {version.version_number}: {version.summary_of_changes || "Snapshot"} {version.is_published_version ? "(published)" : ""}
                    </div>
                  ))}
                </div>
              </section>
            ))}
          </div>
        )}
      </main>
    </InstructorGuard>
  );
}
