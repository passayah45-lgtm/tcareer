"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useAuthStore } from "@/stores/auth.store";
import { getMe, refreshToken } from "@/lib/api/auth.api";
import { getAccessToken } from "@/lib/api/client";
import { ToastContainer } from "@/components/shared/Toast";
const queryClient = new QueryClient({ defaultOptions: { queries: { staleTime: 60 * 1000, retry: 1 } } });
function AuthInitializer({ children }: { children: React.ReactNode }) {
  const { setAuth, clearAuth, setLoading } = useAuthStore();
  useEffect(() => {
    async function initAuth() {
      try {
        const tokens = await refreshToken();
        const user = await getMe();
        setAuth(user, tokens.access);
      } catch {
        if (!getAccessToken()) clearAuth();
      }
      finally { setLoading(false); }
    }
    initAuth();
  }, [setAuth, clearAuth, setLoading]);
  return <>{children}</>;
}
export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(() => queryClient);
  return (
    <QueryClientProvider client={client}>
      <AuthInitializer>
        {children}
        <ToastContainer />
      </AuthInitializer>
    </QueryClientProvider>
  );
}
