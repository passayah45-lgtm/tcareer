import { notFound } from "next/navigation";
import { PlayCircle, FileText, HelpCircle } from "lucide-react";
import { Navbar } from "@/components/layout/Navbar";
import { formatPrice } from "@/lib/utils";
import { EnrollButton } from "@/components/course/EnrollButton";
import type { Course } from "@/types/course.types";

export const dynamic = "force-dynamic";

async function fetchCourse(slug: string): Promise<Course | null> {
  try {
    const res = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/courses/${slug}/`,
      { cache: "no-store" }
    );
    if (!res.ok) return null;
    const data = await res.json();
    return (data.data || data) as Course;
  } catch {
    return null;
  }
}

interface PageProps {
  params: { slug: string };
}

function LessonTypeIcon({ type }: { type: string }) {
  if (type === "video") return <PlayCircle className="w-4 h-4 text-primary" />;
  if (type === "quiz") return <HelpCircle className="w-4 h-4 text-orange-500" />;
  return <FileText className="w-4 h-4 text-muted-foreground" />;
}

export default async function CourseDetailPage({ params }: PageProps) {
  const course = await fetchCourse(params.slug);
  if (!course) notFound();

  const publishedLessons = course.lessons.filter((l) => l.is_published);
  const freePreviewLessons = publishedLessons.filter((l) => l.is_free_preview);

  return (
    <>
      <Navbar />
      <main className="max-w-6xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

          <div className="lg:col-span-2">
            <div className="mb-4">
              <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded-full capitalize">
                {course.level}
              </span>
            </div>
            <h1 className="text-3xl font-bold mb-3">{course.title}</h1>
            <p className="text-muted-foreground mb-4">{course.short_description}</p>

            <p className="text-sm text-muted-foreground mb-6">
              Taught by{" "}
              <span className="text-foreground font-medium">
                {course.instructor?.full_name}
              </span>
            </p>

            {course.what_you_learn.length > 0 && (
              <div className="border rounded-xl p-6 mb-6">
                <h2 className="font-semibold mb-3">What you will learn</h2>
                <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {course.what_you_learn.map((item, i) => (
                    <li key={i} className="text-sm flex gap-2">
                      <span className="text-primary mt-0.5">&#10003;</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div>
              <h2 className="font-semibold mb-3">
                Course content ({publishedLessons.length} lessons)
              </h2>
              <div className="border rounded-xl overflow-hidden divide-y">
                {publishedLessons.map((lesson, index) => (
                  <div
                    key={lesson.id}
                    className="flex items-center gap-3 px-4 py-3 hover:bg-muted/30 transition-colors"
                  >
                    <div className="w-6 text-center flex-shrink-0">
                      <LessonTypeIcon type={lesson.lesson_type} />
                    </div>
                    <span className="text-sm text-muted-foreground w-6 flex-shrink-0">
                      {index + 1}.
                    </span>
                    <span className="text-sm flex-1">{lesson.title}</span>
                    {lesson.is_free_preview && (
                      <span className="text-xs text-primary font-medium bg-primary/10 px-2 py-0.5 rounded-full">
                        Free preview
                      </span>
                    )}
                  </div>
                ))}
              </div>

              <div className="flex items-center gap-4 mt-3 px-1">
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <PlayCircle className="w-3.5 h-3.5 text-primary" />
                  Video
                </div>
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <FileText className="w-3.5 h-3.5 text-muted-foreground" />
                  Text
                </div>
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <HelpCircle className="w-3.5 h-3.5 text-orange-500" />
                  Quiz
                </div>
              </div>
            </div>
          </div>

          <div className="lg:col-span-1">
            <div className="border rounded-xl overflow-hidden sticky top-20">
              {course.thumbnail_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={course.thumbnail_url}
                  alt={course.title}
                  className="w-full aspect-video object-cover"
                />
              ) : (
                <div className="w-full aspect-video bg-muted flex items-center justify-center">
                  <span className="text-5xl text-muted-foreground/30">T</span>
                </div>
              )}
              <div className="p-5">
                <div className="text-2xl font-bold mb-4">
                  {formatPrice(course.price)}
                </div>

                <EnrollButton
                  courseId={course.id}
                  courseSlug={course.slug}
                  firstLessonId={publishedLessons[0]?.id || ""}
                  price={course.price}
                />

                <ul className="mt-4 space-y-2">
                  <li className="flex items-center gap-2 text-sm text-muted-foreground">
                    <PlayCircle className="w-4 h-4 text-primary" />
                    {publishedLessons.length} lessons
                  </li>
                  {freePreviewLessons.length > 0 && (
                    <li className="flex items-center gap-2 text-sm text-muted-foreground">
                      <span className="text-primary">&#10003;</span>
                      {freePreviewLessons.length} free preview lessons
                    </li>
                  )}
                  <li className="flex items-center gap-2 text-sm text-muted-foreground capitalize">
                    <span>&#127891;</span>
                    {course.level} level
                  </li>
                  <li className="flex items-center gap-2 text-sm text-muted-foreground">
                    <span>&#127941;</span>
                    Certificate on completion
                  </li>
                </ul>
              </div>
            </div>
          </div>

        </div>
      </main>
    </>
  );
}
