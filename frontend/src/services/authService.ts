import { UserProfile } from "@/types";
import { API_URL } from "@/utils/const";

/**
 * Helper to check if the code is currently running in a browser environment.
 * Next.js executes code on the server during the build process where Web APIs 
 * like sessionStorage and window do not exist.
 */
const isBrowser = typeof window !== "undefined";

export const authService = {
  /**
   * Mengambil data profil user yang sedang login dari Backend.
   */
  async getCurrentUser(): Promise<UserProfile> {
    // SSR Safe: Check for browser before accessing storage
    const token = isBrowser ? sessionStorage.getItem("app_token") : null;
    
    if (!token) {
      throw new Error("No token found");
    }

    try {
      const response = await fetch(`${API_URL}/users/me`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch user profile");
      }

      const data = await response.json();
      const userData: UserProfile = {
        name: data.name,
        email: data.email,
      };

      this.saveUserToSession(userData);
      return userData;
    } catch (error) {
      // Only attempt logout cleanup if in browser
      if (isBrowser) {
        this.logout();
      }
      throw error;
    }
  },

  /**
   * Menangani proses logout.
   */
  async logout(): Promise<void> {
    if (isBrowser) {
      sessionStorage.removeItem("app_token");
      sessionStorage.removeItem("app_user");
      sessionStorage.removeItem("chat_messages");
    }

    try {
      // Using a relative check or guarding the fetch if API_URL is dynamic
      await fetch(`${API_URL}/auth/logout`, { method: "POST" });
    } catch (e) {
      // Abaikan jika API gagal saat logout
    }
  },

  /**
   * Menangani proses login.
   */
  async login(email: string, password: string): Promise<void> {
    const response = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || "Login failed");
    }

    const data = await response.json();
    if (data.access_token) {
      if (isBrowser) {
        sessionStorage.setItem("app_token", data.access_token);
      }
      await this.getCurrentUser();
    } else {
      throw new Error("Token not found in response");
    }
  },

  /**
   * Menangani proses registrasi akun baru.
   */
  async register(name: string, email: string, password: string): Promise<void> {
    const response = await fetch(`${API_URL}/auth/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ name, email, password }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || "Registration failed");
    }

    const data = await response.json();
    if (data.access_token) {
      if (isBrowser) {
        sessionStorage.setItem("app_token", data.access_token);
        const userData: UserProfile = { name, email };
        this.saveUserToSession(userData);
      }
    } else {
      throw new Error("Token not found in response");
    }
  },

  /**
   * Menangani redirect OAuth (Google/etc).
   */
  async oauth(provider: string = "google"): Promise<void> {
    const response = await fetch(`${API_URL}/auth/${provider}`);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || "OAuth failed");
    }

    const data = await response.json();
    if (data.access_token) {
      if (isBrowser) {
        sessionStorage.setItem("app_token", data.access_token);
      }
      await this.getCurrentUser();
    } else {
      throw new Error("Token not found in response");
    }
  },

  /**
   * Menyimpan data user secara manual ke storage.
   */
  saveUserToSession(user: UserProfile): void {
    if (isBrowser) {
      sessionStorage.setItem("app_user", JSON.stringify(user));
      // Trigger a custom event for other components to react to login state
      window.dispatchEvent(new Event("user_updated"));
    }
  },
};