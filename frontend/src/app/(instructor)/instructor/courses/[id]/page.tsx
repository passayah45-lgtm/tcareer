"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import { InstructorGuard } from "@/components/shared/InstructorGuard";
import { toast, ToastContainer } from "@/components/shared/Toast";
import {
  getCourseById,
  updateCourse,
  publishCourse,
  deleteCourse,
  getLessons,
  createLesson,
  inlineUpdateLesson,
  reorderLessons,
  getUploadUrl,
  confirmUpload,
  uploadVideoToS3,
} from "@/lib/api/courses.api";
import {
  getInstructorQuizQuestions,
  bulkCreateQuestions,
  deleteQuestion,
} from "@/lib/api/assessments.api";
import type { Course, Lesson } from "@/types/course.types";
import type { QuizQuestion } from "@/lib/api/assessments.api";

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "fr", label: "French" },
  { code: "ar", label: "Arabic" },
  { code: "es", label: "Spanish" },
  { code: "pt", label: "Portuguese" },
  { code: "de", label: "German" },
  { code: "zh", label: "Chinese (Mandarin)" },
  { code: "hi", label: "Hindi" },
  { code: "ru", label: "Russian" },
  { code: "ja", label: "Japanese" },
  { code: "ko", label: "Korean" },
  { code: "it", label: "Italian" },
  { code: "tr", label: "Turkish" },
  { code: "nl", label: "Dutch" },
  { code: "id", label: "Indonesian" },
];

type Tab = "overview" | "curriculum" | "quiz" | "settings";

function TabBar({ active, onChange }: { active: Tab; onChange: (t: Tab) => void }) {
  const tabs: { id: Tab; label: string }[] = [
    { id: "overview", label: "Overview" },
    { id: "curriculum", label: "Curriculum" },
    { id: "quiz", label: "Quiz" },
    { id: "settings", label: "Settings" },
  ];
  return (
    <div className="flex border-b border-border mb-6 overflow-x-auto scrollbar-hide">
      {tabs.map((t) => (
        <button
          key={t.id}
          onClick={() => onChange(t.id)}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 -mb-px whitespace-nowrap transition-all duration-150 ${
            active === t.id
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
          }`}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}

function Field({ label, children, hint }: { label: string; children: React.ReactNode; hint?: string }) {
  return (
    <div className="space-y-1.5">
      <label className="block text-sm font-medium">{label}</label>
      {children}
      {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}

function SaveButton({ saving, onClick, label = "Save changes" }: { saving: boolean; onClick: () => void; label?: string }) {
  return (
    <button
      onClick={onClick}
      disabled={saving}
      className="h-9 px-4 inline-flex items-center gap-2 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary-600 disabled:opacity-50 transition-colors"
    >
      {saving ? (
        <>
          <svg className="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Saving...
        </>
      ) : label}
    </button>
  );
}

// Overview Tab
function OverviewTab({ course, onUpdated }: { course: Course; onUpdated: (c: Course) => void }) {
  const [form, setForm] = useState({
    title: course.title,
    short_description: course.short_description,
    description: course.description,
    level: course.level,
    price: course.price,
    language: course.language,
  });
  const [saving, setSaving] = useState(false);

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleSave() {
    setSaving(true);
    try {
      const updated = await updateCourse(course.id, form);
      onUpdated(updated);
      toast("Course details saved.");
    } catch {
      toast("Failed to save changes.", "error");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-5 max-w-2xl">
      <Field label="Course title">
        <input name="title" value={form.title} onChange={handleChange}
          className="w-full h-10 px-3 text-sm rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-colors"
          placeholder="e.g. Python for Data Analysis" />
      </Field>
      <Field label="Short description" hint="Shown on course cards. Max 500 characters.">
        <textarea name="short_description" value={form.short_description} onChange={handleChange}
          rows={2} maxLength={500}
          className="w-full px-3 py-2 text-sm rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-none transition-colors"
          placeholder="One or two sentences about what students will learn." />
      </Field>
      <Field label="Full description" hint="Shown on the course detail page.">
        <textarea name="description" value={form.description} onChange={handleChange}
          rows={6}
          className="w-full px-3 py-2 text-sm rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-y transition-colors"
          placeholder="Describe what students will build, what skills they will gain, and who the course is for." />
      </Field>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Field label="Level">
          <select name="level" value={form.level} onChange={handleChange}
            className="w-full h-10 px-3 text-sm rounded-lg border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring transition-colors">
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>
        </Field>
        <Field label="Price (USD)" hint="Set 0 for free.">
          <input name="price" type="number" step="0.01" min="0" max="999" value={form.price} onChange={handleChange}
            className="w-full h-10 px-3 text-sm rounded-lg border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring transition-colors" />
        </Field>
        <Field label="Language">
          <select name="language" value={form.language} onChange={handleChange}
            className="w-full h-10 px-3 text-sm rounded-lg border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring transition-colors">
            {LANGUAGES.map((l) => (
              <option key={l.code} value={l.code}>{l.label}</option>
            ))}
          </select>
        </Field>
      </div>
      <div className="pt-2">
        <SaveButton saving={saving} onClick={handleSave} />
      </div>
    </div>
  );
}

// Lesson Row Component
function LessonRow({ lesson, courseId, onUpdated }: { lesson: Lesson; courseId: string; onUpdated: (l: Lesson) => void }) {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(lesson.title);
  const [content, setContent] = useState(lesson.content);
  const [saving, setSaving] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadState, setUploadState] = useState<"idle" | "uploading" | "processing" | "done" | "error">("idle");
  const fileRef = useRef<HTMLInputElement>(null);

  async function saveLesson() {
    if (title === lesson.title && content === lesson.content) { setEditing(false); return; }
    setSaving(true);
    try {
      const updated = await inlineUpdateLesson(lesson.id, { title, content });
      onUpdated(updated);
      toast("Lesson saved.");
      setEditing(false);
    } catch {
      toast("Failed to save lesson.", "error");
    } finally {
      setSaving(false);
    }
  }

  async function togglePublish() {
    try {
      const updated = await inlineUpdateLesson(lesson.id, { is_published: !lesson.is_published });
      onUpdated(updated);
      toast(updated.is_published ? "Lesson published." : "Lesson unpublished.");
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      toast(e?.response?.data?.detail || "Failed to update lesson.", "error");
    }
  }

  async function handleVideoUpload(file: File) {
    setUploadState("uploading");
    setUploadProgress(0);
    try {
      const { upload_url, key } = await getUploadUrl(courseId, lesson.id, file.name, file.type);
      await uploadVideoToS3(upload_url, file, setUploadProgress);
      setUploadState("processing");
      await confirmUpload(courseId, lesson.id, key, file.size);
      setUploadState("done");
      toast("Video uploaded. Transcoding started.");
    } catch {
      setUploadState("error");
      toast("Video upload failed.", "error");
    }
  }

  return (
    <div className="border border-border rounded-xl bg-card">
      <div className="flex items-center gap-3 p-4">
        <div className="flex-shrink-0 text-muted-foreground/30">
          {lesson.lesson_type === "video" ? (
            <svg className="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z" />
            </svg>
          ) : (
            <svg className="w-4 h-4 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
          )}
        </div>
        <div className="flex-1 min-w-0">
          {editing ? (
            <input value={title} onChange={(e) => setTitle(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && saveLesson()}
              className="w-full h-8 px-2 text-sm rounded border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              autoFocus />
          ) : (
            <p className="text-sm font-medium truncate">{lesson.title}</p>
          )}
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {lesson.is_free_preview && (
            <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">Preview</span>
          )}
          <span className={`text-xs px-2 py-0.5 rounded-full ${lesson.is_published ? "bg-emerald-50 text-emerald-700" : "bg-muted text-muted-foreground"}`}>
            {lesson.is_published ? "Published" : "Draft"}
          </span>
          {editing ? (
            <>
              <button onClick={saveLesson} disabled={saving}
                className="h-7 px-2.5 text-xs font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary-600 disabled:opacity-50 transition-colors">
                {saving ? "Saving..." : "Save"}
              </button>
              <button onClick={() => { setEditing(false); setTitle(lesson.title); setContent(lesson.content); }}
                className="h-7 px-2.5 text-xs border border-border rounded-md hover:bg-muted transition-colors">
                Cancel
              </button>
            </>
          ) : (
            <>
              <button onClick={() => setEditing(true)}
                className="h-7 px-2.5 text-xs border border-border rounded-md hover:bg-muted transition-colors">
                Edit
              </button>
              <button onClick={togglePublish}
                className="h-7 px-2.5 text-xs border border-border rounded-md hover:bg-muted transition-colors">
                {lesson.is_published ? "Unpublish" : "Publish"}
              </button>
            </>
          )}
        </div>
      </div>
      {editing && (
        <div className="border-t border-border p-4 space-y-3">
          <Field label="Content">
            <textarea value={content} onChange={(e) => setContent(e.target.value)} rows={5}
              className="w-full px-3 py-2 text-sm rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-y transition-colors"
              placeholder="Write the lesson content. Markdown is supported." />
          </Field>
          {lesson.lesson_type === "video" && (
            <div>
              <input ref={fileRef} type="file" accept="video/*" className="hidden"
                onChange={(e) => { const f = e.target.files?.[0]; if (f) handleVideoUpload(f); }} />
              {uploadState === "idle" && (
                <div
                  onClick={() => fileRef.current?.click()}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    const file = e.dataTransfer.files?.[0];
                    if (file && file.type.startsWith("video/")) handleVideoUpload(file);
                  }}
                  className="flex flex-col items-center justify-center gap-2 border-2 border-dashed border-border rounded-xl p-6 cursor-pointer hover:border-primary hover:bg-primary/5 transition-all duration-200 group"
                >
                  <svg className="w-8 h-8 text-muted-foreground group-hover:text-primary transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                  </svg>
                  <div className="text-center">
                    <p className="text-sm font-medium">{lesson.video ? "Replace video" : "Upload video"}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">Drag and drop or click to browse</p>
                    <p className="text-xs text-muted-foreground">MP4, MOV, AVI up to 2GB</p>
                  </div>
                </div>
              )}
              {uploadState === "uploading" && (
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground">Uploading... {uploadProgress}%</p>
                  <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                    <div className="h-full bg-primary rounded-full transition-all duration-300" style={{ width: `${uploadProgress}%` }} />
                  </div>
                </div>
              )}
              {uploadState === "processing" && <p className="text-xs text-amber-600">Transcoding in progress...</p>}
              {uploadState === "done" && <p className="text-xs text-emerald-600">Video uploaded successfully.</p>}
              {uploadState === "error" && (
                <div className="flex items-center gap-2">
                  <p className="text-xs text-destructive">Upload failed.</p>
                  <button onClick={() => { setUploadState("idle"); setUploadProgress(0); }}
                    className="text-xs text-primary hover:underline">Try again</button>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Curriculum Tab
function CurriculumTab({ course, lessons, setLessons }: { course: Course; lessons: Lesson[]; setLessons: React.Dispatch<React.SetStateAction<Lesson[]>> }) {
  const [addingLesson, setAddingLesson] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newType, setNewType] = useState<"video" | "text">("video");
  const [saving, setSaving] = useState(false);
  const [reordering, setReordering] = useState(false);
  const [draggedId, setDraggedId] = useState<string | null>(null);
  const [dragOverId, setDragOverId] = useState<string | null>(null);

  async function addLesson() {
    if (!newTitle.trim()) return;
    setSaving(true);
    try {
      const maxPos = lessons.reduce((m, l) => Math.max(m, l.position), 0);
      const lesson = await createLesson(course.id, { title: newTitle.trim(), lesson_type: newType, position: maxPos + 10, is_published: false });
      setLessons((prev) => [...prev, lesson]);
      setNewTitle("");
      setAddingLesson(false);
      toast("Lesson added.");
    } catch {
      toast("Failed to add lesson.", "error");
    } finally {
      setSaving(false);
    }
  }

  async function handleDrop(targetId: string) {
    if (!draggedId || draggedId === targetId) { setDraggedId(null); setDragOverId(null); return; }
    const fromIndex = lessons.findIndex((l) => l.id === draggedId);
    const toIndex = lessons.findIndex((l) => l.id === targetId);
    if (fromIndex === -1 || toIndex === -1) return;
    const reordered = [...lessons];
    const [moved] = reordered.splice(fromIndex, 1);
    reordered.splice(toIndex, 0, moved);
    const withPositions = reordered.map((l, i) => ({ ...l, position: (i + 1) * 10 }));
    setLessons(withPositions);
    setDraggedId(null);
    setDragOverId(null);
    setReordering(true);
    try {
      await reorderLessons(course.id, withPositions.map((l) => ({ id: l.id, position: l.position })));
      toast("Lesson order saved.");
    } catch {
      toast("Failed to save order.", "error");
      setLessons(lessons);
    } finally {
      setReordering(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-semibold">Curriculum</h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            {lessons.length} lesson{lessons.length !== 1 ? "s" : ""}
            {reordering && " · Saving order..."}
          </p>
        </div>
        <button onClick={() => setAddingLesson(true)}
          className="h-9 px-4 inline-flex items-center gap-2 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary-600 transition-colors">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          Add lesson
        </button>
      </div>

      {addingLesson && (
        <div className="border border-primary/30 bg-primary/5 rounded-xl p-4 space-y-3">
          <h3 className="text-sm font-semibold">New lesson</h3>
          <div className="flex gap-3">
            <input value={newTitle} onChange={(e) => setNewTitle(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addLesson()}
              placeholder="Lesson title" autoFocus
              className="flex-1 h-9 px-3 text-sm rounded-lg border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring transition-colors" />
            <select value={newType} onChange={(e) => setNewType(e.target.value as "video" | "text")}
              className="h-9 px-3 text-sm rounded-lg border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring transition-colors">
              <option value="video">Video</option>
              <option value="text">Text</option>
            </select>
          </div>
          <div className="flex gap-2">
            <SaveButton saving={saving} onClick={addLesson} label="Add lesson" />
            <button onClick={() => { setAddingLesson(false); setNewTitle(""); }}
              className="h-9 px-4 text-sm border border-border rounded-lg hover:bg-muted transition-colors">
              Cancel
            </button>
          </div>
        </div>
      )}

      {lessons.length === 0 && !addingLesson ? (
        <div className="border border-border rounded-xl p-8 text-center bg-card">
          <p className="text-sm text-muted-foreground mb-3">No lessons yet.</p>
          <button onClick={() => setAddingLesson(true)}
            className="inline-flex items-center h-9 px-4 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary-600 transition-colors">
            Add first lesson
          </button>
        </div>
      ) : lessons.length > 0 && (
        <p className="text-xs text-muted-foreground">Drag to reorder lessons.</p>
      )}

      <div className="space-y-2">
        {lessons.map((lesson) => (
          <div key={lesson.id} draggable
            onDragStart={() => setDraggedId(lesson.id)}
            onDragOver={(e) => { e.preventDefault(); setDragOverId(lesson.id); }}
            onDrop={() => handleDrop(lesson.id)}
            onDragEnd={() => { setDraggedId(null); setDragOverId(null); }}
            className={`transition-all duration-150 ${dragOverId === lesson.id && draggedId !== lesson.id ? "ring-2 ring-primary rounded-xl" : ""} ${draggedId === lesson.id ? "opacity-50" : ""}`}>
            <LessonRow lesson={lesson} courseId={course.id}
              onUpdated={(updated) => setLessons((prev) => prev.map((l) => (l.id === updated.id ? updated : l)))} />
          </div>
        ))}
      </div>
    </div>
  );
}

// Quiz Tab
interface QuestionForm {
  question_text: string;
  options: [string, string, string, string];
  correct_index: number;
  explanation: string;
}

function emptyQuestion(): QuestionForm {
  return { question_text: "", options: ["", "", "", ""], correct_index: 0, explanation: "" };
}

function QuizTab({ course }: { course: Course }) {
  const [questions, setQuestions] = useState<QuizQuestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [forms, setForms] = useState<QuestionForm[]>([emptyQuestion()]);
  const [saving, setSaving] = useState(false);
  const [replacing, setReplacing] = useState(false);

  useEffect(() => {
    getInstructorQuizQuestions(course.id).then(setQuestions).catch(() => {}).finally(() => setLoading(false));
  }, [course.id]);

  function updateOption(qi: number, oi: number, value: string) {
    setForms((prev) => {
      const next = [...prev];
      next[qi] = { ...next[qi], options: next[qi].options.map((o, i) => (i === oi ? value : o)) as [string, string, string, string] };
      return next;
    });
  }

  async function saveQuestions() {
    const valid = forms.filter((f) => f.question_text.trim().length >= 5);
    if (valid.length === 0) { toast("Add at least one question with 5+ characters.", "error"); return; }
    setSaving(true);
    try {
      const result = await bulkCreateQuestions(course.id, {
        questions: valid.map((f) => ({ question_text: f.question_text, options: f.options, correct_index: f.correct_index, explanation: f.explanation })),
        replace: replacing,
      });
      setQuestions(result.questions);
      setForms([emptyQuestion()]);
      setReplacing(false);
      toast(`${result.total} question${result.total !== 1 ? "s" : ""} saved.`);
    } catch {
      toast("Failed to save questions.", "error");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(questionId: string) {
    try {
      await deleteQuestion(course.id, questionId);
      setQuestions((prev) => prev.filter((q) => q.id !== questionId));
      toast("Question deleted.");
    } catch {
      toast("Failed to delete question.", "error");
    }
  }

  return (
    <div className="space-y-6">
      {loading ? (
        <div className="space-y-2">{[...Array(3)].map((_, i) => <div key={i} className="h-16 bg-muted rounded-xl animate-pulse" />)}</div>
      ) : questions.length > 0 ? (
        <div>
          <h2 className="font-semibold mb-3">Existing questions <span className="text-xs text-muted-foreground font-normal">({questions.length})</span></h2>
          <div className="space-y-2">
            {questions.map((q, i) => (
              <div key={q.id} className="border border-border rounded-xl p-4 bg-card">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium">{i + 1}. {q.question_text}</p>
                    <div className="mt-2 grid grid-cols-2 gap-1">
                      {q.options.map((opt, oi) => (
                        <p key={oi} className={`text-xs px-2 py-1 rounded ${oi === q.correct_index ? "bg-emerald-50 text-emerald-700 font-medium" : "text-muted-foreground"}`}>
                          {["A", "B", "C", "D"][oi]}. {opt}
                        </p>
                      ))}
                    </div>
                  </div>
                  <button onClick={() => handleDelete(q.id)}
                    className="flex-shrink-0 h-7 w-7 inline-flex items-center justify-center text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-lg transition-colors">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="border border-border rounded-xl p-8 text-center bg-card">
          <p className="text-sm text-muted-foreground">No quiz questions yet. Add questions below.</p>
        </div>
      )}

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold">Add questions</h2>
          <button onClick={() => setForms((prev) => [...prev, emptyQuestion()])}
            className="h-8 px-3 inline-flex items-center gap-1.5 text-xs font-medium border border-border rounded-lg hover:bg-muted transition-colors">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            Add question
          </button>
        </div>

        {forms.map((form, qi) => (
          <div key={qi} className="border border-border rounded-xl p-4 space-y-3 bg-card">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-muted-foreground">Question {qi + 1}</p>
              {forms.length > 1 && (
                <button onClick={() => setForms((prev) => prev.filter((_, i) => i !== qi))}
                  className="h-6 w-6 inline-flex items-center justify-center text-muted-foreground hover:text-destructive rounded transition-colors">
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
            <textarea value={form.question_text}
              onChange={(e) => setForms((prev) => { const n = [...prev]; n[qi] = { ...n[qi], question_text: e.target.value }; return n; })}
              placeholder="Enter the question (min. 5 characters)" rows={2}
              className="w-full px-3 py-2 text-sm rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-none transition-colors" />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {form.options.map((opt, oi) => (
                <div key={oi} className="flex items-center gap-2">
                  <input type="radio" name={`correct-${qi}`} checked={form.correct_index === oi}
                    onChange={() => setForms((prev) => { const n = [...prev]; n[qi] = { ...n[qi], correct_index: oi }; return n; })}
                    className="w-4 h-4 text-primary flex-shrink-0" />
                  <input value={opt} onChange={(e) => updateOption(qi, oi, e.target.value)}
                    placeholder={`Option ${["A", "B", "C", "D"][oi]}`}
                    className={`flex-1 h-8 px-2.5 text-xs rounded-lg border focus:outline-none focus:ring-2 focus:ring-ring transition-colors ${form.correct_index === oi ? "border-emerald-400 bg-emerald-50 text-emerald-900" : "border-input bg-background"}`} />
                </div>
              ))}
            </div>
            <p className="text-xs text-muted-foreground">Select the radio button next to the correct answer.</p>
            <input value={form.explanation}
              onChange={(e) => setForms((prev) => { const n = [...prev]; n[qi] = { ...n[qi], explanation: e.target.value }; return n; })}
              placeholder="Explanation shown after answering (optional)"
              className="w-full h-8 px-3 text-xs rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-colors" />
          </div>
        ))}

        <div className="flex items-center gap-3 flex-wrap">
          <SaveButton saving={saving} onClick={saveQuestions} label="Save questions" />
          <label className="flex items-center gap-2 text-sm cursor-pointer select-none">
            <input type="checkbox" checked={replacing} onChange={(e) => setReplacing(e.target.checked)}
              className="w-4 h-4 rounded border-input text-primary focus:ring-ring" />
            Replace all existing questions
          </label>
        </div>
      </div>
    </div>
  );
}

// Settings Tab
function SettingsTab({ course, onUpdated }: { course: Course; onUpdated: (c: Course) => void }) {
  const router = useRouter();
  const [publishing, setPublishing] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [passThreshold, setPassThreshold] = useState(String(course.pass_threshold));
  const [saving, setSaving] = useState(false);

  async function handlePublish() {
    setPublishing(true);
    try {
      const updated = await publishCourse(course.id);
      onUpdated(updated);
      toast("Course published.");
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      toast(e?.response?.data?.detail || "Failed to publish.", "error");
    } finally {
      setPublishing(false);
    }
  }

  async function handleUnpublish() {
    setPublishing(true);
    try {
      const updated = await updateCourse(course.id, { status: "draft" });
      onUpdated(updated);
      toast("Course set back to draft.");
    } catch {
      toast("Failed to unpublish.", "error");
    } finally {
      setPublishing(false);
    }
  }

  async function handleDelete() {
    setDeleting(true);
    try {
      await deleteCourse(course.id);
      toast("Course deleted.");
      router.push("/instructor/courses");
    } catch {
      toast("Failed to delete course.", "error");
      setDeleting(false);
    }
  }

  async function saveThreshold() {
    const val = parseInt(passThreshold);
    if (isNaN(val) || val < 1 || val > 100) { toast("Pass threshold must be between 1 and 100.", "error"); return; }
    setSaving(true);
    try {
      const updated = await updateCourse(course.id, { pass_threshold: val } as Partial<Course>);
      onUpdated(updated);
      toast("Pass threshold saved.");
    } catch {
      toast("Failed to save threshold.", "error");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6 max-w-lg">
      <div className="border border-border rounded-xl p-5 bg-card">
        <h3 className="font-semibold mb-1 text-sm">Quiz pass threshold</h3>
        <p className="text-xs text-muted-foreground mb-3">Students must score at least this percentage to earn a certificate.</p>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <input type="number" min={1} max={100} value={passThreshold} onChange={(e) => setPassThreshold(e.target.value)}
              className="w-20 h-9 px-3 text-sm rounded-lg border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring transition-colors" />
            <span className="text-sm text-muted-foreground">%</span>
          </div>
          <SaveButton saving={saving} onClick={saveThreshold} label="Save" />
        </div>
      </div>

      <div className="border border-border rounded-xl p-5 bg-card">
        <h3 className="font-semibold mb-1 text-sm">Course visibility</h3>
        <p className="text-xs text-muted-foreground mb-3">Published courses appear in the catalog and are visible to all students.</p>
        <div className="flex items-center gap-3">
          <span className={`text-xs px-2.5 py-1 rounded-full font-medium capitalize border ${course.status === "published" ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-muted text-muted-foreground border-border"}`}>
            {course.status}
          </span>
          {course.status !== "published" ? (
            <button onClick={handlePublish} disabled={publishing}
              className="h-9 px-4 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary-600 disabled:opacity-50 transition-colors">
              {publishing ? "Publishing..." : "Publish course"}
            </button>
          ) : (
            <button onClick={handleUnpublish} disabled={publishing}
              className="h-9 px-4 text-sm font-medium border border-border rounded-lg hover:bg-muted disabled:opacity-50 transition-colors">
              {publishing ? "Updating..." : "Unpublish"}
            </button>
          )}
        </div>
      </div>

      <div className="border border-destructive/20 rounded-xl p-5 bg-destructive/5">
        <h3 className="font-semibold mb-1 text-sm text-destructive">Delete course</h3>
        <p className="text-xs text-muted-foreground mb-3">Archives the course. Enrolled students keep access. This cannot be undone.</p>
        {!confirmDelete ? (
          <button onClick={() => setConfirmDelete(true)}
            className="h-9 px-4 text-sm font-medium text-destructive border border-destructive/30 rounded-lg hover:bg-destructive/10 transition-colors">
            Delete course
          </button>
        ) : (
          <div className="space-y-2">
            <p className="text-sm font-medium text-destructive">Are you sure?</p>
            <div className="flex gap-2">
              <button onClick={handleDelete} disabled={deleting}
                className="h-9 px-4 text-sm font-medium bg-destructive text-destructive-foreground rounded-lg hover:bg-destructive/90 disabled:opacity-50 transition-colors">
                {deleting ? "Deleting..." : "Yes, delete"}
              </button>
              <button onClick={() => setConfirmDelete(false)}
                className="h-9 px-4 text-sm border border-border rounded-lg hover:bg-muted transition-colors">
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Main Page
export default function CourseBuilderPage({ params }: { params: { id: string } }) {
  const [course, setCourse] = useState<Course | null>(null);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>("overview");

  const load = useCallback(async () => {
    try {
      const [c, l] = await Promise.all([getCourseById(params.id), getLessons(params.id)]);
      setCourse(c);
      setLessons(l.sort((a, b) => a.position - b.position));
    } catch {
      toast("Failed to load course.", "error");
    } finally {
      setLoading(false);
    }
  }, [params.id]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  return (
    <InstructorGuard>
      <ToastContainer />
      <Navbar />
      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-6">
          <Link href="/instructor/courses" className="hover:text-foreground transition-colors">My courses</Link>
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
          </svg>
          <span className="text-foreground font-medium truncate">{loading ? "Loading..." : course?.title || "Course"}</span>
        </div>

        {loading ? (
          <div className="space-y-4">
            <div className="h-8 bg-muted rounded w-64 animate-pulse" />
            <div className="h-48 bg-muted rounded-xl animate-pulse" />
          </div>
        ) : !course ? (
          <div className="text-center py-16">
            <p className="text-muted-foreground mb-3">Course not found.</p>
            <Link href="/instructor/courses" className="text-sm text-primary hover:text-primary-600 transition-colors">Back to courses</Link>
          </div>
        ) : (
          <>
            <div className="mb-6">
              <div className="flex items-start gap-3 justify-between flex-wrap">
                <div>
                  <h1 className="text-xl md:text-2xl font-bold tracking-tight">{course.title}</h1>
                  <p className="text-sm text-muted-foreground mt-1 capitalize">
                    {course.level} · {course.language.toUpperCase()} · {lessons.length} lesson{lessons.length !== 1 ? "s" : ""}
                  </p>
                </div>
                <span className={`text-xs px-2.5 py-1 rounded-full font-medium capitalize border flex-shrink-0 ${
                  course.status === "published" ? "bg-emerald-50 text-emerald-700 border-emerald-200" :
                  course.status === "draft" ? "bg-amber-50 text-amber-700 border-amber-200" :
                  "bg-muted text-muted-foreground border-border"
                }`}>
                  {course.status}
                </span>
              </div>
            </div>
            <TabBar active={activeTab} onChange={setActiveTab} />
            {activeTab === "overview" && <OverviewTab course={course} onUpdated={setCourse} />}
            {activeTab === "curriculum" && <CurriculumTab course={course} lessons={lessons} setLessons={setLessons} />}
            {activeTab === "quiz" && <QuizTab course={course} />}
            {activeTab === "settings" && <SettingsTab course={course} onUpdated={setCourse} />}
          </>
        )}
      </main>
    </InstructorGuard>
  );
}
