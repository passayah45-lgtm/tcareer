"use client";
import { useState } from "react";
import Link from "next/link";
import api from "@/lib/api/client";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setLoading(true);
    try { await api.post("/auth/forgot-password/", { email }); } catch { /* always show success */ }
    finally { setSent(true); setLoading(false); }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-muted/30">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <Link href="/" className="text-xl font-bold text-primary">T-Career</Link>
          <h1 className="text-2xl font-semibold mt-4 mb-1">Reset password</h1>
          <p className="text-sm text-muted-foreground">Enter your email and we will send a reset link</p>
        </div>
        <div className="bg-background border rounded-xl p-6 shadow-sm">
          {sent ? (
            <div className="text-center py-4">
              <div className="text-4xl mb-3">📧</div>
              <p className="text-sm text-muted-foreground">If an account exists with that email, a reset link has been sent. Check your inbox.</p>
              <Link href="/login" className="block mt-4 text-sm text-primary hover:underline">Back to sign in</Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="text-sm font-medium block mb-1">Email</label>
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="you@example.com"
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 bg-background" />
              </div>
              <button type="submit" disabled={loading} className="w-full bg-primary text-primary-foreground py-2.5 rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50">
                {loading ? "Sending..." : "Send reset link"}
              </button>
              <p className="text-center text-sm text-muted-foreground"><Link href="/login" className="text-primary hover:underline">Back to sign in</Link></p>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
