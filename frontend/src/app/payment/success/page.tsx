"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function PaymentSuccessPage() {
  const router = useRouter();
  useEffect(() => { const t = setTimeout(() => router.push("/dashboard"), 5000); return () => clearTimeout(t); }, [router]);
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="max-w-sm text-center">
        <div className="text-6xl mb-4">🎉</div>
        <h1 className="text-2xl font-bold mb-2">Payment successful</h1>
        <p className="text-muted-foreground text-sm mb-6">Your T-Career Pro subscription is now active. You have full access to all courses.</p>
        <Link href="/courses" className="bg-primary text-primary-foreground px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors">Browse all courses</Link>
        <p className="text-xs text-muted-foreground mt-4">Redirecting to dashboard in 5 seconds...</p>
      </div>
    </div>
  );
}
