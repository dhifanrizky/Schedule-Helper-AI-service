"use client";

import { useEffect } from "react";
import { useUser } from "@/hooks/useUser";
import { useChat } from "@/hooks/useChat";
import { useSchedule } from "@/hooks/useSchedule";
import { StartState } from "@/components/dashboard/StartState";
import { AnalyzingState } from "@/components/dashboard/AnalyzingState";
import { ResultState } from "@/components/dashboard/ResultState";
import { ChatState } from "@/components/dashboard/ChatState";

const formatTimeRange = (startTime: string, durationMinutes: number) => {
  let hours: number | null = null;
  let minutes: number | null = null;

  const parsed = new Date(startTime);
  if (!Number.isNaN(parsed.getTime())) {
    hours = parsed.getHours();
    minutes = parsed.getMinutes();
  } else {
    const timePart = startTime.includes("T")
      ? startTime.split("T")[1]
      : startTime;
    const [rawHours, rawMinutes] = timePart.split(":");
    hours = Number(rawHours);
    minutes = Number(rawMinutes);
  }

  if (hours === null || minutes === null || Number.isNaN(hours) || Number.isNaN(minutes)) {
    return `${startTime} (${durationMinutes} min)`;
  }

  const startTotalMinutes = hours * 60 + minutes;
  const endTotalMinutes = startTotalMinutes + durationMinutes;
  const endHours = Math.floor(endTotalMinutes / 60) % 24;
  const endMinutes = endTotalMinutes % 60;
  const pad = (value: number) => value.toString().padStart(2, "0");

  return `${pad(hours)}:${pad(minutes)} - ${pad(endHours)}:${pad(endMinutes)}`;
};

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
    handleSend,
    hitlPayload
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
    scheduleItems, setScheduleItems
  } = useSchedule();

  useEffect(() => {
    if (hitlPayload?.type !== "task_review") return;
    if (!hitlPayload.proposed_schedule?.length) return;

    const mappedScheduleItems = hitlPayload.proposed_schedule.map((item) => ({
      time: formatTimeRange(item.start_time, item.duration_minutes),
      title: item.task
    }));

    setScheduleItems(mappedScheduleItems);
  }, [hitlPayload, setScheduleItems]);

  const handleConfirmPriorities = () => {
    if (hitlPayload?.type !== "task_review") return;

    handleSend(null, {
      tasks: hitlPayload.tasks.map((task) => ({
        task: task.title,
        priority: task.priority,
        deadline: task.deadline ?? ""
      }))
    });
  };

  // === RENDERING STRATEGY ===

  if (hitlPayload?.type === "task_review" && isResult) {
    return (
      <ResultState
        scheduleItems={scheduleItems}
        setScheduleItems={setScheduleItems}
        isEditingSchedule={isEditingSchedule}
        setIsEditingSchedule={setIsEditingSchedule}
        setIsResult={setIsResult}
        setIsAnalyzing={setIsResult}
        prioritizerTasks={hitlPayload.tasks}
        onApprove={handleConfirmPriorities}
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
        energyLevel={energyLevel}
        setEnergyLevel={setEnergyLevel}
        mood={mood}
        setMood={setMood}
        availableTime={availableTime}
        setAvailableTime={setAvailableTime}
        isDropdownOpen={isDropdownOpen}
        setIsDropdownOpen={setIsDropdownOpen}
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
      hitlPayload={hitlPayload}
    />
  );
}
