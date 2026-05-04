"use client";

import { Inter } from "next/font/google";
import Link from "next/link";
import { useDemoChat } from "@/hooks/useDemoChat";
import { ChatMessage } from "@/components/dashboard/ChatMessage";
import { TypingIndicator } from "@/components/dashboard/TypingIndicator";

const inter = Inter({ subsets: ["latin"] });

export default function DemoPage() {
  const {
    messages,
    inputValue,
    setInputValue,
    isTyping,
    isLimitReached,
    messageCount,
    messagesEndRef,
    handleSend
  } = useDemoChat();

  return (
    <div className={`flex flex-col h-screen bg-white ${inter.className}`}>
      
      {/* HEADER */}
      <header className="px-8 py-5 flex justify-between items-center border-b border-gray-100 shrink-0">
        <Link
          href="/"
          className="flex items-center gap-3 text-[15px] text-[#717182] hover:text-[#0A0A0A] transition-colors"
        >
          <img 
            src="/images-button/Icon%20Back%20To%20Home.webp" 
            alt="Back" 
            className="w-5 h-5 object-contain"
          />
          Back to Home
        </Link>
        <div className="flex items-center gap-3">
          <span className="text-[14px] text-[#717182]">Demo Mode</span>
          <div className="bg-[#D3C1FF] text-[#8A38F5] px-4 py-1.5 rounded-full text-[13px] font-semibold">
            {messageCount}/3 messages
          </div>
        </div>
      </header>

      {/* MAIN CHAT AREA */}
      <main className="flex-1 overflow-y-auto p-6 md:p-12 flex justify-center">
        <div className="w-full max-w-4xl flex flex-col gap-8">
          {messages.map((msg, idx) => (
            <ChatMessage 
              key={idx} 
              message={msg} 
              showAvatar={false} 
            />
          ))}

          {isTyping && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-100 px-6 py-5 rounded-[20px] shadow-sm">
                <TypingIndicator />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* FOOTER */}
      <footer className="p-8 flex justify-center border-t border-gray-100 shrink-0 bg-[#F9FAFB]">
        {isLimitReached ? (
          <div className="bg-white border border-[#E5E7EB] rounded-[20px] p-10 w-full max-w-4xl text-center shadow-sm flex flex-col items-center">
             <div className="w-12 h-12 bg-[#F3E8FF] rounded-2xl flex items-center justify-center mb-4">
                <img src="/images-homepage/AI%20Clarifies%20&%20Prioritizes.webp" alt="AI" className="w-6 h-6 object-contain" />
             </div>
             <h3 className="text-[22px] font-bold text-[#0A0A0A] mb-2">Demo Limit Reached</h3>
             <p className="text-[#717182] text-[16px] mb-8 max-w-md">
               Unlock unlimited conversations and full AI-powered scheduling by signing up for free.
             </p>
             <Link
               href="/auth/register"
               className="bg-[#8A38F5] text-white px-10 py-3.5 rounded-xl text-[16px] font-semibold hover:bg-[#7b32db] transition-all shadow-md"
             >
               Sign Up Free
             </Link>
          </div>
        ) : (
          <div className="w-full max-w-4xl flex items-center gap-4">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Write all your thoughts, tasks, and plans freely..."
              className="flex-1 bg-white border border-[#E5E7EB] rounded-[16px] px-6 py-4 text-[15px] text-[#0A0A0A] focus:outline-none focus:border-[#8A38F5] shadow-sm transition-all"
              disabled={isTyping}
            />
            <button
              onClick={handleSend}
              disabled={isTyping || !inputValue.trim()}
              className="shrink-0 hover:scale-105 transition-all disabled:opacity-50"
            >
              <img 
                src="/images-button/Send%20Button.webp" 
                alt="Send" 
                className="w-[52px] h-[52px] object-contain"
              />
            </button>
          </div>
        )}
      </footer>
    </div>
  );
}
