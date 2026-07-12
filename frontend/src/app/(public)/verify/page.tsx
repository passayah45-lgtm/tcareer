"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";

export default function CertificateVerificationLandingPage() {
  const router = useRouter();
  const [certNumber, setCertNumber] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = certNumber.trim();
    if (value) router.push(`/verify/${encodeURIComponent(value)}`);
  }

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-3xl px-4 py-12">
        <p className="text-sm font-medium text-primary">Trust & support</p>
        <h1 className="mt-2 text-3xl font-bold">Certificate verification</h1>
        <p className="mt-3 text-sm leading-7 text-muted-foreground">
          Enter a T-Career certificate number to confirm whether the credential is valid and still active.
        </p>
        <form onSubmit={handleSubmit} className="mt-8 rounded-xl border border-border bg-card p-5">
          <label className="text-sm font-medium" htmlFor="certificate-number">Certificate number</label>
          <div className="mt-3 flex flex-col gap-3 sm:flex-row">
            <input
              id="certificate-number"
              className="input flex-1"
              value={certNumber}
              onChange={(event) => setCertNumber(event.target.value)}
              placeholder="Example: TC-2026-0001"
            />
            <button type="submit" className="btn-base btn-primary" disabled={!certNumber.trim()}>
              Verify certificate
            </button>
          </div>
        </form>
      </main>
    </>
  );
}
