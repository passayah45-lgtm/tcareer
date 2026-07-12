"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { EmptyState, RecruiterShell, useRecruiterContext } from "@/components/recruiter/RecruiterShell";
import {
  addApplicationNote,
  assignApplication,
  bulkArchiveApplications,
  changeApplicationStage,
  getApplicationDetail,
  getOrganizationMembers,
  scheduleInterview,
} from "@/lib/api/recruiter.api";
import type { ApplicationDetail, ApplicationStage, OrganizationMember } from "@/types/recruiter.types";

const STAGES: Array<{ id: ApplicationStage; label: string }> = [
  { id: "applied", label: "Applied" },
  { id: "under_review", label: "Under Review" },
  { id: "shortlisted", label: "Shortlisted" },
  { id: "assessment", label: "Assessment" },
  { id: "interview_scheduled", label: "Interview Scheduled" },
  { id: "interview_completed", label: "Interview Completed" },
  { id: "offer_sent", label: "Offer Sent" },
  { id: "offer_accepted", label: "Offer Accepted" },
  { id: "offer_declined", label: "Offer Declined" },
  { id: "rejected", label: "Rejected" },
  { id: "withdrawn", label: "Withdrawn" },
];

function formatDate(value?: string | null) {
  return value ? new Date(value).toLocaleString() : "Not set";
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="border border-border rounded-xl bg-card p-5">
      <h2 className="font-semibold mb-4">{title}</h2>
      {children}
    </section>
  );
}

function ApplicationDetailContent() {
  const params = useParams<{ applicationId: string }>();
  const { organization } = useRecruiterContext();
  const [detail, setDetail] = useState<ApplicationDetail | null>(null);
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [noteBody, setNoteBody] = useState("");
  const [interviewStart, setInterviewStart] = useState("");
  const [meetingLink, setMeetingLink] = useState("");
  const [actionLoading, setActionLoading] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!organization) return;
    setLoading(true);
    try {
      const [detailData, memberData] = await Promise.all([
        getApplicationDetail(organization.id, params.applicationId),
        getOrganizationMembers(organization.id),
      ]);
      setDetail(detailData);
      setMembers(memberData.filter((item) => item.status === "active"));
      setError("");
    } catch {
      setError("Unable to load application detail.");
    } finally {
      setLoading(false);
    }
  }, [organization, params.applicationId]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function runAction(name: string, action: () => Promise<void>) {
    setActionLoading(name);
    try {
      await action();
      await load();
      setError("");
    } catch {
      setError("Action failed. Please refresh and try again.");
    } finally {
      setActionLoading("");
    }
  }

  async function setStage(stage: ApplicationStage) {
    if (!organization || !detail) return;
    await runAction("stage", async () => {
      await changeApplicationStage(organization.id, detail.application.id, stage);
    });
  }

  async function assign(payload: { assigned_recruiter?: string | null; hiring_manager?: string | null }) {
    if (!organization || !detail) return;
    await runAction("assign", async () => {
      await assignApplication(organization.id, detail.application.id, payload);
    });
  }

  async function addNote(event: FormEvent) {
    event.preventDefault();
    if (!organization || !detail || !noteBody.trim()) return;
    await runAction("note", async () => {
      await addApplicationNote(organization.id, detail.application.id, { body: noteBody.trim(), is_internal: true });
      setNoteBody("");
    });
  }

  async function schedule(event: FormEvent) {
    event.preventDefault();
    if (!organization || !detail || !interviewStart) return;
    await runAction("interview", async () => {
      await scheduleInterview(organization.id, {
        application_id: detail.application.id,
        interview_type: "online",
        scheduled_start: new Date(interviewStart).toISOString(),
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        meeting_link: meetingLink,
      });
      setInterviewStart("");
      setMeetingLink("");
    });
  }

  async function archive() {
    if (!organization || !detail) return;
    await runAction("archive", async () => {
      await bulkArchiveApplications(organization.id, [detail.application.id]);
    });
  }

  if (loading) return <div className="h-72 bg-muted rounded-xl animate-pulse" />;
  if (!detail) return <EmptyState title="Application not found" body={error || "The application may be archived or outside the selected organization."} />;

  const { application, candidate, job } = detail;

  return (
    <div className="space-y-5">
      {error && <EmptyState title="Application action failed" body={error} />}

      <section className="border border-border rounded-xl bg-card p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{job.title} at {job.company_name}</p>
            <h2 className="text-2xl font-bold mt-1">{candidate.full_name || application.candidate_name}</h2>
            <p className="text-sm text-muted-foreground">{candidate.email || application.candidate_email}</p>
            {candidate.profile_headline && <p className="text-sm mt-3">{candidate.profile_headline}</p>}
            {candidate.profile_location && <p className="text-sm text-muted-foreground">{candidate.profile_location}</p>}
          </div>
          <div className="flex flex-wrap gap-2">
            <span className="badge-primary">{application.stage_display}</span>
            {candidate.is_verified && <span className="badge-default">Verified</span>}
            {application.is_archived && <span className="badge-default">Archived</span>}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3 mt-6">
          <select
            className="input"
            value={application.stage}
            disabled={actionLoading === "stage"}
            onChange={(event) => setStage(event.target.value as ApplicationStage)}
          >
            {STAGES.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}
          </select>
          <select
            className="input"
            value={application.assigned_recruiter || ""}
            disabled={actionLoading === "assign"}
            onChange={(event) => assign({ assigned_recruiter: event.target.value || null })}
          >
            <option value="">Unassigned recruiter</option>
            {members.map((member) => <option key={member.id} value={member.user}>{member.user_full_name} ({member.role})</option>)}
          </select>
          <select
            className="input"
            value={application.hiring_manager || ""}
            disabled={actionLoading === "assign"}
            onChange={(event) => assign({ hiring_manager: event.target.value || null })}
          >
            <option value="">No hiring manager</option>
            {members.map((member) => <option key={member.id} value={member.user}>{member.user_full_name} ({member.role})</option>)}
          </select>
          <div className="flex gap-2">
            <button onClick={() => setStage("rejected")} disabled={actionLoading !== ""} className="btn-base btn-secondary flex-1">Reject</button>
            <button onClick={archive} disabled={actionLoading !== ""} className="btn-base btn-secondary flex-1">Archive</button>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 space-y-5">
          <Section title="Timeline and stage history">
            {detail.timeline.length === 0 ? <p className="text-sm text-muted-foreground">No timeline yet.</p> : (
              <div className="space-y-3">
                {detail.timeline.map((item) => (
                  <div key={item.id} className="border-l-2 border-primary/30 pl-3">
                    <p className="text-sm font-medium capitalize">{item.event_type.replaceAll("_", " ")}</p>
                    <p className="text-xs text-muted-foreground">{item.message || `${item.from_stage || "start"} -> ${item.to_stage || "current"}`}</p>
                    <p className="text-xs text-muted-foreground">{formatDate(item.created_at)}</p>
                  </div>
                ))}
              </div>
            )}
          </Section>

          <Section title="Recruiter notes">
            <form onSubmit={addNote} className="flex flex-col gap-2 sm:flex-row mb-4">
              <input className="input" value={noteBody} onChange={(event) => setNoteBody(event.target.value)} placeholder="Add an internal note..." />
              <button className="btn-base btn-primary" disabled={actionLoading === "note"} type="submit">Add</button>
            </form>
            {detail.notes.length === 0 ? <p className="text-sm text-muted-foreground">No notes yet.</p> : (
              <div className="space-y-3">
                {detail.notes.map((note) => (
                  <div key={note.id} className="border border-border rounded-lg p-3">
                    <p className="text-sm whitespace-pre-wrap">{note.body}</p>
                    <p className="text-xs text-muted-foreground mt-1">{note.author_name} - {formatDate(note.created_at)}</p>
                  </div>
                ))}
              </div>
            )}
          </Section>

          <Section title="Activity and audit history">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-3">
                <p className="text-sm font-medium">Application activity</p>
                {detail.activity.length === 0 ? <p className="text-sm text-muted-foreground">No activity yet.</p> : detail.activity.map((item) => (
                  <div key={item.id} className="border border-border rounded-lg p-3">
                    <p className="text-sm capitalize">{item.activity_type.replaceAll("_", " ")}</p>
                    <p className="text-xs text-muted-foreground">{item.actor_name || "System"} - {formatDate(item.created_at)}</p>
                  </div>
                ))}
              </div>
              <div className="space-y-3">
                <p className="text-sm font-medium">Audit-style history</p>
                {detail.audit_history.length === 0 ? <p className="text-sm text-muted-foreground">No privileged audit events yet.</p> : detail.audit_history.map((item) => (
                  <div key={item.id} className="border border-border rounded-lg p-3">
                    <p className="text-sm capitalize">{item.action.replaceAll("_", " ")}</p>
                    <p className="text-xs text-muted-foreground">{item.target_type} - {formatDate(item.created_at)}</p>
                  </div>
                ))}
              </div>
            </div>
          </Section>
        </div>

        <aside className="space-y-5">
          <Section title="Candidate and job">
            <div className="space-y-3 text-sm">
              <div>
                <p className="text-muted-foreground">Candidate</p>
                <p className="font-medium">{candidate.full_name || application.candidate_name}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Job</p>
                <p className="font-medium">{job.title}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Applied</p>
                <p className="font-medium">{formatDate(application.created_at)}</p>
              </div>
              {application.cover_letter && (
                <div>
                  <p className="text-muted-foreground">Cover letter</p>
                  <p className="whitespace-pre-wrap">{application.cover_letter}</p>
                </div>
              )}
            </div>
          </Section>

          <Section title="Attachments">
            {detail.attachments.length === 0 ? <p className="text-sm text-muted-foreground">No attachments available.</p> : (
              <div className="space-y-2">
                {detail.attachments.map((attachment) => (
                  <a key={attachment.id} className="block border border-border rounded-lg p-3 text-sm hover:bg-muted" href={attachment.file_url} target="_blank" rel="noreferrer">
                    {attachment.file_name}
                    {attachment.is_private && <span className="ml-2 text-xs text-muted-foreground">Private</span>}
                  </a>
                ))}
              </div>
            )}
          </Section>

          <Section title="Application answers">
            {detail.answers.length === 0 ? <p className="text-sm text-muted-foreground">No custom answers submitted.</p> : (
              <div className="space-y-3">
                {detail.answers.map((answer) => (
                  <div key={answer.id} className="border border-border rounded-lg p-3">
                    <p className="text-sm font-medium">{answer.question_text}</p>
                    <p className="text-sm text-muted-foreground mt-1">{String(answer.answer.value)}</p>
                  </div>
                ))}
              </div>
            )}
          </Section>

          <Section title="Schedule interview">
            <form onSubmit={schedule} className="space-y-3">
              <input className="input" type="datetime-local" value={interviewStart} onChange={(event) => setInterviewStart(event.target.value)} required />
              <input className="input" value={meetingLink} onChange={(event) => setMeetingLink(event.target.value)} placeholder="Meeting link" />
              <button className="btn-base btn-primary w-full" disabled={actionLoading === "interview"} type="submit">Schedule</button>
            </form>
          </Section>

          <Section title="Interviews, feedback, and scorecards">
            {detail.interviews.length === 0 ? <p className="text-sm text-muted-foreground">No interviews scheduled.</p> : (
              <div className="space-y-3">
                {detail.interviews.map((interview) => (
                  <div key={interview.id} className="border border-border rounded-lg p-3">
                    <p className="text-sm font-medium capitalize">{interview.interview_type} - {interview.status}</p>
                    <p className="text-xs text-muted-foreground">{formatDate(interview.scheduled_start)}</p>
                    {interview.meeting_link && <a className="text-xs text-primary hover:underline" href={interview.meeting_link} target="_blank" rel="noreferrer">Meeting link</a>}
                    {interview.feedback.length > 0 && <p className="text-xs mt-2">{interview.feedback.length} feedback item(s)</p>}
                    {interview.scorecards.length > 0 && <p className="text-xs text-muted-foreground">{interview.scorecards.length} scorecard(s)</p>}
                  </div>
                ))}
              </div>
            )}
          </Section>
        </aside>
      </div>
    </div>
  );
}

export default function RecruiterApplicationDetailPage() {
  return (
    <RecruiterShell title="Application detail" description="Review candidate context, timeline, notes, assignments, interviews, and audit history.">
      <ApplicationDetailContent />
    </RecruiterShell>
  );
}
