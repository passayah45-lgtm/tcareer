"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import api from "@/lib/api/client";

function VerifyEmailForm() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) return;

    api.post("/auth/verify-email/", { token })
      .then((res) => {
        setStatus("success");
        setMessage(res.data.detail);
      })
      .catch((err) => {
        setStatus("error");
        setMessage(
          err?.response?.data?.detail ||
          "This verification link is invalid or has expired."
        );
      });
  }, [token]);

  if (!token) {
    return (
      <VerificationShell
        status="error"
        message="Invalid verification link."
      />
    );
  }

  return <VerificationShell status={status} message={message} />;
}

function VerificationShell({
  status,
  message,
}: {
  status: "loading" | "success" | "error";
  message: string;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-muted/30">
      <div className="max-w-sm w-full text-center">
        <Link href="/" className="text-xl font-bold text-primary block mb-8">
          T-Career
        </Link>

        <div className="bg-background border rounded-xl p-8 shadow-sm">
          {status === "loading" && (
            <>
              <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-sm text-muted-foreground">Verifying your email...</p>
            </>
          )}

          {status === "success" && (
            <>
              <div className="text-4xl mb-4">&#10003;</div>
              <h1 className="font-semibold mb-2">Email verified</h1>
              <p className="text-sm text-muted-foreground mb-6">{message}</p>
              <Link
                href="/dashboard"
                className="block w-full bg-primary text-primary-foreground py-2.5 rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
              >
                Go to dashboard
              </Link>
            </>
          )}

          {status === "error" && (
            <>
              <div className="text-4xl mb-4">&#10007;</div>
              <h1 className="font-semibold mb-2">Verification failed</h1>
              <p className="text-sm text-muted-foreground mb-6">{message}</p>
              <Link
                href="/login"
                className="block w-full border py-2.5 rounded-lg text-sm hover:bg-muted transition-colors"
              >
                Back to sign in
              </Link>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default function VerifyEmailPage() { return <Suspense><VerifyEmailForm /></Suspense>; }
