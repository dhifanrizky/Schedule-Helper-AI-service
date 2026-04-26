import { HistoryItem, ScheduleItem, UserProfile } from "@/types";

// =============================================================
// MOCK DATA: Digunakan sementara sebelum API Backend siap
// =============================================================

// Data profil user default untuk simulasi login
export const mockUserProfile: UserProfile = {
  name: "John Doe",
  email: "john.doe@example.com",
};

// Item jadwal harian default untuk Result Page
export const defaultScheduleItems: ScheduleItem[] = [
  { time: "9:00 - 9:25", title: "Quick Wins Session" },
  { time: "9:30 - 10:15", title: "Review client feedback" },
  { time: "10:15 - 10:30", title: "Break" },
  { time: "10:30 - 12:30", title: "Complete project proposal" },
  { time: "12:30 - 1:30", title: "Lunch Break" },
  { time: "1:30 - 2:30", title: "Team meeting preparation" },
];

// Data riwayat jadwal default untuk History Page
export const mockHistoryData: HistoryItem[] = [
  {
    id: "1",
    title: "Monday Sprint Planning",
    date: "May 20, 2024",
    priorities: 3,
    quickWins: 5,
    status: "completed",
  },
  {
    id: "2",
    title: "Mid-week Focus Session",
    date: "May 22, 2024",
    priorities: 2,
    quickWins: 3,
    status: "completed",
  },
  {
    id: "3",
    title: "Friday Wrap-up",
    date: "May 24, 2024",
    priorities: 4,
    quickWins: 2,
    status: "in_progress",
  },
];
