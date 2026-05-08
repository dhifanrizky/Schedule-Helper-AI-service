from functools import lru_cache
from typing import Any
import logging

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

    def _handle_response(
        self, response: httpx.Response, method: str, url: str
    ) -> Any:
        if response.status_code >= 400:
            detail = response.text
            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type:
                try:
                    payload = response.json()
                    if isinstance(payload, dict):
                        # NestJS class-validator biasanya mereturn array of error strings di field "message"
                        msg = payload.get("message")
                        if isinstance(msg, list):
                            detail = ", ".join(msg)
                        else:
                            detail = msg or payload.get("error") or detail
                except ValueError:
                    pass
            detail = detail.strip() if isinstance(detail, str) else str(detail)
            logging.getLogger(__name__).error(
                "[calendar_client] %s %s status=%s headers=%s body=%s",
                method,
                url,
                response.status_code,
                dict(response.headers),
                detail,
            )
            raise ValueError(
                f"Calendar API error {response.status_code} {method} {url}: {detail}"
            )
        if not response.content:
            return None
        try:
            return response.json()
        except ValueError:
            return response.text

    def _request_json(
        self,
        method: str,
        path: str,
        token: str | None = None,
        payload: dict | None = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        logging.getLogger(__name__).info(
            "[calendar_client] request %s %s payload=%s",
            method,
            url,
            payload,
        )
        try:
            response = self._client.request(
                method,
                url,
                headers=self._build_headers(token),
                json=payload,
            )
        except httpx.TimeoutException as exc:
            raise ValueError(
                f"Calendar API timeout (10s) {method} {url}"
            ) from exc
        except httpx.RequestError as exc:
            raise ValueError(
                f"Calendar API connection error {method} {url}: {exc}"
            ) from exc
        return self._handle_response(response, method, url)

    def list_schedules(self, token: str | None = None) -> list[dict]:
        data = self._request_json("GET", "/api/calendar", token=token)
        return data if isinstance(data, list) else []

    def get_schedule(self, schedule_id: str, token: str | None = None) -> dict:
        data = self._request_json(
            "GET",
            f"/api/calendar/{schedule_id}",
            token=token,
        )
        return data if isinstance(data, dict) else {}

    def create_schedule(self, dto: dict, token: str | None = None) -> dict:
        data = self._request_json(
            "POST",
            "/api/calendar",
            token=token,
            payload=dto,
        )
        return data if isinstance(data, dict) else {}

    def update_schedule(self, schedule_id: str, dto: dict, token: str | None = None) -> dict:
        data = self._request_json(
            "PATCH",
            f"/api/calendar/{schedule_id}",
            token=token,
            payload=dto,
        )
        return data if isinstance(data, dict) else {}

    def delete_schedule(self, schedule_id: str, token: str | None = None) -> dict:
        data = self._request_json(
            "DELETE",
            f"/api/calendar/{schedule_id}",
            token=token,
        )
        return data if isinstance(data, dict) else {}


# Backward-compatible alias for any existing imports.
CalendarService = BackendCalendarClient


@lru_cache
def get_calendar_client() -> BackendCalendarClient:
    return BackendCalendarClient(base_url=settings.backend_api_url)