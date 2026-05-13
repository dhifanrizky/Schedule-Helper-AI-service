import { useState } from "react";
import { ScheduleItem } from "@/types";
import {
  ChevronRight,
  ChevronLeft,
  Clock,
  Calendar,
  Star,
  Tag,
  Edit2,
  X,
} from "lucide-react";

interface ResultStateProps {
  scheduleItems: ScheduleItem[];
  onApprove?: () => void;
  onEditTask?: (task: ScheduleItem) => void;
  onEditSchedule?: () => void;
}

export function ResultState({
  scheduleItems,
  onApprove,
  onEditTask,
  onEditSchedule,
}: ResultStateProps) {
  // Menggunakan task_id untuk state aktif
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(
    scheduleItems.length > 0 ? scheduleItems[0].task_id : null,
  );

  const selectedItem = scheduleItems.find(
    (item) => item.task_id === selectedTaskId,
  );

  // Helper untuk mengubah angka priority menjadi label dan styling
  const getPriorityInfo = (priority: number) => {
    if (priority === 1)
      return {
        label: "Tinggi",
        badge: "High",
        color: "bg-[#FEF2F2] text-[#DC2626]",
      };
    if (priority === 2)
      return {
        label: "Sedang",
        badge: "Medium",
        color: "bg-[#FFFBEB] text-[#D97706]",
      };
    return {
      label: "Rendah",
      badge: "Low",
      color: "bg-[#F0FDF4] text-[#16A34A]",
    };
  };

  return (
    <main className="flex-1 flex flex-row h-full p-4 gap-4 overflow-y-auto font-sans animate-in fade-in duration-500">
      {/* Panel Kiri: DRAFT JADWAL */}
      <div className="w-95 bg-[#F8FAFC] rounded-2xl flex flex-col p-6 shadow-sm animate-in slide-in-from-left-4 fade-in duration-500">
        <div className="mb-6 border-b border-[#E2E8F0] pb-4">
          <h1 className="text-[14px] font-bold text-[#0F172A]">
            DRAFT JADWAL
          </h1>
        </div>

        {/* Timeline List */}
        <div className="flex flex-col gap-4 relative pl-3 flex-1 overflow-y-auto">
          {/* Garis vertikal timeline */}
          <div className="absolute left-[17.5px] top-4 bottom-4 w-0.5 bg-[#CBD5E1]" />

          {scheduleItems.map((item, index) => {
            const isSelected = item.task_id === selectedTaskId;
            const priorityInfo = getPriorityInfo(item.priority);

            return (
              <div
                key={item.task_id}
                className="flex items-start gap-4 relative cursor-pointer animate-in fade-in slide-in-from-bottom-2 group p-2"
                style={{
                  animationFillMode: "both",
                  animationDelay: `${index * 100}ms`,
                }}
                onClick={() =>
                  setSelectedTaskId(isSelected ? null : item.task_id)
                }
              >
                {/* Titik Timeline */}
                <div className="relative mt-4 z-10 flex items-center justify-center w-2.75 h-2.75 right-[7px]">
                  {isSelected && (
                    <div className="absolute w-5 h-5 bg-[#E0F2FE] rounded-full animate-in zoom-in duration-300" />
                  )}
                  <div
                    className={`w-2.75 h-2.75 rounded-full relative z-20 transition-colors duration-300 ${isSelected ? "bg-[#0EA5E9]" : "bg-[#CBD5E1] group-hover:bg-[#94A3B8]"}`}
                  />
                </div>

                {/* Kartu Jadwal */}
                <div
                  className={`flex-1 p-4 rounded-xl bg-white border transition-all duration-300 ${isSelected ? "border-[#0EA5E9] shadow-[0_0_10px_rgba(14,165,233,0.15)] scale-[1.02]" : "border-[#E2E8F0] hover:border-[#CBD5E1]"}`}
                >
                  <div className="flex items-center gap-3">
                    {/* Teks & Badge */}
                    <div className="flex-1 flex flex-col gap-1">
                      <div className="flex justify-between gap-2 items-center">
                        <span
                          className={`flex flex-col text-[15px] transition-colors duration-300 ${isSelected ? "font-semibold text-[#0F172A]" : "font-medium text-[#0F172A]"}`}
                        >
                          <span className="text-xs text-gray-700">
                            {item.time}
                          </span>
                          <span>{item.title}</span>
                        </span>
                        {/* Priority Badge */}
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded-md whitespace-nowrap mt-0.5 h-full self-center ${priorityInfo.color}`}
                        >
                          {priorityInfo.badge}
                        </span>
                      </div>
                    </div>

                    {/* Arrow Indicator: Menyesuaikan arah berdasarkan isSelected */}
                    <div
                      className={`w-8 h-8 rounded-md flex items-center justify-center shrink-0 transition-colors duration-200 ${isSelected ? "bg-[#F1F5F9] text-[#64748B]" : "text-[#94A3B8] group-hover:text-[#64748B]"}`}
                    >
                      {isSelected ? (
                        <ChevronLeft className="w-4 h-4" />
                      ) : (
                        <ChevronRight className="w-4 h-4" />
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Actions Button */}
        <div
          className="mt-6 pt-4 flex gap-3 animate-in fade-in slide-in-from-bottom-4 duration-500 delay-300"
          style={{ animationFillMode: "both" }}
        >
          <button
            onClick={onEditSchedule}
            className="w-25 bg-white border border-[#F87171] text-[#EF4444] py-3 rounded-[10px] text-[14px] font-semibold hover:bg-red-50 transition-colors"
          >
            Edit
          </button>
          <button
            onClick={onApprove}
            className="flex-1 bg-[#10B981] text-white py-3 rounded-[10px] text-[14px] font-semibold hover:bg-[#059669] transition-colors"
          >
            APPROVE
          </button>
        </div>
      </div>

      {/* Panel Kanan: DETAIL TUGAS */}
      {selectedItem && (
        <div
          key={selectedItem.task_id}
          className="flex-1 bg-[#F8FAFC] rounded-2xl p-8 shadow-sm flex flex-col overflow-y-auto animate-in slide-in-from-right-8 fade-in duration-300"
        >
          <div className="flex justify-between items-center mb-6 border-b border-[#E2E8F0] pb-6">
            <h2 className="text-[14px] font-medium text-[#475569]">
              DETAIL TUGAS: {selectedItem.title}
            </h2>
            <button
              onClick={() => setSelectedTaskId(null)}
              className="text-[#94A3B8] hover:text-[#0F172A] transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <h3
            className="text-[28px] font-semibold text-[#0F172A] mb-8 animate-in slide-in-from-bottom-2 fade-in duration-500 delay-100"
            style={{ animationFillMode: "both" }}
          >
            {selectedItem.title}
          </h3>

          {/* Subtasks Section */}
          <div
            className="mb-10 animate-in slide-in-from-bottom-2 fade-in duration-500 delay-200"
            style={{ animationFillMode: "both" }}
          >
            <div className="flex justify-between items-center mb-5">
              <h4 className="text-[16px] font-semibold text-[#0F172A]">
                Subtasks
              </h4>
              <button
                onClick={() => onEditTask?.(selectedItem)}
                className="text-[13px] font-medium text-[#475569] bg-white border border-[#E2E8F0] px-3 py-1.5 rounded-md flex items-center gap-2 hover:bg-gray-50 transition-colors shadow-sm"
              >
                <Edit2 className="w-3.5 h-3.5" />
                Edit Task
              </button>
            </div>

            <div className="flex flex-col gap-3">
              {selectedItem.subtasks?.map((subtask, idx) => (
                <div key={idx} className="flex items-start gap-3">
                  <div className="mt-0.5">
                    <input
                      type="checkbox"
                      className="w-4 h-4 rounded border-[#CBD5E1] text-[#0EA5E9] focus:ring-[#0EA5E9] transition-all cursor-pointer"
                    />
                  </div>
                  <label className="text-[15px] text-[#334155] leading-relaxed cursor-pointer">
                    {subtask}
                  </label>
                </div>
              ))}
            </div>
          </div>

          {/* Meta Data Section */}
          <div
            className="animate-in slide-in-from-bottom-2 fade-in duration-500 delay-300"
            style={{ animationFillMode: "both" }}
          >
            <h4 className="text-[16px] font-semibold text-[#0F172A] mb-5">
              Meta Data
            </h4>

            <div className="grid grid-cols-2 gap-4">
              {/* Card Durasi */}
              <div className="bg-white border border-[#E2E8F0] rounded-xl p-4 flex items-center gap-4 shadow-sm hover:border-[#CBD5E1] transition-colors">
                <div className="w-10 h-10 rounded-full bg-[#F1F5F9] flex items-center justify-center shrink-0">
                  <Clock className="w-5 h-5 text-[#64748B]" />
                </div>
                <div className="flex flex-col">
                  <span className="text-[13px] text-[#64748B]">Durasi</span>
                  <span className="text-[14px] font-medium text-[#0F172A]">
                    {selectedItem.estimated_minutes
                      ? `${selectedItem.estimated_minutes} Menit`
                      : "-"}
                  </span>
                </div>
              </div>

              {/* Card Deadline */}
              <div className="bg-white border border-[#E2E8F0] rounded-xl p-4 flex items-center gap-4 shadow-sm hover:border-[#CBD5E1] transition-colors">
                <div className="w-10 h-10 rounded-full bg-[#F1F5F9] flex items-center justify-center shrink-0">
                  <Calendar className="w-5 h-5 text-[#64748B]" />
                </div>
                <div className="flex flex-col">
                  <span className="text-[13px] text-[#64748B]">Deadline</span>
                  <span className="text-[14px] font-medium text-[#0F172A]">
                    {selectedItem.deadline || "-"}
                  </span>
                </div>
              </div>

              {/* Card Priority */}
              <div className="bg-white border border-[#E2E8F0] rounded-xl p-4 flex items-center gap-4 shadow-sm hover:border-[#CBD5E1] transition-colors">
                <div className="w-10 h-10 rounded-full bg-[#F1F5F9] flex items-center justify-center shrink-0">
                  <Star className="w-5 h-5 text-[#64748B]" />
                </div>
                <div className="flex flex-col">
                  <span className="text-[13px] text-[#64748B]">Priority</span>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-[14px] font-medium text-[#0F172A]">
                      {getPriorityInfo(selectedItem.priority).label}
                    </span>
                    <span
                      className={`text-[11px] font-semibold px-2 py-0.5 rounded-md ${getPriorityInfo(selectedItem.priority).color}`}
                    >
                      {getPriorityInfo(selectedItem.priority).badge}
                    </span>
                  </div>
                </div>
              </div>

              {/* Card Category */}
              <div className="bg-white border border-[#E2E8F0] rounded-xl p-4 flex items-center gap-4 shadow-sm hover:border-[#CBD5E1] transition-colors">
                <div className="w-10 h-10 rounded-full bg-[#F1F5F9] flex items-center justify-center shrink-0">
                  <Tag className="w-5 h-5 text-[#64748B]" />
                </div>
                <div className="flex flex-col">
                  <span className="text-[13px] text-[#64748B]">Category</span>
                  <span className="text-[14px] font-medium text-[#0F172A] capitalize">
                    {selectedItem.category}
                  </span>
                </div>
              </div>

              {/* Card Preferred Window */}
              <div className="bg-white border border-[#E2E8F0] rounded-xl p-4 flex items-center gap-4 shadow-sm col-span-2 hover:border-[#CBD5E1] transition-colors">
                <div className="w-10 h-10 rounded-full bg-[#F1F5F9] flex items-center justify-center shrink-0">
                  <Clock className="w-5 h-5 text-[#64748B]" />
                </div>
                <div className="flex flex-col">
                  <span className="text-[13px] text-[#64748B]">
                    Preferred Window
                  </span>
                  <span className="text-[14px] font-medium text-[#0F172A] capitalize">
                    {selectedItem.preferred_window || "-"}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
