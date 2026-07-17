import { formatPrice } from "@/lib/utils";
import type { CareerTrack, TrackCourse } from "@/types/track.types";

function parsePrice(value?: string | number | null): number {
  if (value === null || value === undefined || value === "") return 0;
  const parsed = typeof value === "number" ? value : Number.parseFloat(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function trackCourses(track: CareerTrack): TrackCourse[] {
  return (track.courses_by_stage ?? []).flatMap((stage) => stage.courses);
}

export function formatTrackFee(track: CareerTrack): string {
  if (track.track_fee !== undefined) {
    return formatPrice(track.track_fee);
  }

  const requiredCourses = trackCourses(track).filter((course) => course.is_required);
  if (requiredCourses.length === 0) {
    return "View pricing";
  }

  const total = requiredCourses.reduce(
    (sum, course) => sum + parsePrice(course.course_price),
    0
  );

  return total === 0 ? "Free" : formatPrice(total);
}
