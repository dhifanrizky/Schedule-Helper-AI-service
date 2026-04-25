interface QuestionnaireCardProps {
  energyLevel: number;
  setEnergyLevel: (val: number) => void;
  mood: number;
  setMood: (val: number) => void;
  availableTime: string;
  setAvailableTime: (val: string) => void;
  isDropdownOpen: boolean;
  setIsDropdownOpen: (val: boolean) => void;
  onGenerate: () => void;
}

export function QuestionnaireCard({
  energyLevel,
  setEnergyLevel,
  mood,
  setMood,
  availableTime,
  setAvailableTime,
  isDropdownOpen,
  setIsDropdownOpen,
  onGenerate
}: QuestionnaireCardProps) {
  const timeOptions = ["Less than 2 Hours", "2 - 4 Hours", "4 - 6 Hours", "More than 6 Hours"];

  return (
    <div className="w-full max-w-2xl bg-white border border-[#E5E7EB] rounded-[20px] p-6 shadow-sm mt-4 animate-in fade-in slide-in-from-bottom-4 duration-500 self-center">
      <h3 className="text-[18px] font-semibold text-[#0A0A0A] mb-8 font-inter">
        How are you feeling right now?
      </h3>

      {/* Energy Level */}
      <div className="mb-10">
        <label className="text-[14px] text-[#717182] font-medium block mb-4 font-inter">
          Energy Level
        </label>
        <div className="flex justify-between items-center px-2 mb-3">
          <img src="/images-dashboard/Energy%20Level%201.webp" alt="Low" className="w-8 h-8 object-contain" />
          <img src="/images-dashboard/Energy%20Level%202.webp" alt="Medium" className="w-8 h-8 object-contain" />
          <img src="/images-dashboard/Energy%20Level%203.webp" alt="High" className="w-8 h-8 object-contain" />
        </div>
        <input
          type="range"
          min="1" max="3" step="1"
          value={energyLevel}
          onChange={(e) => setEnergyLevel(Number(e.target.value))}
          style={{ background: `linear-gradient(to right, #8A38F5 ${(energyLevel - 1) * 50}%, #E5E7EB ${(energyLevel - 1) * 50}%)` }}
          className="w-full h-2 rounded-lg appearance-none cursor-pointer accent-[#8A38F5] outline-none"
        />
      </div>

      {/* Mood */}
      <div className="mb-10">
        <label className="text-[14px] text-[#717182] font-medium block mb-4 font-inter">
          Mood
        </label>
        <div className="flex justify-between items-center px-2 mb-3">
          <img src="/images-dashboard/Happy%20Icon.webp" alt="Happy" className="w-8 h-8 object-contain" />
          <img src="/images-dashboard/Medium%20Icon.webp" alt="Medium" className="w-8 h-8 object-contain" />
          <img src="/images-dashboard/Stressed%20Icon.webp" alt="Stressed" className="w-8 h-8 object-contain" />
        </div>
        <input
          type="range"
          min="1" max="3" step="1"
          value={mood}
          onChange={(e) => setMood(Number(e.target.value))}
          style={{ background: `linear-gradient(to right, #8A38F5 ${(mood - 1) * 50}%, #E5E7EB ${(mood - 1) * 50}%)` }}
          className="w-full h-2 rounded-lg appearance-none cursor-pointer accent-[#8A38F5] outline-none"
        />
      </div>

      {/* Available Time */}
      <div className="mb-8 relative">
        <label className="text-[14px] text-[#717182] font-medium block mb-3 font-inter">
          Available Time Today
        </label>
        <div
          onClick={() => setIsDropdownOpen(!isDropdownOpen)}
          className="w-full border border-[#E5E7EB] rounded-[10px] px-4 py-3.5 flex items-center justify-between cursor-pointer hover:bg-gray-50 transition-colors bg-white"
        >
          <div className="flex items-center gap-3">
            <svg className="w-[18px] h-[18px] text-[#717182]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className={`text-[15px] font-inter ${availableTime ? "text-[#0A0A0A]" : "text-[#717182]"}`}>
              {availableTime || "Select Time Available"}
            </span>
          </div>
          <svg className={`w-5 h-5 text-gray-400 transition-transform duration-200 ${isDropdownOpen ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
          </svg>
        </div>

        {isDropdownOpen && (
          <div className="absolute top-full left-0 w-full mt-2 bg-white border border-[#E5E7EB] rounded-[10px] shadow-lg z-50 py-2 animate-in fade-in slide-in-from-top-2">
            {timeOptions.map((option) => (
              <div
                key={option}
                onClick={() => {
                  setAvailableTime(option);
                  setIsDropdownOpen(false);
                }}
                className="px-4 py-3 hover:bg-gray-50 text-[14px] text-[#0A0A0A] cursor-pointer transition-colors"
              >
                {option}
              </div>
            ))}
          </div>
        )}
      </div>

      <button
        onClick={onGenerate}
        disabled={!availableTime}
        className="w-full bg-[#8A38F5] text-white py-4 rounded-[12px] font-semibold text-[15px] font-inter shadow-md hover:bg-[#7b32db] disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-[0.98]"
      >
        Generate My Schedule
      </button>
    </div>
  );
}
