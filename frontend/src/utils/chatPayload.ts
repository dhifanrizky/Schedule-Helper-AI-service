import type { QuestionnairePayload } from "@/types";

export const buildUserContent = (
  trimmed: string,
  questionnaireData?: QuestionnairePayload,
) => {
  if (!questionnaireData) return trimmed;
  return `USER STATE: ${JSON.stringify(questionnaireData)}\nwith Energy level: 0 (low) - 100 (energetic), Mood: 0 (good) - 100 (bad)\nUSER MESSAGES: ${trimmed}`;
};
