"use client";

import { useState, useRef, FormEvent, useCallback, useEffect } from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { Message, QuestionnairePayload, RawTasks } from "@/types";
import { buildUserContent } from "@/utils/chatPayload";
import { API_URL, getAppToken } from "@/utils/const";

const THREAD_ID_PATTERN = /\x00THREAD_ID:([^\x00]+)\x00/;
const EXECUTION_COMPLETE_PATTERN = /\x00EXECUTION_COMPLETE:([\s\S]+?)\x00/;
const AGENT_STEP_PATTERN = /\x00AGENT_STEP:([\s\S]+?)\x00/;

const CONTROL_TOKEN_PATTERN =
  /\x00(?:THREAD_ID|EXECUTION_COMPLETE|AGENT_STEP):[\s\S]*?\x00/g;
// Fallback pattern jika backend membocorkan JSON ini langsung ke dalam text stream biasa
// (tanpa event khusus dari route.ts / tanpa prefix \x00)
const LEAKED_EXEC_PATTERN = /EXECUTION_COMPLETE:(\{[\s\S]*?\})/g;

export type HitlPayload =
  | {
      type: "counselor_chat" | "counselor_review";
      draft: string;
      message: string;
    }
  | {
      type: "task_review";
      tasks: PrioritizerTask[];
      message: string;
      proposed_schedule: ProposedSchedule[];
    };

export type ProposedSchedule = {
  task_id: string;
  task: string;
  priority: number;
  start_time: string;
  duration_minutes: number;
  category: string;
};

export type PrioritizerTask = {
  task_id: string;
  title: string;
  subtasks: string[];
  estimated_minutes: number;
  priority: number;
  deadline: string | null;
  category: string;
  preferred_window: string;
};

export type ExecutionComplete = {
  thread_id: string;
  status: "completed" | "waiting_hitl";
  next_node?: string[];
  hitl_payload?: HitlPayload;
};

export type ResumeData =
  | { approved: boolean; additional_context?: string | null }
  | { tasks: { task: string; priority: number; deadline: string }[] };

export function useChat(userEmail?: string) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [messages, setMessages] = useState<Message[]>([]);
  const [isStarted, setIsStarted] = useState(false);
  const [hitlPayload, setHitlPayload] = useState<HitlPayload | null>(null);

  useEffect(() => {
    if (!hitlPayload && !messages?.length) return;

    console.group("UPDATED STATE");

    console.group("HITL PAYLOAD");
    console.log(hitlPayload);
    console.groupEnd();

    console.group("MESSAGES");
    console.table(messages);
    console.groupEnd();

    console.groupEnd();
  }, [hitlPayload, messages]);

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

  useEffect(() => {
    const current = searchParams.get("thread_id");

    if (!current) {
      sessionStorage.removeItem("chat_messages");
      setMessages([]);
      setIsStarted(false);
      return;
    }

    const loadThread = async () => {
      const token = getAppToken();
      if (!token) {
        return;
      }

      try {
        const response = await fetch(`${API_URL}/agent/${current}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error("Gagal mengambil thread");
        }

        const result = await response.json();

        const { hitl, messages } = result.data;

        if (hitl?.hitl_payload) {
          setHitlPayload(hitl.hitl_payload);
        }

        if (Array.isArray(messages)) {
          const formattedMessages: Message[] = messages
            .filter((msg) => msg?.content?.trim() !== "")
            .map((msg) => ({
              role: msg.role || "system",
              content: msg.content,
            }));

          setMessages(formattedMessages);

          sessionStorage.setItem(
            "chat_messages",
            JSON.stringify(formattedMessages),
          );
        }
      } catch (error) {
        console.error("Gagal mengambil thread:", error);
      }
    };

    loadThread();
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
      headers: {
        "Content-Type": "application/json",
        Authorization:
          typeof window !== "undefined" && sessionStorage.getItem("app_token")
            ? `Bearer ${sessionStorage.getItem("app_token")}`
            : "",
      },
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
        let replacementText = "";

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
              if (execData.hitl_payload.message) {
                replacementText = execData.hitl_payload.message;
              }
            } else {
              setHitlPayload(null);
            }
          } catch (e) {
            console.error("Gagal memparsing JSON Execution Complete:", e);
          }
        }

        const agentMatch = AGENT_STEP_PATTERN.exec(token);
        if (agentMatch) {
          try {
            const stepData = JSON.parse(agentMatch[1]);
            const nodeName = stepData?.update?.node;

            console.log("update data: ", stepData?.update);
            const tasks: RawTasks[] = stepData.update?.update?.raw_tasks || [];
            if (tasks.length > 0 && nodeName !== "__interrupt__") {
              console.log("lebih 0");
              sessionStorage.setItem("raw_tasks", JSON.stringify(tasks));
            } else if (nodeName === "__interrupt__") {
              // Interrupt biasanya ditimpa oleh HITL, jadi kita biarkan kosong agar tidak double
              replacementText = "";
            }
          } catch (e) {
            console.error("Gagal memparsing JSON Agent Step:", e);
          }
        }

        return replacementText;
      });

      // 2. Fallback: Parsing teks EXECUTION_COMPLETE yang bocor dari backend (tanpa \x00)
      combined = combined.replace(LEAKED_EXEC_PATTERN, (match, jsonString) => {
        try {
          const execData = JSON.parse(jsonString) as ExecutionComplete;
          if (execData.status === "waiting_hitl" && execData.hitl_payload) {
            setHitlPayload(execData.hitl_payload);

            return execData.hitl_payload.message || "";
          } else {
            setHitlPayload(null);
          }
        } catch (e) {
          console.error(
            "Gagal memparsing JSON Execution Complete (Leaked):",
            e,
          );
        }
        return "";
      });

      const trailingControlStart = combined.lastIndexOf("\x00");
      if (trailingControlStart !== -1) {
        controlBuffer = combined.slice(trailingControlStart);
        combined = combined.slice(0, trailingControlStart);
      }

      if (combined.startsWith(accumulated)) {
        accumulated = combined;
      } else {
        accumulated += combined;
      }

      setMessages((prev) => {
        const updated = [...prev];
        const lastIdx = updated.length - 1;

        if (updated[lastIdx]?.role === "system") {
          updated[lastIdx] = { role: "system", content: accumulated };
        } else if (accumulated.trim() !== "") {
          updated.push({ role: "system", content: accumulated });
        }

        return updated;
      });
    }

    setMessages((prev) => {
      persistMessages(prev);
      return prev;
    });
  };

  const executeChatStream = async (userContent: string, streamPayload: any) => {
    // 1. Reset UI & Preparation
    setHitlPayload(null);
    setInputValue(""); // Bersihkan input (aman dilakukan di kedua kondisi)
    setIsStarted(true);
    setIsTyping(true);

    // 2. Update Message State
    const userMessage = { role: "user" as const, content: userContent };

    setMessages((prev) => {
      const nextMessages = [...prev, userMessage];
      persistMessages(nextMessages); // Simpan pesan user
      return [...nextMessages, { role: "system" as const, content: "" }];
    });

    // 3. API Call
    try {
      await stream(streamPayload);
    } catch (err) {
      console.error("Stream error:", err);
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

  const handleSend = async (
    e: FormEvent | null,
    resumeData?: ResumeData,
    questionnaireData?: QuestionnairePayload,
  ) => {
    e?.preventDefault();
    if (isTyping) return;

    const threadId = searchParams.get("thread_id");
    const isResume = resumeData !== undefined;

    // --- LOGIKA RESUME ---
    if (isResume) {
      if (!threadId) {
        console.error("Resume dipanggil tapi thread_id tidak ada");
        return;
      }

      const resumeContent =
        "approved" in resumeData
          ? resumeData.additional_context?.trim() ||
            (resumeData.approved ? "Approved." : "Not approved.")
          : "Submitted tasks.";

      return executeChatStream(resumeContent, {
        user_id: userEmail ?? "anonymous",
        thread_id: threadId,
        approved_data: resumeData,
      });
    }

    // --- LOGIKA CHAT BIASA ---
    const trimmed = inputValue.trim();
    if (!trimmed) return;

    const userContent = buildUserContent(trimmed, questionnaireData);
    const nextMessages = [
      ...messages,
      { role: "user" as const, content: userContent },
    ];

    return executeChatStream(userContent, {
      message: userContent,
      messages: nextMessages,
      user_id: userEmail ?? "anonymous",
      ...(threadId ? { thread_id: threadId } : {}),
    });
  };

  return {
    messages,
    inputValue,
    setInputValue,
    isTyping,
    isStarted,
    messagesEndRef,
    hitlPayload,
    handleSend,
  };
}
