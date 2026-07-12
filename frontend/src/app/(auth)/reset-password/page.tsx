"use client";
import { Suspense } from "react";
import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import api from "@/lib/api/client";

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password !== confirm) { setError("Passwords do not match."); return; }
    if (password.length < 8) { setError("Password must be at least 8 characters."); return; }
    setLoading(true); setError("");
    try {
      await api.post("/auth/reset-password/", { token, password, password_confirm: confirm });
      setSuccess(true);
      setTimeout(() => router.push("/login"), 3000);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { errors?: { detail?: string } } } };
      setError(e?.response?.data?.errors?.detail || "Reset failed. The link may have expired.");
    } finally { setLoading(false); }
  }

  if (!token) return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="text-center">
        <p className="text-muted-foreground">Invalid reset link.</p>
        <Link href="/forgot-password" className="text-primary text-sm hover:underline mt-2 block">Request a new one</Link>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-muted/30">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <Link href="/" className="text-xl font-bold text-primary">T-Career</Link>
          <h1 className="text-2xl font-semibold mt-4 mb-1">Set new password</h1>
        </div>
        <div className="bg-background border rounded-xl p-6 shadow-sm">
          {success ? (
            <div className="text-center py-4"><div className="text-4xl mb-3">✓</div><p className="text-sm text-muted-foreground">Password reset successfully. Redirecting to sign in...</p></div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm">{error}</div>}
              <div>
                <label className="text-sm font-medium block mb-1">New password</label>
                <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} placeholder="At least 8 characters"
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 bg-background" />
              </div>
              <div>
                <label className="text-sm font-medium block mb-1">Confirm password</label>
                <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required placeholder="Repeat your password"
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 bg-background" />
              </div>
              <button type="submit" disabled={loading} className="w-full bg-primary text-primary-foreground py-2.5 rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50">
                {loading ? "Resetting..." : "Reset password"}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() { return <Suspense><ResetPasswordForm /></Suspense>; }
