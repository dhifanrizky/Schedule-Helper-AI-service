from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import cast
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import json
import logging

from app.graph.state import GraphState
from app.graph.agents.helpers import get_proposed_schedule, get_metadata, ai_msg
from app.graph.types import CategoryType, ScheduleItem


# ---------------------------------------------------------------------------
# Agent 4: SchedulerAgent
#
# Tugas:
# 1. Menerima proposed_schedule final dari Agent 3.
# 2. Memastikan jadwal sudah di-approve user (cek hitl_status atau hitl_input).
# 3. Validasi format proposed_schedule.
# 4. Mapping proposed_schedule ke format CreateCalendarDto untuk BE.
# 5. Memanggil calendar_client.create_schedule() agar BE upload ke Google Calendar.
# ---------------------------------------------------------------------------


DEFAULT_TIMEZONE = "Asia/Jakarta"
logger = logging.getLogger(__name__)


def make_scheduler(llm=None, calendar_client=None):
    """
    Factory untuk Agent 4 / Scheduler.
    """

    def run(state: GraphState) -> dict:
        metadata = get_metadata(state) or {}
        schedule_items = get_proposed_schedule(state)
        
        # Ambil status HITL dari state
        hitl_status = state.get("hitl_status")
        # hitl_input biasanya berisi payload dari HITLResumeRequest.approved_data
        hitl_input = state.get("hitl_input") or {}

        # Logika Approval: 
        # Dianggap approved jika hitl_status == "approved"
        # ATAU jika di hitl_input ada field {"approved": true} (hasil resume)
        is_approved = (hitl_status == "approved") or (hitl_input.get("approved") is True)

        if not is_approved:
            return {
                **ai_msg("Jadwal belum di-approve user, jadi belum bisa dikirim ke Calendar."),
                "error_message": "Jadwal belum di-approve user.",
                "api_status": 400,
                "api_payload": {
                    "error": "Jadwal belum di-approve user.",
                    "hitl_status": hitl_status
                },
                "final_message": None,
            }

        if not schedule_items:
            return {
                **ai_msg("Belum ada proposed_schedule yang bisa dijadwalkan."),
                "error_message": "proposed_schedule kosong.",
                "api_status": 400,
                "api_payload": {
                    "error": "proposed_schedule kosong.",
                },
                "final_message": None,
            }

        if calendar_client is None:
            return {
                **ai_msg("Calendar client belum tersedia."),
                "error_message": "calendar_client tidak tersedia.",
                "api_status": 500,
                "api_payload": {
                    "error": "calendar_client tidak tersedia.",
                },
                "final_message": None,
            }

        try:
            # Langkah 1: Coba validasi awal secara normal
            normalized_items = _validate_schedule_items(schedule_items)
        except ValueError as validation_err:
            # Jika gagal, dan LLM tersedia, minta LLM untuk mengoreksi struktur datanya
            if llm is not None:
                try:
                    fixed_items = _fix_format_with_llm(llm, schedule_items, str(validation_err))
                    normalized_items = _validate_schedule_items(fixed_items)
                except Exception as llm_err:
                    return {
                        **ai_msg("Format jadwal sangat tidak beraturan dan sistem AI gagal memformat ulang secara otomatis."),
                        "error_message": f"Init Error: {validation_err} | LLM Auto-Fix Error: {llm_err}",
                        "api_status": 400,
                        "api_payload": {"error": f"LLM fix failed: {llm_err}"},
                        "final_message": None,
                    }
            else:
                return {
                    **ai_msg("Format jadwal belum valid. Mohon perbaiki dulu."),
                    "error_message": str(validation_err),
                    "api_status": 400,
                    "api_payload": {"error": str(validation_err)},
                    "final_message": None,
                }

        try:
            # Langkah 2: Proses pembuatan payload & kirim ke Calendar Backend
            calendar_payloads = _build_calendar_payloads(
                schedule_items=normalized_items,
                metadata=metadata,
            )
            logger.info("[scheduler] calendar_payloads=%s", json.dumps(calendar_payloads))
            auth_token = _extract_auth_token(metadata) or _extract_auth_token(hitl_input)
            logger.info(
                "[scheduler] auth_token_present=%s base_url=%s",
                bool(auth_token),
                getattr(calendar_client, "base_url", None),
            )

            # Jika backend butuh token JWT tapi metadata kosong,
            # pastikan Frontend sudah mem-passing JWT token user ke input LangGraph (metadata)
            created_events = _send_to_backend_calendar(
                calendar_client=calendar_client,
                calendar_payloads=calendar_payloads,
                auth_token=auth_token,
            )

        except ValueError as err:
            # Menangkap kegagalan konversi tanggal (ISO format) di build_calendar_payloads
            logger.exception("[scheduler] build payload error: %s", err)
            return {
                **ai_msg("Terdapat kesalahan fatal pada format tanggal saat mempersiapkan data jadwal."),
                "error_message": str(err),
                "api_status": 400,
                "api_payload": {"error": str(err)},
                "final_message": None,
            }

        except Exception as err:
            # Jika gagal (seperti backend down/network error), kita set hitl_status ke "pending"
            # agar node ini berhenti di tengah jalan dan butuh "Resume" (Retry)
            logger.exception("[scheduler] backend send error: %s", err)
            return {
                **ai_msg(
                    f"Gagal mengirim ke Google Calendar. Error: {str(err)}. Sistem siap mencoba ulang, silakan klik 'Coba Lagi'."
                ),
                "error_message": str(err),
                "api_status": 500,
                "api_payload": {
                    "error": str(err),
                    "retryable": True,
                },
                "hitl_status": "pending", # Set ke pending agar user bisa resume lagi
                "final_message": None,
            }

        event_ids = [event["event_id"] for event in created_events]

        return {
            **ai_msg(f"Berhasil menjadwalkan {len(created_events)} kegiatan ke Google Calendar."),
            "metadata": {
                **metadata,
                "scheduled": True,
                "event_ids": event_ids,
            },
            "api_status": 200,
            "api_payload": {
                "scheduled_count": len(created_events),
                "event_ids": event_ids,
                "calendar_items": calendar_payloads,
                "created_events": created_events,
            },
            "hitl_status": None,  # Reset status HITL karena sukses
            "hitl_input": None,   # Bersihkan input HITL sebelumnya
            "error_message": None,
            "final_message": f"Berhasil menjadwalkan {len(created_events)} kegiatan ke Google Calendar.",
    }

    return run


def _fix_format_with_llm(llm, raw_items: list, error_msg: str) -> list:
    """
    Menggunakan LLM untuk memperbaiki format schedule yang tidak valid menjadi JSON list murni.
    """
    prompt = f"""
    Anda adalah sistem data-formatting. Data array jadwal di bawah ini gagal divalidasi oleh sistem.
    Alasan error: {error_msg}
    
    Data saat ini:
    {json.dumps(raw_items, indent=2)}
    
    Tugas Anda: Perbaiki data tersebut dan kembalikan HANYA array JSON (list of objects).
    Setiap object HARUS memiliki key berikut:
    - "task_id": string (buatkan ID unik acak jika sebelumnya kosong/hilang)
    - "task": string (nama atau deskripsi tugas)
    - "priority": integer (harus berupa angka 1 sampai 5)
    - "start_time": string (harus format ISO 8601, contoh: "2026-05-06T09:00:00Z")
    - "duration_minutes": integer (harus berupa angka/integer)
    - "category": string (wajib salah satu dari: "serius", "santai", "biasa", "lainnya")
    
    Jangan berikan penjelasan apa pun, output harus berupa text JSON Murni tanpa markdown formatting (tanpa ```json ... ```).
    """
    
    response = llm.invoke(prompt)
    content = response.content.strip()
    
    # Antisipasi jika LLM masih bandel mengembalikan markdown backticks
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    
    if content.endswith("```"):
        content = content[:-3]
        
    return json.loads(content.strip())


def _validate_schedule_items(schedule_items: list[ScheduleItem]) -> list[ScheduleItem]:
    """
    Validasi proposed_schedule sesuai tipe data ScheduleItem.
    """
    if not isinstance(schedule_items, list) or not schedule_items:
        raise ValueError("proposed_schedule kosong.")

    required_keys = {"task_id", "task", "priority", "start_time", "duration_minutes", "category"}
    normalized_items: list[ScheduleItem] = []

    for idx, item in enumerate(schedule_items, start=1):
        missing = required_keys - set(item.keys())
        if missing:
            raise ValueError(f"Item {idx} missing field: {', '.join(sorted(missing))}")

        # Normalisasi category sesuai Literal CategoryType
        raw_cat = str(item.get("category") or "biasa").strip().lower()
        if raw_cat not in ["serius", "santai", "biasa", "lainnya"]:
            raw_cat = "biasa"
        category = cast(CategoryType, raw_cat)

        try:
            duration = int(item["duration_minutes"])
            priority = int(item["priority"])
        except (TypeError, ValueError):
            raise ValueError(f"Item {idx}: priority/duration harus angka.")

        _parse_iso_datetime(str(item["start_time"]))

        normalized_items.append({
            "task_id": str(item["task_id"]),
            "task": str(item["task"]),
            "priority": priority,
            "start_time": str(item["start_time"]),
            "duration_minutes": duration,
            "category": category,
        })

    return normalized_items


def _build_calendar_payloads(schedule_items: list[ScheduleItem], metadata: dict) -> list[dict]:
    timezone_name = metadata.get("timezone") or DEFAULT_TIMEZONE
    payloads = []
    for item in schedule_items:
        start_dt = _parse_iso_datetime(item["start_time"], timezone_name)
        
        # FIX: Hapus microsecond. class-validator NestJS akan menolak format 
        # dengan microseconds Python (6 digit) karena dianggap tidak standar ISO JS.
        start_dt = start_dt.replace(microsecond=0)
        end_dt = start_dt + timedelta(minutes=item["duration_minutes"])
        
        # FIX: Berikan fallback string pada 'task' agar tidak gagal validasi @IsNotEmpty()
        title = item["task"].strip() if item["task"].strip() else "Untitled Task"
        
        payloads.append({
            "title": title,
            "description": f"ID: {item['task_id']} | Priority: {item['priority']}",
            "category": item["category"],
            "estimatedMinutes": item["duration_minutes"],
            "priority": item["priority"],
            "deadline": end_dt.isoformat(),
            "startTime": start_dt.isoformat(),
            "status": "pending",
        })
    return payloads


def _send_to_backend_calendar(calendar_client, calendar_payloads: list[dict], auth_token: str | None) -> list[dict]:
    events = []
    for p in calendar_payloads:
        resp = calendar_client.create_schedule(p, token=auth_token)
        events.append({
            "event_id": _extract_event_id(resp),
            **p,
            "raw_response": resp
        })
    return events


def _extract_event_id(response) -> str:
    if isinstance(response, dict):
        for key in ("id", "event_id"):
            if response.get(key): return str(response[key])
        data = response.get("data")
        if isinstance(data, dict):
            for key in ("id", "event_id"):
                if data.get(key): return str(data[key])
    return ""


def _parse_iso_datetime(value: str, timezone_name: str = DEFAULT_TIMEZONE) -> datetime:
    normalized = value.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        raise ValueError(f"ISO format invalid: {value}")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_get_tzinfo(timezone_name))
    return dt


def _get_tzinfo(timezone_name: str):
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return timezone(timedelta(hours=7)) if timezone_name == DEFAULT_TIMEZONE else timezone.utc


def _extract_auth_token(metadata: dict) -> str | None:
    for key in ("auth_token", "access_token", "authorization"):
        val = metadata.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return None