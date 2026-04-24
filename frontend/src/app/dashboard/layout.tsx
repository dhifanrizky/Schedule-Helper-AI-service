"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

type UserProfile = {
  name: string;
  email: string;
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();

  // Dynamic User Profile state
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isUserLoading, setIsUserLoading] = useState(true);
  const [hasMessages, setHasMessages] = useState(false);

  // Fetch User Simulation (Persisted across dashboard pages)
  useEffect(() => {
    const fetchUser = async () => {
      try {
        const storedUser = sessionStorage.getItem("app_user");
        if (storedUser) {
          setUser(JSON.parse(storedUser));
          setIsUserLoading(false);
          return;
        }

        await new Promise((res) => setTimeout(res, 2500));
        const userData = { name: "Dipson", email: "dipson@gmail.com" };
        setUser(userData);
        sessionStorage.setItem("app_user", JSON.stringify(userData));
        // Dispatch custom event if other components are listening
        window.dispatchEvent(new Event("user_updated"));
      } catch (e) {
        console.error(e);
      } finally {
        setIsUserLoading(false);
      }
    };
    fetchUser();
  }, []);

  // Listen to chat message changes for showing/hiding sidebar
  useEffect(() => {
    const checkMessages = () => {
      const msgs = sessionStorage.getItem("chat_messages");
      setHasMessages(msgs ? JSON.parse(msgs).length > 0 : false);
    };
    
    checkMessages();
    window.addEventListener("storage", checkMessages);
    window.addEventListener("chat_updated", checkMessages);
    
    return () => {
      window.removeEventListener("storage", checkMessages);
      window.removeEventListener("chat_updated", checkMessages);
    };
  }, []);

  const userInitial = user?.name ? user.name.charAt(0).toUpperCase() : "";

  // The sidebar should only be hidden on the /dashboard route IF there are no messages (Start State)
  const isDashboardStart = pathname === "/dashboard" && !hasMessages;

  if (isDashboardStart) {
    // Return children directly (the full-screen gradient Start State)
    return <>{children}</>;
  }

  // Active state logic
  const isDashboardActive = pathname === "/dashboard";
  const isHistoryActive = pathname === "/dashboard/history";

  return (
    <div className="flex h-screen bg-[#FDFDFD] transition-all duration-500 ease-in-out overflow-hidden">
      {/* 3. Global Sidebar Component */}
      <aside className="w-[260px] sm:w-[280px] h-full border-r border-gray-100 flex flex-col flex-shrink-0 bg-white z-10">
        <div className="p-6 pb-8 border-b border-gray-100">
          <h1 className="text-[20px] font-bold text-[#0A0A0A]">
            Schedule Helper
          </h1>
        </div>

        <nav className="flex-1 px-4 py-6 space-y-2">
          <Link
            href="/dashboard"
            className={`flex items-center gap-3 px-4 py-3.5 rounded-xl font-medium transition-colors cursor-pointer ${
              isDashboardActive
                ? "bg-[#8A38F5] text-white shadow-sm"
                : "text-gray-500 hover:bg-gray-50 hover:text-gray-900"
            }`}
          >
            <img
              src="/images%20dashboard/Dashboard.webp"
              alt="Dashboard"
              className={`w-5 h-5 object-contain ${
                isDashboardActive ? "filter brightness-0 invert" : ""
              }`}
            />
            Dashboard
          </Link>
          <Link
            href="/dashboard/history"
            className={`flex items-center gap-3 px-4 py-3.5 rounded-xl font-medium transition-colors cursor-pointer ${
              isHistoryActive
                ? "bg-[#8A38F5] text-white shadow-sm"
                : "text-gray-500 hover:bg-gray-50 hover:text-gray-900"
            }`}
          >
            <img
              src="/images%20dashboard/History.webp"
              alt="History"
              className={`w-5 h-5 object-contain ${
                isHistoryActive ? "filter brightness-0 invert" : ""
              }`}
            />
            History
          </Link>
          <Link
            href="/dashboard/profile"
            className={`flex items-center gap-3 px-4 py-3.5 rounded-xl font-medium transition-colors cursor-pointer ${
              pathname === "/dashboard/profile"
                ? "bg-[#8A38F5] text-white shadow-sm"
                : "text-gray-500 hover:bg-gray-50 hover:text-gray-900"
            }`}
          >
            <img
              src="/images%20dashboard/Profile.webp"
              alt="Profile"
              className={`w-5 h-5 object-contain ${
                pathname === "/dashboard/profile" ? "filter brightness-0 invert" : ""
              }`}
            />
            Profile
          </Link>
        </nav>

        {/* Dynamic User Profile Section */}
        <div className="p-4 border-t border-gray-100">
          <div 
            onClick={() => router.push("/dashboard/profile")}
            className="flex items-center gap-3 p-2 rounded-xl hover:bg-gray-50 cursor-pointer transition-colors"
          >
            {isUserLoading || !user ? (
              <>
                <div className="w-10 h-10 bg-[#C2C2C2] rounded-full animate-pulse shrink-0" />
                <div className="flex flex-col gap-2 w-full">
                  <div className="h-4 bg-gray-200 rounded w-2/3 animate-pulse" />
                  <div className="h-3 bg-gray-100 rounded w-full animate-pulse" />
                </div>
              </>
            ) : (
              <>
                <div className="w-10 h-10 bg-[#0A0A0A] text-white rounded-full flex items-center justify-center font-semibold text-[15px] shrink-0 animate-in fade-in duration-300">
                  {userInitial}
                </div>
                <div className="flex flex-col overflow-hidden animate-in fade-in duration-300">
                  <span className="text-[14px] font-semibold text-[#0A0A0A] truncate leading-tight">
                    {user?.name}
                  </span>
                  <span className="text-[13px] text-gray-500 truncate mt-0.5">
                    {user?.email}
                  </span>
                </div>
              </>
            )}
          </div>
          <button
            onClick={() => {
              // Reset logic 
              sessionStorage.removeItem("chat_messages");
              router.push("/");
            }}
            className="flex items-center gap-3 mt-4 px-3 text-[14px] text-gray-500 hover:text-gray-900 font-medium w-full text-left transition-colors"
          >
            <img
              src="/images%20dashboard/Logout.webp"
              alt="Logout"
              className="w-[18px] h-[18px] object-contain opacity-80"
            />
            Logout
          </button>
        </div>
      </aside>

      {/* Render the specific page content inside the remaining space */}
      {children}
    </div>
  );
}
