"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useUser } from "@/hooks/useUser";
import { chatService } from "@/services/chatService";
import {
  IoIosArrowDropleftCircle,
  IoIosArrowDroprightCircle,
} from "react-icons/io";
import { removeChatSession } from "@/utils/removeChatMsgs";

/**
 * DASHBOARD LAYOUT
 * Mengelola Sidebar global dan state profil pengguna.
 */
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();

  // 1. Logika User (menggantikan useEffect fetchUser manual)
  const { user, isUserLoading, userInitial, logout } = useUser();

  // 2. Logika Sidebar (hasMessages menentukan apakah sidebar muncul)
  const [hasMessages, setHasMessages] = useState(false);

  useEffect(() => {
    const checkMessages = () => {
      const messages = chatService.getStoredMessages();
      setHasMessages(messages.length > 0);
    };

    checkMessages();
    // Dengerkan event pembaruan chat agar sidebar muncul otomatis
    window.addEventListener("chat_updated", checkMessages);
    return () => window.removeEventListener("chat_updated", checkMessages);
  }, []);

  // Kondisi "Start State": berada di /dashboard dan belum ada chat
  const [isSdbrClose, setIsSdbrClose] = useState(false);

  // Navigasi Active
  const isDashboardActive = pathname === "/dashboard";
  const isHistoryActive = pathname === "/dashboard/history";
  const isProfileActive = pathname === "/dashboard/profile";

  return (
    <div
      className={
        "flex h-screen bg-[#FDFDFD] transition-all duration-500 ease-in-out overflow-hidden"
      }
    >
      {/* Sidebar Component */}
      <aside
        className={`relative transition-all duration-300 h-full border-r border-gray-100 flex flex-col shrink-0 bg-white z-10 ${isSdbrClose ? "w-65 sm:w-70" : "w-20"}`}
      >
        <button
          onClick={() => setIsSdbrClose(!isSdbrClose)}
          className={`absolute text-black z-50 cursor-pointer top-5 ${isSdbrClose ? "-right-5" : "-right-5"}`}
        >
          {isSdbrClose ? (
            <IoIosArrowDropleftCircle className="w-10 h-10" />
          ) : (
            <IoIosArrowDroprightCircle className="w-10 h-10" />
          )}
        </button>
        {isSdbrClose ? (
          <>
            <div className="p-6 pb-8 border-b border-gray-100 group-[content]:">
              <Link
                href="/"
                onClick={() => chatService.clearChat()}
                className="text-[20px] font-bold text-[#0A0A0A] cursor-pointer no-underline block"
              >
                Schedule Helper
              </Link>
            </div>
            <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
              <Link
                href="/dashboard"
                className={`flex items-center gap-3 px-4 py-3.5 rounded-xl font-medium transition-colors cursor-pointer ${
                  isDashboardActive
                    ? "bg-[#8A38F5] text-white shadow-sm"
                    : "text-gray-500 hover:bg-gray-50"
                }`}
                onClick={() => removeChatSession()}
              >
                <img
                  src="/images-dashboard/Dashboard.webp"
                  alt="Dashboard"
                  className={`w-5 h-5 ${isDashboardActive ? "filter brightness-0 invert" : ""}`}
                />
                Dashboard
              </Link>
              <Link
                href="/dashboard/history"
                className={`flex items-center gap-3 px-4 py-3.5 rounded-xl font-medium transition-colors cursor-pointer ${
                  isHistoryActive
                    ? "bg-[#8A38F5] text-white shadow-sm"
                    : "text-gray-500 hover:bg-gray-50"
                }`}
              >
                <img
                  src="/images-dashboard/History.webp"
                  alt="History"
                  className={`w-5 h-5 ${isHistoryActive ? "filter brightness-0 invert" : ""}`}
                />
                History
              </Link>
              <Link
                href="/dashboard/profile"
                className={`flex items-center gap-3 px-4 py-3.5 rounded-xl font-medium transition-colors cursor-pointer ${
                  isProfileActive
                    ? "bg-[#8A38F5] text-white shadow-sm"
                    : "text-gray-500 hover:bg-gray-50"
                }`}
              >
                <img
                  src="/images-dashboard/Profile.webp"
                  alt="Profile"
                  className={`w-5 h-5 ${isProfileActive ? "filter brightness-0 invert" : ""}`}
                />
                Profile
              </Link>
            </nav>
            {/* User Profile Section */}
            <div className="p-4 border-t border-gray-100 mt-auto">
              <div
                onClick={() => router.push("/dashboard/profile")}
                className="flex items-center gap-3 p-2 rounded-xl hover:bg-gray-50 cursor-pointer transition-colors"
              >
                {isUserLoading || !user ? (
                  <div className="w-10 h-10 bg-[#C2C2C2] rounded-full animate-pulse shrink-0" />
                ) : (
                  <>
                    <div className="w-10 h-10 bg-[#0A0A0A] text-white rounded-full flex items-center justify-center font-semibold text-[15px] shrink-0">
                      {userInitial}
                    </div>
                    <div className="flex flex-col overflow-hidden">
                      <span className="text-[14px] font-semibold text-[#0A0A0A] truncate leading-tight">
                        {user.name}
                      </span>
                      <span className="text-[13px] text-gray-500 truncate mt-0.5">
                        {user.email}
                      </span>
                    </div>
                  </>
                )}
              </div>
              <button
                onClick={logout}
                className="flex items-center gap-3 mt-4 px-3 text-[14px] text-gray-500 hover:text-gray-900 font-medium w-full text-left transition-colors"
              >
                <img
                  src="/images-dashboard/Logout.webp"
                  alt="Logout"
                  className="w-4.5 h-[18px] opacity-80"
                />
                Logout
              </button>
            </div>
          </>
        ) : (
          <>
            <div className="p-6 pb-8 border-b border-gray-100 group-[content]:">
              <Link
                href="/"
                onClick={() => chatService.clearChat()}
                className="text-[20px] font-bold text-[#0A0A0A] cursor-pointer no-underline block"
              >
                SH
              </Link>
            </div>
            <nav className="flex-1 px-2 py-6 space-y-2 overflow-y-auto">
              <Link
                href="/dashboard"
                className={`flex items-center justify-center p-3 rounded-xl transition-colors ${
                  isDashboardActive
                    ? "bg-[#8A38F5] shadow-sm"
                    : "hover:bg-gray-50"
                }`}
                onClick={() => removeChatSession()}
              >
                <img
                  src="/images-dashboard/Dashboard.webp"
                  alt="Dashboard"
                  className={`w-5 h-5 ${
                    isDashboardActive ? "filter brightness-0 invert" : ""
                  }`}
                />
              </Link>
              <Link
                href="/dashboard/history"
                className={`flex items-center justify-center p-3 rounded-xl transition-colors ${
                  isHistoryActive
                    ? "bg-[#8A38F5] shadow-sm"
                    : "hover:bg-gray-50"
                }`}
              >
                <img
                  src="/images-dashboard/History.webp"
                  alt="History"
                  className={`w-5 h-5 ${
                    isHistoryActive ? "filter brightness-0 invert" : ""
                  }`}
                />
              </Link>
              <Link
                href="/dashboard/profile"
                className={`flex items-center justify-center p-3 rounded-xl transition-colors  ${
                  isProfileActive
                    ? "bg-[#8A38F5] text-white shadow-sm"
                    : "text-gray-500 hover:bg-gray-50"
                }`}
              >
                <img
                  src="/images-dashboard/Profile.webp"
                  alt="Profile"
                  className={`w-5 h-5 ${isProfileActive ? "filter brightness-0 invert" : ""}`}
                />
              </Link>
            </nav>
            <div className="p-4 border-t border-gray-100 mt-auto">
              <div
                onClick={() => router.push("/dashboard/profile")}
                className="flex items-center gap-3 p-2 rounded-xl hover:bg-gray-50 cursor-pointer transition-colors"
              >
                {isUserLoading || !user ? (
                  <div className="w-10 h-10 bg-[#C2C2C2] rounded-full animate-pulse shrink-0" />
                ) : (
                  <>
                    <div className="w-10 h-10 bg-[#0A0A0A] text-white rounded-full flex items-center justify-center font-semibold text-[15px] shrink-0">
                      {userInitial}
                    </div>
                    <div className="flex flex-col overflow-hidden">
                      <span className="text-[14px] font-semibold text-[#0A0A0A] truncate leading-tight">
                        {user.name}
                      </span>
                      <span className="text-[13px] text-gray-500 truncate mt-0.5">
                        {user.email}
                      </span>
                    </div>
                  </>
                )}
              </div>
              <button
                onClick={logout}
                className="flex items-center gap-3 mt-4 px-3 text-[14px] text-gray-500 hover:text-gray-900 font-medium w-full text-left transition-colors"
              >
                <img
                  src="/images-dashboard/Logout.webp"
                  alt="Logout"
                  className="w-4.5 h-4.5 opacity-80"
                />
              </button>
            </div>
          </>
        )}
      </aside>

      {children}
    </div>
  );
}
