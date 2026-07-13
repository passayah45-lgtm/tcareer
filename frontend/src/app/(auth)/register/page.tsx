"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { register as registerUser } from "@/lib/api/auth.api";
import { useAuthStore } from "@/stores/auth.store";
import { getDashboardPathForUser } from "@/lib/auth/role-redirects";
import { registerSchema, type RegisterFormValues } from "@/lib/validations/auth.schema";

export default function RegisterPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();
  const [serverError, setServerError] = useState("");

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { role: "student" },
  });

  async function onSubmit(values: RegisterFormValues) {
    setServerError("");
    try {
      const data = await registerUser(values);
      setAuth(data.user, data.access);
      router.push(data.user.role === "student" ? "/onboarding" : getDashboardPathForUser(data.user));
    } catch (err: unknown) {
      const error = err as { response?: { data?: { errors?: Record<string, string> } } };
      const errs = error?.response?.data?.errors;
      setServerError(errs?.detail || errs?.email || "Registration failed. Please try again.");
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-gradient-to-br from-primary/5 via-background to-background">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <Link href="/" className="inline-block text-xl font-bold text-primary mb-6 hover:opacity-80 transition-opacity">T-Career</Link>
          <h1 className="text-2xl font-bold tracking-tight">Create your account</h1>
          <p className="text-sm text-muted-foreground mt-1.5">Start learning and building your career</p>
        </div>
        <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
          {serverError && (
            <div className="mb-5 flex items-start gap-3 p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm">{serverError}</div>
          )}
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-1.5">
              <label className="block text-sm font-medium">Full name</label>
              <input {...register("full_name")} type="text" placeholder="Your full name" autoComplete="name"
                className={"w-full h-10 px-3 text-sm rounded-lg border bg-background text-foreground placeholder:text-muted-foreground transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent " + (errors.full_name ? "border-destructive" : "border-input")} />
              {errors.full_name && <p className="text-xs text-destructive">{errors.full_name.message}</p>}
            </div>
            <div className="space-y-1.5">
              <label className="block text-sm font-medium">Email</label>
              <input {...register("email")} type="email" placeholder="you@example.com" autoComplete="email"
                className={"w-full h-10 px-3 text-sm rounded-lg border bg-background text-foreground placeholder:text-muted-foreground transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent " + (errors.email ? "border-destructive" : "border-input")} />
              {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
            </div>
            <div className="space-y-1.5">
              <label className="block text-sm font-medium">Password</label>
              <input {...register("password")} type="password" placeholder="At least 8 characters" autoComplete="new-password"
                className={"w-full h-10 px-3 text-sm rounded-lg border bg-background text-foreground placeholder:text-muted-foreground transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent " + (errors.password ? "border-destructive" : "border-input")} />
              {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
            </div>
            <div className="space-y-1.5">
              <label className="block text-sm font-medium">Confirm password</label>
              <input {...register("password_confirm")} type="password" placeholder="Repeat your password" autoComplete="new-password"
                className={"w-full h-10 px-3 text-sm rounded-lg border bg-background text-foreground placeholder:text-muted-foreground transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent " + (errors.password_confirm ? "border-destructive" : "border-input")} />
              {errors.password_confirm && <p className="text-xs text-destructive">{errors.password_confirm.message}</p>}
            </div>
            <div className="space-y-1.5">
              <label className="block text-sm font-medium">I am joining as</label>
              <select {...register("role")} className="w-full h-10 px-3 text-sm rounded-lg border border-input bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-colors">
                <option value="student">Student</option>
                <option value="instructor">Instructor</option>
                <option value="mentor">Mentor</option>
                <option value="recruiter">Recruiter</option>
              </select>
            </div>
            <button type="submit" disabled={isSubmitting}
              className="w-full h-10 flex items-center justify-center bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary-600 disabled:opacity-50 disabled:pointer-events-none transition-colors mt-2">
              {isSubmitting ? "Creating account..." : "Create account"}
            </button>
          </form>
        </div>
        <p className="text-center text-sm text-muted-foreground mt-5">
          Already have an account?{" "}
          <Link href="/login" className="text-primary hover:text-primary-600 font-medium transition-colors">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
