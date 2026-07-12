"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth.store";
import { enrollInTrack } from "@/lib/api/tracks.api";
import type { CareerTrack } from "@/types/track.types";

interface TrackEnrollSectionProps {
  track: CareerTrack;
}

export function TrackEnrollSection({ track }: TrackEnrollSectionProps) {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [enrolled, setEnrolled] = useState(track.is_enrolled);
  const [error, setError] = useState("");

  async function handleEnroll() {
    if (!isAuthenticated) {
      router.push(`/register?next=/tracks/${track.slug}`);
      return;
    }
    setLoading(true);
    setError("");
    try {
      await enrollInTrack(track.slug);
      setEnrolled(true);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { errors?: { detail?: string } } } };
      const msg = e?.response?.data?.errors?.detail || "";
      if (msg.includes("already enrolled")) {
        setEnrolled(true);
      } else {
        setError("Could not enroll. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="border rounded-xl overflow-hidden sticky top-20">
      <div
        className="p-5 text-white"
        style={{ backgroundColor: track.color }}
      >
        <p className="text-sm opacity-80 mb-1">Career Track</p>
        <h2 className="text-lg font-bold">{track.title}</h2>
      </div>

      <div className="p-5 space-y-4">
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Courses</span>
            <span className="font-medium">{track.required_courses_count}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Duration</span>
            <span className="font-medium">{track.duration_display}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Level</span>
            <span className="font-medium capitalize">{track.difficulty}</span>
          </div>
          {track.avg_salary_min > 0 && (
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Avg salary</span>
              <span className="font-medium text-primary">
                ${Math.round(track.avg_salary_min / 1000)}k - ${Math.round(track.avg_salary_max / 1000)}k
              </span>
            </div>
          )}
        </div>

        {error && (
          <p className="text-xs text-destructive">{error}</p>
        )}

        {enrolled ? (
          <div className="space-y-2">
            <div className="w-full text-center bg-green-50 border border-green-200 text-green-800 px-4 py-2.5 rounded-lg text-sm font-medium">
              Enrolled in this track
            </div>
            <button
              onClick={() => router.push("/dashboard")}
              className="w-full border px-4 py-2 rounded-lg text-sm hover:bg-muted transition-colors"
            >
              Go to dashboard
            </button>
          </div>
        ) : (
          <button
            onClick={handleEnroll}
            disabled={loading}
            className="w-full bg-primary text-primary-foreground px-4 py-2.5 rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            {loading ? "Enrolling..." : "Start this track"}
          </button>
        )}

        <p className="text-xs text-muted-foreground text-center">
          Free to enroll. Paid courses require a subscription.
        </p>
      </div>
    </div>
  );
}
