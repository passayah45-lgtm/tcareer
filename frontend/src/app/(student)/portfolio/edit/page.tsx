"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import { toast } from "@/components/shared/Toast";
import {
  getMyPortfolio,
  updateMyPortfolio,
  addSkill,
  deleteSkill,
  syncSkills,
  createProject,
  updateProject,
  deleteProject,
} from "@/lib/api/careers.api";
import type {
  Portfolio,
  PortfolioUpdatePayload,
  PortfolioSkill,
  PortfolioProject,
  VisibilityChoice,
  ExperienceLevel,
} from "@/types/careers.types";

const EXPERIENCE_OPTIONS: { value: ExperienceLevel; label: string }[] = [
  { value: "student", label: "Student" },
  { value: "entry", label: "Entry Level" },
  { value: "mid", label: "Mid Level" },
  { value: "senior", label: "Senior" },
  { value: "lead", label: "Lead / Manager" },
];

const VISIBILITY_OPTIONS: { value: VisibilityChoice; label: string; description: string }[] = [
  { value: "public", label: "Public", description: "Anyone can view your portfolio." },
  { value: "unlisted", label: "Unlisted", description: "Only people with the link can view it." },
  { value: "private", label: "Private", description: "Only you can see it." },
];

const SOURCE_LABELS: Record<string, string> = {
  manual: "Manual",
  track: "From track",
  course: "From course",
};

const SOURCE_COLORS: Record<string, string> = {
  manual: "bg-blue-50 text-blue-700 border-blue-200",
  track: "bg-purple-50 text-purple-700 border-purple-200",
  course: "bg-green-50 text-green-700 border-green-200",
};

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium">{label}</label>
      {children}
      {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}

function Input({
  value,
  onChange,
  placeholder,
  type = "text",
  disabled,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
  disabled?: boolean;
}) {
  return (
    <input
      type={type}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      disabled={disabled}
      className="w-full px-3 py-2 rounded-lg border bg-background text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50"
    />
  );
}

function Textarea({
  value,
  onChange,
  placeholder,
  rows = 4,
  disabled,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  rows?: number;
  disabled?: boolean;
}) {
  return (
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      rows={rows}
      disabled={disabled}
      className="w-full px-3 py-2 rounded-lg border bg-background text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50 resize-none"
    />
  );
}

function SectionCard({
  title,
  description,
  action,
  children,
}: {
  title: string;
  description?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="border rounded-xl p-6 bg-card space-y-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="font-semibold text-base">{title}</h2>
          {description && <p className="text-sm text-muted-foreground mt-0.5">{description}</p>}
        </div>
        {action}
      </div>
      {children}
    </div>
  );
}

interface ProfileForm {
  headline: string;
  bio: string;
  location: string;
  desired_role: string;
  experience_level: ExperienceLevel;
  linkedin_url: string;
  github_url: string;
  website_url: string;
  visibility: VisibilityChoice;
}

function portfolioToForm(p: Portfolio): ProfileForm {
  return {
    headline: p.headline ?? "",
    bio: p.bio ?? "",
    location: p.location ?? "",
    desired_role: p.desired_role ?? "",
    experience_level: p.experience_level ?? "student",
    linkedin_url: p.linkedin_url ?? "",
    github_url: p.github_url ?? "",
    website_url: p.website_url ?? "",
    visibility: p.visibility ?? "public",
  };
}

function isDirty(form: ProfileForm, original: ProfileForm): boolean {
  return (Object.keys(form) as (keyof ProfileForm)[]).some((k) => form[k] !== original[k]);
}

function SkillsSection({
  skills,
  onSkillsChange,
}: {
  skills: PortfolioSkill[];
  onSkillsChange: (skills: PortfolioSkill[]) => void;
}) {
  const [name, setName] = useState("");
  const [category, setCategory] = useState("");
  const [adding, setAdding] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  async function handleAdd() {
    const trimmed = name.trim();
    if (!trimmed) {
      toast("Enter a skill name.", "error");
      return;
    }
    setAdding(true);
    try {
      const created = await addSkill({ name: trimmed, category: category.trim() || undefined });
      onSkillsChange([...skills, created]);
      setName("");
      setCategory("");
      toast("Skill added.", "success");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { error?: { details?: { name?: string[] } } } } })?.response?.data
          ?.error?.details?.name?.[0] ?? "Failed to add skill.";
      toast(msg, "error");
    } finally {
      setAdding(false);
    }
  }

  async function handleDelete(skillId: string) {
    setDeletingId(skillId);
    try {
      await deleteSkill(skillId);
      onSkillsChange(skills.filter((s) => s.id !== skillId));
      toast("Skill removed.", "success");
    } catch {
      toast("Failed to remove skill.", "error");
    } finally {
      setDeletingId(null);
    }
  }

  async function handleSync() {
    setSyncing(true);
    try {
      const result = await syncSkills();
      if (result.total_added === 0) {
        toast("No new skills found to import.", "info");
      } else {
        toast(
          `Imported ${result.total_added} new skill${result.total_added === 1 ? "" : "s"} from your courses and tracks.`,
          "success"
        );
      }
      const fresh = await getMyPortfolio();
      onSkillsChange(fresh.skills);
    } catch {
      toast("Skill sync failed. Please try again.", "error");
    } finally {
      setSyncing(false);
    }
  }

  return (
    <SectionCard
      title={`Skills (${skills.length})`}
      description="Skills can be added manually or synced automatically from completed courses and tracks."
      action={
        <button
          onClick={handleSync}
          disabled={syncing}
          className="text-xs px-3 py-1.5 rounded-lg border hover:bg-muted transition-colors disabled:opacity-50 shrink-0"
        >
          {syncing ? "Syncing..." : "Sync from courses"}
        </button>
      }
    >
      <div className="flex flex-col sm:flex-row gap-2">
        <div className="flex-1">
          <Input value={name} onChange={setName} placeholder="Skill name, e.g. Python" disabled={adding} />
        </div>
        <div className="flex-1">
          <Input value={category} onChange={setCategory} placeholder="Category (optional)" disabled={adding} />
        </div>
        <button
          onClick={handleAdd}
          disabled={adding || !name.trim()}
          className="px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 shrink-0"
        >
          {adding ? "Adding..." : "Add skill"}
        </button>
      </div>

      {skills.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-4">
          No skills yet. Add one above or sync from your courses.
        </p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {skills.map((skill) => {
            const color = SOURCE_COLORS[skill.source] ?? "bg-gray-100 text-gray-700 border-gray-200";
            return (
              <span
                key={skill.id}
                className={`inline-flex items-center gap-2 pl-3 pr-2 py-1 rounded-full text-xs font-medium border ${color}`}
              >
                <span>
                  {skill.name}
                  {skill.category && <span className="opacity-60"> - {skill.category}</span>}
                </span>
                <span className="opacity-50 text-[10px] uppercase tracking-wide">
                  {SOURCE_LABELS[skill.source] ?? skill.source}
                </span>
                <button
                  onClick={() => handleDelete(skill.id)}
                  disabled={deletingId === skill.id}
                  aria-label={`Remove ${skill.name}`}
                  className="ml-0.5 w-4 h-4 flex items-center justify-center rounded-full hover:bg-black/10 transition-colors disabled:opacity-50"
                >
                  x
                </button>
              </span>
            );
          })}
        </div>
      )}
    </SectionCard>
  );
}

interface ProjectFormState {
  title: string;
  description: string;
  tech_stack: string;
  project_url: string;
  github_url: string;
  demo_video_url: string;
  gallery_urls: string;
  is_featured: boolean;
  start_date: string;
  end_date: string;
}

const EMPTY_PROJECT_FORM: ProjectFormState = {
  title: "",
  description: "",
  tech_stack: "",
  project_url: "",
  github_url: "",
  demo_video_url: "",
  gallery_urls: "",
  is_featured: false,
  start_date: "",
  end_date: "",
};

function projectToForm(p: PortfolioProject): ProjectFormState {
  return {
    title: p.title ?? "",
    description: p.description ?? "",
    tech_stack: (p.tech_stack ?? []).join(", "),
    project_url: p.project_url ?? "",
    github_url: p.github_url ?? "",
    demo_video_url: p.demo_video_url ?? "",
    gallery_urls: (p.gallery_urls ?? []).join(", "),
    is_featured: p.is_featured ?? false,
    start_date: p.start_date ?? "",
    end_date: p.end_date ?? "",
  };
}

function formToPayload(f: ProjectFormState): Partial<PortfolioProject> {
  return {
    title: f.title.trim(),
    description: f.description.trim(),
    tech_stack: f.tech_stack.split(",").map((t) => t.trim()).filter(Boolean),
    project_url: f.project_url.trim(),
    github_url: f.github_url.trim(),
    demo_video_url: f.demo_video_url.trim(),
    gallery_urls: f.gallery_urls.split(",").map((t) => t.trim()).filter(Boolean),
    is_featured: f.is_featured,
    start_date: f.start_date || null,
    end_date: f.end_date || null,
  };
}

function ProjectModal({
  initial,
  onClose,
  onSave,
}: {
  initial: ProjectFormState;
  onClose: () => void;
  onSave: (payload: Partial<PortfolioProject>) => Promise<void>;
}) {
  const [form, setForm] = useState<ProjectFormState>(initial);
  const [saving, setSaving] = useState(false);

  function set<K extends keyof ProjectFormState>(key: K, value: ProjectFormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit() {
    if (!form.title.trim()) {
      toast("Project title is required.", "error");
      return;
    }
    if (form.start_date && form.end_date && form.end_date < form.start_date) {
      toast("End date cannot be before start date.", "error");
      return;
    }
    setSaving(true);
    try {
      await onSave(formToPayload(form));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={saving ? undefined : onClose} />
      <div className="relative w-full sm:max-w-lg max-h-[90vh] overflow-y-auto bg-background border rounded-t-2xl sm:rounded-2xl p-6 space-y-4">
        <h3 className="font-semibold text-base">
          {initial.title ? "Edit project" : "Add project"}
        </h3>

        <Field label="Title *">
          <Input value={form.title} onChange={(v) => set("title", v)} placeholder="e.g. E-commerce Platform" disabled={saving} />
        </Field>

        <Field label="Description">
          <Textarea
            value={form.description}
            onChange={(v) => set("description", v)}
            placeholder="What does this project do and what did you build?"
            rows={3}
            disabled={saving}
          />
        </Field>

        <Field label="Tech stack" hint="Comma-separated, e.g. React, Django, PostgreSQL">
          <Input value={form.tech_stack} onChange={(v) => set("tech_stack", v)} placeholder="React, Django, PostgreSQL" disabled={saving} />
        </Field>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Field label="Project URL">
            <Input value={form.project_url} onChange={(v) => set("project_url", v)} placeholder="https://..." type="url" disabled={saving} />
          </Field>
          <Field label="GitHub URL">
            <Input value={form.github_url} onChange={(v) => set("github_url", v)} placeholder="https://github.com/..." type="url" disabled={saving} />
          </Field>
        </div>

        <Field label="Demo video URL">
          <Input value={form.demo_video_url} onChange={(v) => set("demo_video_url", v)} placeholder="https://..." type="url" disabled={saving} />
        </Field>

        <Field label="Gallery image URLs" hint="Comma-separated, up to 10 images">
          <Input value={form.gallery_urls} onChange={(v) => set("gallery_urls", v)} placeholder="https://img1.png, https://img2.png" disabled={saving} />
        </Field>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Field label="Start date">
            <Input value={form.start_date} onChange={(v) => set("start_date", v)} type="date" disabled={saving} />
          </Field>
          <Field label="End date">
            <Input value={form.end_date} onChange={(v) => set("end_date", v)} type="date" disabled={saving} />
          </Field>
        </div>

        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={form.is_featured}
            onChange={(e) => set("is_featured", e.target.checked)}
            disabled={saving}
            className="w-4 h-4"
          />
          Feature this project at the top of my portfolio
        </label>

        <div className="flex items-center justify-end gap-3 pt-2">
          <button
            onClick={onClose}
            disabled={saving}
            className="px-4 py-2 rounded-lg text-sm text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={saving}
            className="px-5 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save project"}
          </button>
        </div>
      </div>
    </div>
  );
}

function ProjectRow({
  project,
  onEdit,
  onDelete,
  deleting,
}: {
  project: PortfolioProject;
  onEdit: () => void;
  onDelete: () => void;
  deleting: boolean;
}) {
  return (
    <div className="border rounded-xl p-4 bg-background space-y-2">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="text-sm font-semibold truncate">{project.title}</p>
            {project.is_featured && (
              <span className="text-xs bg-amber-100 text-amber-700 border border-amber-200 px-2 py-0.5 rounded-full shrink-0">
                Featured
              </span>
            )}
          </div>
          {project.description && (
            <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{project.description}</p>
          )}
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <button onClick={onEdit} className="text-xs text-primary hover:underline">
            Edit
          </button>
          <button
            onClick={onDelete}
            disabled={deleting}
            className="text-xs text-destructive hover:underline disabled:opacity-50"
          >
            {deleting ? "Removing..." : "Delete"}
          </button>
        </div>
      </div>
      {project.tech_stack.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {project.tech_stack.map((tech) => (
            <span key={tech} className="text-xs bg-secondary text-secondary-foreground px-2 py-0.5 rounded">
              {tech}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function ProjectsSection({
  projects,
  onProjectsChange,
}: {
  projects: PortfolioProject[];
  onProjectsChange: (projects: PortfolioProject[]) => void;
}) {
  const [modalProject, setModalProject] = useState<PortfolioProject | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  function openCreate() {
    setModalProject(null);
    setModalOpen(true);
  }

  function openEdit(project: PortfolioProject) {
    setModalProject(project);
    setModalOpen(true);
  }

  async function handleSave(payload: Partial<PortfolioProject>) {
    try {
      if (modalProject) {
        const updated = await updateProject(modalProject.id, payload);
        onProjectsChange(projects.map((p) => (p.id === updated.id ? updated : p)));
        toast("Project updated.", "success");
      } else {
        const created = await createProject(payload);
        onProjectsChange([...projects, created]);
        toast("Project added.", "success");
      }
      setModalOpen(false);
    } catch {
      toast("Failed to save project. Please try again.", "error");
    }
  }

  async function handleDelete(projectId: string) {
    setDeletingId(projectId);
    try {
      await deleteProject(projectId);
      onProjectsChange(projects.filter((p) => p.id !== projectId));
      toast("Project removed.", "success");
    } catch {
      toast("Failed to remove project.", "error");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <SectionCard
      title={`Projects (${projects.length})`}
      description="Show recruiters what you have built."
      action={
        <button
          onClick={openCreate}
          className="text-xs px-3 py-1.5 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors shrink-0"
        >
          Add project
        </button>
      }
    >
      {projects.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-4">
          No projects yet. Click &quot;Add project&quot; to create one.
        </p>
      ) : (
        <div className="space-y-3">
          {projects.map((project) => (
            <ProjectRow
              key={project.id}
              project={project}
              onEdit={() => openEdit(project)}
              onDelete={() => handleDelete(project.id)}
              deleting={deletingId === project.id}
            />
          ))}
        </div>
      )}

      {modalOpen && (
        <ProjectModal
          initial={modalProject ? projectToForm(modalProject) : EMPTY_PROJECT_FORM}
          onClose={() => setModalOpen(false)}
          onSave={handleSave}
        />
      )}
    </SectionCard>
  );
}

export default function PortfolioEditPage() {
  const router = useRouter();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [original, setOriginal] = useState<ProfileForm | null>(null);
  const [form, setForm] = useState<ProfileForm | null>(null);
  const [skills, setSkills] = useState<PortfolioSkill[]>([]);
  const [projects, setProjects] = useState<PortfolioProject[]>([]);

  const load = useCallback(async () => {
    try {
      const data = await getMyPortfolio();
      const state = portfolioToForm(data);
      setOriginal(state);
      setForm(state);
      setSkills(data.skills);
      setProjects(data.projects);
    } catch {
      toast("Failed to load your portfolio.", "error");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);

  function set(field: keyof ProfileForm, value: string) {
    setForm((prev) => (prev ? { ...prev, [field]: value } : prev));
  }

  async function handleSaveProfile() {
    if (!form || !original) return;
    if (!isDirty(form, original)) {
      toast("No profile changes to save.", "info");
      return;
    }

    setSaving(true);
    try {
      const payload: PortfolioUpdatePayload = { ...form };
      await updateMyPortfolio(payload);
      setOriginal(form);
      toast("Portfolio saved.", "success");
    } catch {
      toast("Failed to save. Please try again.", "error");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="max-w-2xl mx-auto px-4 py-10 space-y-4 animate-pulse">
          <div className="h-8 w-48 bg-muted rounded" />
          <div className="h-64 bg-muted rounded-xl" />
          <div className="h-48 bg-muted rounded-xl" />
          <div className="h-40 bg-muted rounded-xl" />
          <div className="h-40 bg-muted rounded-xl" />
        </main>
      </div>
    );
  }

  if (!form) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="max-w-2xl mx-auto px-4 py-10">
          <p className="text-sm text-muted-foreground text-center">
            Could not load your portfolio. Please refresh the page.
          </p>
        </main>
      </div>
    );
  }

  const dirty = original ? isDirty(form, original) : false;

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="max-w-2xl mx-auto px-4 py-10 space-y-6">

        <div className="flex items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold">Edit Portfolio</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Update your public career profile.
            </p>
          </div>
          <button
            onClick={() => router.push("/portfolio")}
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            Done
          </button>
        </div>

        <SectionCard title="Profile" description="This information appears on your public portfolio page.">
          <Field label="Headline" hint="A short phrase that describes what you do.">
            <Input
              value={form.headline}
              onChange={(v) => set("headline", v)}
              placeholder="e.g. Full-Stack Developer | Open to internships"
              disabled={saving}
            />
          </Field>

          <Field label="Bio" hint="A brief introduction about yourself.">
            <Textarea
              value={form.bio}
              onChange={(v) => set("bio", v)}
              placeholder="Tell recruiters who you are, what you are working on, and what you are looking for."
              rows={4}
              disabled={saving}
            />
          </Field>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <Field label="Location">
              <Input
                value={form.location}
                onChange={(v) => set("location", v)}
                placeholder="e.g. Conakry, Guinea"
                disabled={saving}
              />
            </Field>

            <Field label="Desired role">
              <Input
                value={form.desired_role}
                onChange={(v) => set("desired_role", v)}
                placeholder="e.g. Backend Developer"
                disabled={saving}
              />
            </Field>
          </div>

          <Field label="Experience level">
            <select
              value={form.experience_level}
              onChange={(e) => set("experience_level", e.target.value)}
              disabled={saving}
              className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50"
            >
              {EXPERIENCE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </Field>

          <Field label="LinkedIn URL">
            <Input
              value={form.linkedin_url}
              onChange={(v) => set("linkedin_url", v)}
              placeholder="https://linkedin.com/in/yourname"
              type="url"
              disabled={saving}
            />
          </Field>

          <Field label="GitHub URL">
            <Input
              value={form.github_url}
              onChange={(v) => set("github_url", v)}
              placeholder="https://github.com/yourname"
              type="url"
              disabled={saving}
            />
          </Field>

          <Field label="Website URL">
            <Input
              value={form.website_url}
              onChange={(v) => set("website_url", v)}
              placeholder="https://yourwebsite.com"
              type="url"
              disabled={saving}
            />
          </Field>

          <Field label="Visibility" hint="Control who can see your portfolio.">
            <div className="space-y-2">
              {VISIBILITY_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => set("visibility", opt.value)}
                  disabled={saving}
                  className={`w-full flex items-start gap-3 px-4 py-3 rounded-lg border text-left transition-colors disabled:opacity-50 ${
                    form.visibility === opt.value ? "border-primary bg-primary/5" : "hover:bg-muted"
                  }`}
                >
                  <div
                    className={`mt-0.5 w-4 h-4 rounded-full border-2 flex items-center justify-center shrink-0 ${
                      form.visibility === opt.value ? "border-primary" : "border-muted-foreground"
                    }`}
                  >
                    {form.visibility === opt.value && <div className="w-2 h-2 rounded-full bg-primary" />}
                  </div>
                  <div>
                    <p className="text-sm font-medium">{opt.label}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">{opt.description}</p>
                  </div>
                </button>
              ))}
            </div>
          </Field>

          <div className="flex justify-end pt-2">
            <button
              onClick={handleSaveProfile}
              disabled={saving || !dirty}
              className="px-6 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              {saving ? "Saving..." : "Save profile"}
            </button>
          </div>
        </SectionCard>

        <SkillsSection skills={skills} onSkillsChange={setSkills} />

        <ProjectsSection projects={projects} onProjectsChange={setProjects} />

        <div className="pb-10" />
      </main>
    </div>
  );
}
