from functools import lru_cache
from typing import Any

import httpx

from app.config import settings


class BackendCalendarClient:
    """HTTP client untuk Calendar API backend (NestJS)."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(timeout=10.0)

    def _build_headers(self, token: str | None) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        auth_token = token or settings.backend_api_token
        if auth_token:
            if auth_token.lower().startswith("bearer "):
                headers["Authorization"] = auth_token
            else:
                headers["Authorization"] = f"Bearer {auth_token}"
        return headers

    def _handle_response(self, response: httpx.Response) -> Any:
        if response.status_code >= 400:
            raise ValueError(
                f"Calendar API error {response.status_code}: {response.text}"
            )
        if not response.content:
            return None
        return response.json()

    def list_schedules(self, token: str | None = None) -> list[dict]:
        response = self._client.get(
            f"{self.base_url}/calendar",
            headers=self._build_headers(token),
        )
        data = self._handle_response(response)
        return data if isinstance(data, list) else []

    def get_schedule(self, schedule_id: str, token: str | None = None) -> dict:
        response = self._client.get(
            f"{self.base_url}/calendar/{schedule_id}",
            headers=self._build_headers(token),
        )
        data = self._handle_response(response)
        return data if isinstance(data, dict) else {}

    def create_schedule(self, dto: dict, token: str | None = None) -> dict:
        response = self._client.post(
            f"{self.base_url}/calendar",
            headers=self._build_headers(token),
            json=dto,
        )
        data = self._handle_response(response)
        return data if isinstance(data, dict) else {}

    def update_schedule(self, schedule_id: str, dto: dict, token: str | None = None) -> dict:
        response = self._client.patch(
            f"{self.base_url}/calendar/{schedule_id}",
            headers=self._build_headers(token),
            json=dto,
        )
        data = self._handle_response(response)
        return data if isinstance(data, dict) else {}

    def delete_schedule(self, schedule_id: str, token: str | None = None) -> dict:
        response = self._client.delete(
            f"{self.base_url}/calendar/{schedule_id}",
            headers=self._build_headers(token),
        )
        data = self._handle_response(response)
        return data if isinstance(data, dict) else {}


# Backward-compatible alias for any existing imports.
CalendarService = BackendCalendarClient


@lru_cache
def get_calendar_client() -> BackendCalendarClient:
    return BackendCalendarClient(base_url=settings.backend_api_url)