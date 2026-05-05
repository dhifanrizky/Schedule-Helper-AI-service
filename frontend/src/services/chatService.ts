import { Message } from "@/types";

// =============================================================
// CHAT SERVICE: Mengelola pengiriman pesan dan riwayat chat
// =============================================================

export const chatService = {
  /**
   * Mengirim pesan user ke AI dan mendapatkan respons.
   * === INTEGRASI BE: Ganti dengan POST /api/chat/send ===
   */
  async sendMessage(
    message: string,
    history: Message[]
  ): Promise<Message> {
    // 1. Simulasi delay network
    await new Promise((resolve) => setTimeout(resolve, 1500));

    // 2. Logika simulasi respons AI berdasarkan jumlah pesan
    let reply = "Great! I can see several tasks here. Which of these is most urgent or has the closest deadline?";
    
    // Jika user sudah mengirim setidaknya 1 pesan sebelumnya (history.length >= 2 karena termasuk pesan user yang baru saja dikirim di level UI)
    if (history.length >= 2) {
      reply = "Perfect! Now let me understand your current state to create the best schedule for you.";
    }

    return {
      role: "system",
      content: reply,
    };
  },

  /**
   * Memuat riwayat pesan dari storage.
   */
  getStoredMessages(): Message[] {
    const saved = sessionStorage.getItem("chat_messages");
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        console.error("Failed to parse chat messages", e);
        return [];
      }
    }
    return [];
  },

  /**
   * Menyimpan riwayat pesan ke storage.
   */
  saveMessages(messages: Message[]): void {
    if (messages.length > 0) {
      sessionStorage.setItem("chat_messages", JSON.stringify(messages));
      // Dispatch event agar komponen lain tahu chat berubah
      window.dispatchEvent(new Event("chat_updated"));
    }
  },

  /**
   * Menghapus seluruh riwayat chat.
   */
  clearChat(): void {
    sessionStorage.removeItem("chat_messages");
    window.dispatchEvent(new Event("chat_updated"));
  }
};
