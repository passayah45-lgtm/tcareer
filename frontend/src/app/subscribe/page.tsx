"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth.store";
import { createCheckoutSession } from "@/lib/api/payments.api";

export default function SubscribePage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubscribe() {
    if (!isAuthenticated) { router.push("/register?next=/subscribe"); return; }
    setLoading(true); setError("");
    try {
      const { checkout_url } = await createCheckoutSession();
      window.location.href = checkout_url;
    } catch { setError("Could not start the payment process. Please try again."); setLoading(false); }
  }

  const features = [
    "Unlimited access to all courses",
    "AI tutor on every lesson",
    "Verified certificates on completion",
    "Progress tracking across all courses",
    "Access to new courses as they launch",
    "Cancel anytime",
  ];

  return (
    <div className="min-h-screen bg-muted/30 flex items-center justify-center px-4 py-12">
      <div className="max-w-sm w-full">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold">T-Career Pro</h1>
          <p className="text-muted-foreground text-sm mt-2">Full access to every course and every feature</p>
        </div>
        <div className="bg-background border rounded-xl overflow-hidden">
          <div className="bg-primary p-6 text-center text-primary-foreground">
            <p className="text-4xl font-bold">$19</p>
            <p className="text-primary-foreground/70 text-sm">per month</p>
          </div>
          <div className="p-6">
            <ul className="space-y-3 mb-6">
              {features.map((f) => <li key={f} className="flex items-start gap-2 text-sm"><span className="text-primary mt-0.5 flex-shrink-0">✓</span>{f}</li>)}
            </ul>
            {error && <p className="text-sm text-destructive mb-3 text-center">{error}</p>}
            <button onClick={handleSubscribe} disabled={loading} className="w-full bg-primary text-primary-foreground py-3 rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50">
              {loading ? "Redirecting to payment..." : "Subscribe now"}
            </button>
            <p className="text-xs text-muted-foreground text-center mt-3">Secure payment via Stripe. Cancel anytime.</p>
          </div>
        </div>
        <p className="text-center text-xs text-muted-foreground mt-4">Free courses remain free. Subscribe only for paid courses.</p>
      </div>
    </div>
  );
}
