"use client";

import { type FormEvent, useEffect, useRef, useState } from "react";
import Link from "next/link";

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

  // Questionnaire States
  const [energyLevel, setEnergyLevel] = useState<number>(2);
  const [mood, setMood] = useState<number>(2);
  const [availableTime, setAvailableTime] = useState<string>("");
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  // Analyzing State
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isResult, setIsResult] = useState(false);
  const [isEditingSchedule, setIsEditingSchedule] = useState(false);
  const [scheduleItems, setScheduleItems] = useState([
    { time: "9:00 - 9:25", title: "Quick Wins Session" },
    { time: "9:30 - 10:15", title: "Review client feedback" },
    { time: "10:15 - 10:30", title: "Break" },
    { time: "10:30 - 12:30", title: "Complete project proposal" },
    { time: "12:30 - 1:30", title: "Lunch Break" },
    { time: "1:30 - 2:30", title: "Team meeting preparation" },
  ]);

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

  // === INTEGRASI BE: AMBIL DATA USER UNTUK HEADER AWAL ===
  // [PENJELASAN]: Ganti simulasi ini dengan GET /api/users/me menggunakan token dari Cookie/localStorage.
  // [METHOD]: GET | [ENDPOINT]: /api/users/me
  // [HEADERS]: Authorization: Bearer <token>
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

  // === INTEGRASI BE: KIRIM CHAT USER DAN AMBIL RESPON AI ===
  // [PENJELASAN]: Kirim pesan user ke AI service dan tampilkan respons secara streaming atau batch.
  // [METHOD]: POST | [ENDPOINT]: /api/chat/send
  // [HEADERS]: Authorization: Bearer <token>
  // [BODY]: { userId: string, message: string, conversationHistory: Message[] }
  // [RESPONSE]: { reply: string, sessionId: string }
  // [CATATAN]: Gunakan streaming (SSE / WebSocket) untuk efek ketik real-time.
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

      let simulatedResponse =
        "Great! I can see several tasks here. Which of these is most urgent or has the closest deadline?";

      // If it's at least the second message from the user, trigger the questionnaire
      if (messages.length >= 1) {
        simulatedResponse =
          "Perfect! Now let me understand your current state to create the best schedule for you.";
      }

      // Sanitization: React natively escapes HTML tags in strings.
      setMessages((prev) => [
        ...prev,
        { role: "ai", content: simulatedResponse },
      ]);
    } catch (error) {
      console.error("AI Assistant Error:", error);
      // Null & Error Handling: Graceful degradation
      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          content:
            "Sorry, Schedule Helper is having trouble connecting. Please try again.",
        },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  const userInitial = user?.name ? user.name.charAt(0).toUpperCase() : "";

  // === INTEGRASI BE: KIRIM DATA KUESIONER & TERIMA HASIL JADWAL ===
  // [PENJELASAN]: Kirim data mood/energy/waktu ke AI untuk dianalisis dan hasilkan jadwal.
  // [METHOD]: POST | [ENDPOINT]: /api/schedules/generate
  // [HEADERS]: Authorization: Bearer <token>
  // [BODY]: { userId, energyLevel: number (1-3), mood: number (1-3), availableTime: string }
  // [RESPONSE]: { scheduleId, topPriorities: ScheduleItem[], quickWins: ScheduleItem[], timeline: TimelineItem[], reasoning: string }
  // [MAPPING]: Gunakan response untuk mengisi state scheduleItems, topPriorities, dsb.
  const handleGenerateSchedule = async () => {
    setIsAnalyzing(true);
    // === INTEGRASI BACKEND: AMBIL DATA JADWAL FINAL ===
    // Di sini tempat untuk melakukan fetch data hasil analisis AI dari database/API.
    // Pastikan data yang diterima sesuai dengan interface ScheduleItem[].

    // Simulate analyzing time
    await new Promise((resolve) => setTimeout(resolve, 3000));

    setIsAnalyzing(false);
    setIsResult(true);
  };

  // 1. Core Layout Strategy - Start State
  if (!isStarted) {
    return (
      <div className="flex flex-col min-h-screen bg-gradient-to-b from-[#FFFFFF] to-[#B597FF] transition-all duration-500 ease-in-out">
        <header className="w-full flex items-center justify-between p-6 sm:px-10 max-w-[1440px] mx-auto">
          <Link
            href="/"
            onClick={() => {
              // === INTEGRASI BACKEND: NAVIGASI KE LANDING PAGE ===
              // Pastikan fungsi ini membersihkan sessionStorage sebelum dialihkan ke '/'
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
                <img
                  src="/images-button/Send%20Button.webp"
                  alt="Send"
                  className="w-[44px] h-[44px] object-contain"
                />
              </button>
            )}
          </form>
        </main>
      </div>
    );
  }

  // 2. Analyzing State
  if (isAnalyzing) {
    return (
      <main className="flex-1 flex flex-col items-center justify-center h-full bg-[#FFFFFF] animate-in fade-in duration-500">
        <div className="flex flex-col items-center justify-center text-center">
          <img
            src="/images-homepage/AI%20Clarifies%20&%20Prioritizes.webp"
            alt="Analyzing"
            className="w-[64px] h-[64px] object-contain mb-6 animate-pulse"
          />
          <h2 className="text-[20px] font-bold text-[#0A0A0A] font-inter mb-2">
            Analyzing Your Tasks
          </h2>
          <p className="text-[14px] text-[#717182] font-inter">
            Prioritizing based on your context and available time...
          </p>
        </div>
      </main>
    );
  }

  // 3. Result State
  if (isResult) {
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
                {/* Priority Card 1 */}
                <div className="border border-[#E5E7EB] rounded-[12px] p-5 flex flex-col gap-2">
                  <div className="flex justify-between items-start">
                    <h4 className="text-[15px] font-medium text-[#0A0A0A] font-inter">Complete project proposal</h4>
                    <span className="bg-[#FEF2F2] text-[#DC2626] text-[12px] font-medium px-2.5 py-1 rounded-full font-inter">High</span>
                  </div>
                  <p className="text-[14px] text-[#717182] font-inter">Closest deadline (tomorrow)</p>
                  <p className="text-[14px] text-[#717182] font-inter mt-1">Duration: 2 hours</p>
                </div>

                {/* Priority Card 2 */}
                <div className="border border-[#E5E7EB] rounded-[12px] p-5 flex flex-col gap-2">
                  <div className="flex justify-between items-start">
                    <h4 className="text-[15px] font-medium text-[#0A0A0A] font-inter">Review client feedback</h4>
                    <span className="bg-[#FEF2F2] text-[#DC2626] text-[12px] font-medium px-2.5 py-1 rounded-full font-inter">High</span>
                  </div>
                  <p className="text-[14px] text-[#717182] font-inter">Blocks other tasks</p>
                  <p className="text-[14px] text-[#717182] font-inter mt-1">Duration: 45 minutes</p>
                </div>

                {/* Priority Card 3 */}
                <div className="border border-[#E5E7EB] rounded-[12px] p-5 flex flex-col gap-2">
                  <div className="flex justify-between items-start">
                    <h4 className="text-[15px] font-medium text-[#0A0A0A] font-inter">Team meeting preparation</h4>
                    <span className="bg-[#F3F4F6] text-[#4B5563] text-[12px] font-medium px-2.5 py-1 rounded-full font-inter">Medium</span>
                  </div>
                  <p className="text-[14px] text-[#717182] font-inter">Important but can be rescheduled</p>
                  <p className="text-[14px] text-[#717182] font-inter mt-1">Duration: 1 hour</p>
                </div>
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
                    <div
                      onClick={() => {
                        // === INTEGRASI BACKEND: UPDATE STATUS TUGAS ===
                        // Hubungkan fungsi ini ke endpoint PATCH untuk menandai tugas sebagai 'completed'.
                      }}
                      className="w-10 h-10 rounded-full bg-[#F3E8FF] flex items-center justify-center shrink-0 cursor-pointer hover:bg-[#E9D5FF] transition-colors overflow-hidden"
                    >
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
                            // Block any alphabet character
                            if (/[a-zA-Z]/.test(val)) {
                              alert("Warning: Only numbers allowed");
                              return;
                            }
                            const newItems = [...scheduleItems];
                            newItems[idx].time = val;
                            setScheduleItems(newItems);
                          }}
                          placeholder="09:00 - 10:00"
                          className="w-[140px] text-[14px] text-[#717182] font-inter border border-gray-300 rounded px-2 py-1 outline-none focus:border-[#8A38F5]"
                        />
                        <input
                          value={item.title}
                          onChange={(e) => {
                            const newItems = [...scheduleItems];
                            newItems[idx].title = e.target.value;
                            setScheduleItems(newItems);
                          }}
                          className="flex-1 text-[14px] text-[#0A0A0A] font-medium font-inter border border-gray-300 rounded px-2 py-1 outline-none focus:border-[#8A38F5]"
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
                Based on your medium energy level and neutral mood, I've scheduled your most demanding task (project proposal) during your peak morning hours. Quick wins are placed first to build momentum. Breaks are included to maintain energy throughout the day.
              </p>
            </div>

            {/* Bottom Actions */}
            <div className="flex justify-start sm:justify-start gap-4 mt-2">
              <button className="bg-[#8A38F5] text-white px-5 py-3 rounded-xl text-[14px] font-medium font-inter hover:bg-[#7b32db] transition-colors flex items-center gap-2 shadow-sm">
                <img src="/images-dashboard/Ceklis.webp" className="w-[18px] h-[18px] filter brightness-0 invert" alt="Approve" />
                Approve & Save Plan
              </button>
              <button
                onClick={() => setIsEditingSchedule(!isEditingSchedule)}
                className="bg-white border border-[#E5E7EB] text-[#0A0A0A] px-5 py-3 rounded-xl text-[14px] font-medium font-inter hover:bg-gray-50 transition-colors flex items-center gap-2 shadow-sm"
              >
                <img src="/images-dashboard/Edit.webp" className="w-[18px] h-[18px]" alt="Edit" />
                {isEditingSchedule ? "Save Edits" : "Edit Plan"}
              </button>
              <button
                onClick={async () => {
                  // === INTEGRASI BACKEND: LOGIKA REGENERATE ===
                  // Fungsi ini nantinya akan memanggil ulang API analisis dengan parameter energy/mood yang sama.
                  setIsResult(false);
                  setIsAnalyzing(true);
                  // Simulasi re-generasi API
                  await new Promise((resolve) => setTimeout(resolve, 2000));
                  setIsAnalyzing(false);
                  setIsResult(true);
                }}
                className="bg-white border border-[#E5E7EB] text-[#0A0A0A] px-5 py-3 rounded-xl text-[14px] font-medium font-inter hover:bg-gray-50 transition-colors flex items-center gap-2 shadow-sm"
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

  // 4. Active Chat State (Sidebar dikendalikan oleh layout.tsx)
  return (
    <main className="flex-1 flex flex-col h-full bg-[#FFFFFF]">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-6 pt-10 pb-6">
        <div className="max-w-4xl mx-auto flex flex-col gap-8">
          {messages.map((msg, index) => (
            <div key={index} className="flex flex-col gap-4">
              <div
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"
                  } animate-in fade-in slide-in-from-bottom-2 duration-300`}
              >
                {msg.role === "ai" && (
                  <div className="w-8 h-8 rounded-full bg-[#8A38F5] shrink-0 mr-4 flex items-center justify-center shadow-sm">
                    <span className="text-white text-xs font-bold">AI</span>
                  </div>
                )}
                <div
                  className={`max-w-[80%] rounded-[20px] px-6 py-4 text-[15px] leading-relaxed shadow-sm ${msg.role === "user"
                    ? "bg-[#B597FF] text-white rounded-tr-none"
                    : "bg-[#FFFFFF] text-[#0A0A0A] border border-[#E5E7EB] rounded-tl-none"
                    }`}
                >
                  {msg.content}
                </div>
              </div>

              {/* Form Card Questionnaire Trigger */}
              {index === messages.length - 1 &&
                msg.role === "ai" &&
                msg.content ===
                "Perfect! Now let me understand your current state to create the best schedule for you." && (
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
                        <img
                          src="/images-dashboard/Energy%20Level%201.webp"
                          alt="Low Energy"
                          className="w-8 h-8 object-contain"
                        />
                        <img
                          src="/images-dashboard/Energy%20Level%202.webp"
                          alt="Medium Energy"
                          className="w-8 h-8 object-contain"
                        />
                        <img
                          src="/images-dashboard/Energy%20Level%203.webp"
                          alt="High Energy"
                          className="w-8 h-8 object-contain"
                        />
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
                        <img
                          src="/images-dashboard/Happy%20Icon.webp"
                          alt="Happy"
                          className="w-8 h-8 object-contain"
                        />
                        <img
                          src="/images-dashboard/Medium%20Icon.webp"
                          alt="Medium"
                          className="w-8 h-8 object-contain"
                        />
                        <img
                          src="/images-dashboard/Stressed%20Icon.webp"
                          alt="Stressed"
                          className="w-8 h-8 object-contain"
                        />
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

                    {/* Available Time Today */}
                    <div className="mb-8 relative">
                      <label className="text-[14px] text-[#717182] font-medium block mb-3 font-inter">
                        Available Time Today
                      </label>
                      <div
                        onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                        className="w-full border border-[#E5E7EB] rounded-[10px] px-4 py-3.5 flex items-center justify-between cursor-pointer hover:bg-gray-50 transition-colors bg-white"
                      >
                        <div className="flex items-center gap-3">
                          <svg
                            className="w-[18px] h-[18px] text-[#717182]"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth="2"
                              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                            ></path>
                          </svg>
                          <span
                            className={`text-[15px] font-inter ${availableTime ? "text-[#0A0A0A]" : "text-[#717182]"}`}
                          >
                            {availableTime || "Select Time Available"}
                          </span>
                        </div>
                        <svg
                          className={`w-5 h-5 text-gray-400 transition-transform duration-200 ${isDropdownOpen ? "rotate-180" : ""}`}
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth="2"
                            d="M19 9l-7 7-7-7"
                          ></path>
                        </svg>
                      </div>
                      {isDropdownOpen && (
                        <div className="absolute z-20 w-full mt-1.5 bg-white border border-[#E5E7EB] rounded-[10px] shadow-sm overflow-hidden">
                          {[
                            "1 - 2 Hours",
                            "2 - 4 Hours",
                            "4 - 6 Hours",
                            "6+ Hours",
                          ].map((option) => (
                            <div
                              key={option}
                              onClick={() => {
                                setAvailableTime(option);
                                setIsDropdownOpen(false);
                              }}
                              className="px-4 py-3.5 text-[15px] text-[#0A0A0A] hover:bg-[#F9FAFB] cursor-pointer border-b border-[#E5E7EB] last:border-0 font-inter transition-colors"
                            >
                              {option}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* CTA Button */}
                    <button
                      onClick={handleGenerateSchedule}
                      disabled={!availableTime}
                      className="w-full bg-[#8A38F5] text-white font-semibold py-3.5 rounded-[10px] hover:bg-[#7b32db] transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-inter"
                    >
                      Generate My Schedule
                    </button>
                  </div>
                )}
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
            <img
              src="/images-button/Send%20Button.webp"
              alt="Send"
              className="w-[44px] h-[44px] object-contain"
            />
          </button>
        </form>
      </div>
    </main>
  );
}
