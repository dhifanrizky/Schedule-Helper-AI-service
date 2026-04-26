"use client";

import { useUser } from "@/hooks/useUser";
import { useChat } from "@/hooks/useChat";
import { useSchedule } from "@/hooks/useSchedule";
import { StartState } from "@/components/dashboard/StartState";
import { AnalyzingState } from "@/components/dashboard/AnalyzingState";
import { ResultState } from "@/components/dashboard/ResultState";
import { ChatState } from "@/components/dashboard/ChatState";

/**
 * DASHBOARD MAIN PAGE
 */
export default function DashboardPage() {
  // 1. Logika User & Profil
  const { user, isUserLoading, userInitial } = useUser();

  // 2. Logika Chat & Percakapan
  const {
    messages,
    inputValue,
    setInputValue,
    isTyping,
    isStarted,
    messagesEndRef,
    handleSend
  } = useChat(user?.email);

  // 3. Logika Kuesioner & Pembuatan Jadwal
  const {
    energyLevel, setEnergyLevel,
    mood, setMood,
    availableTime, setAvailableTime,
    isDropdownOpen, setIsDropdownOpen,
    isAnalyzing,
    isResult, setIsResult,
    isEditingSchedule, setIsEditingSchedule,
    scheduleItems, setScheduleItems,
    handleGenerateSchedule
  } = useSchedule();

  // === RENDERING STRATEGY ===

  // Tampilan 1: Hasil Jadwal (setelah klik "Generate My Schedule")
  if (isResult) {
    return (
      <ResultState
        scheduleItems={scheduleItems}
        setScheduleItems={setScheduleItems}
        isEditingSchedule={isEditingSchedule}
        setIsEditingSchedule={setIsEditingSchedule}
        setIsResult={setIsResult}
        setIsAnalyzing={setIsResult}
      />
    );
  }

  // Tampilan 2: Animasi Loading AI saat menganalisis
  if (isAnalyzing) {
    return <AnalyzingState />;
  }

  // Tampilan 3: Landing awal dashboard (sebelum chat dimulai)
  if (!isStarted) {
    return (
      <StartState
        user={user}
        isUserLoading={isUserLoading}
        userInitial={userInitial}
        inputValue={inputValue}
        setInputValue={setInputValue}
        isTyping={isTyping}
        handleSend={handleSend}
      />
    );
  }

  // Tampilan 4: Percakapan Chat Aktif
  return (
    <ChatState
      messages={messages}
      isTyping={isTyping}
      inputValue={inputValue}
      setInputValue={setInputValue}
      handleSend={handleSend}
      messagesEndRef={messagesEndRef}
      // Props kuesioner
      energyLevel={energyLevel}
      setEnergyLevel={setEnergyLevel}
      mood={mood}
      setMood={setMood}
      availableTime={availableTime}
      setAvailableTime={setAvailableTime}
      isDropdownOpen={isDropdownOpen}
      setIsDropdownOpen={setIsDropdownOpen}
      handleGenerateSchedule={handleGenerateSchedule}
    />
  );
}
