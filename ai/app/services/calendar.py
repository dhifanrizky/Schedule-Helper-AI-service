import os
from datetime import datetime, timedelta, timezone
from typing import Any, List
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

        self.api_resource: Any = build_calendar_service(credentials=credentials)

    def _fetch_events(self, time_min: str, time_max: str, max_results=20):
        try:
            result = self.api_resource.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            return result.get('items', [])
        except Exception as e:
            print("Error:", e)
            return None

    def _parse_event(self, event, now=None):
        start_str = event.get("start", {}).get(
            "dateTime",
            event.get("start", {}).get("date")
        )

        try:
            dt = datetime.fromisoformat(start_str)

            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            status = ""
            if now:
                status = "(Sudah Lewat)" if dt < now else ""

            if 'T' in start_str:
                formatted_time = dt.strftime("%d %b %Y, %H:%M")
            else:
                formatted_time = dt.strftime("%d %b %Y (Seharian)")

            return f"- {event.get('summary')} {status} (at {formatted_time})"

        except ValueError:
            return f"- {event.get('summary')} (at {start_str})"

    def _format_events(self, events: List[Any], header: str, now=None):
        if events is None:
            return "No calendar data available."

        if not events:
            return header + "\n(No events found)"

        parsed = [self._parse_event(e, now) for e in events]
        return header + "\n" + "\n".join(parsed)


    def fetch_calendar_by_date(self, target_date: str, max_results=20):
        date_obj = datetime.strptime(target_date, "%Y-%m-%d")

        time_min = date_obj.replace(tzinfo=timezone.utc).isoformat()
        time_max = (date_obj + timedelta(days=1)).replace(tzinfo=timezone.utc).isoformat()

        events = self._fetch_events(time_min, time_max, max_results)

        return self._format_events(
            events, # type: ignore
            header=f"Jadwal pada {target_date}:"
        )

    def fetch_calendar_by_range(self, days_back=3, days_ahead=7, max_results=20):
        now = datetime.now(timezone.utc)

        time_min = (now - timedelta(days=days_back)).isoformat()
        time_max = (now + timedelta(days=days_ahead)).isoformat()

        events = self._fetch_events(time_min, time_max, max_results)

        return self._format_events(
            events, # type: ignore
            header=f"Jadwal ({days_back} hari lalu s/d {days_ahead} hari depan):",
            now=now
        )