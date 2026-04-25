"use client";

import { Fragment, useEffect, useState } from "react";

// Tipe data untuk satu item riwayat jadwal
// === INTEGRASI BE: Sesuaikan field ini dengan schema response dari /api/schedules/history ===
type HistoryItem = {
  id: string;         // ID unik jadwal untuk keperluan routing ke detail
  title: string;      // Judul sesi (biasanya ringkasan dari chat user)
  date: string;       // Tanggal dibuat, format string (format dari backend perlu disesuaikan)
  priorities: number; // Jumlah tugas prioritas tinggi
  quickWins: number;  // Jumlah tugas quick win
  status: string;     // Status jadwal: 'completed' | 'in_progress' | 'cancelled'
};

export default function HistoryPage() {
  // Data riwayat jadwal (null = belum dimuat, [] = kosong, [...] = ada data)
  const [historyData, setHistoryData] = useState<HistoryItem[] | null>(null);
  // Menandai apakah data masih dalam proses dimuat (menampilkan skeleton loader)
  const [isLoading, setIsLoading] = useState(true);

  // === INTEGRASI BE: FETCHING ARRAY RIWAYAT JADWAL ===
  // [PENJELASAN]: Ganti simulasi dengan GET request ke endpoint history.
  // [METHOD]: GET | [ENDPOINT]: /api/schedules/history
  // [HEADERS]: Authorization: Bearer <token>
  // [QUERY PARAMS]: ?userId=<userId>&page=1&limit=10
  // [RESPONSE]: { data: HistoryItem[], total: number, page: number }
  // [MAPPING]: Pastikan interface HistoryItem sesuai dengan shape response JSON dari backend.
  // [CATATAN]: Tambahkan pagination jika daftar history panjang.
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        await new Promise((res) => setTimeout(res, 2500)); // 2.5s delay

        // Mock Data based on Figma bisa dimasukkan ke backend nanti untuk di sesuaikan
        const mockData: HistoryItem[] = [
          {
            id: "1",
            title: "Project Deadline & Personal Tasks",
            date: "Sunday, April 12, 2026",
            priorities: 3,
            quickWins: 5,
            status: "completed",
          },
          {
            id: "2",
            title: "Weekly Planning Session",
            date: "Saturday, April 11, 2026",
            priorities: 4,
            quickWins: 6,
            status: "completed",
          },
          {
            id: "3",
            title: "Morning Task Organization",
            date: "Friday, April 10, 2026",
            priorities: 2,
            quickWins: 4,
            status: "completed",
          },
        ];
        setHistoryData(mockData);
      } catch (e) {
        console.error(e);
      } finally {
        setIsLoading(false);
      }
    };
    fetchHistory();
  }, []);

  return (
    <main className="flex-1 flex flex-col h-full bg-[#FFFFFF]">
      {/* Judul halaman dan deskripsi singkat */}
      {/* Header */}
      <div className="px-8 pt-10 pb-6 border-b border-transparent shrink-0">
        <h1 className="text-[26px] font-semibold text-[#0A0A0A] mb-1">
          Schedule History
        </h1>
        <p className="text-[15px] text-[#717182]">
          View all your past schedules and task plans
        </p>
      </div>

      {/* Area konten utama yang bisa di-scroll secara vertikal */}
      <div className="flex-1 overflow-y-auto px-8 pb-10">
        <div className="max-w-4xl flex flex-col gap-4">
          {/* Skeleton Loader: Muncul saat data sedang dimuat dari API */}
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

          {/* Tampilan kosong: Muncul jika API mengembalikan array kosong ([]) */}
          {!isLoading && historyData?.length === 0 && (
            <div className="flex flex-col items-center justify-center text-center mt-20 p-10 border border-dashed border-gray-200 rounded-[16px] bg-gray-50">
              <svg
                className="w-12 h-12 text-gray-400 mb-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <p className="text-[15px] text-[#717182] font-medium">
                No history found. Start your first session on the Dashboard!
              </p>
            </div>
          )}

          {/* Tampilan kartu riwayat: Di-render setelah data berhasil dimuat dari API */}
          {!isLoading &&
            historyData &&
            historyData.length > 0 &&
            historyData?.map((item) => (
              <Fragment key={item.id}>
                {/* === INTEGRASI BE: LIHAT DETAIL RIWAYAT JADWAL === */}
                {/* [PENJELASAN]: Saat card diklik, navigasi ke halaman detail atau tampilkan modal. */}
                {/* [METHOD]: GET | [ENDPOINT]: /api/schedules/:id */}
                {/* [RESPONSE]: Data lengkap jadwal termasuk topPriorities, quickWins, timeline, reasoning */}
                <div
                  className="w-full bg-white border border-[#F3F4F6] rounded-[16px] p-6 hover:shadow-[0_4px_20px_rgb(0,0,0,0.04)] transition-shadow cursor-pointer flex flex-col gap-2.5 relative"
                >
                  {/* Status Badge */}
                  <div className="absolute top-6 right-6 bg-[#D3C1FF] text-[#8A38F5] px-4 py-1 rounded-full text-[13px] font-medium tracking-wide">
                    {item.status}
                  </div>

                  <h3 className="text-[17px] font-bold text-[#0A0A0A] pr-32">
                    {/* Sanitization is naturally handled by React curly braces */}
                    {item.title}
                  </h3>

                  <div className="flex items-center gap-2 text-[14px] text-[#717182]">
                    <img
                      src="/images-history/Date.webp"
                      alt="Date"
                      className="w-[18px] h-[18px] object-contain"
                    />
                    <span>{item.date}</span>
                  </div>

                  <div className="flex items-center gap-6 mt-1.5 text-[14px] text-[#717182]">
                    <div className="flex items-center gap-2">
                      <img
                        src="/images-history/Priorities.webp"
                        alt="Priorities"
                        className="w-[18px] h-[18px] object-contain"
                      />
                      <span>{item.priorities} priorities</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <img
                        src="/images-history/Quick%20Wins.webp"
                        alt="Quick Wins"
                        className="w-[18px] h-[18px] object-contain"
                      />
                      <span>{item.quickWins} quick wins</span>
                    </div>
                  </div>
                </div>
              </Fragment>
            ))}
        </div>
      </div>
    </main>
  );
}
