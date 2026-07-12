"use client";

import { useCallback, useEffect, useState } from "react";
import { EmptyState, RecruiterShell, useRecruiterContext } from "@/components/recruiter/RecruiterShell";
import {
  addInterviewFeedback,
  addInterviewScorecard,
  getInterviews,
  getPipelineApplications,
  scheduleInterview,
  updateInterview,
} from "@/lib/api/recruiter.api";
import type { Interview, JobApplication } from "@/types/recruiter.types";

function InterviewsContent() {
  const { organization } = useRecruiterContext();
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [applications, setApplications] = useState<JobApplication[]>([]);
  const [selectedApplication, setSelectedApplication] = useState("");
  const [scheduledStart, setScheduledStart] = useState("");
  const [meetingLink, setMeetingLink] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!organization) return;
    setLoading(true);
    try {
      const [interviewData, pipeline] = await Promise.all([
        getInterviews(organization.id),
        getPipelineApplications(organization.id, { page_size: 100 }),
      ]);
      setInterviews(interviewData);
      setApplications(pipeline.data);
      setError("");
    } catch {
      setError("Unable to load interviews.");
    } finally {
      setLoading(false);
    }
  }, [organization]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function submitSchedule(event: React.FormEvent) {
    event.preventDefault();
    if (!organization || !selectedApplication || !scheduledStart) return;
    await scheduleInterview(organization.id, {
      application_id: selectedApplication,
      interview_type: "online",
      scheduled_start: new Date(scheduledStart).toISOString(),
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      meeting_link: meetingLink,
    });
    setSelectedApplication("");
    setScheduledStart("");
    setMeetingLink("");
    await load();
  }

  async function setStatus(interview: Interview, status: Interview["status"]) {
    if (!organization) return;
    await updateInterview(organization.id, interview.id, { status });
    await load();
  }

  async function feedback(interview: Interview) {
    if (!organization) return;
    const recommendation = window.prompt("Recommendation", "advance") || "";
    const text = window.prompt("Feedback", "") || "";
    await addInterviewFeedback(organization.id, interview.id, { rating: 4, recommendation, feedback: text });
    await load();
  }

  async function scorecard(interview: Interview) {
    if (!organization) return;
    const recommendation = window.prompt("Scorecard recommendation", "advance") || "";
    await addInterviewScorecard(organization.id, interview.id, {
      criteria: { technical: 4, communication: 4 },
      total_score: 8,
      recommendation,
    });
    await load();
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <section className="lg:col-span-2 space-y-4">
        {loading ? <div className="h-52 bg-muted rounded-xl animate-pulse" /> : null}
        {error ? <EmptyState title="Interviews unavailable" body={error} /> : null}
        {!loading && !error && interviews.length === 0 ? <EmptyState title="No interviews" body="Schedule an interview from an application or use the form on this page." /> : null}
        {interviews.map((interview) => {
          const application = applications.find((item) => item.id === interview.application);
          return (
            <div key={interview.id} className="border border-border rounded-xl bg-card p-5">
              <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div>
                  <h2 className="font-semibold">{application?.candidate_name || "Candidate interview"}</h2>
                  <p className="text-sm text-muted-foreground">{application?.job_title || interview.application}</p>
                  <p className="text-sm mt-2">{new Date(interview.scheduled_start).toLocaleString()} - {interview.timezone}</p>
                  {interview.meeting_link && <a href={interview.meeting_link} target="_blank" rel="noreferrer" className="text-sm text-primary hover:underline">Meeting link</a>}
                </div>
                <select className="input max-w-48" value={interview.status} onChange={(event) => setStatus(interview, event.target.value as Interview["status"])}>
                  <option value="scheduled">Scheduled</option>
                  <option value="rescheduled">Rescheduled</option>
                  <option value="completed">Completed</option>
                  <option value="cancelled">Cancelled</option>
                  <option value="no_show">No show</option>
                </select>
              </div>
              <div className="flex gap-2 mt-4">
                <button onClick={() => feedback(interview)} className="btn-sm btn-secondary">Add feedback</button>
                <button onClick={() => scorecard(interview)} className="btn-sm btn-secondary">Scorecard</button>
              </div>
            </div>
          );
        })}
      </section>

      <aside className="border border-border rounded-xl bg-card p-5 h-fit">
        <h2 className="font-semibold mb-4">Schedule interview</h2>
        <form onSubmit={submitSchedule} className="space-y-3">
          <select className="input" value={selectedApplication} onChange={(event) => setSelectedApplication(event.target.value)} required>
            <option value="">Choose application</option>
            {applications.map((application) => (
              <option key={application.id} value={application.id}>
                {application.candidate_name} - {application.job_title}
              </option>
            ))}
          </select>
          <input className="input" type="datetime-local" value={scheduledStart} onChange={(event) => setScheduledStart(event.target.value)} required />
          <input className="input" value={meetingLink} onChange={(event) => setMeetingLink(event.target.value)} placeholder="Meeting link" />
          <button className="btn-base btn-primary w-full" type="submit">Schedule</button>
        </form>
      </aside>
    </div>
  );
}

export default function RecruiterInterviewsPage() {
  return (
    <RecruiterShell title="Interviews" description="Schedule, update, complete, and score interviews without calendar integration.">
      <InterviewsContent />
    </RecruiterShell>
  );
}
