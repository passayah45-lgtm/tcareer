"use client";

import Link from "next/link";
import { PlayCircle, FileText, HelpCircle, CheckCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Lesson, LessonProgress } from "@/types/course.types";

interface LessonSidebarProps {
  courseSlug: string;
  lessons: Lesson[];
  currentLessonId: string;
  progress: LessonProgress[];
}

function getProgressForLesson(lessonId: string, progress: LessonProgress[]) {
  return progress.find((p) => p.lesson_id === lessonId);
}

function LessonIcon({ type, completed }: { type: string; completed: boolean }) {
  if (completed) return <CheckCircle className="w-4 h-4 text-primary-foreground" />;
  if (type === "video") return <PlayCircle className="w-4 h-4" />;
  if (type === "quiz") return <HelpCircle className="w-4 h-4" />;
  return <FileText className="w-4 h-4" />;
}

export function LessonSidebar({
  courseSlug,
  lessons,
  currentLessonId,
  progress,
}: LessonSidebarProps) {
  const completedCount = progress.filter((p) => p.is_completed).length;
  const total = lessons.filter((l) => l.is_published).length;
  const percentage = total > 0 ? Math.round((completedCount / total) * 100) : 0;

  return (
    <aside className="w-72 border-r bg-background flex flex-col h-full overflow-hidden">
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium">Course progress</span>
          <span className="text-sm text-muted-foreground">{percentage}%</span>
        </div>
        <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-primary rounded-full transition-all duration-500"
            style={{ width: `${percentage}%` }}
          />
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          {completedCount} of {total} lessons completed
        </p>
      </div>

      <div className="flex-1 overflow-y-auto">
        {lessons
          .filter((l) => l.is_published)
          .map((lesson) => {
            const lessonProgress = getProgressForLesson(lesson.id, progress);
            const isCompleted = lessonProgress?.is_completed ?? false;
            const isCurrent = lesson.id === currentLessonId;

            return (
              <Link
                key={lesson.id}
                href={`/learn/${courseSlug}/${lesson.id}`}
                className={cn(
                  "flex items-start gap-3 px-4 py-3 text-sm border-b hover:bg-muted/50 transition-colors",
                  isCurrent && "bg-primary/5 border-l-2 border-l-primary"
                )}
              >
                <div
                  className={cn(
                    "w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5",
                    isCompleted
                      ? "bg-primary text-primary-foreground"
                      : isCurrent
                      ? "bg-primary/20 text-primary"
                      : "bg-muted text-muted-foreground"
                  )}
                >
                  <LessonIcon type={lesson.lesson_type} completed={isCompleted} />
                </div>

                <div className="flex-1 min-w-0">
                  <p
                    className={cn(
                      "truncate text-sm",
                      isCurrent ? "font-medium text-foreground" : "text-muted-foreground"
                    )}
                  >
                    {lesson.title}
                  </p>
                  {lessonProgress && !isCompleted && lessonProgress.watch_percentage > 0 && (
                    <div className="w-full h-0.5 bg-muted rounded-full mt-1">
                      <div
                        className="h-full bg-primary/50 rounded-full"
                        style={{ width: `${lessonProgress.watch_percentage}%` }}
                      />
                    </div>
                  )}
                </div>

                {lesson.is_free_preview && !isCompleted && (
                  <span className="text-xs text-primary flex-shrink-0 mt-0.5">Free</span>
                )}
              </Link>
            );
          })}
      </div>
    </aside>
  );
}