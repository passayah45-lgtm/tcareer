"use client";

import { FormEvent, useRef, useState } from "react";
import { cancelAIRequest, streamAIChat } from "@/lib/api/ai.api";

const FEATURES = ["chat", "resume_review", "portfolio_review", "career_advice", "learning_recommendations", "job_matching"];

export function AIChatPanel() {
  const [feature, setFeature] = useState("chat");
  const [inputText, setInputText] = useState("");
  const [streamText, setStreamText] = useState("");
  const [activeRequestId, setActiveRequestId] = useState<string | null>(null);
  const [usage, setUsage] = useState<{ total_tokens: number; estimated_cost: string; latency_ms: number } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const controllerRef = useRef<AbortController | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!inputText.trim()) return;
    setLoading(true);
    setError("");
    setStreamText("");
    setUsage(null);
    controllerRef.current = new AbortController();
    try {
      await streamAIChat(inputText, feature, (streamEvent) => {
        if (streamEvent.request_id) setActiveRequestId(streamEvent.request_id);
        if (streamEvent.event === "token" && streamEvent.chunk) setStreamText((current) => current + streamEvent.chunk);
        if (streamEvent.event === "done" && streamEvent.usage) setUsage(streamEvent.usage);
        if (streamEvent.event === "error") setError(streamEvent.error || "AI stream failed.");
      }, controllerRef.current.signal);
      setInputText("");
    } catch {
      setError("AI is unavailable or your request was blocked.");
    } finally {
      setLoading(false);
    }
  }

  async function cancel() {
    controllerRef.current?.abort();
    if (activeRequestId) {
      await cancelAIRequest(activeRequestId).catch(() => undefined);
    }
    setLoading(false);
  }

  return (
    <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px]">
      <form onSubmit={submit} className="rounded-lg border border-border bg-card p-5 space-y-4">
        {error && <p className="text-sm text-destructive">{error}</p>}
        <label className="block text-sm">Feature<select className="input mt-1" value={feature} onChange={(event) => setFeature(event.target.value)}>{FEATURES.map((item) => <option key={item} value={item}>{item.replaceAll("_", " ")}</option>)}</select></label>
        <label className="block text-sm">Prompt<textarea className="input mt-1 min-h-48" value={inputText} onChange={(event) => setInputText(event.target.value)} placeholder="Ask for career advice, resume feedback, portfolio review, or job matching guidance." /></label>
        <div className="flex gap-2">
          <button disabled={loading} className="btn-base btn-primary disabled:opacity-50">{loading ? "Streaming..." : "Generate"}</button>
          <button type="button" disabled={!loading} onClick={cancel} className="btn-base btn-secondary disabled:opacity-50">Cancel</button>
        </div>
      </form>
      <aside className="rounded-lg border border-border bg-card p-5">
        <h2 className="font-semibold mb-3">Latest response</h2>
        {!streamText ? <p className="text-sm text-muted-foreground">Responses will stream here with token and cost estimates.</p> : (
          <div className="space-y-3">
            <p className="text-sm whitespace-pre-wrap">{streamText}</p>
            <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
              <span>{usage?.total_tokens ?? 0} tokens</span>
              <span>{usage?.latency_ms ?? 0} ms</span>
              <span>${usage?.estimated_cost ?? "0"}</span>
              <span>{loading ? "running" : "completed"}</span>
            </div>
          </div>
        )}
      </aside>
    </div>
  );
}
