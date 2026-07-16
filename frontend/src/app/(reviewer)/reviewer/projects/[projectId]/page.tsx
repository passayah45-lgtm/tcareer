"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import { structuredProjectReview } from "@/lib/api/courses.api";

const projectAreas = ["brief", "dataset", "deliverables", "rubric", "passing_criteria", "submission_format", "example_solution", "required_resources", "certificate_requirement"];

export default function ReviewerProjectPage() {
  const search = useSearchParams();
  const courseId = search.get("course") || "";
  const [decision, setDecision] = useState("request_changes");
  const [sections, setSections] = useState<Record<string, string>>({});
  const [message, setMessage] = useState("");

  async function submit() {
    await structuredProjectReview(courseId, { decision, review_sections: sections });
    setMessage("Project review submitted.");
  }

  return (
    <>
      <Navbar />
      <main className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        <div>
          <p className="text-sm font-semibold text-primary">Final project review</p>
          <h1 className="text-2xl font-bold">Project decision</h1>
        </div>
        <select className="input" value={decision} onChange={(event) => setDecision(event.target.value)} aria-label="Project decision">
          {["approve", "approve_minor_edits", "request_changes", "reject", "escalate"].map((item) => <option key={item} value={item}>{item}</option>)}
        </select>
        <div className="grid gap-3">
          {projectAreas.map((area) => (
            <label key={area} className="grid gap-1 text-sm font-medium">
              {area.replaceAll("_", " ")}
              <textarea className="input min-h-20" value={sections[area] || ""} onChange={(event) => setSections({ ...sections, [area]: event.target.value })} />
            </label>
          ))}
        </div>
        <button type="button" className="btn-base btn-primary" onClick={() => void submit()} disabled={!courseId}>Submit project review</button>
        {message && <p className="text-sm text-emerald-700">{message}</p>}
      </main>
    </>
  );
}
