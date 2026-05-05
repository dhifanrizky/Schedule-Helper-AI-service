import { describe, expect, it } from "vitest";
import { buildUserContent } from "../../src/utils/chatPayload";

describe("buildUserContent", () => {
  it("embeds questionnaire data before the message", () => {
    const trimmed = "Tolong bantu prioritaskan tugas ini";
    const questionnaire = {
      energyLevel: 60,
      mood: 40,
      availableTime: "2 - 4 Hours"
    };

    const result = buildUserContent(trimmed, questionnaire);

    expect(result).toContain("USER STATE:");
    expect(result).toContain("USER MESSAGES:");
    expect(result).toContain("availableTime");
    expect(result.endsWith(trimmed)).toBe(true);
  });

  it("returns plain message when questionnaire is missing", () => {
    const trimmed = "Halo";
    const result = buildUserContent(trimmed);

    expect(result).toBe(trimmed);
  });
});
