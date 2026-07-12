"use client";
import { useEffect, useState } from "react";
export type ToastType = "success" | "error" | "info";
interface ToastItem { id: string; message: string; type: ToastType; }
let addToastFn: ((message: string, type: ToastType) => void) | null = null;
export function toast(message: string, type: ToastType = "success") { if (addToastFn) addToastFn(message, type); }
export function ToastContainer() {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  useEffect(() => {
    addToastFn = (message, type) => {
      const id = Math.random().toString(36).slice(2);
      setToasts((prev) => [...prev, { id, message, type }]);
      setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 3500);
    };
    return () => { addToastFn = null; };
  }, []);
  if (toasts.length === 0) return null;
  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
      {toasts.map((t) => (
        <div key={t.id} className={`flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg text-sm font-medium pointer-events-auto max-w-sm ${t.type === "success" ? "bg-emerald-600 text-white" : t.type === "error" ? "bg-destructive text-destructive-foreground" : "bg-primary text-primary-foreground"}`}>
          {t.type === "success" && <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>}
          {t.type === "error" && <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" /></svg>}
          {t.message}
        </div>
      ))}
    </div>
  );
}
