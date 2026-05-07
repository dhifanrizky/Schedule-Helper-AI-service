import os
import json
import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

# Sesuaikan import dengan struktur folder project Anda
from app.services.llm import get_llm
from app.services.calendar import get_calendar_client
from app.graph.agents.scheduler import make_scheduler
from app.graph.state import AppState
# Load environment variables (Pastikan BASE_URL dan API key LLM ada di .env Anda)
load_dotenv()


# ==============================================================================
# KONFIGURASI TEST
# ==============================================================================
# WAJIB GANTI: Masukkan Token asli Anda yang valid di backend NestJS.
# Anda bisa menaruhnya di file .env dengan nama TEST_AUTH_TOKEN
TEST_AUTH_TOKEN = os.getenv("TEST_AUTH_TOKEN", "Bearer YOUR_REAL_TOKEN_HERE")
TIMEZONE = "Asia/Jakarta"


def test_live_calendar():
    """
    Test end-to-end untuk nge-hit API Calendar backend secara langsung.
    Jalankan dengan perintah: pytest test_live_calendar.py -s
    (Gunakan flag -s agar hasil print() tetap muncul di terminal)
    """
    print("\n🚀 Memulai Live Test Scheduler Agent (Nge-Hit API Beneran)...")

    # 1. Siapkan Waktu Dinamis (Agar tidak menjadwalkan di masa lalu)
    now = datetime.now(ZoneInfo(TIMEZONE))
    waktu_task_1 = now + timedelta(minutes=15)  # 15 menit dari sekarang

    # 2. Buat Mock AppState (Data Mentah dari Agent Sebelumnya)
    mock_state: AppState = {
        "current_intent": "manage_task",
        "raw_tasks": [],
        "messages": [], 
        "proposed_schedule": [
            {
                "task_id": "test-live-001",
                "task": "Review Dokumen API (Live Test)",
                "priority": 1,
                "start_time": waktu_task_1.isoformat(),
                "duration_minutes": 45,
                "category": "serius"
            }
        ],
        "metadata": {
            "timezone": TIMEZONE,
            "auth_token": TEST_AUTH_TOKEN
        }
    }

    # 3. Inisialisasi Dependencies
    print("⏳ Menginisialisasi LLM dan Calendar Client...")
    try:
        llm = get_llm(provider="groq", model="openai/gpt-oss-120b", temperature=0.0)
        calendar_client = get_calendar_client() 
        scheduler_agent = make_scheduler(llm, calendar_client)
    except Exception as e:
        pytest.fail(f"❌ Gagal inisialisasi dependencies: {e}")

    # 4. Eksekusi Agent
    print(f"📡 Mengirim data ke URL Backend: {calendar_client.base_url}")
    print(f"🗓️ Mencoba menjadwalkan event pada: {waktu_task_1.strftime('%Y-%m-%d %H:%M')}")
    
    result = scheduler_agent(mock_state)
    
    # 5. Evaluasi Hasil
    print("\n================ HASIL EKSEKUSI ================")
    print(f"Status API   : {result.get('api_status')}")
    
    messages = result.get('messages', [])
    if messages:
        print(f"Pesan AI     : {messages[-1].content}")
    
    print(f"Error        : {result.get('error_message')}")
    
    # Menggunakan assert ala pytest
    if result.get("api_status") == 200:
        print("\n✅ BERHASIL MENGIRIM KE BACKEND!")
        print("Response Metadata (Event IDs):")
        print(json.dumps(result.get("metadata", {}).get("event_ids"), indent=2))
        print("\n👉 Silakan buka aplikasi Google Calendar Anda sekarang.")
    else:
        print("\n❌ GAGAL MENGIRIM KE BACKEND!")
        print("Kemungkinan penyebab:")
        print("1. Token otentikasi (TEST_AUTH_TOKEN) salah/kadaluarsa.")
        print("2. Backend NestJS belum berjalan / URL salah di .env.")
        print("3. LLM gagal merespons dengan format JSON yang benar.")
        
        # Buat test gagal jika status bukan 200
        pytest.fail(f"Gagal memanggil API. Status: {result.get('api_status')}, Error: {result.get('error_message')}")

    assert result.get("api_status") == 200