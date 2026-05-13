import { HistoryItem, UserProfile } from "@/types";

import { ScheduleItem } from "@/types";
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
    time: "09:00 - 09:25",
    category: "Work",
    subtasks: [
      "Review pending quick tasks",
      "Complete low-effort items",
      "Update progress tracker"
    ],
    estimated_minutes: 25,
    deadline: "2026-05-14 10:00",
    preferred_window: "Morning"
  },
  {
    task_id: "T-002",
    title: "Review Client Feedback",
    priority: 2,
    time: "09:30 - 10:15",
    category: "Review",
    subtasks: [
      "Read feedback documents",
      "Highlight revision requests",
      "Prepare response summary"
    ],
    estimated_minutes: 45,
    deadline: "2026-05-14 13:00",
    preferred_window: "Morning"
  },
  {
    task_id: "T-003",
    title: "Break",
    priority: 3,
    time: "10:15 - 10:30",
    category: "Break",
    subtasks: [
      "Stretch body",
      "Drink water",
      "Relax eyes"
    ],
    estimated_minutes: 15,
    deadline: "2026-05-14 10:30",
    preferred_window: "Morning"
  },
  {
    task_id: "T-004",
    title: "Complete Project Proposal",
    priority: 1,
    time: "10:30 - 12:30",
    category: "Project",
    subtasks: [
      "Write introduction",
      "Finalize system architecture",
      "Review proposal formatting"
    ],
    estimated_minutes: 120,
    deadline: "2026-05-14 17:00",
    preferred_window: "Late Morning"
  },
  {
    task_id: "T-005",
    title: "Lunch Break",
    priority: 3,
    time: "12:30 - 13:30",
    category: "Break",
    subtasks: [
      "Eat lunch",
      "Take short walk",
      "Recharge energy"
    ],
    estimated_minutes: 60,
    deadline: "2026-05-14 13:30",
    preferred_window: "Afternoon"
  },
  {
    task_id: "T-006",
    title: "Team Meeting Preparation",
    priority: 2,
    time: "13:30 - 14:30",
    category: "Meeting",
    subtasks: [
      "Prepare agenda",
      "Collect project updates",
      "Create discussion notes"
    ],
    estimated_minutes: 60,
    deadline: "2026-05-14 15:00",
    preferred_window: "Afternoon"
  }
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
