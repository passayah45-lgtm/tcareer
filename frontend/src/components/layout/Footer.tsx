import Link from "next/link";

const FOOTER_GROUPS = [
  {
    title: "Company",
    links: [
      { label: "Blog", href: "/blog" },
      { label: "About us", href: "/about" },
      { label: "Careers", href: "/careers" },
      { label: "Contact", href: "/contact" },
      { label: "Security", href: "/security" },
      { label: "Accessibility", href: "/accessibility" },
    ],
  },
  {
    title: "Learning",
    links: [
      { label: "Courses", href: "/courses" },
      { label: "Career tracks", href: "/tracks" },
      { label: "Certificates", href: "/certificates" },
      { label: "AI tutor", href: "/ai" },
    ],
  },
  {
    title: "Career",
    links: [
      { label: "Jobs", href: "/jobs" },
      { label: "Resume builder", href: "/resumes" },
      { label: "Portfolio", href: "/portfolio" },
      { label: "Career profile", href: "/career-profile" },
    ],
  },
  {
    title: "For partners",
    links: [
      { label: "For recruiters", href: "/recruit" },
      { label: "For companies", href: "/organization" },
      { label: "For universities", href: "/organization" },
      { label: "Organization console", href: "/organization/dashboard" },
    ],
  },
  {
    title: "Trust & support",
    links: [
      { label: "Help centre", href: "/help" },
      { label: "Certificate verification", href: "/verify" },
      { label: "Privacy policy", href: "/privacy" },
      { label: "Terms of service", href: "/terms" },
    ],
  },
];

export function Footer() {
  return (
    <footer className="border-t border-primary/30 bg-[#6366f1] text-white">
      <div className="mx-auto max-w-7xl px-4 py-7 sm:px-6 lg:px-8">
        <div className="grid gap-6 md:grid-cols-3 xl:grid-cols-[1.25fr_repeat(5,1fr)]">
          <div>
            <Link href="/" className="text-xl font-bold tracking-tight text-white">
              T-Career
            </Link>
            <p className="mt-3 max-w-xs text-xs leading-6 text-white/85">
              Learn in-demand skills, build your career profile, earn verified certificates, and connect with employers.
            </p>
          </div>

          {FOOTER_GROUPS.map((group) => (
            <div key={group.title}>
              <h2 className="text-xs font-semibold text-white">{group.title}</h2>
              <div className="mt-3 space-y-2">
                {group.links.map((link) => (
                  <Link key={link.href + link.label} href={link.href} className="block text-xs text-white/85 transition-colors hover:text-white">
                    {link.label}
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-7 flex flex-col gap-2 border-t border-white/20 pt-4 text-[11px] text-white/75 sm:flex-row sm:items-center sm:justify-between">
          <p>{new Date().getFullYear()} T-Career. All rights reserved.</p>
          <p>Learning, hiring, trust, and career growth in one platform.</p>
        </div>
      </div>
    </footer>
  );
}
