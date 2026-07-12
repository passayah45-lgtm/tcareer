"use client";

import { useEffect, useState } from "react";
import { Navbar } from "@/components/layout/Navbar";
import { toast } from "@/components/shared/Toast";
import {
  getMyResume,
  updateMyResume,
  generateResumePdf,
} from "@/lib/api/careers.api";
import type {
  Resume,
  EducationEntry,
  ExperienceEntry,
} from "@/types/careers.types";

function genId() {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

function SectionCard({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="border rounded-xl p-6 bg-card">
      <h2 className="font-semibold text-base mb-4">{title}</h2>
      {children}
    </div>
  );
}

function FieldGroup({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium">{label}</label>
      {children}
    </div>
  );
}

function Input({
  value,
  onChange,
  placeholder,
  type = "text",
}: {
  value: string | number;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
}) {
  return (
    <input
      type={type}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
    />
  );
}

function EducationForm({
  entries,
  onChange,
}: {
  entries: EducationEntry[];
  onChange: (entries: EducationEntry[]) => void;
}) {
  const add = () =>
    onChange([
      ...entries,
      {
        id: genId(),
        institution: "",
        degree: "",
        field: "",
        start_year: new Date().getFullYear(),
        end_year: null,
        grade: "",
        description: "",
      },
    ]);

  const update = (id: string, key: keyof EducationEntry, value: unknown) =>
    onChange(entries.map((e) => (e.id === id ? { ...e, [key]: value } : e)));

  const remove = (id: string) => onChange(entries.filter((e) => e.id !== id));

  return (
    <div className="space-y-4">
      {entries.length === 0 && (
        <p className="text-sm text-muted-foreground text-center py-2">
          No education entries yet.
        </p>
      )}
      {entries.map((entry) => (
        <div key={entry.id} className="border rounded-lg p-4 bg-background space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium">
              {entry.institution || "New Entry"}
            </p>
            <button
              onClick={() => remove(entry.id)}
              className="text-xs text-destructive hover:underline"
            >
              Remove
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <FieldGroup label="Institution *">
              <Input
                value={entry.institution}
                onChange={(v) => update(entry.id, "institution", v)}
                placeholder="Universite Gamal Abdel Nasser de Conakry"
              />
            </FieldGroup>
            <FieldGroup label="Degree">
              <Input
                value={entry.degree}
                onChange={(v) => update(entry.id, "degree", v)}
                placeholder="Bachelor of Science"
              />
            </FieldGroup>
            <FieldGroup label="Field of Study">
              <Input
                value={entry.field}
                onChange={(v) => update(entry.id, "field", v)}
                placeholder="Computer Science"
              />
            </FieldGroup>
            <FieldGroup label="Grade / GPA">
              <Input
                value={entry.grade}
                onChange={(v) => update(entry.id, "grade", v)}
                placeholder="3.8 / 4.0"
              />
            </FieldGroup>
            <FieldGroup label="Start Year">
              <Input
                type="number"
                value={entry.start_year}
                onChange={(v) => update(entry.id, "start_year", parseInt(v))}
                placeholder="2020"
              />
            </FieldGroup>
            <FieldGroup label="End Year">
              <Input
                type="number"
                value={entry.end_year ?? ""}
                onChange={(v) =>
                  update(entry.id, "end_year", v ? parseInt(v) : null)
                }
                placeholder="2024 (leave blank if ongoing)"
              />
            </FieldGroup>
          </div>
        </div>
      ))}
      <button
        onClick={add}
        disabled={entries.length >= 10}
        className="w-full py-2 rounded-lg border border-dashed text-sm text-muted-foreground hover:text-foreground hover:border-foreground transition-colors disabled:opacity-40"
      >
        + Add Education
      </button>
    </div>
  );
}

function ExperienceForm({
  entries,
  onChange,
}: {
  entries: ExperienceEntry[];
  onChange: (entries: ExperienceEntry[]) => void;
}) {
  const add = () =>
    onChange([
      ...entries,
      {
        id: genId(),
        company: "",
        title: "",
        location: "",
        start_date: "",
        end_date: "",
        is_current: false,
        description: "",
      },
    ]);

  const update = (id: string, key: keyof ExperienceEntry, value: unknown) =>
    onChange(entries.map((e) => (e.id === id ? { ...e, [key]: value } : e)));

  const remove = (id: string) => onChange(entries.filter((e) => e.id !== id));

  return (
    <div className="space-y-4">
      {entries.length === 0 && (
        <p className="text-sm text-muted-foreground text-center py-2">
          No experience entries yet.
        </p>
      )}
      {entries.map((entry) => (
        <div key={entry.id} className="border rounded-lg p-4 bg-background space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium">
              {entry.company || "New Entry"}
            </p>
            <button
              onClick={() => remove(entry.id)}
              className="text-xs text-destructive hover:underline"
            >
              Remove
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <FieldGroup label="Company *">
              <Input
                value={entry.company}
                onChange={(v) => update(entry.id, "company", v)}
                placeholder="T-Career SARL"
              />
            </FieldGroup>
            <FieldGroup label="Job Title *">
              <Input
                value={entry.title}
                onChange={(v) => update(entry.id, "title", v)}
                placeholder="Software Engineer"
              />
            </FieldGroup>
            <FieldGroup label="Location">
              <Input
                value={entry.location}
                onChange={(v) => update(entry.id, "location", v)}
                placeholder="Conakry, Guinea"
              />
            </FieldGroup>
            <div className="flex items-center gap-2 self-end pb-2">
              <input
                id={`current-${entry.id}`}
                type="checkbox"
                checked={entry.is_current}
                onChange={(e) => update(entry.id, "is_current", e.target.checked)}
                className="w-4 h-4"
              />
              <label htmlFor={`current-${entry.id}`} className="text-sm">
                Currently working here
              </label>
            </div>
            <FieldGroup label="Start Date (YYYY-MM)">
              <Input
                value={entry.start_date}
                onChange={(v) => update(entry.id, "start_date", v)}
                placeholder="2023-06"
              />
            </FieldGroup>
            {!entry.is_current && (
              <FieldGroup label="End Date (YYYY-MM)">
                <Input
                  value={entry.end_date}
                  onChange={(v) => update(entry.id, "end_date", v)}
                  placeholder="2024-01"
                />
              </FieldGroup>
            )}
          </div>
          <FieldGroup label="Description">
            <textarea
              value={entry.description}
              onChange={(e) => update(entry.id, "description", e.target.value)}
              placeholder="What you did in this role..."
              rows={3}
              className="w-full px-3 py-2 rounded-lg border bg-card text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none"
            />
          </FieldGroup>
        </div>
      ))}
      <button
        onClick={add}
        disabled={entries.length >= 15}
        className="w-full py-2 rounded-lg border border-dashed text-sm text-muted-foreground hover:text-foreground hover:border-foreground transition-colors disabled:opacity-40"
      >
        + Add Experience
      </button>
    </div>
  );
}

export default function ResumeEditPage() {
  const [resume, setResume] = useState<Resume | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(false);

  const [summary, setSummary] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [education, setEducation] = useState<EducationEntry[]>([]);
  const [experience, setExperience] = useState<ExperienceEntry[]>([]);

  useEffect(() => {
    getMyResume()
      .then((r) => {
        setResume(r);
        setSummary(r.summary);
        setTargetRole(r.target_role);
        setEducation(r.education);
        setExperience(r.experience);
      })
      .catch(() => toast("Failed to load resume.", "error"))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      const updated = await updateMyResume({
        summary,
        target_role: targetRole,
        education,
        experience,
      });
      setResume(updated);
      toast("Resume saved.", "success");
    } catch (err: unknown) {
      const errors = (err as { response?: { data?: { errors?: Record<string, string[]> } } })
        ?.response?.data?.errors;
      const msg = errors
        ? Object.values(errors).flat().join(" ")
        : "Failed to save resume.";
      toast(msg, "error");
    } finally {
      setSaving(false);
    }
  };

  const handleGeneratePdf = async () => {
    setGenerating(true);
    try {
      await updateMyResume({ summary, target_role: targetRole, education, experience });
      const result = await generateResumePdf();
      setResume((prev) =>
        prev ? { ...prev, pdf_url: result.pdf_url, last_generated_at: result.generated_at } : prev
      );
      toast("PDF generated. You can download it below.", "success");
    } catch {
      toast("PDF generation failed. Please try again.", "error");
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <>
        <Navbar />
        <main className="max-w-3xl mx-auto px-4 py-8 space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-40 rounded-xl bg-muted animate-pulse" />
          ))}
        </main>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <main className="max-w-3xl mx-auto px-4 py-8 space-y-6">

        <div>
          <h1 className="text-2xl font-bold tracking-tight">Resume Builder</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Your resume is auto-populated with your certificates and skills from your portfolio.
          </p>
        </div>

        <SectionCard title="Professional Summary">
          <textarea
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            placeholder="A concise summary of your background, skills, and career goals..."
            rows={4}
            className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none"
          />
        </SectionCard>

        <SectionCard title="Target Role">
          <input
            value={targetRole}
            onChange={(e) => setTargetRole(e.target.value)}
            placeholder="e.g. Backend Developer, Data Analyst"
            className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
          <p className="text-xs text-muted-foreground mt-1.5">
            Used for AI recommendations and shown at the top of your PDF.
          </p>
        </SectionCard>

        <SectionCard title="Experience">
          <ExperienceForm entries={experience} onChange={setExperience} />
        </SectionCard>

        <SectionCard title="Education">
          <EducationForm entries={education} onChange={setEducation} />
        </SectionCard>

        {resume?.skills && resume.skills.length > 0 && (
          <SectionCard title="Skills (from your portfolio)">
            <div className="flex flex-wrap gap-2">
              {resume.skills.map((skill) => (
                <span
                  key={skill.id}
                  className="px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-medium"
                >
                  {skill.name}
                </span>
              ))}
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Skills are pulled from your portfolio.{" "}
              <a href="/portfolio/edit" className="text-primary hover:underline">
                Manage skills
              </a>
            </p>
          </SectionCard>
        )}

        {resume?.certificates && resume.certificates.length > 0 && (
          <SectionCard title="Certificates (from your learning)">
            <div className="space-y-2">
              {resume.certificates.map((cert) => (
                <div
                  key={cert.cert_number}
                  className="flex items-center justify-between py-2 border-b last:border-0"
                >
                  <div>
                    <p className="text-sm font-medium">{cert.course_title}</p>
                    <p className="text-xs font-mono text-muted-foreground">
                      {cert.cert_number}
                    </p>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {new Date(cert.issued_at).toLocaleDateString("en-US", {
                      month: "short",
                      year: "numeric",
                    })}
                  </p>
                </div>
              ))}
            </div>
          </SectionCard>
        )}

        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex-1 py-2.5 rounded-xl bg-primary text-primary-foreground font-medium text-sm disabled:opacity-50 hover:opacity-90 transition-opacity"
          >
            {saving ? "Saving..." : "Save Resume"}
          </button>
          <button
            onClick={handleGeneratePdf}
            disabled={generating || saving}
            className="flex-1 py-2.5 rounded-xl border font-medium text-sm disabled:opacity-50 hover:bg-muted transition-colors"
          >
            {generating ? "Generating PDF..." : "Generate PDF"}
          </button>
        </div>

        {resume?.pdf_url && (
          <div className="border rounded-xl p-4 bg-card flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Resume PDF ready</p>
              {resume.last_generated_at && (
                <p className="text-xs text-muted-foreground mt-0.5">
                  Generated{" "}
                  {new Date(resume.last_generated_at).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              )}
            </div>
            
             <a href={resume.pdf_url}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:opacity-90"
            >
              Download PDF
            </a>
          </div>
        )}
      </main>
    </>
  );
}
