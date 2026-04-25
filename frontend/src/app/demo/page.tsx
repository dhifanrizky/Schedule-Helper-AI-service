"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

type Message = {
  role: "ai" | "user";
  content: string;
};

export default function DemoPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [userMessageCount, setUserMessageCount] = useState(0);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isLimitReached, setIsLimitReached] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    // 4. Input Validation: Lakukan trimming.
    const userText = inputValue.trim();
    if (!userText || isTyping || isLimitReached) return;

    setMessages((prev) => [...prev, { role: "user", content: userText }]);
    setInputValue("");

    // 5. Loading States: Set mengetik saat menunggu backend.
    setIsTyping(true);

    try {
      /* 
        [BACKEND INTEGRATION PLACEHOLDER]
        ========================================================
        const res = await fetch("/api/ai", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: userText }),
        });
        if (!res.ok) throw new Error("Server error");
        const data = await res.json();
      */

      // Simulasi backend response & delay
      await new Promise((resolve) => setTimeout(resolve, 1000));
      // Simulasi backend mengecek limit:
      const simulatedCount = userMessageCount + 1;
      const data: any = {
        message: "",
        current_count: simulatedCount,
        demo_limit_reached: simulatedCount >= 3,
      };

      // 2. Null & Error Handling: Cek format jika backend mengirim data kacau
      if (!data || typeof data.demo_limit_reached !== "boolean") {
        throw new Error("Invalid response format from backend.");
      }

      // Sinkronkan UI dengan counter dan limit dari backend
      if (typeof data.current_count === "number") {
        setUserMessageCount(data.current_count);
      }

      // 3. State Management (Demo Limit)
      if (data.demo_limit_reached === true) {
        setIsLimitReached(true);
      }

      // 1. Data Sanitization: Pastikan hanya render string valid. (React secara bawaan sudah escape plain string xss)
      if (data.message && typeof data.message === "string") {
        setMessages((prev) => [...prev, { role: "ai", content: data.message }]);
      }
    } catch (error) {
      console.error("AI Assistant Error:", error);
      // 2. Graceful Degradation: Menampilkan pesan fallback yang ramah
      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          content:
            "Sorry, Schedule Helper is having trouble connecting. Please try again.",
        },
      ]);
    } finally {
      // Selesai status loading
      setIsTyping(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-[#FDFDFD]">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 bg-white border-b border-gray-100 z-10 sticky top-0">
        <Link
          href="/"
          className="flex items-center gap-2 text-gray-500 hover:text-gray-800 transition-colors text-[15px] font-medium"
        >
          <img
            src="/images-button/Icon%20Back%20To%20Home.webp"
            alt="Back to Home"
            className="w-5 h-5 object-contain"
          />
          Back to Home
        </Link>

        <div className="flex items-center gap-3">
          <span className="text-gray-500 text-[15px] font-medium">
            Demo Mode
          </span>
          <div className="bg-[#D3C1FF] text-[#8A38F5] px-3 py-1 rounded-full text-[14px] font-semibold">
            {userMessageCount}/3 messages
          </div>
        </div>
      </header>

      {/* Chat Area */}
      <main className="flex-1 overflow-y-auto px-6 py-8">
        <div className="max-w-3xl mx-auto flex flex-col gap-6">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${
                msg.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-[80%] sm:max-w-[70%] px-5 py-3.5 rounded-[20px] text-[15px] leading-relaxed shadow-sm ${
                  msg.role === "user"
                    ? "bg-[#B597FF] text-white rounded-br-sm"
                    : "bg-white text-gray-800 border border-gray-100 rounded-bl-sm"
                }`}
              >
                {/* React mengamankan string dengan sendirinya, tidak membutuhkan dangerouslySetInnerHTML */}
                {msg.content}
              </div>
            </div>
          ))}

          {isTyping && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-100 px-5 py-4 rounded-[20px] rounded-bl-sm shadow-sm flex items-center gap-2">
                <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" />
                <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce [animation-delay:0.2s]" />
                <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce [animation-delay:0.4s]" />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Footer / Input Area or Limit Reached */}
      <footer className="bg-white border-t border-gray-100 p-6 flex flex-col items-center">
        {isLimitReached ? (
          <div className="bg-[#030213]/5 border border-[#030213]/20 rounded-[14px] w-full max-w-[979px] h-[209px] flex flex-col items-center justify-center text-center">
            <img
              src="/images-homepage/AI%20Clarifies%20&%20Prioritizes.webp"
              alt="AI Icon"
              className="w-8 h-8 mb-3 object-contain"
            />
            <h3 className="text-[20px] font-semibold text-[#0A0A0A] mb-1">
              Demo Limit Reached
            </h3>
            <p className="text-[#717182] text-[15px] mb-5">
              Unlock unlimited conversations and full AI-powered scheduling by
              signing up.
            </p>
            <Link
              href="/auth/register"
              className="bg-[#8A38F5] hover:opacity-90 transition-opacity text-white text-[15px] font-medium px-8 py-2.5 rounded-[10px] shadow-sm"
            >
              Sign Up Free
            </Link>
          </div>
        ) : (
          <div className="w-full max-w-3xl mx-auto">
            <form onSubmit={handleSend} className="flex items-center gap-4">
              <input
                type="text"
                maxLength={500}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Write all your thoughts, tasks, and plans freely..."
                className="flex-1 bg-white border border-gray-200 rounded-full px-6 py-4 text-[15px] text-[#0A0A0A]/50 focus:outline-none focus:border-[#8A38F5] focus:ring-1 focus:ring-[#8A38F5] transition-all"
                disabled={isTyping}
              />
              <button
                type="submit"
                disabled={isTyping || !inputValue.trim()}
                className="shrink-0 rounded-full hover:scale-105 transition-transform disabled:opacity-50 disabled:hover:scale-100 cursor-pointer"
              >
                <img
                  src="/images-button/Send%20Button.webp"
                  alt="Send"
                  className="w-12 h-12 object-contain"
                />
              </button>
            </form>
          </div>
        )}
      </footer>
    </div>
  );
}
