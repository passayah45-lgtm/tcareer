import Link from "next/link";
import Image from "next/image";
import { formatPrice, truncate } from "@/lib/utils";
import type { Course } from "@/types/course.types";

interface CourseCardProps {
  course: Course;
}

const levelColors = {
  beginner: "bg-green-100 text-green-800",
  intermediate: "bg-yellow-100 text-yellow-800",
  advanced: "bg-red-100 text-red-800",
};

export function CourseCard({ course }: CourseCardProps) {
  return (
    <Link href={`/courses/${course.slug}`} className="group block">
      <div className="border rounded-xl overflow-hidden hover:shadow-md transition-shadow bg-card">
        <div className="aspect-video bg-muted relative overflow-hidden">
          {course.thumbnail_url ? (
            <Image
              src={course.thumbnail_url}
              alt={course.title}
              fill
              sizes="(min-width: 1280px) 25vw, (min-width: 1024px) 33vw, (min-width: 640px) 50vw, 100vw"
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-primary/10">
              <span className="text-4xl text-primary/30">T</span>
            </div>
          )}
        </div>
        <div className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <span
              className={`text-xs px-2 py-0.5 rounded-full font-medium capitalize ${
                levelColors[course.level]
              }`}
            >
              {course.level}
            </span>
            {course.is_enrolled && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary font-medium">
                Enrolled
              </span>
            )}
          </div>
          <h3 className="font-medium text-sm leading-tight mb-1 group-hover:text-primary transition-colors">
            {truncate(course.title, 60)}
          </h3>
          <p className="text-xs text-muted-foreground mb-3">
            {truncate(course.short_description, 80)}
          </p>
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">
              {course.instructor_name || course.instructor?.full_name}
            </span>
            <span className="text-sm font-semibold">
              {formatPrice(course.price)}
            </span>
          </div>
          <div className="flex items-center gap-1 mt-2">
            <span className="text-xs text-muted-foreground">
              {course.total_lessons} lessons
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
}
