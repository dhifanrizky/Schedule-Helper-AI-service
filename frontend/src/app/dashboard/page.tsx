"use client";

import { useState, useEffect, useRef, FormEvent } from "react";

type Message = {
  role: "user" | "ai";
  content: string;
};

type UserProfile = {
  name: string;
  email: string;
};

export default function DashboardPage() {
  const [isStarted, setIsStarted] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 1. Persistensi Chat menggunakan SessionStorage
  useEffect(() => {
    // Muat pesan saat awal mount
    const savedMessages = sessionStorage.getItem("chat_messages");
    if (savedMessages) {
      const parsed = JSON.parse(savedMessages);
      if (parsed.length > 0) {
        setMessages(parsed);
        setIsStarted(true);
      }
    }
  }, []);

  useEffect(() => {
    // Simpan pesan setiap kali ada perubahan, dan dispatch event
    if (messages.length > 0) {
      sessionStorage.setItem("chat_messages", JSON.stringify(messages));
      window.dispatchEvent(new Event("chat_updated"));
    }
  }, [messages]);

  // Fetching simulation ONLY for Start State Header
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isUserLoading, setIsUserLoading] = useState(true);

  useEffect(() => {
    if (isStarted) return; // Tidak perlu fetch ulang jika sudah masuk Chat State (diurus Layout)
    const fetchUser = async () => {
      try {
        await new Promise((res) => setTimeout(res, 2500));
        setUser({ name: "Dipson", email: "dipson@gmail.com" });
      } catch (e) {
        console.error(e);
      } finally {
        setIsUserLoading(false);
      }
    };
    fetchUser();
  }, [isStarted]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (isStarted) {
      scrollToBottom();
    }
  }, [messages, isTyping, isStarted]);

  // 4. Chat Interaction & Security (Input Guard & Sanitization)
  const handleSend = async (e: FormEvent) => {
    e.preventDefault();
    const userText = inputValue.trim();
    if (!userText || isTyping) return;

    if (!isStarted) {
      setIsStarted(true);
    }

    setMessages((prev) => [...prev, { role: "user", content: userText }]);
    setInputValue("");
    setIsTyping(true);

    try {
      /* 
       [BACKEND INTEGRATION PLACEHOLDER]
      */

      // Simulasi delay backend
      await new Promise((resolve) => setTimeout(resolve, 1000));
      
      const simulatedResponse = "Great! I can see several tasks here. Which of these is most urgent or has the closest deadline?";
      
      // Sanitization: React natively escapes HTML tags in strings.
      setMessages((prev) => [...prev, { role: "ai", content: simulatedResponse }]);
    } catch (error) {
      console.error("AI Assistant Error:", error);
      // Null & Error Handling: Graceful degradation
      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          content: "Sorry, Schedule Helper is having trouble connecting. Please try again.",
        },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  const userInitial = user?.name ? user.name.charAt(0).toUpperCase() : "";

  // 1. Core Layout Strategy - Start State
  if (!isStarted) {
    return (
      <div className="flex flex-col min-h-screen bg-gradient-to-b from-[#FFFFFF] to-[#B597FF] transition-all duration-500 ease-in-out">
        <header className="w-full flex items-center justify-between p-6 sm:px-10 max-w-[1440px] mx-auto">
          <div className="text-[20px] font-bold text-[#0A0A0A]">
            Schedule Helper
          </div>
          <div>
            {isUserLoading || !user ? (
              <div className="w-10 h-10 bg-[#C2C2C2] rounded-full animate-pulse" />
            ) : (
              <div className="w-10 h-10 bg-[#0A0A0A] text-white rounded-full flex items-center justify-center font-semibold text-[15px] cursor-pointer shadow-sm animate-in fade-in duration-300">
                {userInitial}
              </div>
            )}
          </div>
        </header>

        <main className="flex-1 flex flex-col items-center justify-center px-6 text-center animate-in fade-in zoom-in duration-500 pb-20">
          <h1 className="w-[183px] mx-auto text-[40px] font-bold text-[#8A38F5] leading-[24px] mb-6 [text-shadow:0px_4px_4px_rgba(0,0,0,0.25)]">
            Hi There!
          </h1>
          <p className="w-[300px] mx-auto text-[16px] font-normal text-[#0A0A0A] leading-[24px] mb-10 [text-shadow:0px_4px_4px_rgba(0,0,0,0.25)]">
            Hi! I'm here to help organize your tasks
          </p>

          <form
            onSubmit={handleSend}
            className="w-full max-w-[800px] bg-white rounded-full shadow-[0_4px_20px_rgb(0,0,0,0.06)] py-3.5 pl-8 pr-3.5 flex items-center gap-4 transition-transform hover:scale-[1.01]"
          >
            <input
              type="text"
              maxLength={500}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Write down everything on your mind - all your tasks, thoughts, and plans."
              className="flex-1 bg-transparent border-none focus:outline-none focus:ring-0 text-[#0A0A0A]/70 text-[16px]"
              disabled={isTyping}
            />
            {/* Hanya tampilkan tombol jika ada input, untuk mencocokkan desain yang terlihat clean saat kosong */}
            {inputValue.trim() && (
              <button
                type="submit"
                disabled={isTyping}
                className="shrink-0 hover:scale-105 transition-transform animate-in zoom-in duration-200"
              >
                <img src="/images%20button/Send%20Button.webp" alt="Send" className="w-[44px] h-[44px] object-contain" />
              </button>
            )}
          </form>
        </main>
      </div>
    );
  }

  // 2. Active Chat State (Sidebar dikendalikan oleh layout.tsx)
  return (
    <main className="flex-1 flex flex-col h-full bg-[#FFFFFF]">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-6 pt-10 pb-6">
        <div className="max-w-4xl mx-auto flex flex-col gap-8">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex ${
                msg.role === "user" ? "justify-end" : "justify-start"
              } animate-in fade-in slide-in-from-bottom-2 duration-300`}
            >
              {msg.role === "ai" && (
                <div className="w-8 h-8 rounded-full bg-[#8A38F5] shrink-0 mr-4 flex items-center justify-center shadow-sm">
                  <span className="text-white text-xs font-bold">AI</span>
                </div>
              )}
              <div
                className={`max-w-[80%] rounded-[20px] px-6 py-4 text-[15px] leading-relaxed shadow-sm ${
                  msg.role === "user"
                    ? "bg-[#B597FF] text-white rounded-tr-none"
                    : "bg-[#FFFFFF] text-[#0A0A0A] border border-[#E5E7EB] rounded-tl-none"
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}
          {isTyping && (
            <div className="flex justify-start animate-in fade-in">
              <div className="w-8 h-8 rounded-full bg-[#8A38F5] shrink-0 mr-4 flex items-center justify-center shadow-sm">
                <span className="text-white text-xs font-bold">AI</span>
              </div>
              <div className="bg-[#FFFFFF] border border-[#E5E7EB] text-[#0A0A0A] rounded-[20px] rounded-tl-none px-6 py-5 flex gap-1.5 items-center shadow-sm">
                <div className="w-2 h-2 bg-[#B597FF] rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                <div className="w-2 h-2 bg-[#B597FF] rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                <div className="w-2 h-2 bg-[#B597FF] rounded-full animate-bounce"></div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area (Bottom Fixed with Border Top) */}
      <div className="w-full bg-[#FFFFFF] border-t border-gray-100 p-6 shrink-0 flex justify-center">
        <form
          onSubmit={handleSend}
          className="max-w-4xl w-full bg-[#FFFFFF] border border-[#E5E7EB] rounded-full py-3.5 pl-6 pr-3.5 flex items-center gap-4 transition-all focus-within:border-[#D1D5DB] focus-within:shadow-[0_2px_10px_rgb(0,0,0,0.02)]"
        >
          <input
            type="text"
            maxLength={500}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Type your reply here..."
            className="flex-1 bg-transparent border-none focus:outline-none focus:ring-0 text-[#717182] placeholder:text-[#9CA3AF] text-[15px]"
            disabled={isTyping}
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || isTyping}
            className="shrink-0 disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 transition-transform"
          >
            <img src="/images%20button/Send%20Button.webp" alt="Send" className="w-[44px] h-[44px] object-contain" />
          </button>
        </form>
      </div>
    </main>
  );
}
