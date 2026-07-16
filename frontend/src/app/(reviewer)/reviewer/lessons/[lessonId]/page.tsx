"use client";

import { useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import { structuredLessonReview } from "@/lib/api/courses.api";

const areas = ["educational_accuracy", "objective_alignment", "clarity", "examples", "exercises", "resource_quality", "grammar", "accessibility", "copyright", "assessment_alignment"];

export default function ReviewerLessonPage() {
  const params = useParams<{ lessonId: string }>();
  const search = useSearchParams();
  const courseId = search.get("course") || "";
  const [decision, setDecision] = useState("request_changes");
  const [comments, setComments] = useState<Record<string, string>>({});
  const [message, setMessage] = useState("");

  async function submit() {
    await structuredLessonReview(courseId, params.lessonId, { decision, section_comments: comments });
    setMessage("Lesson review submitted.");
  }

  return (
    <>
      <Navbar />
      <main className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        <div>
          <p className="text-sm font-semibold text-primary">Lesson review</p>
          <h1 className="text-2xl font-bold">Structured lesson review</h1>
        </div>
        <select className="input" value={decision} onChange={(event) => setDecision(event.target.value)} aria-label="Review decision">
          {["approve", "approve_minor_edits", "request_changes", "reject", "escalate"].map((item) => <option key={item} value={item}>{item}</option>)}
        </select>
        <div className="grid gap-3">
          {areas.map((area) => (
            <label key={area} className="grid gap-1 text-sm font-medium">
              {area.replaceAll("_", " ")}
              <textarea className="input min-h-20" value={comments[area] || ""} onChange={(event) => setComments({ ...comments, [area]: event.target.value })} />
            </label>
          ))}
        </div>
        <button type="button" className="btn-base btn-primary" onClick={() => void submit()} disabled={!courseId}>Submit review</button>
        {message && <p className="text-sm text-emerald-700">{message}</p>}
      </main>
    </>
  );
}
