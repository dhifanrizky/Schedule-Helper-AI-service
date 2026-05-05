"use client";

interface PrioritizerReviewCardProps {
  payload: {
    tasks: { task: string; priority: number; deadline: string }[];
    message: string;
  };
  onConfirm: (
    tasks: { task: string; priority: number; deadline: string }[],
  ) => void;
}

const getPriorityLabel = (priority: number) => {
  if (priority >= 5) return "Highest";
  if (priority >= 4) return "High";
  if (priority >= 3) return "Medium";
  return "Low";
};

export function PrioritizerReviewCard({
  payload,
  onConfirm
}: PrioritizerReviewCardProps) {
  const totalTasks = payload.tasks.length;
  const highPriorityCount = payload.tasks.filter((task) => task.priority >= 4)
    .length;

  return (
    <div className="rounded-3xl border border-[#E5E7EB] bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-full bg-[#8A38F5]/10 px-3 py-1 text-[12px] font-semibold text-[#8A38F5]">
          Prioritizer Review
        </span>
        <span className="rounded-full bg-[#F3F4F6] px-3 py-1 text-[12px] font-semibold text-[#111827]">
          {totalTasks} tasks
        </span>
        {highPriorityCount > 0 && (
          <span className="rounded-full bg-[#FEF3C7] px-3 py-1 text-[12px] font-semibold text-[#92400E]">
            {highPriorityCount} high priority
          </span>
        )}
      </div>

      {payload.message && (
        <p className="mt-3 text-[14px] text-[#111827]">
          {payload.message}
        </p>
      )}

      <div className="mt-4 space-y-3">
        {payload.tasks.map((task, index) => (
          <div
            key={`${task.task}-${index}`}
            className="rounded-2xl border border-[#E5E7EB] bg-[#F9FAFB] p-4"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-[14px] font-semibold text-[#0A0A0A]">
                  {task.task}
                </p>
                <p className="mt-1 text-[12px] text-[#6B7280]">
                  Deadline: {task.deadline || "-"}
                </p>
              </div>
              <span className="rounded-full bg-white px-3 py-1 text-[12px] font-semibold text-[#0A0A0A] border border-[#E5E7EB]">
                {getPriorityLabel(task.priority)}
              </span>
            </div>
          </div>
        ))}
      </div>

      <button
        type="button"
        className="mt-5 rounded-full bg-[#8A38F5] px-5 py-2 text-[14px] font-semibold text-white transition hover:brightness-110"
        onClick={() => onConfirm(payload.tasks)}
      >
        Konfirmasi
      </button>
    </div>
  );
}
