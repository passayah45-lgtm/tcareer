"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Navbar } from "@/components/layout/Navbar";
import { getApplicationDetail, getMyApplications, submitApplication, withdrawApplication } from "@/lib/api/student-career.api";
import type { StudentApplication, StudentApplicationDetail } from "@/types/student-career.types";

export default function StudentApplicationsPage() {
  const [applications, setApplications] = useState<StudentApplication[]>([]);
  const [detail, setDetail] = useState<StudentApplicationDetail | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setApplications(await getMyApplications());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function open(applicationId: string) {
    setDetail(await getApplicationDetail(applicationId));
  }

  async function submitDraft(applicationId: string) {
    await submitApplication(applicationId);
    await load();
    await open(applicationId);
  }

  async function withdraw(applicationId: string) {
    await withdrawApplication(applicationId);
    await load();
    await open(applicationId);
  }

  return (
    <>
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 py-8 grid grid-cols-1 lg:grid-cols-3 gap-6">
        <section className="lg:col-span-1 space-y-4">
          <div>
            <h1 className="text-2xl font-bold">Applications</h1>
            <p className="text-sm text-muted-foreground mt-1">Track submitted applications, drafts, interviews, and history.</p>
          </div>
          {loading && <div className="h-52 bg-muted rounded-xl animate-pulse" />}
          {!loading && applications.length === 0 && <div className="border border-border rounded-xl bg-card p-8 text-center">No applications yet.</div>}
          {applications.map((application) => (
            <button key={application.id} onClick={() => open(application.id)} className="w-full text-left border border-border rounded-xl bg-card p-4 hover:bg-muted">
              <p className="text-sm font-medium">{application.job_title}</p>
              <p className="text-xs text-muted-foreground">{application.company_name}</p>
              <span className="badge-primary mt-3">{application.stage_display}</span>
            </button>
          ))}
        </section>
        <section className="lg:col-span-2">
          {!detail ? (
            <div className="border border-border rounded-xl bg-card p-10 text-center text-sm text-muted-foreground">Choose an application to view history.</div>
          ) : (
            <div className="space-y-5">
              <div className="border border-border rounded-xl bg-card p-6">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">{detail.job.company_name}</p>
                    <h2 className="text-xl font-bold">{detail.job.title}</h2>
                    <p className="text-sm text-muted-foreground mt-1">{detail.job.location}</p>
                  </div>
                  <span className="badge-primary">{detail.application.stage_display}</span>
                </div>
                <p className="text-sm mt-4 whitespace-pre-wrap">{detail.application.cover_letter || "No cover letter yet."}</p>
                <div className="flex gap-2 mt-5">
                  <Link href={`/jobs/${detail.job.id}`} className="btn-sm btn-secondary">View job</Link>
                  {detail.application.stage === "draft" && <button onClick={() => submitDraft(detail.application.id)} className="btn-sm btn-primary">Submit draft</button>}
                  {!["withdrawn", "rejected", "offer_accepted", "offer_declined"].includes(detail.application.stage) && <button onClick={() => withdraw(detail.application.id)} className="btn-sm btn-secondary">Withdraw</button>}
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <section className="border border-border rounded-xl bg-card p-5">
                  <h3 className="font-semibold mb-4">Application answers</h3>
                  {detail.answers.length === 0 ? <p className="text-sm text-muted-foreground">No extra questions were answered.</p> : detail.answers.map((answer) => (
                    <div key={answer.id || answer.question} className="border-b border-border last:border-0 py-2">
                      <p className="text-sm font-medium">{answer.question_text}</p>
                      <p className="text-sm text-muted-foreground">{String(answer.answer.value)}</p>
                    </div>
                  ))}
                </section>
                <section className="border border-border rounded-xl bg-card p-5">
                  <h3 className="font-semibold mb-4">Timeline</h3>
                  {detail.timeline.map((item) => (
                    <div key={item.id} className="border-l-2 border-primary/30 pl-3 mb-3">
                      <p className="text-sm capitalize">{item.event_type.replaceAll("_", " ")}</p>
                      <p className="text-xs text-muted-foreground">{item.message || `${item.from_stage} -> ${item.to_stage}`}</p>
                    </div>
                  ))}
                </section>
                <section className="border border-border rounded-xl bg-card p-5">
                  <h3 className="font-semibold mb-4">Interviews and attachments</h3>
                  {detail.interviews.length === 0 && detail.attachments.length === 0 ? <p className="text-sm text-muted-foreground">No interviews or public attachments yet.</p> : null}
                  {detail.interviews.map((interview) => <p key={interview.id} className="text-sm mb-2">{interview.status} - {new Date(interview.scheduled_start).toLocaleString()}</p>)}
                  {detail.attachments.map((attachment) => <a key={attachment.id} className="block text-sm text-primary hover:underline" href={attachment.file_url}>{attachment.file_name}</a>)}
                </section>
              </div>
            </div>
          )}
        </section>
      </main>
    </>
  );
}
