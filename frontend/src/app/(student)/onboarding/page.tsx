"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AxiosError } from "axios";
import { enrollInTrack } from "@/lib/api/tracks.api";

const CAREER_GOALS = [
  { slug: "backend-developer", title: "Backend Developer", icon: "⚙", color: "#6366f1", desc: "Build APIs and server-side apps" },
  { slug: "frontend-developer", title: "Frontend Developer", icon: "🖥", color: "#06b6d4", desc: "Build web interfaces with React" },
  { slug: "full-stack-developer", title: "Full Stack Developer", icon: "⚡", color: "#10b981", desc: "Build complete web applications" },
  { slug: "data-analyst", title: "Data Analyst", icon: "📊", color: "#0ea5e9", desc: "Analyse data and build dashboards" },
  { slug: "data-scientist", title: "Data Scientist", icon: "🔬", color: "#8b5cf6", desc: "Build predictive models" },
  { slug: "ai-engineer", title: "AI Engineer", icon: "🤖", color: "#f59e0b", desc: "Build AI-powered applications" },
  { slug: "ml-engineer", title: "ML Engineer", icon: "🧠", color: "#ef4444", desc: "Deploy ML systems at scale" },
  { slug: "devops-engineer", title: "DevOps Engineer", icon: "🔄", color: "#84cc16", desc: "Automate and scale infrastructure" },
  { slug: "cloud-engineer", title: "Cloud Engineer", icon: "☁", color: "#f97316", desc: "Design and manage cloud systems" },
  { slug: "cybersecurity-analyst", title: "Cybersecurity Analyst", icon: "🛡", color: "#dc2626", desc: "Protect systems from threats" },
  { slug: "product-manager", title: "Product Manager", icon: "🎯", color: "#7c3aed", desc: "Lead products from idea to launch" },
  { slug: "ui-ux-designer", title: "UI/UX Designer", icon: "✏", color: "#ec4899", desc: "Design beautiful interfaces" },
  { slug: "digital-marketer", title: "Digital Marketer", icon: "📈", color: "#059669", desc: "Grow businesses with digital strategy" },
];

export default function OnboardingPage() {
  const router = useRouter();
  const [selected, setSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<"goal" | "hours">("goal");
  const [hours, setHours] = useState<string>("10");

  async function handleStart() {
    if (!selected) return;
    setLoading(true);
    let shouldContinue = true;
    try {
      await enrollInTrack(selected);
    } catch (error) {
      if (error instanceof AxiosError && error.response?.status === 401) {
        shouldContinue = false;
        router.push("/login?next=/onboarding");
      }
      // Already enrolled or track not found - continue anyway
    } finally {
      if (shouldContinue) {
        // Store onboarding completion in localStorage
        localStorage.setItem("onboarding_completed", "true");
        router.push("/dashboard");
      }
      setLoading(false);
    }
  }

  if (step === "hours") {
    return (
      <div className="min-h-screen bg-muted/30 flex items-center justify-center px-4 py-8">
        <div className="max-w-md w-full">
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold mb-2">How much time can you dedicate?</h1>
            <p className="text-muted-foreground text-sm">
              This helps us estimate how long your track will take.
            </p>
          </div>

          <div className="bg-background border rounded-xl p-6 space-y-4">
            {[
              { value: "5", label: "5 hours per week", desc: "Casual learner" },
              { value: "10", label: "10 hours per week", desc: "Consistent learner" },
              { value: "20", label: "20 hours per week", desc: "Intensive learner" },
              { value: "40", label: "Full time", desc: "Dedicated bootcamp pace" },
            ].map((option) => (
              <button
                key={option.value}
                onClick={() => setHours(option.value)}
                className={`w-full text-left p-3 rounded-lg border transition-all ${
                  hours === option.value
                    ? "border-primary bg-primary/5"
                    : "hover:bg-muted"
                }`}
              >
                <p className="text-sm font-medium">{option.label}</p>
                <p className="text-xs text-muted-foreground">{option.desc}</p>
              </button>
            ))}

            <div className="flex gap-3 pt-2">
              <button
                onClick={() => setStep("goal")}
                className="flex-1 border rounded-lg py-2.5 text-sm hover:bg-muted transition-colors"
              >
                Back
              </button>
              <button
                onClick={handleStart}
                disabled={loading}
                className="flex-1 bg-primary text-primary-foreground rounded-lg py-2.5 text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                {loading ? "Setting up..." : "Start learning"}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-muted/30 py-8 px-4">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold mb-2">What is your career goal?</h1>
          <p className="text-muted-foreground text-sm">
            Select the role you want to work toward. We will build a personalised learning path for you.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-6">
          {CAREER_GOALS.map((goal) => (
            <button
              key={goal.slug}
              onClick={() => setSelected(goal.slug)}
              className={`text-left p-4 rounded-xl border transition-all ${
                selected === goal.slug
                  ? "border-primary bg-primary/5 shadow-sm"
                  : "bg-background hover:shadow-sm hover:border-primary/30"
              }`}
            >
              <div className="flex items-center gap-3 mb-1.5">
                <span className="text-xl">{goal.icon}</span>
                <span className="font-medium text-sm">{goal.title}</span>
              </div>
              <p className="text-xs text-muted-foreground">{goal.desc}</p>
            </button>
          ))}
        </div>

        <div className="flex justify-between items-center">
          <button
            onClick={() => {
              localStorage.setItem("onboarding_completed", "true");
              router.push("/dashboard");
            }}
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            Skip for now
          </button>
          <button
            onClick={() => selected && setStep("hours")}
            disabled={!selected}
            className="bg-primary text-primary-foreground px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            Continue
          </button>
        </div>
      </div>
    </div>
  );
}
