"use client";

import { useEffect, useState } from "react";
import { HistoryItem } from "@/types";
import { scheduleService } from "@/services/scheduleService";
import { HistoryCard } from "@/components/dashboard/HistoryCard";

/**
 * HISTORY PAGE
 * Menampilkan daftar riwayat jadwal yang pernah dibuat.
 */
export default function HistoryPage() {
  const [historyData, setHistoryData] = useState<HistoryItem[] | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const data = await scheduleService.getHistory();
        setHistoryData(data);
      } catch (e) {
        console.error("Failed to fetch history:", e);
      } finally {
        setIsLoading(false);
      }
    };
    fetchHistory();
  }, []);

  return (
    <main className="flex-1 flex flex-col h-full bg-[#FFFFFF]">
      <div className="px-8 pt-10 pb-6 shrink-0">
        <h1 className="text-[26px] font-semibold text-[#0A0A0A] mb-1">Schedule History</h1>
        <p className="text-[15px] text-[#717182]">View all your past schedules and task plans</p>
      </div>

      <div className="flex-1 overflow-y-auto px-8 pb-10">
        <div className="max-w-4xl flex flex-col gap-4">
          {/* Skeleton Loader */}
          {isLoading && (
            <>
              {[1, 2, 3].map((skeleton) => (
                <div
                  key={skeleton}
                  className="w-full bg-white border border-[#F3F4F6] rounded-[16px] h-[124px] animate-pulse flex flex-col justify-center px-6 py-5 gap-3 shadow-sm"
                >
                  <div className="flex justify-between items-center w-full">
                    <div className="h-5 bg-gray-200 rounded w-1/3"></div>
                    <div className="h-7 bg-[#D3C1FF]/40 rounded-full w-24"></div>
                  </div>
                  <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                  <div className="h-4 bg-gray-200 rounded w-2/4 mt-2"></div>
                </div>
              ))}
            </>
          )}

          {/* Empty State */}
          {!isLoading && historyData?.length === 0 && (
            <div className="flex flex-col items-center justify-center text-center mt-20 p-10 border border-dashed border-gray-200 rounded-[16px] bg-gray-50">
              <svg className="w-12 h-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-[15px] text-[#717182] font-medium">No history found. Start your first session on the Dashboard!</p>
            </div>
          )}

          {/* History Cards */}
          {!isLoading && historyData && historyData.length > 0 &&
            historyData.map((item) => <HistoryCard key={item.id} item={item} />)
          }
        </div>
      </div>
    </main>
  );
}
