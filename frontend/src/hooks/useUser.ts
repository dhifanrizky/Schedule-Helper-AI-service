import { useState, useEffect } from "react";
import { UserProfile } from "@/types";
import { authService } from "@/services/authService";

/**
 * Hook untuk mengelola data profil pengguna yang sedang login.
 * Menangani fetching, loading state, dan sinkronisasi antar komponen.
 */
export function useUser() {
  const [user, setUser] = useState<UserProfile | null>({
    name: "raka",
    email: "rakafadillah@gmail.com",
  });
  const [isUserLoading, setIsUserLoading] = useState(true);

  const loadUser = async () => {
    setIsUserLoading(true);
    try {
      const userData = await authService.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error("Failed to load user:", error);
    } finally {
      setIsUserLoading(false);
    }
  };

  const logout = async () => {
    await authService.logout();
    setUser(null);
    window.location.href = "/";
  };

  useEffect(() => {
    // Muat data user saat awal mount
    loadUser();

    // Dengerkan event pembaruan user (misal setelah login/refresh delay)
    window.addEventListener("user_updated", loadUser);

    return () => {
      window.removeEventListener("user_updated", loadUser);
    };
  }, []);

  return {
    user,
    isUserLoading,
    userInitial: user?.name ? user.name.charAt(0).toUpperCase() : "",
    refreshUser: loadUser,
    logout,
  };
}
