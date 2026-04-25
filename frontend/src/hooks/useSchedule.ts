import { useState } from "react";
import { ScheduleItem, QuestionnairePayload } from "@/types";
import { scheduleService } from "@/services/scheduleService";
import { defaultScheduleItems } from "@/data/mockData";

/**
 * Hook untuk mengelola state kuesioner dan hasil pembuatan jadwal.
 */
export function useSchedule() {
  // Questionnaire States
  const [energyLevel, setEnergyLevel] = useState<number>(2);
  const [mood, setMood] = useState<number>(2);
  const [availableTime, setAvailableTime] = useState<string>("");
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  // Status States
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isResult, setIsResult] = useState(false);
  const [isEditingSchedule, setIsEditingSchedule] = useState(false);
  
  // Data States
  const [scheduleItems, setScheduleItems] = useState<ScheduleItem[]>(defaultScheduleItems);

  const handleGenerateSchedule = async () => {
    setIsAnalyzing(true);
    
    try {
      const payload: QuestionnairePayload = { energyLevel, mood, availableTime };
      const result = await scheduleService.generateSchedule(payload);
      
      // === INTEGRASI BE: Update state dengan data nyata dari response ===
      // setScheduleItems(result.timeline);
      
      setIsAnalyzing(false);
      setIsResult(true);
    } catch (error) {
      console.error("Failed to generate schedule:", error);
      setIsAnalyzing(false);
    }
  };

  return {
    // Questionnaire
    energyLevel, setEnergyLevel,
    mood, setMood,
    availableTime, setAvailableTime,
    isDropdownOpen, setIsDropdownOpen,
    
    // Status
    isAnalyzing,
    isResult, setIsResult,
    isEditingSchedule, setIsEditingSchedule,
    
    // Data
    scheduleItems, setScheduleItems,
    
    // Logic
    handleGenerateSchedule
  };
}
