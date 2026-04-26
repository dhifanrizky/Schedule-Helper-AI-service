import { UserProfile } from "@/types";
import { mockUserProfile } from "@/data/mockData";

// =============================================================
// AUTH SERVICE: Mengelola komunikasi API terkait Otentikasi
// =============================================================

export const authService = {
  /**
   * Mengambil data profil user yang sedang login.
   * Saat ini masih mensimulasikan delay network dan mengambil dari sessionStorage/mock.
   * === INTEGRASI BE: Ganti dengan fetch('/api/users/me') ===
   */
  async getCurrentUser(): Promise<UserProfile> {
    // 1. Cek Cache di SessionStorage
    const storedUser = sessionStorage.getItem("app_user");
    if (storedUser) {
      return JSON.parse(storedUser);
    }

    // 2. Simulasi Delay Network (2.5 detik)
    await new Promise((resolve) => setTimeout(resolve, 2500));

    // 3. Kembalikan Mock Data (Ganti dengan real API call nanti)
    const userData = mockUserProfile;

    // Simpan ke cache
    sessionStorage.setItem("app_user", JSON.stringify(userData));
    return userData;
  },

  /**
   * Menangani proses logout.
   * Membersihkan data sesi dan token.
   * === INTEGRASI BE: Tambahkan panggilan POST /api/auth/logout ===
   */
  async logout(): Promise<void> {
    // 1. Simulasi Delay
    await new Promise((resolve) => setTimeout(resolve, 500));

    // 2. Bersihkan SessionStorage
    sessionStorage.removeItem("app_user");
    sessionStorage.removeItem("chat_messages");

    // 3. Redirect ke Landing Page dilakukan di level komponen/hook
  },

  /**
   * Menangani proses login.
   * === INTEGRASI BE: POST /api/auth/login ===
   */
  async login(email: string, password: string): Promise<void> {
    // 1. Simulasi Delay
    await new Promise((resolve) => setTimeout(resolve, 1500));

    // 2. Simulasi Login Berhasil (Selalu berhasil untuk demo)
    const userData: UserProfile = {
      name: "Dhifan Rizky", // Contoh nama dari DB
      email: email
    };

    this.saveUserToSession(userData);
  },

  /**
   * Menangani proses registrasi akun baru.
   * === INTEGRASI BE: POST /api/auth/register ===
   */
  async register(name: string, email: string, password: string): Promise<void> {
    // 1. Simulasi Delay
    await new Promise((resolve) => setTimeout(resolve, 1500));

    // 2. Simulasi Registrasi Berhasil
    const userData: UserProfile = {
      name: name,
      email: email
    };

    this.saveUserToSession(userData);
  },

  /**
   * Menyimpan data user secara manual ke storage (misal setelah login/register).
   */
  saveUserToSession(user: UserProfile): void {
    sessionStorage.setItem("app_user", JSON.stringify(user));
    window.dispatchEvent(new Event("user_updated"));
  }
};
