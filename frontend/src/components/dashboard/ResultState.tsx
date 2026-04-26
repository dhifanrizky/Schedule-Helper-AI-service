import { ScheduleItem } from "@/types";

interface ResultStateProps {
  scheduleItems: ScheduleItem[];
  setScheduleItems: (items: ScheduleItem[]) => void;
  isEditingSchedule: boolean;
  setIsEditingSchedule: (val: boolean) => void;
  setIsResult: (val: boolean) => void;
  setIsAnalyzing: (val: boolean) => void;
}

export function ResultState({
  scheduleItems,
  setScheduleItems,
  isEditingSchedule,
  setIsEditingSchedule,
  setIsResult,
  setIsAnalyzing
}: ResultStateProps) {
  
  const handleRegenerate = async () => {
    setIsResult(false);
    setIsAnalyzing(true);
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setIsAnalyzing(false);
    setIsResult(true);
  };

  return (
    <main className="flex-1 flex flex-col h-full bg-[#FFFFFF] overflow-y-auto">
      <div className="w-full max-w-[1000px] mx-auto px-10 py-12 flex flex-col items-center">
        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-[28px] font-bold text-[#0A0A0A] font-inter mb-2">Your Personalized Schedule</h1>
          <p className="text-[15px] text-[#717182] font-inter">Here's your optimized action plan for today</p>
        </div>

        <div className="w-full max-w-3xl flex flex-col gap-6">
          {/* Top Priorities */}
          <div className="bg-white border border-[#E5E7EB] rounded-[16px] p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-6">
              <svg className="w-[18px] h-[18px] text-[#DC2626]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"></path>
              </svg>
              <h3 className="text-[16px] font-semibold text-[#0A0A0A] font-inter">Top Priorities</h3>
            </div>
            <div className="flex flex-col gap-4">
              {[
                { 
                  title: "Complete project proposal", 
                  urgency: "High", 
                  reason: "Closest deadline (tomorrow)", 
                  duration: "2 hours" 
                }
              ].map((item, idx) => (
                <div key={idx} className="border border-[#E5E7EB] rounded-[12px] p-5 flex flex-col gap-2">
                  <div className="flex justify-between items-start">
                    <h4 className="text-[15px] font-medium text-[#0A0A0A] font-inter">{item.title}</h4>
                    <span className={`text-[12px] font-medium px-2.5 py-1 rounded-full font-inter ${
                      item.urgency === "High" ? "bg-[#FEF2F2] text-[#DC2626]" : "bg-[#F3F4F6] text-[#4B5563]"
                    }`}>
                      {item.urgency}
                    </span>
                  </div>
                  <p className="text-[14px] text-[#717182] font-inter">{item.reason}</p>
                  <p className="text-[14px] text-[#717182] font-inter mt-1">Duration: {item.duration}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Wins */}
          <div className="bg-white border border-[#E5E7EB] rounded-[16px] p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-6">
              <img src="/images-dashboard/Quick%20Wins.webp" alt="Quick Wins" className="w-[18px] h-[18px] object-contain" />
              <h3 className="text-[16px] font-semibold text-[#0A0A0A] font-inter">Quick Wins</h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {[
                { title: "Reply to urgent emails", time: "15 min" },
                { title: "Update task tracker", time: "10 min" },
                { title: "Schedule next week's meetings", time: "20 min" },
                { title: "Review daily metrics", time: "10 min" }
              ].map((task, idx) => (
                <div key={idx} className="border border-[#E5E7EB] rounded-[12px] p-4 flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-[#F3E8FF] flex items-center justify-center shrink-0">
                    <img src="/images-dashboard/Ceklis.webp" alt="Check" className="w-full h-full object-contain scale-110" />
                  </div>
                  <div className="flex flex-col">
                    <span className="text-[14px] font-medium text-[#0A0A0A] font-inter">{task.title}</span>
                    <span className="text-[13px] text-[#717182] font-inter">{task.time}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Today's Schedule */}
          <div className="bg-white border border-[#E5E7EB] rounded-[16px] p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-6">
              <img src="/images-dashboard/Schedule.webp" alt="Schedule" className="w-[18px] h-[18px] object-contain opacity-70" />
              <h3 className="text-[16px] font-semibold text-[#0A0A0A] font-inter">Today's Schedule</h3>
            </div>
            <div className="flex flex-col gap-2.5">
              {scheduleItems.map((item, idx) => (
                <div key={idx} className="border border-[#E5E7EB] bg-[#F9FAFB] rounded-[10px] px-5 py-3 flex items-center min-h-[52px]">
                  {isEditingSchedule ? (
                    <div className="flex items-center gap-4 w-full">
                      <input
                        value={item.time}
                        onChange={(e) => {
                          const val = e.target.value;
                          if (/[a-zA-Z]/.test(val)) return;
                          const newItems = [...scheduleItems];
                          newItems[idx].time = val;
                          setScheduleItems(newItems);
                        }}
                        className="w-[140px] text-[14px] text-[#717182] border rounded px-2 py-1 outline-none focus:border-[#8A38F5]"
                      />
                      <input
                        value={item.title}
                        onChange={(e) => {
                          const newItems = [...scheduleItems];
                          newItems[idx].title = e.target.value;
                          setScheduleItems(newItems);
                        }}
                        className="flex-1 text-[14px] text-[#0A0A0A] font-medium border rounded px-2 py-1 outline-none focus:border-[#8A38F5]"
                      />
                    </div>
                  ) : (
                    <>
                      <span className="w-[140px] text-[14px] text-[#717182] font-inter">{item.time}</span>
                      <span className="text-[14px] text-[#0A0A0A] font-medium font-inter">{item.title}</span>
                    </>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* AI Reasoning */}
          <div className="bg-[#F9FAFB] border border-[#E5E7EB] rounded-[16px] p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <img src="/images-dashboard/AI%20Reasoning.webp" alt="AI Reasoning" className="w-[18px] h-[18px] object-contain" />
              <h3 className="text-[16px] font-semibold text-[#0A0A0A] font-inter">AI Reasoning</h3>
            </div>
            <p className="text-[14px] text-[#717182] leading-relaxed font-inter">
              Based on your medium energy level and neutral mood, I've scheduled your most demanding task during your peak hours.
            </p>
          </div>

          {/* Actions */}
          <div className="flex gap-4 mt-2">
            <button className="bg-[#8A38F5] text-white px-5 py-3 rounded-xl text-[14px] font-medium flex items-center gap-2 shadow-sm cursor-pointer hover:opacity-90 transition-opacity">
              <img src="/images-dashboard/Approved.webp" className="w-[18px] h-[18px] object-contain" alt="Approve" />
              Approve & Save Plan
            </button>
            <button
              onClick={() => setIsEditingSchedule(!isEditingSchedule)}
              className="bg-white border border-[#E5E7EB] text-[#0A0A0A] px-5 py-3 rounded-xl text-[14px] font-medium flex items-center gap-2 shadow-sm cursor-pointer hover:bg-gray-50 transition-colors"
            >
              <img src="/images-dashboard/Edit.webp" className="w-[18px] h-[18px]" alt="Edit" />
              {isEditingSchedule ? "Save Edits" : "Edit Plan"}
            </button>
            <button
              onClick={handleRegenerate}
              className="bg-white border border-[#E5E7EB] text-[#0A0A0A] px-5 py-3 rounded-xl text-[14px] font-medium flex items-center gap-2 shadow-sm cursor-pointer hover:bg-gray-50 transition-colors"
            >
              <img src="/images-dashboard/Regenerate.webp" className="w-[18px] h-[18px]" alt="Regenerate" />
              Regenerate
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}
