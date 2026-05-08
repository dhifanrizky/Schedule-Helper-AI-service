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
  { 
    task_id: "T-001", 
    title: "Quick Wins Session", 
    priority: 1, 
    time: "9:00 - 9:25", 
    category: "Work" 
  },
  { 
    task_id: "T-002", 
    title: "Review client feedback", 
    priority: 2, 
    time: "9:30 - 10:15", 
    category: "Review" 
  },
  { 
    task_id: "T-003", 
    title: "Break", 
    priority: 3, 
    time: "10:15 - 10:30", 
    category: "Break" 
  },
  { 
    task_id: "T-004", 
    title: "Complete project proposal", 
    priority: 1, 
    time: "10:30 - 12:30", 
    category: "Project" 
  },
  { 
    task_id: "T-005", 
    title: "Lunch Break", 
    priority: 3, 
    time: "12:30 - 1:30", 
    category: "Break" 
  },
  { 
    task_id: "T-006", 
    title: "Team meeting preparation", 
    priority: 2, 
    time: "1:30 - 2:30", 
    category: "Meeting" 
  },
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
