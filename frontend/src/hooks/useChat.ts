import { useMemo, useEffect, useRef, useState } from "react";
import { TextStreamChatTransport, type UIMessage } from "ai";
import { useChat as useAiChat } from "ai/react";
import { Message } from "@/types";
import { chatService } from "@/services/chatService";

/**
 * Hook untuk mengelola state percakapan chat antara user dan AI.
 * Menangani pengiriman pesan, riwayat, dan auto-scroll.
 */
function mapUiMessageToText(message: UIMessage) {
  return message.parts
    .map((part) => (part.type === "text" ? part.text : ""))
    .join("")
    .trim();
}

export function useChat(userId?: string) {
  const [inputValue, setInputValue] = useState("");
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const {
    messages: uiMessages,
    sendMessage,
    setMessages: setUiMessages,
    status,
  } = useAiChat({
    transport: new TextStreamChatTransport({
      api: "/api/chat/stream",
      headers: {
        Authorization: typeof window !== "undefined" && sessionStorage.getItem("app_token")
          ? `Bearer ${sessionStorage.getItem("app_token")}`
          : "",
      },
      body: () => ({ user_id: userId ?? "anonymous" }),
    }),
  });

  const messages = useMemo<Message[]>(() => {
    return uiMessages
      .map((message) => {
        const content = mapUiMessageToText(message);

        if (!content) {
          return null;
        }

        return {
          role: message.role === "user" ? "user" : "ai",
          content,
        } satisfies Message;
      })
      .filter((message): message is Message => message !== null);
  }, [uiMessages]);

  const isTyping = status === "submitted" || status === "streaming";
  const isStarted = messages.length > 0;

  // Simpan riwayat setiap ada perubahan
  useEffect(() => {
    chatService.saveMessages(messages);
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();

    const userText = inputValue.trim();
    if (!userText || isTyping) {
      return;
    }

    setInputValue("");

    try {
      await sendMessage({ text: userText });
    } catch (error) {
      console.error("Chat Error:", error);
      setUiMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: "assistant",
          parts: [
            {
              type: "text",
              text: "Sorry, I'm having trouble connecting. Please try again.",
            },
          ],
        },
      ]);
    }
  };

  return {
    messages,
    inputValue,
    setInputValue,
    isTyping,
    isStarted,
    messagesEndRef,
    handleSend,
    scrollToBottom,
    clearChat: () => {
      chatService.clearChat();
      setUiMessages([]);
    },
  };
}
