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
  const [message, setMessage] = useState("");

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
      router.push(`/login?next=/courses/${courseSlug}`);
      return;
    }
    setLoading(true);
    setMessage("");
    try {
      await enroll(courseId);
      setIsEnrolled(true);
      if (firstLessonId) {
        router.push(`/learn/${courseSlug}/${firstLessonId}`);
      } else {
        setMessage("You are enrolled. Lessons are being prepared for this course.");
      }
    } catch (err: unknown) {
      const e = err as { response?: { data?: { errors?: { detail?: string } } } };
      const detail = e?.response?.data?.errors?.detail || "";
      if (detail.toLowerCase().includes("already enrolled")) {
        setIsEnrolled(true);
        if (firstLessonId) {
          router.push(`/learn/${courseSlug}/${firstLessonId}`);
        } else {
          setMessage("You are enrolled. Lessons are being prepared for this course.");
        }
      } else {
        setMessage("Could not enroll right now. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  if (isEnrolled) {
    if (!firstLessonId) {
      return (
        <div className="space-y-2">
          <div className="w-full text-center bg-green-50 border border-green-200 text-green-800 px-4 py-2.5 rounded-lg text-sm font-medium">
            Enrolled
          </div>
          <p className="text-xs text-muted-foreground text-center">
            Lessons are being prepared for this course.
          </p>
        </div>
      );
    }

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
    <div className="space-y-2">
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
      {message && (
        <p className="text-xs text-muted-foreground text-center">{message}</p>
      )}
    </div>
  );
}
