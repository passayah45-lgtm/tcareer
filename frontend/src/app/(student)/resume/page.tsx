"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Navbar } from "@/components/layout/Navbar";
import { useAuthStore } from "@/stores/auth.store";
import api from "@/lib/api/client";

interface Certificate {
  cert_number: string;
  course_title: string;
  issued_at: string;
  pdf_url: string;
  verify_url: string;
}

interface Enrollment {
  course: { title: string; level: string };
  status: string;
}

export default function ResumePage() {
  const { user } = useAuthStore();
  const [certificates, setCertificates] = useState<Certificate[]>([]);
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get("/certificates/").then((r) => setCertificates(r.data.data || [])),
      api.get("/courses/enrollments/").then((r) => setEnrollments(r.data.data || [])),
    ]).finally(() => setLoading(false));
  }, []);

  const completedCourses = enrollments.filter((e) => e.status === "completed");

  return (
    <>
      <Navbar />
      <main className="max-w-3xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold">My Resume</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Your verified skills and certificates.
            </p>
            <p className="text-xs text-muted-foreground mt-1 print:hidden">
              Your resume is auto-populated with your certificates and skills from your{" "}
              <Link href="/portfolio" className="text-primary hover:underline">
                portfolio
              </Link>
              .
            </p>
          </div>
          <div className="flex items-center gap-2 print:hidden shrink-0">
            <Link
              href="/resume/edit"
              className="px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
            >
              Edit resume
            </Link>
            <button
              onClick={() => window.print()}
              className="border px-4 py-2 rounded-lg text-sm hover:bg-muted transition-colors"
            >
              Print / Save PDF
            </button>
          </div>
        </div>

        {loading ? (
          <div className="space-y-4 animate-pulse">
            {[...Array(3)].map((_, i) => <div key={i} className="h-24 bg-muted rounded-xl" />)}
          </div>
        ) : (
          <div className="space-y-6 print:space-y-4">
            <div className="border rounded-xl p-6 bg-card print:border-0 print:p-0">
              <h2 className="text-xl font-bold">{user?.full_name}</h2>
              <p className="text-muted-foreground text-sm mt-0.5">{user?.email}</p>
              <p className="text-sm text-primary mt-1">T-Career Verified Profile</p>
            </div>

            {certificates.length > 0 && (
              <div className="border rounded-xl p-6 bg-card">
                <h2 className="font-semibold mb-4">Verified Certificates</h2>
                <div className="space-y-3">
                  {certificates.map((cert) => (
                    <div key={cert.cert_number} className="flex items-center justify-between py-2 border-b last:border-0">
                      <div>
                        <p className="text-sm font-medium">{cert.course_title}</p>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          Issued {new Date(cert.issued_at).toLocaleDateString("en-US", { year: "numeric", month: "long" })}
                        </p>
                        <p className="text-xs font-mono text-muted-foreground">{cert.cert_number}</p>
                      </div>
                      <div className="flex gap-2">
                        <a href={cert.verify_url} target="_blank" rel="noopener noreferrer"
                          className="text-xs text-primary hover:underline">Verify</a>
                        {cert.pdf_url && (
                          <a href={cert.pdf_url} target="_blank" rel="noopener noreferrer"
                            className="text-xs text-muted-foreground hover:underline">PDF</a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {completedCourses.length > 0 && (
              <div className="border rounded-xl p-6 bg-card">
                <h2 className="font-semibold mb-4">Completed Courses</h2>
                <div className="space-y-2">
                  {completedCourses.map((enrollment, i) => (
                    <div key={i} className="flex items-center justify-between py-1.5 border-b last:border-0">
                      <p className="text-sm">{enrollment.course.title}</p>
                      <span className="text-xs text-muted-foreground capitalize">{enrollment.course.level}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {certificates.length === 0 && completedCourses.length === 0 && (
              <div className="border rounded-xl p-8 text-center text-muted-foreground">
                <p className="mb-2">Your resume is empty right now.</p>
                <p className="text-sm">Complete courses and earn certificates to build your profile.</p>
              </div>
            )}

            <p className="text-xs text-muted-foreground text-center print:hidden">
              Certificates can be verified at tcareer.com/verify/{"{cert-number}"}
            </p>
          </div>
        )}
      </main>
    </>
  );
}