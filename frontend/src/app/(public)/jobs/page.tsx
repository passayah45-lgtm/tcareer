"use client";

export const dynamic = "force-dynamic";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Navbar } from "@/components/layout/Navbar";
import { browseJobs, saveJob } from "@/lib/api/student-career.api";
import type { StudentJob } from "@/types/student-career.types";
import { useAuthStore } from "@/stores/auth.store";

export default function JobsPage() {
  const { isAuthenticated } = useAuthStore();
  const [jobs, setJobs] = useState<StudentJob[]>([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filters, setFilters] = useState({
    search: "",
    skills: "",
    country: "",
    city: "",
    company: "",
    job_type: "",
    experience: "",
    work_mode: "",
    salary_min: "",
    salary_max: "",
    posted_date: "",
    verification_status: "",
    sort: "-created_at",
  });

  function setFilter(field: keyof typeof filters, value: string) {
    setFilters((prev) => ({ ...prev, [field]: value }));
  }

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const result = await browseJobs({ ...filters, page_size: 24 });
      setJobs(result.results);
      setCount(result.count);
      setError("");
    } catch {
      setError("Unable to load jobs.");
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function quickSave(job: StudentJob) {
    if (!isAuthenticated) return;
    await saveJob({ job_id: job.id });
    await load();
  }

  return (
    <>
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 py-8 space-y-6">
        <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold">Job discovery</h1>
            <p className="text-sm text-muted-foreground mt-1">Search roles matched to your skills, location, salary, and work preferences.</p>
          </div>
          <Link href="/saved-jobs" className="btn-base btn-secondary">Saved jobs</Link>
        </div>

        <section className="border border-border rounded-xl bg-card p-4 grid grid-cols-1 md:grid-cols-3 xl:grid-cols-6 gap-3">
          <input className="input md:col-span-2" placeholder="Search title, company, description" value={filters.search} onChange={(e) => setFilter("search", e.target.value)} />
          <input className="input" placeholder="Skills: SQL,Python" value={filters.skills} onChange={(e) => setFilter("skills", e.target.value)} />
          <input className="input" placeholder="Country" value={filters.country} onChange={(e) => setFilter("country", e.target.value)} />
          <input className="input" placeholder="City" value={filters.city} onChange={(e) => setFilter("city", e.target.value)} />
          <input className="input" placeholder="Company" value={filters.company} onChange={(e) => setFilter("company", e.target.value)} />
          <select className="input" value={filters.job_type} onChange={(e) => setFilter("job_type", e.target.value)}>
            <option value="">Any category</option>
            <option value="full_time">Full time</option>
            <option value="part_time">Part time</option>
            <option value="contract">Contract</option>
            <option value="internship">Internship</option>
          </select>
          <select className="input" value={filters.experience} onChange={(e) => setFilter("experience", e.target.value)}>
            <option value="">Any experience</option>
            <option value="student">Student</option>
            <option value="entry">Entry</option>
            <option value="mid">Mid</option>
          </select>
          <select className="input" value={filters.work_mode} onChange={(e) => setFilter("work_mode", e.target.value)}>
            <option value="">Any work mode</option>
            <option value="remote">Remote</option>
            <option value="hybrid">Hybrid</option>
            <option value="onsite">Onsite</option>
          </select>
          <input className="input" placeholder="Min salary" value={filters.salary_min} onChange={(e) => setFilter("salary_min", e.target.value)} />
          <input className="input" placeholder="Max salary" value={filters.salary_max} onChange={(e) => setFilter("salary_max", e.target.value)} />
          <select className="input" value={filters.posted_date} onChange={(e) => setFilter("posted_date", e.target.value)}>
            <option value="">Any date</option>
            <option value="7d">Past 7 days</option>
            <option value="30d">Past 30 days</option>
          </select>
          <select className="input" value={filters.verification_status} onChange={(e) => setFilter("verification_status", e.target.value)}>
            <option value="">Any verification</option>
            <option value="verified">Verified company</option>
          </select>
          <select className="input" value={filters.sort} onChange={(e) => setFilter("sort", e.target.value)}>
            <option value="-created_at">Newest</option>
            <option value="-salary_max">Highest salary</option>
            <option value="-views_count">Popular</option>
            <option value="title">Title</option>
          </select>
          <button onClick={load} className="btn-base btn-primary xl:col-span-2">Search {count ? `(${count})` : ""}</button>
        </section>

        {loading && <div className="h-72 bg-muted rounded-xl animate-pulse" />}
        {error && <div className="border border-destructive/30 rounded-xl p-6 text-sm text-destructive">{error}</div>}
        {!loading && !error && jobs.length === 0 && <div className="border border-border rounded-xl p-10 text-center bg-card">No jobs found. Try broader filters.</div>}

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {jobs.map((job) => (
            <article key={job.id} className="border border-border rounded-xl bg-card p-5 flex flex-col gap-4">
              <div>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h2 className="font-semibold">{job.title}</h2>
                    <p className="text-sm text-muted-foreground">{job.company_name}</p>
                  </div>
                  {job.organization_name && <span className="badge-success">Verified</span>}
                </div>
                <p className="text-sm text-muted-foreground mt-3">{job.location || "Location not set"} - {job.job_type_display}</p>
                <p className="text-sm font-medium text-primary mt-1">{job.salary_display}</p>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {[...job.required_skills, ...job.preferred_skills].slice(0, 6).map((skill) => <span key={skill} className="tag">{skill}</span>)}
              </div>
              <div className="mt-auto flex gap-2">
                <Link href={`/jobs/${job.id}`} className="btn-sm btn-primary">View</Link>
                {isAuthenticated && <button onClick={() => quickSave(job)} className="btn-sm btn-secondary">Save</button>}
              </div>
            </article>
          ))}
        </div>
      </main>
    </>
  );
}
