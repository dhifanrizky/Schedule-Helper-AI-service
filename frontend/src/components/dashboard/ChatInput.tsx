import { FormEvent } from "react";

interface ChatInputProps {
  value: string;
  onChange: (val: string) => void;
  onSubmit: (e: FormEvent) => void;
  disabled: boolean;
}

export function ChatInput({ value, onChange, onSubmit, disabled }: ChatInputProps) {
  return (
    <div className="w-full bg-[#FFFFFF] border-t border-gray-100 p-6 shrink-0 flex justify-center">
      <form
        onSubmit={onSubmit}
        className="w-full max-w-[800px] bg-[#F9FAFB] border border-[#E5E7EB] rounded-full px-6 py-3 flex items-center gap-4 transition-all focus-within:border-[#8A38F5] focus-within:bg-white focus-within:shadow-md"
      >
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Type your message..."
          disabled={disabled}
          className="flex-1 bg-transparent border-none focus:outline-none focus:ring-0 text-[#0A0A0A] text-[15px] font-inter"
        />
        <button
          type="submit"
          disabled={!value.trim() || disabled}
          className="shrink-0 disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 transition-transform rounded-full overflow-clip"
        >
          <img
            src="/images-button/Send%20Button.webp"
            alt="Send"
            className="w-[44px] h-[44px] object-contain"
          />
        </button>
      </form>
    </div>
  );
}
