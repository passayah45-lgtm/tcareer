"use client";

import { useState } from "react";
import type { RecruiterJob, RecruiterJobPayload } from "@/types/recruiter.types";

const JOB_TYPES = ["full_time", "part_time", "contract", "freelance", "internship", "remote"];
const EXPERIENCE_LEVELS = ["student", "entry", "mid", "senior", "lead"];

function splitList(value: string) {
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

export function JobForm({
  initialJob,
  submitting,
  onSubmit,
}: {
  initialJob?: RecruiterJob | null;
  submitting?: boolean;
  onSubmit: (payload: RecruiterJobPayload) => Promise<void>;
}) {
  const [form, setForm] = useState({
    title: initialJob?.title || "",
    company_name: initialJob?.company_name || "",
    description: initialJob?.description || "",
    requirements: initialJob?.requirements?.join(", ") || "",
    job_type: initialJob?.job_type || "full_time",
    experience_level: initialJob?.experience_level || "entry",
    location: initialJob?.location || "",
    apply_url: initialJob?.apply_url || "",
    salary_min: initialJob?.salary_min ? String(initialJob.salary_min) : "",
    salary_max: initialJob?.salary_max ? String(initialJob.salary_max) : "",
    required_skills: "",
    preferred_skills: "",
  });

  function setField(field: keyof typeof form, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    await onSubmit({
      title: form.title,
      company_name: form.company_name,
      description: form.description,
      requirements: splitList(form.requirements),
      job_type: form.job_type,
      experience_level: form.experience_level,
      location: form.location,
      apply_url: form.apply_url,
      salary_min: form.salary_min ? Number(form.salary_min) : null,
      salary_max: form.salary_max ? Number(form.salary_max) : null,
      required_skills: splitList(form.required_skills),
      preferred_skills: splitList(form.preferred_skills),
    });
  }

  return (
    <form onSubmit={submit} className="border border-border rounded-xl bg-card p-6 space-y-5">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="label">Job title</label>
          <input className="input" value={form.title} onChange={(event) => setField("title", event.target.value)} required />
        </div>
        <div>
          <label className="label">Company name</label>
          <input className="input" value={form.company_name} onChange={(event) => setField("company_name", event.target.value)} required />
        </div>
        <div>
          <label className="label">Job type</label>
          <select className="input" value={form.job_type} onChange={(event) => setField("job_type", event.target.value)}>
            {JOB_TYPES.map((type) => <option key={type} value={type}>{type.replaceAll("_", " ")}</option>)}
          </select>
        </div>
        <div>
          <label className="label">Experience level</label>
          <select className="input" value={form.experience_level} onChange={(event) => setField("experience_level", event.target.value)}>
            {EXPERIENCE_LEVELS.map((level) => <option key={level} value={level}>{level.replaceAll("_", " ")}</option>)}
          </select>
        </div>
        <div>
          <label className="label">Location</label>
          <input className="input" value={form.location} onChange={(event) => setField("location", event.target.value)} />
        </div>
        <div>
          <label className="label">Apply URL</label>
          <input className="input" value={form.apply_url} onChange={(event) => setField("apply_url", event.target.value)} placeholder="https://..." />
        </div>
        <div>
          <label className="label">Salary min</label>
          <input className="input" type="number" value={form.salary_min} onChange={(event) => setField("salary_min", event.target.value)} />
        </div>
        <div>
          <label className="label">Salary max</label>
          <input className="input" type="number" value={form.salary_max} onChange={(event) => setField("salary_max", event.target.value)} />
        </div>
      </div>

      <div>
        <label className="label">Description</label>
        <textarea className="input min-h-32 py-3" value={form.description} onChange={(event) => setField("description", event.target.value)} required />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="label">Requirements</label>
          <input className="input" value={form.requirements} onChange={(event) => setField("requirements", event.target.value)} placeholder="Python, APIs" />
        </div>
        <div>
          <label className="label">Required skills</label>
          <input className="input" value={form.required_skills} onChange={(event) => setField("required_skills", event.target.value)} placeholder="Django, SQL" />
        </div>
        <div>
          <label className="label">Preferred skills</label>
          <input className="input" value={form.preferred_skills} onChange={(event) => setField("preferred_skills", event.target.value)} placeholder="Docker, AWS" />
        </div>
      </div>

      <div className="flex justify-end">
        <button disabled={submitting} className="btn-base btn-primary" type="submit">
          {submitting ? "Saving..." : "Save job"}
        </button>
      </div>
    </form>
  );
}
