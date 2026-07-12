"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Navbar } from "@/components/layout/Navbar";
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

import { createCourse } from "@/lib/api/courses.api";
import type { CourseLevel } from "@/types/course.types";

interface CourseForm {
  title: string;
  short_description: string;
  level: CourseLevel;
  price: string;
  language: string;
}

export default function NewCoursePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState<CourseForm>({
    title: "",
    short_description: "",
    level: "beginner",
    price: "0.00",
    language: "en",
  });

  function handleChange(
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const course = await createCourse(form);
      router.push(`/instructor/courses/${course.id}`);
    } catch (err: unknown) {
      const apiErr = err as { response?: { data?: { errors?: Record<string, string> } } };
      const errors = apiErr?.response?.data?.errors;
      setError(errors?.title || errors?.detail || "Could not create course.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Navbar />
      <main className="max-w-2xl mx-auto px-4 py-8">
        <div className="mb-6">
          <Link
            href="/instructor/courses"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            Back to courses
          </Link>
          <h1 className="text-2xl font-bold mt-2">Create a new course</h1>
          <p className="text-sm text-muted-foreground mt-1">
            You can add lessons and publish it after creation.
          </p>
        </div>

        <div className="border rounded-xl p-6 bg-card">
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-destructive/10 text-destructive text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="text-sm font-medium block mb-1">
                Course title
              </label>
              <input
                name="title"
                value={form.title}
                onChange={handleChange}
                required
                minLength={5}
                maxLength={255}
                placeholder="e.g. Python for Data Analysis"
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 bg-background"
              />
            </div>

            <div>
              <label className="text-sm font-medium block mb-1">
                Short description
              </label>
              <textarea
                name="short_description"
                value={form.short_description}
                onChange={handleChange}
                rows={2}
                maxLength={500}
                placeholder="One or two sentences about what students will learn"
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 bg-background resize-none"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium block mb-1">Level</label>
                <select
                  name="level"
                  value={form.level}
                  onChange={handleChange}
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 bg-background"
                >
                  <option value="beginner">Beginner</option>
                  <option value="intermediate">Intermediate</option>
                  <option value="advanced">Advanced</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium block mb-1.5">Language</label>
                <select name="language" value={form.language} onChange={handleChange}
                  className="w-full h-10 border border-input rounded-lg px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring bg-background">
                  {LANGUAGES.map((l) => (<option key={l.code} value={l.code}>{l.label}</option>))}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium block mb-1">
                  Price (USD)
                </label>
                <input
                  name="price"
                  type="number"
                  step="0.01"
                  min="0"
                  max="999"
                  value={form.price}
                  onChange={handleChange}
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 bg-background"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Set to 0 for a free course
                </p>
              </div>
            </div>

            <div className="flex gap-3 pt-2">
              <button
                type="submit"
                disabled={loading || !form.title.trim()}
                className="bg-primary text-primary-foreground px-5 py-2 rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                {loading ? "Creating..." : "Create course"}
              </button>
              <Link
                href="/instructor/courses"
                className="border px-5 py-2 rounded-lg text-sm hover:bg-muted transition-colors"
              >
                Cancel
              </Link>
            </div>
          </form>
        </div>
      </main>
    </>
  );
}

