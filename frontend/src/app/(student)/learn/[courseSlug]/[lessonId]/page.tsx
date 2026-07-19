"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth.store";
import { getCourse, getCourseProgress, getLesson } from "@/lib/api/courses.api";
import { LessonSidebar } from "@/components/course/LessonSidebar";
import { VideoPlayer } from "@/components/course/VideoPlayer";
import { TutorChat } from "@/components/ai-tutor/TutorChat";
import type { Course, Lesson, LessonProgress } from "@/types/course.types";

export default function LessonPlayerPage() {
  const router = useRouter();
  const params = useParams<{ courseSlug: string; lessonId: string }>();
  const { isAuthenticated, isLoading } = useAuthStore();
  const [course, setCourse] = useState<Course | null>(null);
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [progress, setProgress] = useState<LessonProgress[]>([]);
  const [showTutor, setShowTutor] = useState(false);
  const [pageLoading, setPageLoading] = useState(true);

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      router.push(`/login?next=/learn/${params.courseSlug}/${params.lessonId}`);
      return;
    }

    async function load() {
      try {
        const courseData = await getCourse(params.courseSlug);
        setCourse(courseData);

        const lessonData = await getLesson(courseData.id, params.lessonId);
        setLesson(lessonData);

        const progressData = await getCourseProgress(courseData.id);
        setProgress(progressData.lessons);
      } catch {
        router.push(`/courses/${params.courseSlug}`);
      } finally {
        setPageLoading(false);
      }
    }
    load();
  }, [isAuthenticated, isLoading, params.courseSlug, params.lessonId, router]);

  function handleLessonComplete() {
    setProgress((prev) => {
      const existing = prev.find((p) => p.lesson_id === params.lessonId);
      if (existing) {
        return prev.map((p) =>
          p.lesson_id === params.lessonId
            ? { ...p, is_completed: true, watch_percentage: 100 }
            : p
        );
      }
      return [
        ...prev,
        {
          id: "",
          lesson_id: params.lessonId,
          lesson_title: lesson?.title || "",
          is_completed: true,
          watch_percentage: 100,
          last_position_seconds: 0,
          completed_at: new Date().toISOString(),
        },
      ];
    });
  }

  if (pageLoading || !course || !lesson) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const publishedLessons = course.lessons.filter((l) => l.is_published);
  const currentIndex = publishedLessons.findIndex((l) => l.id === lesson.id);
  const nextLesson = publishedLessons[currentIndex + 1];

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <LessonSidebar
        courseSlug={params.courseSlug}
        lessons={publishedLessons}
        currentLessonId={lesson.id}
        progress={progress}
      />

      <div className="flex-1 flex flex-col overflow-auto">
        {/* Video or text content */}
        {lesson.lesson_type === "video" && lesson.video ? (
          lesson.video.transcoding_status === "complete" ? (
            <VideoPlayer
              hlsUrl={lesson.video.hls_url}
              courseId={course.id}
              lessonId={lesson.id}
              lastPositionSeconds={
                progress.find((p) => p.lesson_id === lesson.id)
                  ?.last_position_seconds ?? 0
              }
              onComplete={handleLessonComplete}
            />
          ) : (
            <div className="aspect-video bg-black flex items-center justify-center">
              <div className="text-center text-white">
                <p className="text-sm opacity-70">
                  {lesson.video.transcoding_status === "processing"
                    ? "Video is being processed. Check back in a few minutes."
                    : "Video is not yet available."}
                </p>
              </div>
            </div>
          )
        ) : (
          <div
            className="p-8 max-w-3xl mx-auto w-full prose prose-sm"
            dangerouslySetInnerHTML={{ __html: lesson.content }}
          />
        )}

        {/* Controls and tutor */}
        <div className="p-6 max-w-3xl mx-auto w-full">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-xl font-semibold">{lesson.title}</h1>
              <p className="text-sm text-muted-foreground">
                {course.title}
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setShowTutor(!showTutor)}
                className="text-sm border rounded-lg px-3 py-1.5 hover:bg-muted transition-colors"
              >
                {showTutor ? "Close tutor" : "Ask AI tutor"}
              </button>
              <a
                href={`/ai/learning?course=${course.id}&lesson=${lesson.id}`}
                className="text-sm border rounded-lg px-3 py-1.5 hover:bg-muted transition-colors"
              >
                AI study tools
              </a>
              {nextLesson && (
                <a
                  href={`/learn/${params.courseSlug}/${nextLesson.id}`}
                  className="text-sm bg-primary text-primary-foreground rounded-lg px-3 py-1.5 hover:bg-primary/90 transition-colors"
                >
                  Next lesson
                </a>
              )}
            </div>
          </div>

          {showTutor && <TutorChat key={lesson.id} courseId={course.id} lessonId={lesson.id} />}
        </div>
      </div>
    </div>
  );
}
