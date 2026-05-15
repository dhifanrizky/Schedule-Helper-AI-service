// =============================================================
// TERPUSAT: Semua TypeScript types untuk seluruh aplikasi
// Impor dari file ini di mana pun dibutuhkan:
// import type { Message, UserProfile, ... } from "@/types"
// =============================================================

// Satu pesan dalam percakapan antara user dan AI
export type Message = {
  role: "user" | "system";
  content: string;
};

// Data profil pengguna yang login
// === INTEGRASI BE: Sesuaikan dengan response GET /api/users/me ===
export type UserProfile = {
  name: string;
  email: string;
};

// Satu item dalam daftar riwayat jadwal (History page)
// === INTEGRASI BE: Sesuaikan dengan response GET /api/schedules/history ===
export type HistoryItem = {
  id: string; // ID unik jadwal untuk routing ke halaman detail
  title: string; // Judul sesi (ringkasan dari chat user)
  date: string; // Tanggal dibuat (format string dari backend)
  priorities: number; // Jumlah tugas prioritas tinggi
  quickWins: number; // Jumlah tugas quick win
  status: string; // Status: 'completed' | 'in_progress' | 'cancelled'
};

// Satu item dalam jadwal harian (Today's Schedule di Result page)
// === INTEGRASI BE: Sesuaikan dengan field timeline[] dari /api/schedules/generate ===
export type ScheduleItem = {
  task_id: string;
  title: string;
  priority: number;
  time: string;           // Hasil format jam (misal "19:00 - 20:00")
  start_time?: string;    // String ISO aslinya
  category: string;
  subtasks: string[];
  estimated_minutes: number; 
  deadline: string | null; 
  preferred_window: string; 
  is_locked_time?: boolean;
  locked_start_time?: string;
};

// Payload yang dikirim saat user menekan "Generate My Schedule"
// === INTEGRASI BE: Kirim ke POST /api/schedules/generate ===
export type QuestionnairePayload = {
  energyLevel: number; // 0 - 100 (0 = Rendah, 100 = Tinggi)
  mood: number; // 0 - 100 (0 = Happy, 100 = Stres)
  availableTime: string; // Contoh: "2 - 4 Hours"
};

export interface CreateCalendarPayload {
  title: string;
  description: string;
  category: string;
  priority?: number;
  deadline?: string;
  estimatedMinutes?: number;
  startTime?: string;
  status?: string;
}

export interface RawTasks {
  category: string;
  description: string;
  raw_input: string;
  raw_time: string;
  task_id: string;
  title: string;
}
