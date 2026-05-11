"use client";

import { useEffect } from "react";
import { useUser } from "@/hooks/useUser";
import { useChat } from "@/hooks/useChat";
import { useSchedule } from "@/hooks/useSchedule";
import { StartState } from "@/components/dashboard/StartState";
import { AnalyzingState } from "@/components/dashboard/AnalyzingState";
import { ResultState } from "@/components/dashboard/ResultState";
import { ChatState } from "@/components/dashboard/ChatState";
import { CreateCalendarPayload } from "@/types";
import { API_URL, getAppToken } from "@/utils/const";

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

  if (
    hours === null ||
    minutes === null ||
    Number.isNaN(hours) ||
    Number.isNaN(minutes)
  ) {
    return `${startTime} (${durationMinutes} min)`;
  }

  const startTotalMinutes = hours * 60 + minutes;
  const endTotalMinutes = startTotalMinutes + durationMinutes;
  const endHours = Math.floor(endTotalMinutes / 60) % 24;
  const endMinutes = endTotalMinutes % 60;
  const pad = (value: number) => value.toString().padStart(2, "0");

  return `${pad(hours)}:${pad(minutes)} - ${pad(endHours)}:${pad(endMinutes)}`;
};

export default function DashboardClient() {
  const { user, isUserLoading, userInitial } = useUser();

  const {
    messages,
    inputValue,
    setInputValue,
    isTyping,
    isStarted,
    messagesEndRef,
    handleSend,
    hitlPayload,
  } = useChat(user?.email);

  const {
    energyLevel,
    setEnergyLevel,
    mood,
    setMood,
    availableTime,
    setAvailableTime,
    isDropdownOpen,
    setIsDropdownOpen,
    isAnalyzing,
    isResult,
    setIsResult,
    isEditingSchedule,
    setIsEditingSchedule,
    scheduleItems,
    setScheduleItems,
  } = useSchedule();

  useEffect(() => {
    if (hitlPayload?.type !== "task_review") return;
    if (!hitlPayload.proposed_schedule?.length) return;

    const mappedScheduleItems = hitlPayload.proposed_schedule.map((item) => ({
      time: formatTimeRange(item.start_time, item.duration_minutes),
      title: item.task,
      task_id: item.task_id,
      priority: item.priority,
      category: item.category,
    }));

    setScheduleItems(mappedScheduleItems);
  }, [hitlPayload, setScheduleItems]);

  const handleConfirmPriorities = async () => {
    if (hitlPayload?.type !== "task_review") return;

    const token = getAppToken();
    if (!token) {
      console.error("No token found for task review request");
      return;
    }

    try {
      await Promise.all(
        hitlPayload.tasks.map((task) =>
          fetch(`${API_URL}/calendar`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({
              title: task.title,
              description: task.title,
              category: task.category ?? "general",
              priority: task.priority,
              deadline: task.deadline ?? undefined,
            } satisfies CreateCalendarPayload),
          }).then((res) => {
            if (!res.ok) throw new Error(`Failed to save task: ${task.title}`);
            return res.json();
          }),
        ),
      );

      handleSend(null, {
        tasks: hitlPayload.tasks.map((task) => ({
          task: task.title,
          priority: task.priority,
          deadline: task.deadline ?? "",
        })),
      });
    } catch (error) {
      console.error("Error saving tasks to calendar:", error);
    }
  };

  if (isAnalyzing) {
    return <AnalyzingState />;
  }

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

  return (
    <ChatState
      messages={messages}
      isTyping={isTyping}
      inputValue={inputValue}
      setInputValue={setInputValue}
      handleSend={handleSend}
      messagesEndRef={messagesEndRef}
      hitlPayload={hitlPayload}
      scheduleItems={scheduleItems}
      setScheduleItems={setScheduleItems}
      isEditingSchedule={isEditingSchedule}
      setIsEditingSchedule={setIsEditingSchedule}
      setIsResult={setIsResult}
      setIsAnalyzing={setIsResult}
      prioritizerTasks={
        hitlPayload?.type === "task_review" ? hitlPayload.tasks : undefined
      }
      onApprove={handleConfirmPriorities}
    />
  );
}
