import { Message } from "@/types";

interface ChatMessageProps {
  message: Message;
  showAvatar?: boolean; // Tambahkan prop opsional
}

/**
 * Komponen Pesan Chat.
 */
export function ChatMessage({ message, showAvatar = true }: ChatMessageProps) {
  const isAi = message.role === "system";

  return (
    <div
      className={`flex ${!isAi ? "justify-end" : "justify-start"
        } animate-in fade-in slide-in-from-bottom-2 duration-300`}
    >
      {isAi && showAvatar && (
        <div className="w-8 h-8 rounded-full bg-[#8A38F5] shrink-0 mr-4 flex items-center justify-center shadow-sm">
          <span className="text-white text-xs font-bold">AI</span>
        </div>
      )}
      <div
        className={`max-w-[80%] rounded-[20px] px-6 py-4 text-[15px] leading-relaxed shadow-sm ${!isAi
            ? "bg-[#B597FF] text-white rounded-tr-none"
            : "bg-[#FFFFFF] text-[#0A0A0A] border border-[#E5E7EB] rounded-tl-none"
          }`}
        style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}
      >
        {message.content}
      </div>
    </div>
  );
}
