"use client";

import Link from "next/link";
import Image from "next/image";
import { useRouter, usePathname } from "next/navigation";
import { useState } from "react";
import { useAuthStore } from "@/stores/auth.store";
import { logout } from "@/lib/api/auth.api";
import { getCookie } from "@/lib/api/client";
import { getInitials } from "@/lib/utils";
import { NotificationBell } from "@/components/notifications/NotificationBell";

const NAV_LINKS = [
  { href: "/courses", label: "Courses" },
  { href: "/tracks", label: "Tracks" },
  { href: "/jobs", label: "Jobs" },
];

const RECRUITER_ROLES = new Set(["recruiter", "company_admin", "platform_admin", "super_admin", "admin"]);
const ORGANIZATION_ADMIN_ROLES = new Set(["company_admin", "university_admin", "platform_admin", "super_admin", "admin", "report_viewer", "export_manager", "department_manager", "team_manager", "cohort_manager"]);
const PLATFORM_ADMIN_ROLES = new Set(["platform_admin", "super_admin", "admin"]);

export function Navbar() {
  const { user, isAuthenticated, clearAuth } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();
  const [search, setSearch] = useState("");
  const [mobileOpen, setMobileOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  async function handleLogout() {
    try {
      const refresh = getCookie("tcareer_refresh") || "";
      await logout(refresh);
    } catch {
      /* proceed regardless */
    } finally {
      clearAuth();
      router.push("/login");
    }
  }

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (search.trim()) {
      router.push(`/search?q=${encodeURIComponent(search.trim())}`);
      setSearch("");
      setMobileOpen(false);
    }
  }

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-4">

          <Link href="/" className="flex-shrink-0 text-lg font-bold text-primary tracking-tight hover:opacity-80 transition-opacity">
            T-Career
          </Link>

          <div className="hidden md:flex items-center gap-1">
            {NAV_LINKS.map((link) => (
              <Link key={link.href} href={link.href} className={`px-3 py-2 rounded-md text-sm font-medium transition-colors duration-150 ${pathname === link.href ? "text-primary bg-primary/8" : "text-muted-foreground hover:text-foreground hover:bg-muted"}`}>
                {link.label}
              </Link>
            ))}
          </div>

          <form onSubmit={handleSearch} className="hidden md:flex flex-1 max-w-xs">
            <div className="relative w-full">
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input type="text" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search courses, tracks..." className="w-full h-9 pl-9 pr-3 text-sm rounded-lg border border-input bg-muted/50 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:bg-background transition-all duration-150" />
            </div>
          </form>

          <div className="flex items-center gap-2">
            {isAuthenticated && user ? (
              <>
                <NotificationBell />

                <div className="hidden lg:flex items-center gap-1">
                  {user.role === "student" && (
                    <>
                      <Link href="/dashboard" className={`px-3 py-2 rounded-md text-sm font-medium transition-colors duration-150 ${pathname === "/dashboard" ? "text-primary bg-primary/8" : "text-muted-foreground hover:text-foreground hover:bg-muted"}`}>
                        Dashboard
                      </Link>
                      <Link href="/resumes" className={`px-3 py-2 rounded-md text-sm font-medium transition-colors duration-150 ${pathname.startsWith("/resumes") ? "text-primary bg-primary/8" : "text-muted-foreground hover:text-foreground hover:bg-muted"}`}>
                        Resumes
                      </Link>
                      <Link href="/portfolio" className={`px-3 py-2 rounded-md text-sm font-medium transition-colors duration-150 ${pathname.startsWith("/portfolio") ? "text-primary bg-primary/8" : "text-muted-foreground hover:text-foreground hover:bg-muted"}`}>
                        Portfolio
                      </Link>
                      <Link href="/applications" className={`px-3 py-2 rounded-md text-sm font-medium transition-colors duration-150 ${pathname === "/applications" ? "text-primary bg-primary/8" : "text-muted-foreground hover:text-foreground hover:bg-muted"}`}>
                        Applications
                      </Link>
                    </>
                  )}
                  {user.role === "instructor" && (
                    <>
                      <Link href="/instructor/dashboard" className="px-3 py-2 rounded-md text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors duration-150">
                        Dashboard
                      </Link>
                      <Link href="/instructor/courses" className="px-3 py-2 rounded-md text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors duration-150">
                        Courses
                      </Link>
                    </>
                  )}
                  {RECRUITER_ROLES.has(user.role) && (
                    <>
                      <Link href="/recruiter/dashboard" className={`px-3 py-2 rounded-md text-sm font-medium transition-colors duration-150 ${pathname.startsWith("/recruiter") ? "text-primary bg-primary/8" : "text-muted-foreground hover:text-foreground hover:bg-muted"}`}>
                        Recruiter
                      </Link>
                      <Link href="/recruiter/pipeline" className="px-3 py-2 rounded-md text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors duration-150">
                        Pipeline
                      </Link>
                    </>
                  )}
                  {ORGANIZATION_ADMIN_ROLES.has(user.role) && (
                    <Link href="/organization/dashboard" className={`px-3 py-2 rounded-md text-sm font-medium transition-colors duration-150 ${pathname.startsWith("/organization") ? "text-primary bg-primary/8" : "text-muted-foreground hover:text-foreground hover:bg-muted"}`}>
                      Organization
                    </Link>
                  )}
                  {PLATFORM_ADMIN_ROLES.has(user.role) && (
                    <Link href="/platform/dashboard" className={`px-3 py-2 rounded-md text-sm font-medium transition-colors duration-150 ${pathname.startsWith("/platform") ? "text-primary bg-primary/8" : "text-muted-foreground hover:text-foreground hover:bg-muted"}`}>
                      Platform
                    </Link>
                  )}
                </div>

                <div className="relative">
                  <button onClick={() => setUserMenuOpen(!userMenuOpen)} className="flex items-center gap-2 p-1 rounded-lg hover:bg-muted transition-colors duration-150">
                    <div className="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center text-xs font-semibold overflow-hidden flex-shrink-0">
                      {user.avatar_url ? (
                        <Image src={user.avatar_url} alt={user.full_name} width={32} height={32} className="w-full h-full object-cover" />
                      ) : (
                        getInitials(user.full_name)
                      )}
                    </div>
                    <svg className="hidden lg:block w-3.5 h-3.5 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>

                  {userMenuOpen && (
                    <>
                      <div className="fixed inset-0 z-40" onClick={() => setUserMenuOpen(false)} />
                      <div className="absolute right-0 top-11 w-52 bg-background border border-border rounded-xl shadow-lg z-50 overflow-hidden animate-scale-in">
                        <div className="px-4 py-3 border-b border-border">
                          <p className="text-sm font-medium truncate">{user.full_name}</p>
                          <p className="text-xs text-muted-foreground truncate">{user.email}</p>
                        </div>
                        <div className="py-1">
                          {user.role === "student" && (
                            <>
                              <Link href="/dashboard" onClick={() => setUserMenuOpen(false)} className="flex items-center gap-2 px-4 py-2 text-sm text-foreground hover:bg-muted transition-colors">Dashboard</Link>
                              <Link href="/certificates" onClick={() => setUserMenuOpen(false)} className="flex items-center gap-2 px-4 py-2 text-sm text-foreground hover:bg-muted transition-colors">Certificates</Link>
                              <Link href="/resumes" onClick={() => setUserMenuOpen(false)} className="flex items-center gap-2 px-4 py-2 text-sm text-foreground hover:bg-muted transition-colors">Resumes</Link>
                              <Link href="/portfolio" onClick={() => setUserMenuOpen(false)} className="flex items-center gap-2 px-4 py-2 text-sm text-foreground hover:bg-muted transition-colors">Portfolio</Link>
                              <Link href="/career-profile" onClick={() => setUserMenuOpen(false)} className="flex items-center gap-2 px-4 py-2 text-sm text-foreground hover:bg-muted transition-colors">Career profile</Link>
                              <Link href="/applications" onClick={() => setUserMenuOpen(false)} className="flex items-center gap-2 px-4 py-2 text-sm text-foreground hover:bg-muted transition-colors">Applications</Link>
                              <Link href="/saved-jobs" onClick={() => setUserMenuOpen(false)} className="flex items-center gap-2 px-4 py-2 text-sm text-foreground hover:bg-muted transition-colors">Saved jobs</Link>
                            </>
                          )}
                          {user.role === "instructor" && (
                            <>
                              <Link href="/instructor/dashboard" onClick={() => setUserMenuOpen(false)} className="flex items-center gap-2 px-4 py-2 text-sm text-foreground hover:bg-muted transition-colors">Dashboard</Link>
                              <Link href="/instructor/courses" onClick={() => setUserMenuOpen(false)} className="flex items-center gap-2 px-4 py-2 text-sm text-foreground hover:bg-muted transition-colors">My Courses</Link>
                            </>
                          )}
                          {RECRUITER_ROLES.has(user.role) && (
                            <>
                              <Link href="/recruiter/dashboard" onClick={() => setUserMenuOpen(false)} className="flex items-center gap-2 px-4 py-2 text-sm text-foreground hover:bg-muted transition-colors">Recruiter dashboard</Link>
                              <Link href="/recruiter/jobs" onClick={() => setUserMenuOpen(false)} className="flex items-center gap-2 px-4 py-2 text-sm text-foreground hover:bg-muted transition-colors">Organization jobs</Link>
                              <Link href="/recruiter/pipeline" onClick={() => setUserMenuOpen(false)} className="flex items-center gap-2 px-4 py-2 text-sm text-foreground hover:bg-muted transition-colors">Pipeline</Link>
                            </>
                          )}
                          {ORGANIZATION_ADMIN_ROLES.has(user.role) && (
                            <Link href="/organization/dashboard" onClick={() => setUserMenuOpen(false)} className="flex items-center gap-2 px-4 py-2 text-sm text-foreground hover:bg-muted transition-colors">Organization console</Link>
                          )}
                          {PLATFORM_ADMIN_ROLES.has(user.role) && (
                            <Link href="/platform/dashboard" onClick={() => setUserMenuOpen(false)} className="flex items-center gap-2 px-4 py-2 text-sm text-foreground hover:bg-muted transition-colors">Platform management</Link>
                          )}
                        </div>
                        <div className="border-t border-border py-1">
                          <Link href="/settings/notifications" onClick={() => setUserMenuOpen(false)} className="flex items-center gap-2 px-4 py-2 text-sm text-foreground hover:bg-muted transition-colors">Notification settings</Link>
                          <Link href="/settings/privacy" onClick={() => setUserMenuOpen(false)} className="flex items-center gap-2 px-4 py-2 text-sm text-foreground hover:bg-muted transition-colors">Privacy settings</Link>
                          <button onClick={handleLogout} className="w-full flex items-center gap-2 px-4 py-2 text-sm text-destructive hover:bg-destructive/10 transition-colors">
                            Sign out
                          </button>
                        </div>
                      </div>
                    </>
                  )}
                </div>

                <button onClick={() => setMobileOpen(!mobileOpen)} className="md:hidden p-2 rounded-lg hover:bg-muted transition-colors" aria-label="Menu">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    {mobileOpen ? <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /> : <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />}
                  </svg>
                </button>
              </>
            ) : (
              <>
                <Link href="/login" className="hidden sm:block px-3 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors duration-150">
                  Sign in
                </Link>
                <Link href="/register" className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary-600 transition-colors duration-150">
                  Get started
                </Link>
                <button onClick={() => setMobileOpen(!mobileOpen)} className="sm:hidden p-2 rounded-lg hover:bg-muted transition-colors">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    {mobileOpen ? <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /> : <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />}
                  </svg>
                </button>
              </>
            )}
          </div>
        </div>

        <div className="md:hidden pb-3">
          <form onSubmit={handleSearch}>
            <div className="relative">
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input type="text" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search courses, tracks..." className="w-full h-9 pl-9 pr-3 text-sm rounded-lg border border-input bg-muted/50 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:bg-background transition-all" />
            </div>
          </form>
        </div>

        {mobileOpen && (
          <div className="md:hidden border-t border-border py-3 space-y-1 animate-slide-down">
            {NAV_LINKS.map((link) => (
              <Link key={link.href} href={link.href} onClick={() => setMobileOpen(false)} className="block px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">
                {link.label}
              </Link>
            ))}
            {isAuthenticated && user && (
              <>
                <div className="my-2 border-t border-border" />
                {user.role === "student" && (
                  <>
                    <Link href="/dashboard" onClick={() => setMobileOpen(false)} className="block px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">Dashboard</Link>
                    <Link href="/certificates" onClick={() => setMobileOpen(false)} className="block px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">Certificates</Link>
                    <Link href="/resumes" onClick={() => setMobileOpen(false)} className="block px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">Resumes</Link>
                    <Link href="/portfolio" onClick={() => setMobileOpen(false)} className="block px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">Portfolio</Link>
                    <Link href="/career-profile" onClick={() => setMobileOpen(false)} className="block px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">Career profile</Link>
                    <Link href="/applications" onClick={() => setMobileOpen(false)} className="block px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">Applications</Link>
                    <Link href="/saved-jobs" onClick={() => setMobileOpen(false)} className="block px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">Saved jobs</Link>
                  </>
                )}
                {user.role === "instructor" && (
                  <>
                    <Link href="/instructor/dashboard" onClick={() => setMobileOpen(false)} className="block px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">Dashboard</Link>
                    <Link href="/instructor/courses" onClick={() => setMobileOpen(false)} className="block px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">Courses</Link>
                  </>
                )}
                {RECRUITER_ROLES.has(user.role) && (
                  <>
                    <Link href="/recruiter/dashboard" onClick={() => setMobileOpen(false)} className="block px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">Recruiter dashboard</Link>
                    <Link href="/recruiter/jobs" onClick={() => setMobileOpen(false)} className="block px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">Organization jobs</Link>
                    <Link href="/recruiter/pipeline" onClick={() => setMobileOpen(false)} className="block px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">Pipeline</Link>
                  </>
                )}
                {ORGANIZATION_ADMIN_ROLES.has(user.role) && (
                  <Link href="/organization/dashboard" onClick={() => setMobileOpen(false)} className="block px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">Organization console</Link>
                )}
                {PLATFORM_ADMIN_ROLES.has(user.role) && (
                  <Link href="/platform/dashboard" onClick={() => setMobileOpen(false)} className="block px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">Platform management</Link>
                )}
                <div className="my-2 border-t border-border" />
                <Link href="/settings/notifications" onClick={() => setMobileOpen(false)} className="block px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">Notification settings</Link>
                <Link href="/settings/privacy" onClick={() => setMobileOpen(false)} className="block px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">Privacy settings</Link>
                <button onClick={handleLogout} className="w-full text-left px-3 py-2.5 rounded-lg text-sm font-medium text-destructive hover:bg-destructive/10 transition-colors">
                  Sign out
                </button>
              </>
            )}
            {!isAuthenticated && (
              <Link href="/login" onClick={() => setMobileOpen(false)} className="block px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">
                Sign in
              </Link>
            )}
          </div>
        )}
      </div>
    </nav>
  );
}
