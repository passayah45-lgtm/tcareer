"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth.store";
import { getDashboardPathForUser } from "@/lib/auth/role-redirects";
export function InstructorGuard({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated, isLoading } = useAuthStore();
  const router = useRouter();
  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
    if (!isLoading && isAuthenticated && user?.role !== "instructor" && user?.role !== "admin") {
      router.push(getDashboardPathForUser(user));
    }
  }, [isLoading, isAuthenticated, user, router]);
  if (isLoading) return <div className="min-h-screen flex items-center justify-center"><div className="w-7 h-7 border-2 border-primary border-t-transparent rounded-full animate-spin" /></div>;
  if (!isAuthenticated || (user?.role !== "instructor" && user?.role !== "admin")) return null;
  return <>{children}</>;
}
