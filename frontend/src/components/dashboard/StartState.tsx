import Link from "next/link";
import { FormEvent } from "react";
import { ResumeData } from "@/hooks/useChat";
import { UserProfile } from "@/types";

interface StartStateProps {
  user: UserProfile | null;
  isUserLoading: boolean;
  userInitial: string;
  inputValue: string;
  setInputValue: (val: string) => void;
  isTyping: boolean;
  handleSend: (e: FormEvent | null, resumeData?: ResumeData) => void;
}

export function StartState({
  user,
  isUserLoading,
  userInitial,
  inputValue,
  setInputValue,
  isTyping,
  handleSend
}: StartStateProps) {
  return (
    <div className="flex-col min-h-screen bg-linear-to-b from-[#FFFFFF] to-[#B597FF] transition-all duration-500 ease-in-out w-full align-middle max-h-screen ">
      <header className="w-full flex items-center justify-between p-6 sm:px-10 max-w-360 mx-auto">
        <Link
          href="/"
          onClick={() => {
            sessionStorage.removeItem("chat_messages");
          }}
          className="text-[20px] font-bold text-[#0A0A0A] cursor-pointer no-underline"
        >
          Schedule Helper
        </Link>
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

      <main className="flex-1 flex flex-col h-full items-center justify-center px-6 text-center animate-in fade-in zoom-in duration-500 pb-40">
        <h1 className="w-45.75 mx-auto text-[40px] font-bold text-[#8A38F5] leading-6 mb-6 [text-shadow:0px_4px_4px_rgba(0,0,0,0.25)]">
          Hi There!
        </h1>
        <p className="w-75 mx-auto text-[16px] font-normal text-[#0A0A0A] leading-6 mb-10 [text-shadow:0px_4px_4px_rgba(0,0,0,0.25)]">
          Hi! I'm here to help organize your tasks
        </p>

        <form
          onSubmit={handleSend}
          className="w-full max-w-200 bg-white rounded-full shadow-[0_4px_20px_rgb(0,0,0,0.06)] py-3.5 pl-8 pr-3.5 flex items-center gap-4 transition-transform hover:scale-[1.01]"
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
          {inputValue.trim() && (
            <button
              type="submit"
              disabled={isTyping}
              className="shrink-0 transition-all hover:scale-110 active:scale-95 disabled:opacity-50"
            >
              <img
                src="/images-button/Send%20Button.webp"
                alt="Send"
                className="w-11 h-11 object-contain"
              />
            </button>
          )}
        </form>
      </main>
    </div>
  );
}
