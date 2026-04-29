from app.graph.agents import prioritizer


RAW_TASKS = [
    {
        "task_id": "task_001",
        "title": "Tugas Project Deadline Mepet",
        "description": (
            "Punya tugas project dengan deadline mepet minggu ini, "
            "tapi belum jelas apa saja yang harus dikerjakan dan bagaimana prioritasnya."
        ),
        "raw_time": "minggu ini",
        "raw_input": "Aku punya tugas project dan deadline mepet minggu ini, bantu atur prioritas ya",
        "category": "serius",
    }
]


class FakeStructuredLLM:
    """
    LLM palsu untuk test.
    Jadi test ini tidak memanggil Gemini/Groq asli dan tidak menghabiskan kuota.
    """

    def invoke(self, prompt):
        return {
            "tasks": [
                {
                    "task_id": "task_001",
                    "title": "Tugas Project Deadline Mepet",
                    "subtasks": [
                        "Identifikasi scope project yang harus diselesaikan",
                        "Tentukan bagian project yang paling dekat dengan deadline",
                        "Kerjakan bagian prioritas pertama",
                        "Review hasil dan siapkan catatan revisi",
                    ],
                    "estimated_minutes": 120,
                    "deadline": "2026-05-04T23:59:00",
                    "category": "serius",
                    "preferred_window": "bebas",
                    "urgency": 5,
                    "importance": 5,
                    "effort": 4,
                    "energy_fit": 4,
                }
            ]
        }


def test_priority_formula_high_priority():
    result = prioritizer.calculate_priority(
        urgency=5,
        importance=5,
        effort=4,
        energy_fit=4,
    )

    assert result == 1


def test_priority_formula_low_priority():
    result = prioritizer.calculate_priority(
        urgency=1,
        importance=1,
        effort=5,
        energy_fit=1,
    )

    assert result == 3


def test_llm_task_breakdown_with_fake_llm():
    fake_llm = FakeStructuredLLM()

    result = prioritizer.build_task_breakdown_with_llm(
        RAW_TASKS,
        fake_llm,
    )

    assert isinstance(result, list)
    assert len(result) == 1

    task = result[0]

    assert task["task_id"] == "task_001"
    assert task["title"] == "Tugas Project Deadline Mepet"
    assert task["priority"] == 1
    assert task["estimated_minutes"] == 120
    assert task["category"] == "serius"
    assert task["preferred_window"] == "bebas"
    assert len(task["subtasks"]) >= 1
    assert "Identifikasi scope project" in task["subtasks"][0]


def test_rule_based_fallback_output_structure():
    result = prioritizer.build_task_breakdown_rule_based(RAW_TASKS)

    assert isinstance(result, list)
    assert len(result) == 1

    task = result[0]

    assert task["task_id"] == "task_001"
    assert task["title"]
    assert isinstance(task["subtasks"], list)
    assert len(task["subtasks"]) >= 1
    assert task["estimated_minutes"] > 0
    assert task["priority"] in [1, 2, 3]
    assert task["category"] in ["serius", "santai", "biasa", "lainnya"]
    assert task["preferred_window"] in ["pagi", "siang", "sore", "malam", "bebas"]