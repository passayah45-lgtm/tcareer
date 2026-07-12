"use client";

import { useState } from "react";
import Link from "next/link";
import { Navbar } from "@/components/layout/Navbar";
import api from "@/lib/api/client";

export default function RecruitPage() {
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    company_name: "",
    company_size: "1-10",
    roles_hiring_for: "",
    monthly_hires: "1-2",
  });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await api.post("/jobs/recruit/", form);
      setSuccess(true);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { errors?: { detail?: string } } } };
      setError(e?.response?.data?.errors?.detail || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Navbar />
      <main className="max-w-2xl mx-auto px-4 py-8">
        <div className="mb-8">
          <Link href="/jobs" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
            Back to jobs
          </Link>
          <h1 className="text-3xl font-bold mt-2 mb-2">Hire T-Career candidates</h1>
          <p className="text-muted-foreground">
            Our recruiter portal is launching soon. Join the waitlist to be the first to access
            verified candidates who have completed structured learning tracks.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          {[
            { title: "Verified skills", desc: "Every candidate has completed assessed courses with certificates." },
            { title: "Track-matched", desc: "Filter candidates by the career track they completed." },
            { title: "Job-ready", desc: "Students build real projects and pass quizzes before graduating." },
          ].map((item) => (
            <div key={item.title} className="border rounded-xl p-4 bg-card">
              <h3 className="font-medium text-sm mb-1">{item.title}</h3>
              <p className="text-xs text-muted-foreground">{item.desc}</p>
            </div>
          ))}
        </div>

        {success ? (
          <div className="border rounded-xl p-8 text-center">
            <div className="text-4xl mb-3">&#10003;</div>
            <h2 className="font-semibold mb-2">You are on the waitlist</h2>
            <p className="text-sm text-muted-foreground">
              We will contact you at {form.email} when the recruiter portal launches.
            </p>
          </div>
        ) : (
          <div className="border rounded-xl p-6 bg-card">
            <h2 className="font-semibold mb-4">Join the waitlist</h2>
            {error && <div className="mb-4 p-3 rounded-lg bg-destructive/10 text-destructive text-sm">{error}</div>}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium block mb-1">Your name</label>
                  <input name="full_name" value={form.full_name} onChange={handleChange} required
                    className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 bg-background" />
                </div>
                <div>
                  <label className="text-sm font-medium block mb-1">Work email</label>
                  <input name="email" type="email" value={form.email} onChange={handleChange} required
                    className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 bg-background" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium block mb-1">Company name</label>
                  <input name="company_name" value={form.company_name} onChange={handleChange} required
                    className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 bg-background" />
                </div>
                <div>
                  <label className="text-sm font-medium block mb-1">Company size</label>
                  <select name="company_size" value={form.company_size} onChange={handleChange}
                    className="w-full border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/30">
                    <option value="1-10">1-10 employees</option>
                    <option value="11-50">11-50 employees</option>
                    <option value="51-200">51-200 employees</option>
                    <option value="201-500">201-500 employees</option>
                    <option value="500+">500+ employees</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium block mb-1">Roles you are hiring for</label>
                <textarea name="roles_hiring_for" value={form.roles_hiring_for} onChange={handleChange} rows={2}
                  placeholder="e.g. Backend Developer, Data Analyst, DevOps Engineer"
                  className="w-full border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none" />
              </div>
              <div>
                <label className="text-sm font-medium block mb-1">Monthly hires</label>
                <select name="monthly_hires" value={form.monthly_hires} onChange={handleChange}
                  className="w-full border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/30">
                  <option value="1-2">1-2 per month</option>
                  <option value="3-5">3-5 per month</option>
                  <option value="6-10">6-10 per month</option>
                  <option value="10+">10+ per month</option>
                </select>
              </div>
              <button type="submit" disabled={loading}
                className="w-full bg-primary text-primary-foreground py-2.5 rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50">
                {loading ? "Joining..." : "Join the waitlist"}
              </button>
            </form>
          </div>
        )}
      </main>
    </>
  );
}
