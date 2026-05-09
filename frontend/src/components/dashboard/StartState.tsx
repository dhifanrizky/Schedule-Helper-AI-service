import Link from "next/link";
import { FormEvent, useState } from "react";
import { ResumeData } from "@/hooks/useChat";
import { UserProfile } from "@/types";
import { QuestionnaireCard } from "./QuestionnaireCard";
import { removeChatSession } from "@/utils/removeChatMsgs";

interface StartStateProps {
  user: UserProfile | null;
  isUserLoading: boolean;
  userInitial: string;
  inputValue: string;
  setInputValue: (val: string) => void;
  isTyping: boolean;
  handleSend: (
    e: FormEvent | null,
    resumeData?: ResumeData,
    questionnaireData?: {
      energyLevel: number;
      mood: number;
      availableTime: string;
    },
  ) => void;
  energyLevel: number;
  setEnergyLevel: (val: number) => void;
  mood: number;
  setMood: (val: number) => void;
  availableTime: string;
  setAvailableTime: (val: string) => void;
  isDropdownOpen: boolean;
  setIsDropdownOpen: (val: boolean) => void;
}

export function StartState({
  user,
  isUserLoading,
  userInitial,
  inputValue,
  setInputValue,
  isTyping,
  handleSend,
  energyLevel,
  setEnergyLevel,
  mood,
  setMood,
  availableTime,
  setAvailableTime,
  isDropdownOpen,
  setIsDropdownOpen,
}: StartStateProps) {
  const [isQuestionnaireVisible, setIsQuestionnaireVisible] = useState(true);
  const [isQuestionnaireCompleted, setIsQuestionnaireCompleted] =
    useState(false);

  const handleFirstMessageSubmit = (event: FormEvent | null) => {
    handleSend(event, undefined, { energyLevel, mood, availableTime });
  };

  const handleQuestionnaireComplete = () => {
    setIsQuestionnaireCompleted(true);
    setIsQuestionnaireVisible(false);
  };

  return (
    <div className="flex-col min-h-screen bg-linear-to-b from-[#FFFFFF] to-[#B597FF] transition-all duration-500 ease-in-out w-full align-middle max-h-screen fade-out-30">
      <header className="w-full flex items-center justify-between p-6 sm:px-10 max-w-360 mx-auto"></header>

      <main className="flex-1 flex flex-col h-full items-center justify-center px-6 text-center animate-in fade-in zoom-in duration-500 pb-40">
        {isQuestionnaireVisible ? (
          <QuestionnaireCard
            energyLevel={energyLevel}
            setEnergyLevel={setEnergyLevel}
            mood={mood}
            setMood={setMood}
            availableTime={availableTime}
            setAvailableTime={setAvailableTime}
            isDropdownOpen={isDropdownOpen}
            setIsDropdownOpen={setIsDropdownOpen}
            onComplete={handleQuestionnaireComplete}
          />
        ) : (
          <>
            <h1 className="w-45.75 mx-auto text-[40px] font-bold text-[#8A38F5] leading-6 mb-6 [text-shadow:0px_4px_4px_rgba(0,0,0,0.25)]">
              Hi There!
            </h1>
            <p
              className={`w-75 mx-auto text-[16px] font-normal text-[#0A0A0A] leading-6 ${isQuestionnaireVisible ? "mb-2" : "mb-10"} [text-shadow:0px_4px_4px_rgba(0,0,0,0.25)]`}
            >
              I'm here to help organize your tasks
            </p>
            <div className="w-full max-w-200 flex flex-col items-center gap-4">
              <button
                type="button"
                onClick={() => setIsQuestionnaireVisible(true)}
                className="text-[14px] font-medium text-[#8A38F5] hover:text-[#ffffff] transition-colors cursor-pointer"
              >
                Edit questionnaire
              </button>
              <form
                onSubmit={handleFirstMessageSubmit}
                className="w-full bg-white rounded-full shadow-[0_4px_20px_rgb(0,0,0,0.06)] py-3.5 pl-8 pr-3.5 flex items-center gap-4 transition-transform hover:scale-[1.01]"
              >
                <input
                  type="text"
                  maxLength={500}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Write down everything on your mind - all your tasks, thoughts, and plans."
                  className="flex-1 bg-transparent border-none focus:outline-none focus:ring-0 text-[#0A0A0A]/70 text-[16px] placeholder:text-[16px]"
                  disabled={isTyping || !isQuestionnaireCompleted}
                />
                {inputValue.trim() && (
                  <button
                    type="submit"
                    disabled={isTyping || !isQuestionnaireCompleted}
                    className="shrink-0 transition-all hover:scale-110 active:scale-95 disabled:opacity-50 rounded-full overflow-clip"
                  >
                    <img
                      src="/images-button/Send%20Button.webp"
                      alt="Send"
                      className="w-11 h-11 object-contain"
                    />
                  </button>
                )}
              </form>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
