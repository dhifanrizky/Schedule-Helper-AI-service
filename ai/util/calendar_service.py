import os
from datetime import datetime, timedelta, timezone
from typing import Any
from langchain_google_community.calendar.utils import (
    build_calendar_service,
    get_google_credentials,
)

class CalendarService:
    def __init__(self, token_file="token.json", client_secrets_file="credentials.json"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        token_path = os.path.join(base_dir, token_file)
        credentials_path = os.path.join(base_dir, client_secrets_file)

        credentials = get_google_credentials(
            token_file=token_path,
            scopes=["https://www.googleapis.com/auth/calendar.readonly"],
            client_secrets_file=credentials_path,
        )

        # Menggunakan Any untuk menghindari peringatan linter
        self.api_resource: Any = build_calendar_service(credentials=credentials)

    def fetch_calendar(self, days_back=3, days_ahead=7, max_results=20):
        """
        Mengambil jadwal secara dinamis.
        :param days_back: Jumlah hari ke belakang dari sekarang.
        :param days_ahead: Jumlah hari ke depan dari sekarang.
        :param max_results: Maksimal jumlah event yang diambil.
        """
        now = datetime.now(timezone.utc)
        
        # Tentukan rentang waktu secara dinamis
        time_min = (now - timedelta(days=days_back)).isoformat()
        time_max = (now + timedelta(days=days_ahead)).isoformat()

        try:
            events_result = self.api_resource.events().list(
                calendarId='primary',
                timeMin=time_min, # Mulai dari X hari lalu
                timeMax=time_max, # Sampai Y hari depan
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])

        except Exception as e:
            print("Error:", e)
            return "No calendar data available."

        if not events:
            return "No events found in this range."

        parsed_events = []
        for event in events:
            start_str = event.get("start", {}).get("dateTime", event.get("start", {}).get("date"))
            
            try:
                dt = datetime.fromisoformat(start_str)
                
                # --- TAMBAHAN KODE DI SINI ---
                # Cek apakah waktu (dt) tidak memiliki zona waktu (offset-naive)
                if dt.tzinfo is None:
                    # Jika tidak punya, paksa gunakan zona waktu UTC agar bisa dibandingkan
                    dt = dt.replace(tzinfo=timezone.utc)
                # -----------------------------
                
                # Tandai jika event sudah lewat
                status = "(Sudah Lewat)" if dt < now else ""
                
                if 'T' in start_str:
                    formatted_time = dt.strftime("%d %b %Y, %H:%M")
                else:
                    formatted_time = dt.strftime("%d %b %Y (Seharian)")
                
                parsed_events.append(f"- {event.get('summary')} {status} (at {formatted_time})")
            except ValueError:
                parsed_events.append(f"- {event.get('summary')} (at {start_str})")

        return f"Jadwal ({days_back} hari lalu s/d {days_ahead} hari depan):\n" + "\n".join(parsed_events)
    
# if __name__ == "__main__":
#     calendar_service = CalendarService()
    
#     result = calendar_service.fetch_calendar(days_back=3, days_ahead=10)
#     print(result)