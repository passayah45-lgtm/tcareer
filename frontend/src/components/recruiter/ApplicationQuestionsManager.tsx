"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import {
  createJobApplicationQuestion,
  deleteJobApplicationQuestion,
  getJobApplicationQuestions,
  updateJobApplicationQuestion,
} from "@/lib/api/recruiter.api";
import type { ApplicationQuestion, ApplicationQuestionPayload, ApplicationQuestionType } from "@/types/recruiter.types";

const QUESTION_TYPES: { value: ApplicationQuestionType; label: string }[] = [
  { value: "short_text", label: "Short text" },
  { value: "long_text", label: "Long text" },
  { value: "yes_no", label: "Yes / no" },
  { value: "multiple_choice", label: "Multiple choice" },
  { value: "number", label: "Number" },
  { value: "url", label: "URL" },
];

const emptyForm: ApplicationQuestionPayload = {
  question_text: "",
  question_type: "short_text",
  is_required: false,
  choices: [],
  position: 0,
};

interface Props {
  organizationId: string;
  jobId: string;
}

export function ApplicationQuestionsManager({ organizationId, jobId }: Props) {
  const [questions, setQuestions] = useState<ApplicationQuestion[]>([]);
  const [form, setForm] = useState<ApplicationQuestionPayload>(emptyForm);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const sortedQuestions = useMemo(
    () => [...questions].sort((a, b) => a.position - b.position || a.question_text.localeCompare(b.question_text)),
    [questions],
  );

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setQuestions(await getJobApplicationQuestions(organizationId, jobId));
      setError("");
    } catch {
      setError("Unable to load application questions.");
    } finally {
      setLoading(false);
    }
  }, [jobId, organizationId]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  function resetForm() {
    setForm({ ...emptyForm, position: questions.length });
    setEditingId(null);
  }

  function editQuestion(question: ApplicationQuestion) {
    setEditingId(question.id);
    setForm({
      question_text: question.question_text,
      question_type: question.question_type,
      is_required: question.is_required,
      choices: question.choices,
      position: question.position,
      is_active: question.is_active,
    });
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const payload = {
        ...form,
        choices: form.question_type === "multiple_choice" ? form.choices : [],
        position: Number(form.position || 0),
      };
      if (editingId) await updateJobApplicationQuestion(organizationId, jobId, editingId, payload);
      else await createJobApplicationQuestion(organizationId, jobId, payload);
      resetForm();
      await load();
    } catch {
      setError("Unable to save application question.");
    } finally {
      setSaving(false);
    }
  }

  async function remove(questionId: string) {
    setSaving(true);
    try {
      await deleteJobApplicationQuestion(organizationId, jobId, questionId);
      await load();
    } catch {
      setError("Unable to remove application question.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="border border-border rounded-xl bg-card p-6">
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="font-semibold">Application questions</h2>
          <p className="text-sm text-muted-foreground">Collect structured answers before candidates submit.</p>
        </div>
        {editingId && (
          <button type="button" className="btn-sm btn-secondary" onClick={resetForm}>
            New question
          </button>
        )}
      </div>

      {error && <div className="alert-error mt-4">{error}</div>}

      <form onSubmit={submit} className="mt-5 grid gap-3">
        <label className="grid gap-1 text-sm">
          <span className="font-medium">Question</span>
          <input
            className="input"
            value={form.question_text}
            onChange={(event) => setForm((current) => ({ ...current, question_text: event.target.value }))}
            required
          />
        </label>
        <div className="grid gap-3 md:grid-cols-4">
          <label className="grid gap-1 text-sm md:col-span-2">
            <span className="font-medium">Type</span>
            <select
              className="input"
              value={form.question_type}
              onChange={(event) => setForm((current) => ({ ...current, question_type: event.target.value as ApplicationQuestionType }))}
            >
              {QUESTION_TYPES.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm">
            <span className="font-medium">Position</span>
            <input
              className="input"
              type="number"
              min={0}
              value={form.position ?? 0}
              onChange={(event) => setForm((current) => ({ ...current, position: Number(event.target.value) }))}
            />
          </label>
          <label className="flex items-end gap-2 text-sm pb-2">
            <input
              type="checkbox"
              checked={form.is_required}
              onChange={(event) => setForm((current) => ({ ...current, is_required: event.target.checked }))}
            />
            <span>Required</span>
          </label>
        </div>
        {form.question_type === "multiple_choice" && (
          <label className="grid gap-1 text-sm">
            <span className="font-medium">Choices</span>
            <input
              className="input"
              value={(form.choices || []).join(", ")}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  choices: event.target.value.split(",").map((choice) => choice.trim()).filter(Boolean),
                }))
              }
              placeholder="Remote, Hybrid, Onsite"
              required
            />
          </label>
        )}
        <div>
          <button className="btn-primary" type="submit" disabled={saving}>
            {saving ? "Saving..." : editingId ? "Update question" : "Add question"}
          </button>
        </div>
      </form>

      <div className="mt-6 space-y-3">
        {loading ? (
          <div className="h-20 bg-muted rounded-xl animate-pulse" />
        ) : sortedQuestions.length === 0 ? (
          <div className="rounded-xl border border-dashed border-border p-5 text-sm text-muted-foreground">
            No custom application questions yet.
          </div>
        ) : (
          sortedQuestions.map((question) => (
            <div key={question.id} className="rounded-xl border border-border p-4">
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-medium text-sm">{question.question_text}</p>
                    {question.is_required && <span className="badge-primary">Required</span>}
                    {!question.is_active && <span className="badge">Inactive</span>}
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {QUESTION_TYPES.find((type) => type.value === question.question_type)?.label || question.question_type} · Position {question.position}
                  </p>
                  {question.choices.length > 0 && (
                    <p className="mt-2 text-xs text-muted-foreground">Choices: {question.choices.join(", ")}</p>
                  )}
                </div>
                <div className="flex gap-2">
                  <button type="button" className="btn-sm btn-secondary" onClick={() => editQuestion(question)}>
                    Edit
                  </button>
                  {question.is_active && (
                    <button type="button" className="btn-sm btn-secondary" disabled={saving} onClick={() => void remove(question.id)}>
                      Remove
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </section>
  );
}
