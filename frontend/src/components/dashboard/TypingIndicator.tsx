export function TypingIndicator() {
  return (
    <div className="flex justify-start animate-in fade-in">
      <div className="w-8 h-8 rounded-full bg-[#8A38F5] shrink-0 mr-4 flex items-center justify-center shadow-sm">
        <span className="text-white text-xs font-bold">AI</span>
      </div>
      <div className="bg-[#FFFFFF] border border-[#E5E7EB] rounded-[20px] rounded-tl-none px-6 py-4 shadow-sm flex gap-1 items-center">
        <div className="w-1.5 h-1.5 bg-[#8A38F5] rounded-full animate-bounce [animation-delay:-0.3s]"></div>
        <div className="w-1.5 h-1.5 bg-[#8A38F5] rounded-full animate-bounce [animation-delay:-0.15s]"></div>
        <div className="w-1.5 h-1.5 bg-[#8A38F5] rounded-full animate-bounce"></div>
      </div>
    </div>
  );
}
