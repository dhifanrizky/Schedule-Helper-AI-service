from functools import lru_cache
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Any

from app.config import settings
from langchain_google_community.calendar.utils import (
    build_calendar_service,
    get_google_credentials,
)


class GoogleCalendarClient:
    """Thin wrapper around Google Calendar API calls used by the scheduler."""

    def __init__(self, credentials_path: str, token_path: str):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self._service: Any | None = None

    @staticmethod
    def _resolve_path(path_value: str) -> str:
        path = Path(path_value)
        if path.is_absolute():
            return str(path)
        return str((Path.cwd() / path).resolve())

    def _get_service(self):
        """Lazy-init Google Calendar API service with read/write scope."""
        if self._service is None:
            credentials = get_google_credentials(
                token_file=self._resolve_path(self.token_path),
                scopes=["https://www.googleapis.com/auth/calendar"],
                client_secrets_file=self._resolve_path(self.credentials_path),
            )
            self._service = build_calendar_service(credentials=credentials)
        return self._service

    def create_event(self, task: dict) -> str:
        """Create a Google Calendar event from a task dictionary and return event id."""
        summary = task.get("title") or task.get("summary") or "Untitled Task"
        description = task.get("description") or ""
        timezone_name = task.get("timezone") or "UTC"

        start_value = task.get("start") or task.get("start_time")
        end_value = task.get("end") or task.get("end_time")

        if isinstance(start_value, str):
            start_dt = datetime.fromisoformat(start_value)
        elif isinstance(start_value, datetime):
            start_dt = start_value
        else:
            # Fallback to nearest full hour when start is not provided.
            now = datetime.now(timezone.utc)
            start_dt = now.replace(minute=0, second=0, microsecond=0)

        if isinstance(end_value, str):
            end_dt = datetime.fromisoformat(end_value)
        elif isinstance(end_value, datetime):
            end_dt = end_value
        else:
            end_dt = start_dt + timedelta(hours=1)

        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=timezone.utc)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=timezone.utc)

        event_body = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start_dt.isoformat(), "timeZone": timezone_name},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": timezone_name},
        }

        event = (
            self._get_service()
            .events()
            .insert(calendarId="primary", body=event_body)
            .execute()
        )
        return event["id"]

    def list_events(self, time_min: str, time_max: str, max_results: int = 20) -> list[dict]:
        """List calendar events in a given datetime range."""
        result = (
            self._get_service()
            .events()
            .list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return result.get("items", [])

    def _parse_event(self, event: dict[str, Any], now: datetime | None = None) -> str:
        start_str = event.get("start", {}).get("dateTime", event.get("start", {}).get("date"))
        if not start_str:
            return f"- {event.get('summary', 'Untitled')} (at unknown time)"

        try:
            dt = datetime.fromisoformat(start_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            status = ""
            if now is not None:
                status = "(Sudah Lewat)" if dt < now else ""

            if "T" in start_str:
                formatted_time = dt.strftime("%d %b %Y, %H:%M")
            else:
                formatted_time = dt.strftime("%d %b %Y (Seharian)")

            return f"- {event.get('summary', 'Untitled')} {status} (at {formatted_time})"
        except ValueError:
            return f"- {event.get('summary', 'Untitled')} (at {start_str})"

    def _format_events(self, events: list[dict[str, Any]], header: str, now: datetime | None = None) -> str:
        if not events:
            return header + "\n(No events found)"

        parsed = [self._parse_event(e, now) for e in events]
        return header + "\n" + "\n".join(parsed)

    def fetch_calendar_by_date(self, target_date: str, max_results: int = 20) -> str:
        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        time_min = date_obj.replace(tzinfo=timezone.utc).isoformat()
        time_max = (date_obj + timedelta(days=1)).replace(tzinfo=timezone.utc).isoformat()
        events = self.list_events(time_min=time_min, time_max=time_max, max_results=max_results)
        return self._format_events(events, header=f"Jadwal pada {target_date}:")

    def fetch_calendar_by_range(self, days_back: int = 3, days_ahead: int = 7, max_results: int = 20) -> str:
        now = datetime.now(timezone.utc)
        time_min = (now - timedelta(days=days_back)).isoformat()
        time_max = (now + timedelta(days=days_ahead)).isoformat()
        events = self.list_events(time_min=time_min, time_max=time_max, max_results=max_results)
        return self._format_events(
            events,
            header=f"Jadwal ({days_back} hari lalu s/d {days_ahead} hari depan):",
            now=now,
        )


# Backward-compatible alias for any existing imports.
CalendarService = GoogleCalendarClient


@lru_cache
def get_calendar_client() -> GoogleCalendarClient:
    return GoogleCalendarClient(
        credentials_path=settings.google_calendar_credentials_path,
        token_path=settings.google_calendar_token_path,
    )