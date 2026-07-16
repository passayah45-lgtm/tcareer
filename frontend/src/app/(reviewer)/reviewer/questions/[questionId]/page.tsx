"use client";

import { useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import { structuredQuestionReview } from "@/lib/api/assessments.api";

export default function ReviewerQuestionPage() {
  const params = useParams<{ questionId: string }>();
  const search = useSearchParams();
  const courseId = search.get("course") || "";
  const [decision, setDecision] = useState("request_changes");
  const [notes, setNotes] = useState("");
  const [certificateEligible, setCertificateEligible] = useState(false);
  const [message, setMessage] = useState("");

  async function submit() {
    await structuredQuestionReview(courseId, params.questionId, {
      decision,
      notes,
      certificate_eligible: certificateEligible,
      section_comments: { validity: notes },
    });
    setMessage("Question review submitted.");
  }

  return (
    <>
      <Navbar />
      <main className="max-w-3xl mx-auto px-4 py-8 space-y-5">
        <div>
          <p className="text-sm font-semibold text-primary">Assessment review</p>
          <h1 className="text-2xl font-bold">Question review</h1>
          <p className="text-sm text-muted-foreground mt-1">Approve, request correction, reject, or mark certificate eligibility after approval.</p>
        </div>
        <select className="input" value={decision} onChange={(event) => setDecision(event.target.value)} aria-label="Question decision">
          {["approve", "approve_minor_edits", "request_changes", "reject", "escalate"].map((item) => <option key={item} value={item}>{item}</option>)}
        </select>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={certificateEligible} onChange={(event) => setCertificateEligible(event.target.checked)} />
          Certificate eligible after approval
        </label>
        <textarea className="input min-h-32" value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Question validity, explanation, difficulty, mapping, and certificate notes" />
        <button type="button" className="btn-base btn-primary" onClick={() => void submit()} disabled={!courseId}>Submit question review</button>
        {message && <p className="text-sm text-emerald-700">{message}</p>}
      </main>
    </>
  );
}
