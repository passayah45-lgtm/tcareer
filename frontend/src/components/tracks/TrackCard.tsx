"use client";

import Link from "next/link";
import type { CareerTrack } from "@/types/track.types";

interface TrackCardProps {
  track: CareerTrack;
}

const difficultyLabel: Record<string, string> = {
  beginner: "Beginner friendly",
  intermediate: "Some experience needed",
  advanced: "Advanced",
};

const difficultyColor: Record<string, string> = {
  beginner: "bg-green-100 text-green-800",
  intermediate: "bg-yellow-100 text-yellow-800",
  advanced: "bg-red-100 text-red-800",
};

function formatSalary(min: number, max: number): string {
  if (!min && !max) return "";
  const fmt = (n: number) =>
    n >= 1000 ? `$${Math.round(n / 1000)}k` : `$${n}`;
  return `${fmt(min)} - ${fmt(max)}/yr`;
}

export function TrackCard({ track }: TrackCardProps) {
  return (
    <Link href={`/tracks/${track.slug}`} className="group block">
      <div className="border rounded-xl p-5 hover:shadow-md transition-all bg-card h-full flex flex-col">
        <div className="flex items-start justify-between mb-3">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center text-white text-lg font-bold flex-shrink-0"
            style={{ backgroundColor: track.color }}
          >
            {track.title.charAt(0)}
          </div>
          <span
            className={`text-xs px-2 py-0.5 rounded-full font-medium ${
              difficultyColor[track.difficulty]
            }`}
          >
            {difficultyLabel[track.difficulty]}
          </span>
        </div>

        <h3 className="font-semibold text-sm mb-1 group-hover:text-primary transition-colors">
          {track.title}
        </h3>
        <p className="text-xs text-muted-foreground mb-3 flex-1 line-clamp-2">
          {track.short_description}
        </p>

        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>{track.required_courses_count} courses</span>
            <span>{track.duration_display}</span>
          </div>
          {track.avg_salary_min > 0 && (
            <div className="text-xs font-medium text-primary">
              {formatSalary(track.avg_salary_min, track.avg_salary_max)}
            </div>
          )}
        </div>

        {track.is_enrolled && (
          <div className="mt-3 pt-3 border-t">
            <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full font-medium">
              Enrolled
            </span>
          </div>
        )}
      </div>
    </Link>
  );
}
