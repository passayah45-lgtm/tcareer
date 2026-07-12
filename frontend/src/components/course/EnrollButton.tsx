"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth.store";
import { enroll, getMyEnrollments } from "@/lib/api/courses.api";

interface EnrollmentSummary {
  course?: {
    id?: string;
    slug?: string;
  };
}

interface EnrollButtonProps {
  courseId: string;
  courseSlug: string;
  firstLessonId: string;
  price: string;
}

export function EnrollButton({
  courseId,
  courseSlug,
  firstLessonId,
  price,
}: EnrollButtonProps) {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [isEnrolled, setIsEnrolled] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) return;
    getMyEnrollments()
      .then((data) => {
        const enrolled = (data.results as EnrollmentSummary[]).some(
          (e) =>
            e.course?.id === courseId || e.course?.slug === courseSlug
        );
        setIsEnrolled(enrolled);
      })
      .catch(() => {});
  }, [isAuthenticated, courseId, courseSlug]);

  async function handleEnroll() {
    if (!isAuthenticated) {
      router.push(`/register?next=/courses/${courseSlug}`);
      return;
    }
    setLoading(true);
    try {
      await enroll(courseId);
      setIsEnrolled(true);
      router.push(`/learn/${courseSlug}/${firstLessonId}`);
    } catch {
      router.push(`/learn/${courseSlug}/${firstLessonId}`);
    } finally {
      setLoading(false);
    }
  }

  if (isEnrolled) {
    return (
      <button
        onClick={() => router.push(`/learn/${courseSlug}/${firstLessonId}`)}
        className="w-full text-center bg-primary text-primary-foreground px-4 py-2.5 rounded-lg font-medium hover:bg-primary/90 transition-colors"
      >
        Continue learning
      </button>
    );
  }

  return (
    <button
      onClick={handleEnroll}
      disabled={loading}
      className="w-full bg-primary text-primary-foreground px-4 py-2.5 rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
    >
      {loading
        ? "Enrolling..."
        : price === "0.00"
        ? "Enroll for free"
        : "Enroll now"}
    </button>
  );
}
