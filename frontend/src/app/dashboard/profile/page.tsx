"use client";

import { useEffect, useState } from "react";

export default function ProfilePage() {
  // Data profil user yang ditampilkan di halaman ini
  // Diambil dari sessionStorage (disimpan oleh layout.tsx setelah fetch)
  const [user, setUser] = useState<{ name: string; email: string } | null>(
    null,
  );
  // Menandai apakah data user masih dalam proses dimuat (menampilkan skeleton)
  const [isLoading, setIsLoading] = useState(true);

  // === INTEGRASI BE: AMBIL DATA PROFIL PENGGUNA ===
  // [PENJELASAN]: Baca data user dari sessionStorage (cache) atau fetch ulang dari API.
  // [METHOD]: GET | [ENDPOINT]: /api/users/me
  // [HEADERS]: Authorization: Bearer <token>
  // [RESPONSE]: { id, name, email, createdAt }
  // [CATATAN]: Field 'Member Since' diisi dari createdAt: new Date(user.createdAt).toLocaleDateString()
  // [EDIT PROFIL]: Jika ada fitur edit, gunakan:
  //   [METHOD]: PATCH | [ENDPOINT]: /api/users/me
  //   [BODY]: { name?: string, email?: string, password?: string }
  useEffect(() => {
    const loadUser = () => {
      try {
        const storedUser = sessionStorage.getItem("app_user");
        if (storedUser) {
          const parsedUser = JSON.parse(storedUser);
          if (parsedUser) {
            setUser(parsedUser);
            setIsLoading(false);
          }
        }
      } catch (error) {
        console.error("Failed to parse user data from session storage", error);
      }
    };

    // First load
    loadUser();

    // Listen for events from layout.tsx when the 2.5s delay is done
    window.addEventListener("user_updated", loadUser);

    return () => {
      window.removeEventListener("user_updated", loadUser);
    };
  }, []);

  return (
    <main className="flex-1 flex justify-center items-start h-full bg-[#FFFFFF] overflow-y-auto">
      <div className="w-full max-w-4xl px-12 py-12 flex flex-col">
        {/* Header Section */}
        <div className="mb-6">
          <h1 className="text-[24px] font-bold text-[#0A0A0A] mb-1">Profile</h1>
          <p className="text-[15px] text-[#717182]">
            Manage your account information
          </p>
        </div>

        {/* Profile Card Container */}
        <div className="border border-[#E5E7EB] rounded-[24px] p-8 bg-white flex flex-col gap-8 shadow-[0_2px_10px_rgb(0,0,0,0.02)]">
          {/* Avatar inisial user: Mengambil huruf pertama dari nama user */}
          <div className="flex items-center gap-5">
            <div className="w-[72px] h-[72px] rounded-full bg-[#030213] flex items-center justify-center shrink-0">
              <span className="text-white text-[28px] font-normal">
                {isLoading ? " " : user?.name?.charAt(0)?.toUpperCase() || "?"}
              </span>
            </div>
            <div className="flex flex-col gap-0.5">
              {isLoading ? (
                <>
                  <div className="w-32 h-6 bg-gray-200 rounded animate-pulse mb-1"></div>
                  <div className="w-48 h-4 bg-gray-100 rounded animate-pulse"></div>
                </>
              ) : (
                <>
                  <h2 className="text-[20px] font-bold text-[#0A0A0A] leading-tight">
                    {user?.name || "User"}
                  </h2>
                  <p className="text-[14px] text-[#717182]">
                    Schedule Helper User
                  </p>
                </>
              )}
            </div>
          </div>

          {/* Daftar field informasi profil: Name, Email, Member Since */}
          {/* === INTEGRASI BE: Field ini akan diisi dari response GET /api/users/me */}
          <div className="flex flex-col gap-4">
            {/* Name Field */}
            <div className="border border-[#E5E7EB] rounded-[12px] p-5 flex flex-col gap-1.5">
              <div className="flex items-center gap-2.5 text-[#717182]">
                <img
                  src="/images-profile/Profile.webp"
                  alt="Name"
                  className="w-[18px] h-[18px]"
                />
                <span className="text-[14px]">Name</span>
              </div>
              {isLoading ? (
                <div className="w-40 h-5 bg-gray-200 rounded animate-pulse ml-7"></div>
              ) : (
                <p className="text-[15px] font-medium text-[#0A0A0A] ml-7">
                  {user?.name || "Not provided"}
                </p>
              )}
            </div>

            {/* Email Field */}
            <div className="border border-[#E5E7EB] rounded-[12px] p-5 flex flex-col gap-1.5">
              <div className="flex items-center gap-2.5 text-[#717182]">
                <img
                  src="/images-profile/Email.webp"
                  alt="Email"
                  className="w-[18px] h-[18px]"
                />
                <span className="text-[14px]">Email</span>
              </div>
              {isLoading ? (
                <div className="w-56 h-5 bg-gray-200 rounded animate-pulse ml-7"></div>
              ) : (
                <p className="text-[15px] font-medium text-[#0A0A0A] ml-7">
                  {user?.email || "Not provided"}
                </p>
              )}
            </div>

            {/* Member Since Field */}
            <div className="border border-[#E5E7EB] rounded-[12px] p-5 flex flex-col gap-1.5">
              <div className="flex items-center gap-2.5 text-[#717182]">
                <img
                  src="/images-profile/Member%20Since.webp"
                  alt="Member Since"
                  className="w-[18px] h-[18px]"
                />
                <span className="text-[14px]">Member Since</span>
              </div>
              <p className="text-[15px] font-medium text-[#0A0A0A] ml-7">
                April 2026
              </p>
            </div>
          </div>

          {/* === INTEGRASI BE: CATATAN DEMO PROFILE === */}
          {/* [PENJELASAN]: Hapus section ini di versi produksi. */}
          {/* Ganti dengan form input edit untuk Name dan Email menggunakan PATCH /api/users/me */}
          <div className="bg-[#F9FAFB] rounded-[12px] p-5 text-[14px] text-[#717182] border border-[#E5E7EB] leading-relaxed">
            This is a demo profile. In the full version, you would be able to
            update your information and preferences here.
          </div>
        </div>
      </div>
    </main>
  );
}
