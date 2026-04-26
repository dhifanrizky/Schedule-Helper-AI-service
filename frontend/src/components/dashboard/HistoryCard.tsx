import { HistoryItem } from "@/types";

interface HistoryCardProps {
  item: HistoryItem;
}

/**
 * Komponen kartu untuk menampilkan satu item riwayat jadwal.
 */
export function HistoryCard({ item }: HistoryCardProps) {
  return (
    <div className="w-full bg-white border border-[#F3F4F6] rounded-[16px] p-6 hover:shadow-[0_4px_20px_rgb(0,0,0,0.04)] transition-shadow cursor-pointer flex flex-col gap-2.5 relative">
      <div className="absolute top-6 right-6 bg-[#D3C1FF] text-[#8A38F5] px-4 py-1 rounded-full text-[13px] font-medium tracking-wide">
        {item.status}
      </div>
      <h3 className="text-[17px] font-bold text-[#0A0A0A] pr-32">
        {item.title}
      </h3>
      <div className="flex items-center gap-2 text-[14px] text-[#717182]">
        <img src="/images-history/Date.webp" alt="Date" className="w-[18px] h-[18px] object-contain" />
        <span>{item.date}</span>
      </div>
      <div className="flex items-center gap-6 mt-1.5 text-[14px] text-[#717182]">
        <div className="flex items-center gap-2">
          <img src="/images-history/Priorities.webp" alt="Priorities" className="w-[18px] h-[18px] object-contain" />
          <span>{item.priorities} priorities</span>
        </div>
        <div className="flex items-center gap-2">
          <img src="/images-history/Quick%20Wins.webp" alt="Quick Wins" className="w-[18px] h-[18px] object-contain" />
          <span>{item.quickWins} quick wins</span>
        </div>
      </div>
    </div>
  );
}
