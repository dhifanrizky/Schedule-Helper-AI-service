import { useState, useEffect, useCallback } from "react";
import { UserProfile } from "@/types";
import { authService } from "@/services/authService";

/**
 * Hook untuk mengelola data profil pengguna yang sedang login.
 * Menangani fetching, loading state, dan sinkronisasi antar komponen.
 */
export function useUser() {
  // 1. Inisialisasi awal dengan null, bukan hardcode
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isUserLoading, setIsUserLoading] = useState(true);

  // Fungsi untuk memanggil API
  const loadUser = useCallback(async () => {
    setIsUserLoading(true);
    try {
      const userData = await authService.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error("Failed to load user:", error);
      setUser(null); // Bersihkan state jika token expired / gagal
    } finally {
      setIsUserLoading(false);
    }
  }, []);

  // Fungsi untuk update state tanpa panggil API (Mencegah Infinite Loop)
  const syncUserFromStorage = useCallback(() => {
    try {
      const storedUser = sessionStorage.getItem("app_user");
      if (storedUser) {
        setUser(JSON.parse(storedUser));
      } else {
        setUser(null);
      }
    } catch (e) {
      console.error("Error parsing user from session", e);
    }
  }, []);

  const logout = async () => {
    await authService.logout();
    setUser(null);
    window.location.href = "/";
  };

  useEffect(() => {
    // Muat data user dari API saat pertama kali mount
    loadUser();

    // Dengerkan event pembaruan user (misal dari tab lain / halaman callback)
    // PENTING: Gunakan syncUserFromStorage, JANGAN loadUser!
    window.addEventListener("user_updated", syncUserFromStorage);

    return () => {
      window.removeEventListener("user_updated", syncUserFromStorage);
    };
  }, [loadUser, syncUserFromStorage]);

  return {
    user,
    isUserLoading,
    userInitial: user?.name ? user.name.charAt(0).toUpperCase() : "",
    refreshUser: loadUser,
    logout,
  };
}