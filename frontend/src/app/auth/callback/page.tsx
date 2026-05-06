"use client";

import { useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { authService } from "@/services/authService";

function CallbackHandler() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    // 1. Ambil token dari URL: ?token=xyz...
    const token = searchParams.get("token");

    const processLogin = async () => {
      if (token) {
        try {
          // 2. Simpan token ke session storage
          sessionStorage.setItem("app_token", token);
          
          // 3. Panggil method getCurrentUser dari service untuk memuat dan menyimpan data profil user
          await authService.getCurrentUser();
          
          // 4. Jika sukses, arahkan ke dashboard
          router.push("/dashboard");
        } catch (error) {
          console.error("Gagal memproses data user dari Google:", error);
          router.push("/auth/login?error=FailedToFetchProfile");
        }
      } else {
        // Jika tidak ada token di URL, kembalikan ke halaman login
        router.push("/auth/login?error=NoTokenProvided");
      }
    };

    processLogin();
  }, [router, searchParams]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-[#fafafa]">
      <div className="w-10 h-10 border-4 border-[#8A38F5] border-t-transparent rounded-full animate-spin mb-4"></div>
      <p className="text-[#717182] font-medium animate-pulse">Connecting to your account...</p>
    </div>
  );
}

/**
 * OAUTH CALLBACK PAGE
 * Halaman ini bertugas menangkap redirect dari backend setelah login Google berhasil.
 * Wajib menggunakan Suspense karena menggunakan useSearchParams().
 */
export default function OAuthCallbackPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-screen bg-[#fafafa]">
        <p className="text-[#717182]">Loading...</p>
      </div>
    }>
      <CallbackHandler />
    </Suspense>
  );
}