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
  onReject
}: CounselorApproveBarProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [draft, setDraft] = useState(payload.draft);

  const handleCancelEdit = () => {
    setDraft(payload.draft);
    setIsEditing(false);
  };

  if (isEditing) {
    return (
      <div className="rounded-3xl border border-[#E5E7EB] bg-white p-6 shadow-sm">
        <p className="text-[14px] font-semibold text-[#0A0A0A] mb-3">
          Edit kesimpulan
        </p>
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          rows={5}
          className="w-full resize-none rounded-2xl border border-[#E5E7EB] bg-[#F9FAFB] px-4 py-3 text-[14px] text-[#0A0A0A] focus:outline-none focus:ring-2 focus:ring-[#8A38F5]/40"
        />
        <div className="mt-4 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={handleCancelEdit}
            className="rounded-full border border-[#E5E7EB] bg-white px-5 py-2 text-[14px] font-semibold text-[#0A0A0A] transition hover:border-[#8A38F5]/50"
          >
            Batal
          </button>
          <button
            type="button"
            onClick={() => onApprove(draft)}
            className="rounded-full bg-[#8A38F5] px-5 py-2 text-[14px] font-semibold text-white transition hover:brightness-110"
          >
            Simpan &amp; Lanjut
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-3xl border border-[#E5E7EB] bg-white p-6 shadow-sm">
      <p className="text-[14px] font-semibold text-[#0A0A0A] mb-4">
        Kamu mau gimana?
      </p>
      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={onReject}
          className="rounded-full border border-[#E5E7EB] bg-white px-5 py-2 text-[14px] font-semibold text-[#0A0A0A] transition hover:border-[#8A38F5]/50"
        >
          Tambahin cerita dulu
        </button>
        <button
          type="button"
          onClick={() => setIsEditing(true)}
          className="rounded-full border border-[#8A38F5] bg-white px-5 py-2 text-[14px] font-semibold text-[#8A38F5] transition hover:bg-[#8A38F5]/10"
        >
          Edit kesimpulan
        </button>
        <button
          type="button"
          onClick={() => onApprove()}
          className="rounded-full bg-[#8A38F5] px-5 py-2 text-[14px] font-semibold text-white transition hover:brightness-110"
        >
          Udah pas
        </button>
      </div>
    </div>
  );
}
