import pytest
from typing import Any, cast
from unittest.mock import MagicMock
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.graph.state import AppState
from app.graph.agents.scheduler import make_scheduler, LLMCalendarResponse, LLMCalendarItem

# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def mock_calendar_client():
    """Mock untuk memalsukan request ke Backend/Google Calendar."""
    client = MagicMock()
    # Asumsikan jika create_schedule dipanggil, ia mereturn response dengan ID
    client.create_schedule.return_value = {"id": "mock-event-id-999"}
    return client

@pytest.fixture
def mock_llm():
    """Mock untuk memalsukan response dari LangChain/LLM."""
    llm = MagicMock()
    structured_llm = MagicMock()
    
    # Buat response palsu sesuai schema Pydantic yang diminta agent
    mock_response = LLMCalendarResponse(
        items=[
            LLMCalendarItem(
                title="Mock Task Terjadwal",
                description="Deskripsi dari mock LLM",
                category="work",
                estimatedMinutes=45,
                priority=1,
                status="pending"
            )
        ]
    )
    
    structured_llm.invoke.return_value = mock_response
    llm.with_structured_output.return_value = structured_llm
    
    return llm

@pytest.fixture
def valid_state() -> AppState:
    """Mock state aplikasi yang valid seperti output dari Prioritizer."""
    now = datetime.now(ZoneInfo("Asia/Jakarta"))
    state = {
        "current_intent": "manage_task",
        "raw_tasks": [],
        "messages": [],
        "proposed_schedule": [
            {
                "task_id": "test-task-01",
                "task": "Ngerjain Fitur Login",
                "priority": 1,
                "start_time": (now + timedelta(hours=1)).isoformat(),
                "duration_minutes": 45,
                "category": "development"
            }
        ],
        "metadata": {
            "timezone": "Asia/Jakarta",
            "auth_token": "Bearer valid-token-123"
        }
    }
    return cast(AppState, state)

# ==============================================================================
# TEST CASES
# ==============================================================================

def test_scheduler_success(mock_llm, mock_calendar_client, valid_state: AppState):
    """Skenario sukses: Jadwal valid diproses LLM dan dikirim ke kalender."""
    # Arrange
    scheduler_agent = make_scheduler(mock_llm, mock_calendar_client)
    
    # Act
    result = scheduler_agent(valid_state)
    
    # Assert
    assert result.get("api_status") == 200
    assert result.get("error_message") is None
    assert "mock-event-id-999" in result.get("metadata", {}).get("event_ids", [])
    
    # Verifikasi bahwa calendar_client benar-benar dipanggil
    mock_calendar_client.create_schedule.assert_called_once()
    
    # Verifikasi argument yang dipassing ke calendar_client
    args, kwargs = mock_calendar_client.create_schedule.call_args
    payload_dikirim = args[0]
    assert payload_dikirim["title"] == "Mock Task Terjadwal"
    assert kwargs.get("token") == "Bearer valid-token-123"


def test_scheduler_empty_schedule(mock_llm, mock_calendar_client):
    """Skenario gagal: proposed_schedule kosong."""
    # Arrange
    scheduler_agent = make_scheduler(mock_llm, mock_calendar_client)
    empty_state = cast(AppState, {
        "current_intent": "manage_task",
        "raw_tasks": [],
        "messages": [],
        "proposed_schedule": [],
        "metadata": {}
    })
    
    # Act
    result = scheduler_agent(empty_state)
    
    # Assert
    assert result.get("api_status") == 400
    assert "kosong" in result.get("error_message", "").lower()
    # Kalender API tidak boleh dipanggil jika jadwal kosong
    mock_calendar_client.create_schedule.assert_not_called()


def test_scheduler_validation_error(mock_llm, mock_calendar_client):
    """Skenario gagal: Data pada proposed_schedule tidak lengkap."""
    # Arrange
    scheduler_agent = make_scheduler(mock_llm, mock_calendar_client)
    invalid_state = cast(AppState, {
        "current_intent": "manage_task",
        "raw_tasks": [],
        "messages": [],
        "proposed_schedule": [
            {
                "task_id": "test-task-02",
                # "task": "Task name hilang!", -> Harus memicu error validasi
                "priority": 1,
                "start_time": datetime.now().isoformat(),
                "duration_minutes": 30,
                "category": "work"
            }
        ],
        "metadata": {}
    })
    
    # Act
    result = scheduler_agent(invalid_state)
    
    # Assert
    assert result.get("api_status") == 400
    assert "missing field" in result.get("error_message", "").lower()
    mock_calendar_client.create_schedule.assert_not_called()


def test_scheduler_calendar_api_error(mock_llm, mock_calendar_client, valid_state: AppState):
    """Skenario gagal: Terjadi error saat memanggil API Calendar backend."""
    # Arrange
    # Buat API melempar error saat dipanggil
    mock_calendar_client.create_schedule.side_effect = Exception("Internal Server Error Backend")
    scheduler_agent = make_scheduler(mock_llm, mock_calendar_client)
    
    # Act
    result = scheduler_agent(valid_state)
    
    # Assert
    assert result.get("api_status") == 500
    assert "Internal Server Error Backend" in result.get("error_message", "")
    assert "Gagal mengirim jadwal" in result.get("messages", [])[-1].content

def test_scheduler_multiple_items_success(mock_llm, mock_calendar_client):
    """Skenario sukses: Beberapa jadwal diproses LLM dan dikirim ke kalender berturut-turut."""
    # Arrange
    scheduler_agent = make_scheduler(mock_llm, mock_calendar_client)
    now = datetime.now(ZoneInfo("Asia/Jakarta"))
    
    # Siapkan mock state dengan 3 jadwal
    multiple_items_state = cast(AppState, {
        "current_intent": "manage_task",
        "raw_tasks": [],
        "messages": [],
        "proposed_schedule": [
            {
                "task_id": "test-task-01",
                "task": "Ngerjain Fitur Login",
                "priority": 1,
                "start_time": (now + timedelta(hours=1)).isoformat(),
                "duration_minutes": 45,
                "category": "development"
            },
            {
                "task_id": "test-task-02",
                "task": "Review Code",
                "priority": 2,
                "start_time": (now + timedelta(hours=2)).isoformat(),
                "duration_minutes": 30,
                "category": "work"
            },
            {
                "task_id": "test-task-03",
                "task": "Meeting Tim",
                "priority": 1,
                "start_time": (now + timedelta(hours=3)).isoformat(),
                "duration_minutes": 60,
                "category": "meeting"
            }
        ],
        "metadata": {
            "timezone": "Asia/Jakarta",
            "auth_token": "Bearer valid-token-123"
        }
    })

    # Sesuaikan mock LLM untuk mengembalikan 3 item agar cocok
    mock_response = LLMCalendarResponse(
        items=[
            LLMCalendarItem(title="Ngerjain Fitur Login", description="Deskripsi 1", category="development", estimatedMinutes=45, priority=1, status="pending"),
            LLMCalendarItem(title="Review Code", description="Deskripsi 2", category="work", estimatedMinutes=30, priority=2, status="pending"),
            LLMCalendarItem(title="Meeting Tim", description="Deskripsi 3", category="meeting", estimatedMinutes=60, priority=1, status="pending"),
        ]
    )
    mock_llm.with_structured_output().invoke.return_value = mock_response
    
    # Atur mock calendar client untuk mereturn ID berbeda pada tiap panggilan berurutan
    mock_calendar_client.create_schedule.side_effect = [
        {"id": "event-id-01"},
        {"id": "event-id-02"},
        {"id": "event-id-03"}
    ]
    
    # Act
    result = scheduler_agent(multiple_items_state)
    
    # Assert
    assert result.get("api_status") == 200
    assert result.get("error_message") is None
    
    # Memeriksa apakah event_ids mengumpulkan ketiga ID dengan benar
    event_ids = result.get("metadata", {}).get("event_ids", [])
    assert len(event_ids) == 3
    assert event_ids == ["event-id-01", "event-id-02", "event-id-03"]
    
    # Verifikasi bahwa calendar_client dipanggil tepat 3 kali
    assert mock_calendar_client.create_schedule.call_count == 3