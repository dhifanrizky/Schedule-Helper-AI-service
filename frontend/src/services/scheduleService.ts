import { HistoryItem, QuestionnairePayload, ScheduleItem } from "@/types";
import { mockHistoryData } from "@/data/mockData";

// =============================================================
// SCHEDULE SERVICE: Mengelola pembuatan jadwal dan riwayat
// =============================================================

export const scheduleService = {
  /**
   * Mengirim data kuesioner ke AI untuk menghasilkan jadwal baru.
   * === INTEGRASI BE: Ganti dengan POST /api/schedules/generate ===
   */
  async generateSchedule(payload: QuestionnairePayload): Promise<{
    scheduleId: string;
    topPriorities: any[]; // Sesuaikan dengan tipe yang lebih detail jika perlu
    quickWins: any[];
    timeline: ScheduleItem[];
    reasoning: string;
  }> {
    console.log("Generating schedule with payload:", payload);
    
    // 1. Simulasi delay analisis AI (3 detik)
    await new Promise((resolve) => setTimeout(resolve, 3000));

    // 2. Mock response (Ganti dengan real API call nanti)
    return {
      scheduleId: "new-schedule-id-" + Date.now(),
      topPriorities: [], // Akan diisi di level hook/komponen dari mock atau real data
      quickWins: [],
      timeline: [], // Akan diisi di level hook/komponen
      reasoning: "Based on your current state, I've optimized your schedule..."
    };
  },

  /**
   * Mengambil daftar riwayat jadwal user.
   * === INTEGRASI BE: Ganti dengan GET /api/schedules/history ===
   */
  async getHistory(): Promise<HistoryItem[]> {
    // 1. Simulasi delay network
    await new Promise((resolve) => setTimeout(resolve, 2000));

    // 2. Kembalikan mock data
    return mockHistoryData;
  },

  /**
   * Mengambil detail satu jadwal berdasarkan ID.
   * === INTEGRASI BE: Ganti dengan GET /api/schedules/:id ===
   */
  async getScheduleById(id: string): Promise<any> {
    await new Promise((resolve) => setTimeout(resolve, 1000));
    // Simulasi cari data di history
    return mockHistoryData.find(item => item.id === id);
  }
};
