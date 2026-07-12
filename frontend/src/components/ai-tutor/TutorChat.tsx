"use client";

import { useState, useRef } from "react";
import { askLearningTutor } from "@/lib/api/ai.api";
import type { AICitation } from "@/types/ai.types";

interface Message {
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
  citations?: AICitation[];
}

interface TutorChatProps {
  courseId: string;
  lessonId: string;
}

export function TutorChat({ courseId, lessonId }: TutorChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  async function sendMessage() {
    const question = input.trim();
    if (!question || loading) return;

    setInput("");
    setLoading(true);

    setMessages((prev) => [
      ...prev,
      { role: "user", content: question },
      { role: "assistant", content: "", streaming: true },
    ]);
    scrollToBottom();

    try {
      const response = await askLearningTutor({ course_id: courseId, lesson_id: lessonId, question, mode: "question" });
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        return [...updated.slice(0, -1), { ...last, content: response.answer, streaming: false, citations: response.context?.retrieval?.citations ?? [] }];
      });
      scrollToBottom();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Something went wrong.";
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        return [
          ...updated.slice(0, -1),
          { ...last, content: message, streaming: false },
        ];
      });
    } finally {
      setLoading(false);
    }
  }

  async function clearHistory() {
    setMessages([]);
  }

  return (
    <div className="border rounded-xl flex flex-col h-80 mt-4">
      <div className="px-4 py-2 border-b bg-muted/30 rounded-t-xl flex items-center justify-between">
        <p className="text-xs font-medium text-muted-foreground">
          AI Tutor - ask anything about this lesson
        </p>
        {messages.length > 0 && (
          <button
            onClick={clearHistory}
            className="text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            Clear chat
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center mt-4">
            Ask a question about this lesson.
          </p>
        ) : (
          messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-xs rounded-xl px-3 py-2 text-sm ${
                msg.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted"
              }`}>
                {msg.content}
                {msg.streaming && (
                  <span className="inline-block w-1 h-3 bg-current ml-0.5 animate-pulse" />
                )}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-2 space-y-1 border-t border-border pt-2 text-xs text-muted-foreground">
                    {msg.citations.slice(0, 3).map((citation) => (
                      <p key={citation.chunk_id}>
                        Source: {citation.title || citation.source_type} ({Math.round(citation.confidence)}%)
                      </p>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      <div className="border-t p-3 flex gap-2 items-center">
        <input
          className="flex-1 text-sm border rounded-lg px-3 py-2 bg-background focus:outline-none focus:ring-2 focus:ring-primary/30"
          placeholder="Ask about this lesson..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
          disabled={loading}
        />
        <button
          onClick={sendMessage}
          disabled={loading || !input.trim()}
          className="text-sm px-4 py-2 bg-primary text-primary-foreground rounded-lg disabled:opacity-50 hover:bg-primary/90 transition-colors"
        >
          {loading ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
}
