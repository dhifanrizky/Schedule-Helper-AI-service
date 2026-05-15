import React, { useEffect, useState } from "react";
import { ScheduleItem } from "@/types";
import {
  Clock,
  CalendarDays,
  MoreVertical,
  Plus,
  Pencil,
  Trash2,
  CheckCircle2,
  GripVertical,
  ChevronLeft,
  ChevronRight,
  FileText,
} from "lucide-react";

interface ResultStateProps {
  scheduleItems?: ScheduleItem[];
  onApprove?: () => void;
}

interface Blueprint {
  id: string;
  title: string;
  estimated_minutes: number;
  priority: number;
  subtasks: string[];
  deadline: string;
  preferred_window: string;
  category: string;
  isSpecificTime: boolean;
  specific_start_time: string;
  time: string;
}

interface TaskData {
  title: string;
  estimated_minutes: number | string;
  deadline: string;
  preferred_window: string;
  priority: number;
  category: string;
  isSpecificTime: boolean;
  specific_start_time: string;
}

export function ResultState({
  scheduleItems,
  onApprove,
}: ResultStateProps) {
  const [blueprints, setBlueprints] = useState<Blueprint[]>([]);

  const [selectedBlueprintId, setSelectedBlueprintId] = useState("");

  const selectedBlueprint =
    blueprints.find((b) => b.id === selectedBlueprintId) || blueprints[0];

  const [taskData, setTaskData] = useState<TaskData>({
    title: "Untitled Task",
    estimated_minutes: 30,
    deadline: "",
    preferred_window: "bebas",
    priority: 3,
    category: "general",
    isSpecificTime: false,
    specific_start_time: "19:00",
  });

  useEffect(() => {
    const mapped = (scheduleItems ?? []).map((item, index) => ({
      id: item.task_id || `task-${index}`,
      title: item.title,
      estimated_minutes: item.estimated_minutes,
      priority: item.priority,
      subtasks: item.subtasks ?? [],
      deadline: item.deadline ?? "",
      preferred_window: item.preferred_window ?? "bebas",
      category: item.category ?? "general",
      isSpecificTime: item.is_locked_time ?? false,
      specific_start_time: item.locked_start_time ?? "19:00",
      time: item.time || "Belum dijadwalkan",
    }));

    setBlueprints(mapped);

    if (mapped.length > 0) {
      const first = mapped[0];
      setSelectedBlueprintId(first.id);
      setTaskData({
        title: first.title,
        estimated_minutes: first.estimated_minutes,
        deadline: first.deadline,
        preferred_window: first.preferred_window,
        priority: first.priority,
        category: first.category,
        isSpecificTime: first.isSpecificTime,
        specific_start_time: first.specific_start_time,
      });
    }
  }, [scheduleItems]);

  useEffect(() => {
    if (!selectedBlueprint) return;
    setTaskData({
      title: selectedBlueprint.title,
      estimated_minutes: selectedBlueprint.estimated_minutes,
      deadline: selectedBlueprint.deadline,
      preferred_window: selectedBlueprint.preferred_window,
      priority: selectedBlueprint.priority,
      category: selectedBlueprint.category,
      isSpecificTime: selectedBlueprint.isSpecificTime,
      specific_start_time: selectedBlueprint.specific_start_time,
    });
  }, [selectedBlueprintId, selectedBlueprint]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => {
    const target = e.target as HTMLInputElement | HTMLSelectElement;
    const { name, type } = target as HTMLInputElement;

    let value: any;

    if (type === "checkbox") {
      value = (target as HTMLInputElement).checked;
    } else if (type === "number") {
      const raw = (target as HTMLInputElement).value;
      value = raw === "" ? "" : Number(raw);
    } else if (name === "priority") {
      value = Number((target as HTMLSelectElement).value);
    } else {
      value = (target as HTMLInputElement).value;
    }

    setTaskData((prev) => {
      const next = {
        ...prev,
        [name]: value,
      };

      if (selectedBlueprintId) {
        setBlueprints((current) =>
          current.map((bp) =>
            bp.id === selectedBlueprintId
              ? {
                  ...bp,
                  title: next.title,
                  estimated_minutes:
                    typeof next.estimated_minutes === "number"
                      ? next.estimated_minutes
                      : Number(next.estimated_minutes || 0),
                  priority: next.priority,
                  deadline: next.deadline,
                  preferred_window: next.preferred_window,
                  category: next.category,
                  isSpecificTime: next.isSpecificTime,
                  specific_start_time: next.specific_start_time,
                }
              : bp,
          ),
        );
      }

      return next;
    });
  };

  const handleSubtaskChange = (index: number, value: string) => {
    setBlueprints((prev) =>
      prev.map((bp) =>
        bp.id === selectedBlueprintId
          ? {
              ...bp,
              subtasks: bp.subtasks.map((s, i) =>
                i === index ? value : s,
              ),
            }
          : bp,
      ),
    );
  };

  const addSubtask = () => {
    setBlueprints((prev) =>
      prev.map((bp) =>
        bp.id === selectedBlueprintId
          ? {
              ...bp,
              subtasks: [...bp.subtasks, "Subtask baru"],
            }
          : bp,
      ),
    );
  };

  const removeSubtask = (index: number) => {
    setBlueprints((prev) =>
      prev.map((bp) =>
        bp.id === selectedBlueprintId
          ? {
              ...bp,
              subtasks: bp.subtasks.filter((_, i) => i !== index),
            }
          : bp,
      ),
    );
  };

  const addBlueprint = () => {
    const newBlueprint: Blueprint = {
      id: `manual-${Date.now()}`,
      title: "Blueprint Baru",
      estimated_minutes: 30,
      priority: 3,
      subtasks: ["Task pertama"],
      deadline: "",
      preferred_window: "bebas",
      category: "general",
      isSpecificTime: false,
      specific_start_time: "19:00",
      time: "Belum dijadwalkan",
    };

    setBlueprints((prev) => [...prev, newBlueprint]);
    setSelectedBlueprintId(newBlueprint.id);

    setTaskData((prev) => ({
      ...prev,
      title: newBlueprint.title,
      estimated_minutes: newBlueprint.estimated_minutes,
      priority: newBlueprint.priority,
    }));
  };

  return (
    <div className="grid grid-cols-1 xl:grid-cols-[320px_1fr_420px] gap-5 text-slate-900">
      {/* LEFT SIDEBAR */}
      <div className="bg-white border border-slate-200 rounded-3xl overflow-hidden h-fit">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-xl bg-indigo-50 flex items-center justify-center">
              <FileText size={18} className="text-indigo-600" />
            </div>

            <div>
              <h2 className="font-semibold text-slate-900">
                Blueprint Tugas
              </h2>
              <p className="text-xs text-slate-400">
                {blueprints.length} blueprint
              </p>
            </div>
          </div>

          <button
            onClick={addBlueprint}
            className="h-9 w-9 rounded-xl border border-slate-200 flex items-center justify-center hover:bg-slate-50 transition"
          >
            <Plus size={18} className="text-slate-600" />
          </button>
        </div>

        <div className="max-h-175 overflow-y-auto">
          {blueprints.map((blueprint) => {
            const isActive = blueprint.id === selectedBlueprintId;

            return (
              <button
                key={blueprint.id}
                onClick={() => {
                  setSelectedBlueprintId(blueprint.id);

                  setTaskData((prev) => ({
                    ...prev,
                    title: blueprint.title,
                    estimated_minutes:
                      blueprint.estimated_minutes,
                    priority: blueprint.priority,
                  }));
                }}
                className={`w-full text-left px-5 py-4 border-b border-slate-100 transition ${
                  isActive
                    ? "bg-indigo-50/70"
                    : "hover:bg-slate-50"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3
                      className={`font-medium ${
                        isActive
                          ? "text-indigo-700"
                          : "text-slate-800"
                      }`}
                    >
                      {blueprint.title}
                    </h3>

                    <p className="text-sm text-slate-400 mt-1">
                      {blueprint.subtasks.length} subtasks •{" "}
                      {blueprint.estimated_minutes} menit
                    </p>
                  </div>

                  <MoreVertical
                    size={16}
                    className="text-slate-400 shrink-0"
                  />
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* CENTER */}
      <div className="bg-white border border-slate-200 rounded-3xl p-6">
        <div className="flex items-center justify-between gap-4 mb-8">
          <div>
            <h2 className="text-2xl font-semibold text-slate-900">
              {taskData.title}
            </h2>

            <p className="text-sm text-slate-400 mt-1">
              Review blueprint sebelum dijadwalkan
            </p>
          </div>

          <button className="h-10 w-10 rounded-xl border border-slate-200 flex items-center justify-center hover:bg-slate-50 transition">
            <Pencil size={18} className="text-slate-600" />
          </button>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <label className="text-sm font-medium text-slate-600 mb-2 block">
              Estimasi Waktu
            </label>

            <div className="relative">
              <input
                type="number"
                name="estimated_minutes"
                value={taskData.estimated_minutes}
                onChange={handleChange}
                className="w-full h-12 rounded-2xl border border-slate-200 px-4 bg-white outline-none focus:ring-2 focus:ring-indigo-500/20"
              />

              <span className="absolute right-4 top-1/2 -translate-y-1/2 text-sm text-slate-400">
                menit
              </span>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-slate-600 mb-2 block">
              Prioritas
            </label>

            <select
              name="priority"
              value={taskData.priority}
              onChange={handleChange}
              className="w-full h-12 rounded-2xl border border-slate-200 px-4 bg-white outline-none focus:ring-2 focus:ring-indigo-500/20"
            >
              <option value={1}>🔴 Sangat Penting</option>
              <option value={2}>🟠 Penting</option>
              <option value={3}>🟢 Biasa</option>
            </select>
          </div>
        </div>

        <div className="border-t border-slate-100 pt-6 space-y-6">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="font-semibold text-slate-900">
                  Subtasks
                </h3>

                <p className="text-sm text-slate-400">
                  Bisa diedit langsung
                </p>
              </div>

              <button
                onClick={addSubtask}
                className="flex items-center gap-2 text-sm font-medium text-indigo-600 hover:text-indigo-700"
              >
                <Plus size={16} />
                Tambah
              </button>
            </div>

            <div className="space-y-3">
              {(selectedBlueprint?.subtasks ?? []).map(
                (subtask, index) => (
                  <div
                    key={index}
                    className="group flex items-center gap-3 border border-slate-200 rounded-2xl px-4 py-3 hover:border-slate-300 transition"
                  >
                    <GripVertical
                      size={16}
                      className="text-slate-300"
                    />

                    <CheckCircle2
                      size={18}
                      className="text-indigo-500 shrink-0"
                    />

                    <input
                      value={subtask}
                      onChange={(e) =>
                        handleSubtaskChange(
                          index,
                          e.target.value,
                        )
                      }
                      className="flex-1 bg-transparent outline-none text-sm text-slate-700"
                    />

                    <button className="opacity-0 group-hover:opacity-100 transition">
                      <Pencil
                        size={16}
                        className="text-slate-400"
                      />
                    </button>

                    <button
                      onClick={() => removeSubtask(index)}
                      className="opacity-0 group-hover:opacity-100 transition"
                    >
                      <Trash2
                        size={16}
                        className="text-red-400"
                      />
                    </button>
                  </div>
                ),
              )}
            </div>
          </div>

          <div className="border-t border-slate-100 pt-6">
            <label className="text-sm font-medium text-slate-600 mb-2 block">
              Deadline
            </label>

            <input
              type="date"
              name="deadline"
              value={taskData.deadline}
              onChange={handleChange}
              className="w-full h-12 rounded-2xl border border-slate-200 px-4 bg-white outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
          </div>

          <div className="flex gap-3 pt-2">
            <button className="flex-1 h-12 rounded-2xl border border-slate-200 font-medium text-slate-700 hover:bg-slate-50 transition">
              Simpan Revisi
            </button>

            <button
              onClick={onApprove}
              className="flex-1 h-12 rounded-2xl bg-indigo-600 hover:bg-indigo-700 transition text-white font-medium shadow-sm"
            >
              Approve & Jadwalkan
            </button>
          </div>
        </div>
      </div>

      {/* RIGHT PANEL */}
      <div className="bg-white border border-slate-200 rounded-3xl p-5 h-fit">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 rounded-xl bg-emerald-50 flex items-center justify-center">
            <CalendarDays
              size={18}
              className="text-emerald-600"
            />
          </div>

          <div>
            <h2 className="font-semibold text-slate-900">
              Draft Kalender
            </h2>

            <p className="text-sm text-slate-400">
              Visualisasi jadwal
            </p>
          </div>
        </div>

        <div className="h-14 border border-slate-200 rounded-2xl px-4 flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <CalendarDays
              size={18}
              className="text-slate-500"
            />

            <span className="font-medium text-slate-700">
              Rabu, 13 Mei 2026
            </span>
          </div>

          <div className="flex items-center gap-1">
            <button className="w-8 h-8 rounded-lg hover:bg-slate-100 flex items-center justify-center">
              <ChevronLeft size={16} />
            </button>

            <button className="w-8 h-8 rounded-lg hover:bg-slate-100 flex items-center justify-center">
              <ChevronRight size={16} />
            </button>
          </div>
        </div>

        <div className="relative pl-8">
          <div className="absolute left-1.75 top-2 bottom-0 w-px bg-slate-200"></div>

          <div className="absolute left-0 top-2 w-4 h-4 rounded-full bg-indigo-500 border-4 border-white"></div>

          <div className="pb-8">
            <div className="flex items-center gap-2 text-indigo-600 font-semibold mb-2">
              <Clock size={16} />

              <span>
                {taskData.isSpecificTime
                  ? `${taskData.specific_start_time} - Selesai`
                  : selectedBlueprint?.time || "Belum dijadwalkan"}
              </span>

              <span className="ml-2 text-xs bg-red-50 text-red-600 px-2 py-1 rounded-full font-medium">
                Priority {taskData.priority}
              </span>
            </div>

            <h3 className="text-2xl font-semibold text-slate-900 mb-4">
              {taskData.title}
            </h3>

            <div className="rounded-2xl border border-slate-200 p-4 bg-slate-50/70">
              <h4 className="font-medium text-slate-800 mb-4">
                Subtasks
              </h4>

              <div className="space-y-3">
                {(selectedBlueprint?.subtasks ?? []).map(
                  (subtask, index) => (
                    <div
                      key={index}
                      className="flex items-center gap-3"
                    >
                      <CheckCircle2
                        size={16}
                        className="text-indigo-500 shrink-0"
                      />

                      <span className="text-sm text-slate-600 flex-1">
                        {subtask}
                      </span>

                      <button className="text-slate-400 hover:text-slate-600">
                        <Pencil size={15} />
                      </button>
                    </div>
                  ),
                )}
              </div>
            </div>
          </div>

          <div className="relative pb-2">
            <div className="absolute -left-7.25 top-2 w-3 h-3 rounded-full bg-slate-300 border-2 border-white"></div>

            <p className="text-sm text-slate-400">
              Sisa waktu luang...
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}