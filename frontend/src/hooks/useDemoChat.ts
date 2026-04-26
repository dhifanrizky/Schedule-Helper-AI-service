import { useState, useEffect, useRef } from "react";
import { Message } from "@/types";

/**
 * HOOK: Mengelola logika percakapan khusus untuk halaman DEMO.
 * Versi perbaikan sesuai desain asli (Gambar 1).
 */
export function useDemoChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "ai",
      content: "Welcome to Schedule Helper! Write all your thoughts, tasks, and plans freely. I'll help you organize them.",
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isLimitReached, setIsLimitReached] = useState(false);
  const [messageCount, setMessageCount] = useState(1);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const handleSend = async () => {
    if (!inputValue.trim() || isLimitReached) return;

    const userMessage: Message = { role: "user", content: inputValue };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsTyping(true);
    setMessageCount((prev) => prev + 1);

    setTimeout(() => {
      const assistantMessage: Message = {
        role: "ai",
        content: "Thanks for sharing! I can see you have several tasks. Let me ask a few questions to help prioritize. Which of these tasks has the most urgent deadline?",
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setIsTyping(false);
      
      const newCount = messageCount + 1;
      if (newCount >= 3) {
        setIsLimitReached(true);
      }
    }, 1500);
  };

  return {
    messages,
    inputValue,
    setInputValue,
    isTyping,
    isLimitReached,
    messageCount,
    messagesEndRef,
    handleSend
  };
}
