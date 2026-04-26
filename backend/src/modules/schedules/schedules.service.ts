import { Injectable } from '@nestjs/common';

@Injectable()
export class SchedulesService {
  async generateSchedule(payload: any) {
    // Mock response for frontend
    return {
      scheduleId: "mock-schedule-" + Date.now(),
      topPriorities: [],
      quickWins: [],
      timeline: [],
      reasoning: "Mock generated schedule from backend.",
    };
  }

  async getHistory() {
    // Mock response
    return [];
  }

  async getScheduleById(id: string) {
    // Mock response
    return { id, message: "Mock schedule detail" };
  }
}
