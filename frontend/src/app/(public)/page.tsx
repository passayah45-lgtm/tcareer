import Link from "next/link";
import { Navbar } from "@/components/layout/Navbar";

const FEATURES = [
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
      </svg>
    ),
    title: "Structured learning paths",
    description: "13 career tracks built around real job requirements. Each track maps courses to the exact skills employers look for.",
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
      </svg>
    ),
    title: "AI tutor on every lesson",
    description: "Ask questions about any lesson and get clear explanations tailored to your level, available at any hour.",
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z" />
      </svg>
    ),
    title: "Verified certificates",
    description: "Every certificate has a public verification URL. Employers can confirm authenticity in seconds without contacting us.",
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 14.15v4.25c0 1.094-.787 2.036-1.872 2.18-2.087.277-4.216.42-6.378.42s-4.291-.143-6.378-.42c-1.085-.144-1.872-1.086-1.872-2.18v-4.25m16.5 0a2.18 2.18 0 00.75-1.661V8.706c0-1.081-.768-2.015-1.837-2.175a48.114 48.114 0 00-3.413-.387m4.5 8.006c-.194.165-.42.295-.673.38A23.978 23.978 0 0112 15.75c-2.648 0-5.195-.429-7.577-1.22a2.016 2.016 0 01-.673-.38m0 0A2.18 2.18 0 013 12.489V8.706c0-1.081.768-2.015 1.837-2.175a48.111 48.111 0 013.413-.387m7.5 0V5.25A2.25 2.25 0 0013.5 3h-3a2.25 2.25 0 00-2.25 2.25v.894m7.5 0a48.667 48.667 0 00-7.5 0M12 12.75h.008v.008H12v-.008z" />
      </svg>
    ),
    title: "Direct recruiter access",
    description: "Companies on the platform can view your public profile, certificates, and track progress. No middleman.",
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5M9 11.25v1.5M12 9v3.75m3-6v6" />
      </svg>
    ),
    title: "Real job listings",
    description: "Browse jobs posted by companies specifically looking for T-Career certified candidates.",
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0111.186 0z" />
      </svg>
    ),
    title: "Shareable public profile",
    description: "Your completed courses, certificates, and track progress are all visible on a single shareable profile page.",
  },
];

const STEPS = [
  {
    number: "01",
    title: "Choose a career track",
    description: "Pick from 13 tracks across tech, data, design, and business. Each track gives you a clear roadmap of what to learn and in what order.",
  },
  {
    number: "02",
    title: "Complete courses with AI support",
    description: "Watch lessons, ask the AI tutor when you get stuck, and take a quiz at the end. No time limit. Learn at your own pace.",
  },
  {
    number: "03",
    title: "Earn certificates and get hired",
    description: "Pass the quiz to earn a verified certificate. Share your profile with recruiters or apply directly to jobs listed on the platform.",
  },
];

const STATS = [
  { value: "20+", label: "Courses" },
  { value: "13", label: "Career tracks" },
  { value: "8", label: "Job listings" },
  { value: "100%", label: "Free to start" },
];

const TRACK_CATEGORIES = [
  { name: "Backend Developer", color: "#6366f1", slug: "backend-developer" },
  { name: "Frontend Developer", color: "#6366f1", slug: "frontend-developer" },
  { name: "Data Analyst", color: "#8b5cf6", slug: "data-analyst" },
  { name: "Machine Learning Engineer", color: "#8b5cf6", slug: "ml-engineer" },
  { name: "UI/UX Designer", color: "#ec4899", slug: "ui-ux-designer" },
  { name: "DevOps Engineer", color: "#6366f1", slug: "devops-engineer" },
];

export default function LandingPage() {
  return (
    <>
      <Navbar />
      <main className="min-h-screen">

        {/* Hero section */}
        <section className="relative overflow-hidden bg-gradient-to-br from-primary/5 via-background to-background pt-16 pb-20 md:pt-24 md:pb-28">
          <div className="absolute inset-0 bg-grid-pattern opacity-30 pointer-events-none" />
          <div className="max-w-5xl mx-auto px-4 sm:px-6 text-center relative">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-primary/10 text-primary rounded-full text-xs font-medium mb-6 border border-primary/20">
              <span className="w-1.5 h-1.5 bg-primary rounded-full" />
              Now with AI-powered career guidance
            </div>
            <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight text-foreground mb-6 leading-tight">
              Learn skills.{" "}
              <span className="text-primary">Earn certificates.</span>
              <br />
              Get hired.
            </h1>
            <p className="text-lg md:text-xl text-muted-foreground mb-10 max-w-2xl mx-auto leading-relaxed">
              T-Career connects structured learning, verified credentials, and real job
              opportunities in one place. Start a career track today.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Link
                href="/tracks"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary-600 active:bg-primary-700 transition-colors duration-150 text-sm"
              >
                Browse career tracks
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                </svg>
              </Link>
              <Link
                href="/courses"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-background text-foreground border border-border rounded-lg font-medium hover:bg-muted transition-colors duration-150 text-sm"
              >
                Browse courses
              </Link>
            </div>
          </div>
        </section>

        {/* Stats bar */}
        <section className="border-y border-border bg-muted/30">
          <div className="max-w-4xl mx-auto px-4 py-8">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {STATS.map((stat) => (
                <div key={stat.label} className="text-center">
                  <div className="text-2xl md:text-3xl font-bold text-primary">{stat.value}</div>
                  <div className="text-xs text-muted-foreground mt-0.5">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Career tracks preview */}
        <section className="py-16 md:py-20">
          <div className="max-w-6xl mx-auto px-4 sm:px-6">
            <div className="flex items-end justify-between mb-8">
              <div>
                <h2 className="text-2xl md:text-3xl font-bold tracking-tight">Career tracks</h2>
                <p className="text-muted-foreground mt-1.5 text-sm">
                  Structured learning paths built around real job requirements.
                </p>
              </div>
              <Link href="/tracks" className="text-sm text-primary hover:text-primary-600 font-medium transition-colors hidden sm:block">
                View all tracks
              </Link>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {TRACK_CATEGORIES.map((track) => (
                <Link
                  key={track.slug}
                  href={`/tracks/${track.slug}`}
                  className="group flex items-center gap-4 p-4 bg-card border border-border rounded-xl hover:shadow-md hover:-translate-y-0.5 transition-all duration-200"
                >
                  <div
                    className="w-10 h-10 rounded-lg flex items-center justify-center text-white text-sm font-bold flex-shrink-0"
                    style={{ backgroundColor: track.color }}
                  >
                    {track.name.charAt(0)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm truncate group-hover:text-primary transition-colors">
                      {track.name}
                    </p>
                    <p className="text-xs text-muted-foreground mt-0.5">Career track</p>
                  </div>
                  <svg className="w-4 h-4 text-muted-foreground group-hover:text-primary group-hover:translate-x-0.5 transition-all flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                  </svg>
                </Link>
              ))}
            </div>
            <div className="text-center mt-6 sm:hidden">
              <Link href="/tracks" className="text-sm text-primary hover:text-primary-600 font-medium">
                View all 13 tracks
              </Link>
            </div>
          </div>
        </section>

        {/* How it works */}
        <section className="py-16 md:py-20 bg-muted/30 border-y border-border">
          <div className="max-w-4xl mx-auto px-4 sm:px-6">
            <div className="text-center mb-12">
              <h2 className="text-2xl md:text-3xl font-bold tracking-tight">How T-Career works</h2>
              <p className="text-muted-foreground mt-2 text-sm max-w-xl mx-auto">
                From zero to hired in three steps.
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {STEPS.map((step) => (
                <div key={step.number} className="relative">
                  <div className="text-5xl font-bold text-primary/10 mb-3 leading-none">
                    {step.number}
                  </div>
                  <h3 className="font-semibold text-base mb-2">{step.title}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">{step.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Features grid */}
        <section className="py-16 md:py-20">
          <div className="max-w-6xl mx-auto px-4 sm:px-6">
            <div className="text-center mb-12">
              <h2 className="text-2xl md:text-3xl font-bold tracking-tight">Everything in one place</h2>
              <p className="text-muted-foreground mt-2 text-sm max-w-xl mx-auto">
                Most platforms do one thing. T-Career takes you from your first lesson to your first job.
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
              {FEATURES.map((feature) => (
                <div key={feature.title} className="bg-card border border-border rounded-xl p-5">
                  <div className="w-10 h-10 bg-primary/10 text-primary rounded-lg flex items-center justify-center mb-4">
                    {feature.icon}
                  </div>
                  <h3 className="font-semibold text-sm mb-1.5">{feature.title}</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Recruiter CTA */}
        <section className="py-16 md:py-20 bg-primary">
          <div className="max-w-3xl mx-auto px-4 sm:px-6 text-center">
            <h2 className="text-2xl md:text-3xl font-bold text-white mb-3">
              Hiring tech talent?
            </h2>
            <p className="text-primary-foreground/80 mb-8 text-sm max-w-lg mx-auto leading-relaxed">
              T-Career candidates have completed structured learning tracks and earned
              verified certificates. Every profile is public and verifiable.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Link
                href="/recruit"
                className="inline-flex items-center justify-center px-6 py-3 bg-white text-primary rounded-lg font-medium hover:bg-primary-50 transition-colors duration-150 text-sm"
              >
                Join recruiter waitlist
              </Link>
              <Link
                href="/jobs"
                className="inline-flex items-center justify-center px-6 py-3 bg-primary-700 text-white rounded-lg font-medium hover:bg-primary-900 transition-colors duration-150 text-sm border border-primary-foreground/20"
              >
                View job listings
              </Link>
            </div>
          </div>
        </section>

        {/* Bottom CTA */}
        <section className="py-16 md:py-20">
          <div className="max-w-2xl mx-auto px-4 sm:px-6 text-center">
            <h2 className="text-2xl md:text-3xl font-bold tracking-tight mb-3">
              Start learning today
            </h2>
            <p className="text-muted-foreground text-sm mb-8 leading-relaxed">
              Create a free account, choose your career track, and start your first
              course in under 5 minutes. No credit card required to get started.
            </p>
            <Link
              href="/register"
              className="inline-flex items-center justify-center gap-2 px-8 py-3.5 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary-600 transition-colors duration-150"
            >
              Create free account
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
            </Link>
          </div>
        </section>

      </main>
    </>
  );
}
