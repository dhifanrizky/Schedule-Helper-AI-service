"use client";

import { useState, useRef, FormEvent, useCallback, useEffect } from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { Message } from "@/types";

const THREAD_ID_PATTERN = /\x00THREAD_ID:([^\x00]+)\x00/;
const EXECUTION_COMPLETE_PATTERN = /\x00EXECUTION_COMPLETE:([\s\S]+?)\x00/;
const CONTROL_TOKEN_PATTERN =
  /\x00(?:THREAD_ID|EXECUTION_COMPLETE):[\s\S]*?\x00/g;

export type HitlPayload =
  | { type: "counselor_review"; draft: string; message: string }
  | {
      type: "task_review";
      tasks: PrioritizerTask[];
      message: string;
    };

export type PrioritizerTask = {
  task_id: string;
  title: string;
  subtasks: string[];
  estimated_minutes: number;
  deadline: string | null;
  category: string;
  preferred_window: string;
  urgency: number;
  importance: number;
  effort: number;
  energy_fit: number;
};

export type ExecutionComplete = {
  thread_id: string;
  status: "completed" | "waiting_hitl";
  next_node?: string[];
  hitl_payload?: HitlPayload;
};

export type ResumeData =
  | { approved: boolean; edited_draft?: string | null }
  | { tasks: { task: string; priority: number; deadline: string }[] };

export function useChat(userEmail?: string) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [messages, setMessages] = useState<Message[]>([]);
  const [isStarted, setIsStarted] = useState(false);
  const [hitlPayload, setHitlPayload] = useState<HitlPayload | null>(null);

  useEffect(() => {
    try {
      const saved = sessionStorage.getItem("chat_messages");
      if (saved) {
        const parsed = JSON.parse(saved) as Message[];
        setMessages(parsed);
        setIsStarted(true);
      }
    } catch {
      /* ignore */
    }
  }, []);

  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const setThreadIdInUrl = useCallback(
    (threadId: string) => {
      const current = searchParams.get("thread_id");
      if (current) return;
      const params = new URLSearchParams(searchParams.toString());
      params.set("thread_id", threadId);
      router.replace(`${pathname}?${params.toString()}`);
    },
    [router, pathname, searchParams],
  );

  const persistMessages = (msgs: Message[]) => {
    sessionStorage.setItem("chat_messages", JSON.stringify(msgs));
  };

  /** Core streaming — dipakai handleSend (chat biasa & resume) */
  const stream = async (body: Record<string, unknown>) => {
    const response = await fetch("/api/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!response.ok || !response.body) {
      const errorText = await response.text();
      throw new Error(
        `Stream tidak tersedia — status: ${response.status}, body: ${errorText}`,
      );
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let accumulated = "";
    let threadIdCaptured = false;
    let controlBuffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      let chunk = decoder.decode(value, { stream: true });
      let combined = controlBuffer + chunk;
      controlBuffer = "";

      combined = combined.replace(CONTROL_TOKEN_PATTERN, (token) => {
        if (!threadIdCaptured) {
          const threadMatch = THREAD_ID_PATTERN.exec(token);
          if (threadMatch) {
            setThreadIdInUrl(threadMatch[1]);
            threadIdCaptured = true;
          }
        }

        const execMatch = EXECUTION_COMPLETE_PATTERN.exec(token);
        if (execMatch) {
          try {
            const execData = JSON.parse(execMatch[1]) as ExecutionComplete;
            if (execData.status === "waiting_hitl" && execData.hitl_payload) {
              setHitlPayload(execData.hitl_payload);
            } else {
              setHitlPayload(null);
            }
          } catch {
            /* ignore parse error */
          }
        }

        return "";
      });

      const trailingControlStart = combined.lastIndexOf("\x00");
      if (trailingControlStart !== -1) {
        controlBuffer = combined.slice(trailingControlStart);
        combined = combined.slice(0, trailingControlStart);
      }

      accumulated += combined;

      setMessages((prev) => {
        const updated = [...prev];
        const lastIdx = updated.length - 1;
        if (updated[lastIdx]?.role === "system") {
          updated[lastIdx] = { role: "system", content: accumulated };
        }
        return updated;
      });
    }

    setMessages((prev) => {
      persistMessages(prev);
      return prev;
    });
  };

  const handleSend = async (
    e: FormEvent | null,
    // Jika resume, pass approved_data — handleSend otomatis tahu ini resume
    resumeData?: ResumeData,
  ) => {
    e?.preventDefault();

    const threadId = searchParams.get("thread_id");
    const isResume = resumeData !== undefined;

    // Resume: tidak perlu input teks, tapi wajib thread_id
    if (isResume) {
      if (!threadId) {
        console.error("Resume dipanggil tapi thread_id tidak ada");
        return;
      }
      if (isTyping) return;

      setHitlPayload(null); // tutup UI review
      setMessages((prev) => [
        ...prev,
        { role: "system" as const, content: "" },
      ]);
      setIsTyping(true);

      try {
        await stream({
          user_id: userEmail ?? "anonymous",
          thread_id: threadId,
          approved_data: resumeData,
        });
      } catch (err) {
        console.error("Resume error:", err);
        setMessages((prev) => {
          const updated = [...prev];
          const lastIdx = updated.length - 1;
          if (updated[lastIdx]?.role === "system") {
            updated[lastIdx] = {
              role: "system",
              content: "Maaf, terjadi kesalahan. Silakan coba lagi.",
            };
          }
          persistMessages(updated);
          return updated;
        });
      } finally {
        setIsTyping(false);
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
      }
      return;
    }

    // Chat biasa
    const trimmed = inputValue.trim();
    if (!trimmed || isTyping) return;

    const userMessage: Message = { role: "user", content: trimmed };
    const nextMessages = [...messages, userMessage];

    setMessages([...nextMessages, { role: "system" as const, content: "" }]);
    persistMessages(nextMessages);
    setInputValue("");
    setIsStarted(true);
    setIsTyping(true);

    try {
      await stream({
        message: trimmed,
        messages: nextMessages,
        user_id: userEmail ?? "anonymous",
        ...(threadId ? { thread_id: threadId } : {}),
      });
    } catch (err) {
      console.error("Chat error:", err);
      setMessages((prev) => {
        const updated = [...prev];
        const lastIdx = updated.length - 1;
        if (updated[lastIdx]?.role === "system") {
          updated[lastIdx] = {
            role: "system",
            content: "Maaf, terjadi kesalahan. Silakan coba lagi.",
          };
        }
        persistMessages(updated);
        return updated;
      });
    } finally {
      setIsTyping(false);
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  };

  return {
    messages,
    inputValue,
    setInputValue,
    isTyping,
    isStarted,
    messagesEndRef,
    hitlPayload, // ← gunakan ini untuk render UI review (counselor/prioritizer)
    handleSend, // ← satu fungsi untuk semua
  };
}
