"use client";

import { useState } from "react";

interface CounselorApproveBarProps {
  payload: { draft: string; message: string };
  onApprove: (editedDraft?: string | null) => void;
  onReject: () => void;
}

export function CounselorApproveBar({
  payload,
  onApprove,
  onReject,
}: CounselorApproveBarProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [draft, setDraft] = useState(payload.draft);

  const handleCancelEdit = () => {
    setDraft(payload.draft);
    setIsEditing(false);
  };

  return (
    <div className="flex flex-col rounded-3xl border border-[#E5E7EB] p-6 shadow-sm fade-out-20 max-w-200 w-full self-center">
      <p className="text-[14px] font-semibold text-[#0A0A0A] mb-4">
        Udah pas belum?
      </p>
      <div className="w-full gap-3">
        <button
          type="button"
          onClick={() => onApprove()}
          className="w-full rounded-full bg-[#8A38F5] px-5 py-2 text-[14px] font-semibold text-white transition hover:brightness-110"
        >
          Udah pas
        </button>
      </div>
    </div>
  );
}
