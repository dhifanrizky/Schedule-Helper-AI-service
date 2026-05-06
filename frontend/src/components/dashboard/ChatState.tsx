import { FormEvent, useEffect } from "react";
import { Message } from "@/types";
import { HitlPayload, ResumeData } from "@/hooks/useChat";
import { ChatMessage } from "./ChatMessage";
import { TypingIndicator } from "./TypingIndicator";
import { ChatInput } from "./ChatInput";
import { CounselorApproveBar } from "./CounselorApproveBar";

interface ChatStateProps {
  messages: Message[];
  isTyping: boolean;
  inputValue: string;
  setInputValue: (val: string) => void;
  handleSend: (
    e: FormEvent | null,
    resumeData?: ResumeData,
    questionnaireData?: {
      energyLevel: number;
      mood: number;
      availableTime: string;
    },
  ) => void;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
  hitlPayload: HitlPayload | null;
}

export function ChatState({
  messages,
  isTyping,
  inputValue,
  setInputValue,
  handleSend,
  messagesEndRef,
  hitlPayload,
}: ChatStateProps) {
  // Auto-scroll logic inside component
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  // Bikin flag untuk ngecek apakah status terakhir lagi butuh approval
  const isAwaitingApproval =
    messages.length > 0 &&
    messages[messages.length - 1].role === "system" &&
    hitlPayload?.type === "counselor_chat";

  // Bikin custom submit handler
  const handleInputSubmit = (e: FormEvent) => {
    if (isAwaitingApproval) {
      // Kalau lagi nunggu approval dan user malah ngetik, langsung panggil onReject
      handleSend(e, { approved: false, edited_draft: null });
    } else {
      // Chat normal
      handleSend(e);
    }
  };

  return (
    <main className="flex-1 flex flex-col h-full bg-[#FFFFFF]">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-6 pt-10 pb-6">
        <div className="max-w-4xl mx-auto flex flex-col gap-8">
          {messages.map((msg, index) => (
            <div key={index} className="flex flex-col gap-4">
              {msg.role !== "system" && <ChatMessage message={msg} />}
              {msg.role === "system" &&
                hitlPayload?.type === "counselor_chat" && (
                  <ChatMessage message={msg} payload={hitlPayload} />
                )}
              {index === messages.length - 1 &&
                msg.role === "system" &&
                hitlPayload?.type === "counselor_chat" && (
                  <CounselorApproveBar
                    payload={hitlPayload}
                    onApprove={(editedDraft) =>
                      handleSend(null, {
                        approved: true,
                        edited_draft: editedDraft ?? null,
                      })
                    }
                    onReject={() =>
                      handleSend(null, { approved: false, edited_draft: null })
                    }
                  />
                )}
            </div>
          ))}

          {isTyping && <TypingIndicator />}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <ChatInput
        value={inputValue}
        onChange={setInputValue}
        onSubmit={handleInputSubmit}
        disabled={isTyping}
        placeholder={
          isAwaitingApproval
            ? "Ketik di sini untuk menambah cerita..."
            : "Type your message..."
        }
      />
    </main>
  );
}
