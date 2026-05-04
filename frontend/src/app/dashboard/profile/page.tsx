"use client";

import { useUser } from "@/hooks/useUser";
import { ProfileField } from "@/components/dashboard/ProfileField";

/**
 * PROFILE PAGE
 */
export default function ProfilePage() {
  const { user, isUserLoading, userInitial } = useUser();

  return (
    <main className="flex-1 bg-[#FFFFFF] p-8 sm:p-12 overflow-y-auto">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-[28px] font-bold text-[#0A0A0A] mb-1">Profile</h1>
        <p className="text-[15px] text-[#717182] mb-8">Manage your account information</p>

        {/* Profile Card */}
        <div className="bg-white border border-[#F3F4F6] rounded-[24px] p-10 shadow-sm flex flex-col gap-6">
          {/* Header Profil (Avatar Hitam) */}
          <div className="flex items-center gap-6 mb-4">
            <div className="w-[84px] h-[84px] bg-[#0A0A0A] rounded-full flex items-center justify-center text-white text-[32px] font-bold shrink-0">
              {isUserLoading ? "..." : userInitial}
            </div>
            <div className="flex flex-col gap-0.5">
              <h2 className="text-[24px] font-bold text-[#0A0A0A]">
                {isUserLoading ? "Loading..." : user?.name || "dipson"}
              </h2>
              <p className="text-[16px] text-[#717182]">Schedule Helper User</p>
            </div>
          </div>

          {/* List Informasi */}
          <div className="flex flex-col gap-5">
            <ProfileField
              label="Name"
              value={user?.name || "dipson"}
              icon="/images-profile/Profile.webp"
              isLoading={isUserLoading}
            />
            <ProfileField
              label="Email"
              value={user?.email || "dipson@gmail.com"}
              icon="/images-profile/Email.webp"
              isLoading={isUserLoading}
            />
            <ProfileField
              label="Member Since"
              value="April 2026"
              icon="/images-profile/Member%20Since.webp"
              isLoading={isUserLoading}
            />
          </div>

          {/* Info Box (Sesuai Gambar 3) */}
          <div className="mt-4 p-6 bg-[#F9FAFB] rounded-[16px] border border-[#F3F4F6]">
            <p className="text-[15px] text-[#717182] leading-relaxed">
              This is a demo profile. In the full version, you would be able to update your information and preferences here.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
