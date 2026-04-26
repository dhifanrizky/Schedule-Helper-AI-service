import { FormEvent, useEffect } from "react";
import { Message } from "@/types";
import { ChatMessage } from "./ChatMessage";
import { TypingIndicator } from "./TypingIndicator";
import { QuestionnaireCard } from "./QuestionnaireCard";
import { ChatInput } from "./ChatInput";

interface ChatStateProps {
  messages: Message[];
  isTyping: boolean;
  inputValue: string;
  setInputValue: (val: string) => void;
  handleSend: (e: FormEvent) => void;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
  // Questionnaire props
  energyLevel: number;
  setEnergyLevel: (val: number) => void;
  mood: number;
  setMood: (val: number) => void;
  availableTime: string;
  setAvailableTime: (val: string) => void;
  isDropdownOpen: boolean;
  setIsDropdownOpen: (val: boolean) => void;
  handleGenerateSchedule: () => void;
}

export function ChatState({
  messages,
  isTyping,
  inputValue,
  setInputValue,
  handleSend,
  messagesEndRef,
  energyLevel,
  setEnergyLevel,
  mood,
  setMood,
  availableTime,
  setAvailableTime,
  isDropdownOpen,
  setIsDropdownOpen,
  handleGenerateSchedule
}: ChatStateProps) {
  
  // Auto-scroll logic inside component
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const triggerText = "Perfect! Now let me understand your current state to create the best schedule for you.";

  return (
    <main className="flex-1 flex flex-col h-full bg-[#FFFFFF]">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-6 pt-10 pb-6">
        <div className="max-w-4xl mx-auto flex flex-col gap-8">
          {messages.map((msg, index) => (
            <div key={index} className="flex flex-col gap-4">
              <ChatMessage message={msg} />

              {/* Form Card Questionnaire Trigger */}
              {index === messages.length - 1 &&
                msg.role === "ai" &&
                msg.content === triggerText && (
                  <QuestionnaireCard
                    energyLevel={energyLevel}
                    setEnergyLevel={setEnergyLevel}
                    mood={mood}
                    setMood={setMood}
                    availableTime={availableTime}
                    setAvailableTime={setAvailableTime}
                    isDropdownOpen={isDropdownOpen}
                    setIsDropdownOpen={setIsDropdownOpen}
                    onGenerate={handleGenerateSchedule}
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
        onSubmit={handleSend}
        disabled={isTyping}
      />
    </main>
  );
}
