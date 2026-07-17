import { Navbar } from "@/components/layout/Navbar";
import { CourseCard } from "@/components/course/CourseCard";
import type { Course } from "@/types/course.types";
import Link from "next/link";

export const dynamic = "force-dynamic";

async function fetchCourses(search?: string, level?: string): Promise<Course[]> {
  const params = new URLSearchParams();
  if (search) params.append("search", search);
  if (level) params.append("level", level);

  try {
    const res = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/courses/?${params.toString()}`,
      { cache: "no-store" }
    );
    if (!res.ok) return [];
    const data = await res.json();
    return (data.data as Course[]) || [];
  } catch {
    return [];
  }
}

interface PageProps {
  searchParams: Promise<{ search?: string; level?: string }>;
}

export default async function CourseCatalogPage({ searchParams }: PageProps) {
  const filters = await searchParams;
  const activeLevel = filters.level?.toLowerCase();
  const courses = await fetchCourses(filters.search, activeLevel);

  return (
    <>
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Courses</h1>
          <p className="text-muted-foreground">
            Build skills with courses verified by industry experts.
          </p>
        </div>

        {/* Filters */}
        <div className="flex gap-3 mb-8 flex-wrap">
          {["All", "Beginner", "Intermediate", "Advanced"].map((level) => (
            <Link
              key={level}
              href={
                level === "All"
                  ? "/courses"
                  : `/courses?level=${level.toLowerCase()}`
              }
              className={`px-4 py-1.5 rounded-full text-sm border transition-colors ${
                (level === "All" && !activeLevel) ||
                activeLevel === level.toLowerCase()
                  ? "bg-primary text-primary-foreground border-primary"
                  : "hover:bg-muted"
              }`}
            >
              {level}
            </Link>
          ))}
        </div>

        {courses.length === 0 ? (
          <div className="text-center py-16 text-muted-foreground">
            <p>No courses found. Check back soon.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {courses.map((course) => (
              <CourseCard key={course.id} course={course} />
            ))}
          </div>
        )}
      </main>
    </>
  );
}
