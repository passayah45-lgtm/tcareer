"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Navbar } from "@/components/layout/Navbar";
import api from "@/lib/api/client";

interface Certificate {
  id: string; cert_number: string; course_title: string;
  pdf_url: string; verify_url: string; issued_at: string;
}

export default function CertificatesPage() {
  const [certificates, setCertificates] = useState<Certificate[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/certificates/")
      .then((res) => setCertificates(res.data.data || []))
      .catch(() => setCertificates([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <Navbar />
      <main className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold mb-6">My Certificates</h1>
        {loading ? (
          <div className="space-y-3">{[...Array(3)].map((_, i) => <div key={i} className="h-24 bg-muted rounded-xl animate-pulse" />)}</div>
        ) : certificates.length === 0 ? (
          <div className="border rounded-xl p-12 text-center text-muted-foreground">
            <div className="text-4xl mb-3">🏅</div>
            <p className="mb-3">You have not earned any certificates yet.</p>
            <p className="text-sm mb-4">Complete a course and pass the quiz to earn your first certificate.</p>
            <Link href="/courses" className="text-sm bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors">Browse courses</Link>
          </div>
        ) : (
          <div className="space-y-4">
            {certificates.map((cert) => (
              <div key={cert.id} className="border rounded-xl p-5 bg-card flex items-center gap-4">
                <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center text-2xl flex-shrink-0">🏅</div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium truncate">{cert.course_title}</h3>
                  <p className="text-xs text-muted-foreground font-mono mt-0.5">{cert.cert_number}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">Issued {new Date(cert.issued_at).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}</p>
                </div>
                <div className="flex gap-2 flex-shrink-0">
                  <Link href={`/verify/${cert.cert_number}`} className="text-xs border rounded-lg px-3 py-1.5 hover:bg-muted transition-colors">Verify</Link>
                  {cert.pdf_url && <a href={cert.pdf_url} target="_blank" rel="noopener noreferrer" className="text-xs bg-primary text-primary-foreground rounded-lg px-3 py-1.5 hover:bg-primary/90 transition-colors">Download</a>}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </>
  );
}
