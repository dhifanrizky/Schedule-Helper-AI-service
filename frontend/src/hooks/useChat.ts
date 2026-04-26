import { useState, useEffect, useRef } from "react";
import { Message } from "@/types";
import { chatService } from "@/services/chatService";

/**
 * Hook untuk mengelola state percakapan chat antara user dan AI.
 * Menangani pengiriman pesan, riwayat, dan auto-scroll.
 */
export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isStarted, setIsStarted] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Muat riwayat saat awal mount
  useEffect(() => {
    const savedMessages = chatService.getStoredMessages();
    if (savedMessages.length > 0) {
      setMessages(savedMessages);
      setIsStarted(true);
    }
  }, []);

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
    if (!userText || isTyping) return;

    if (!isStarted) setIsStarted(true);

    const newUserMessage: Message = { role: "user", content: userText };
    const updatedMessages = [...messages, newUserMessage];
    
    setMessages(updatedMessages);
    setInputValue("");
    setIsTyping(true);

    try {
      const aiResponse = await chatService.sendMessage(userText, updatedMessages);
      setMessages((prev) => [...prev, aiResponse]);
    } catch (error) {
      console.error("Chat Error:", error);
      setMessages((prev) => [
        ...prev,
        { role: "ai", content: "Sorry, I'm having trouble connecting. Please try again." }
      ]);
    } finally {
      setIsTyping(false);
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
      setMessages([]);
      setIsStarted(false);
    }
  };
}
