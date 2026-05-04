
"""
Test suite untuk CounselorAgent versi info-gathering.

Perubahan besar dari versi sebelumnya:
- DummyLLM sekarang harus implement with_structured_output DUA kali
  (untuk CounselorOutput dan EnrichedTasksOutput)
- Ada test baru untuk gap_analysis, enrichment, dan raw_tasks update
"""

import app.graph.agents.counselor as counselor_module
from app.graph.agents.counselor import (
    CounselorOutput,
    EnrichedTasksOutput,
    EnrichedTaskItem,
    TaskGapAnalysis,
    TaskGapItem,
)


# ---------------------------------------------------------------------------
# Helpers untuk buat gap_analysis dummy
# ---------------------------------------------------------------------------

def make_gap_analysis(overall_complete: bool, task_ids: list[str] = None) -> TaskGapAnalysis:
    task_ids = task_ids or ["task_001"]
    gaps = [
        TaskGapItem(
            task_id=tid,
            title=f"Task {tid}",
            is_complete=overall_complete,
            missing_info=[] if overall_complete else ["detail belum jelas"],
        )
        for tid in task_ids
    ]
    return TaskGapAnalysis(gaps=gaps, overall_complete=overall_complete)


def make_counselor_output(
    draft: str = "Draft dummy.",
    bridge: str = "Bridge dummy.",
    overall_complete: bool = True,
    task_ids: list[str] = None,
) -> CounselorOutput:
    return CounselorOutput(
        draft=draft,
        bridge=bridge,
        gap_analysis=make_gap_analysis(overall_complete, task_ids or ["task_001"]),
    )


def make_enriched_output(task_id: str = "task_001", title: str = "Updated Title") -> EnrichedTasksOutput:
    return EnrichedTasksOutput(
        enriched_tasks=[
            EnrichedTaskItem(
                task_id=task_id,
                title=title,
                description="Deskripsi yang sudah diupdate.",
                raw_time=None,
                category="biasa",
            )
        ]
    )


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------

class DummyLLM:
    """
    LLM stub yang support dua schema:
    - CounselorOutput (untuk _generate_response)
    - EnrichedTasksOutput (untuk _enrich_tasks)
    """
    def __init__(
        self,
        counselor_output: CounselorOutput = None,
        enriched_output: EnrichedTasksOutput = None,
    ):
        self._counselor_output = counselor_output or make_counselor_output()
        self._enriched_output = enriched_output or EnrichedTasksOutput(enriched_tasks=[])

    def with_structured_output(self, schema):
        if schema is CounselorOutput:
            out = self._counselor_output
            class _CounselorStructured:
                def invoke(self, _prompt):
                    return out
            return _CounselorStructured()

        if schema is EnrichedTasksOutput:
            out = self._enriched_output
            class _EnrichStructured:
                def invoke(self, _prompt):
                    return out
            return _EnrichStructured()

        raise ValueError(f"Unknown schema: {schema}")


class DummyLLMError:
    """LLM yang selalu error untuk test fallback."""
    def with_structured_output(self, schema):
        class _Structured:
            def invoke(self, _prompt):
                raise Exception("API timeout")
        return _Structured()


class CapturingLLM:
    """LLM yang merekam prompt untuk test inspeksi prompt."""
    def __init__(self, counselor_output: CounselorOutput = None):
        self._counselor_output = counselor_output or make_counselor_output()
        self.received_prompts: list = []

    def with_structured_output(self, schema):
        store = self
        out = self._counselor_output

        class _Structured:
            def invoke(self, prompt):
                store.received_prompts.append(prompt)
                return out
        return _Structured()


def make_dummy_interrupt(return_value: dict):
    def _interrupt(_payload):
        return return_value
    return _interrupt


def make_capturing_interrupt(return_value: dict):
    captured = {}
    def _interrupt(payload):
        captured.update(payload)
        return return_value
    _interrupt.captured = captured
    return _interrupt


def make_raw_task(
    task_id: str = "task_001",
    title: str = "Tugas RPL",
    description: str = "Tugas RPL, detail belum jelas.",
    raw_time: str = None,
    raw_input: str = "tugas rpl",
    category: str = "serius",
) -> dict:
    return {
        "task_id": task_id,
        "title": title,
        "description": description,
        "raw_time": raw_time,
        "raw_input": raw_input,
        "category": category,
    }


def make_state(
    user_message: str = "aku stres banget",
    raw_tasks: list = None,
    hitl_input: dict = None,
    counselor_response: list = None,
) -> dict:
    return {
        "user_input": user_message,
        "messages": [],
        "current_intent": "stress",
        "raw_tasks": raw_tasks or [],
        "counselor_response": counselor_response or [],
        "counselor_done": False,
        "task_breakdown": [],
        "proposed_schedule": [],
        "api_status": None,
        "api_payload": None,
        "final_message": None,
        "error_message": None,
        "metadata": {"user_id": "test_user"},
        "hitl_status": None,
        "hitl_input": hitl_input,
    }


# ---------------------------------------------------------------------------
# Tests: _generate_response
# ---------------------------------------------------------------------------

def test_generate_response_returns_counselor_output():
    """Return value harus CounselorOutput dengan draft, bridge, gap_analysis."""
    llm = DummyLLM(make_counselor_output(draft="Berat banget ya.", bridge="Yuk susun jadwal."))
    result = counselor_module._generate_response(
        structured_llm=llm.with_structured_output(CounselorOutput),
        user_msg="pusing banget",
        raw_tasks=[make_raw_task()],
    )
    assert isinstance(result, CounselorOutput)
    assert len(result.draft) > 0
    assert len(result.bridge) > 0
    assert isinstance(result.gap_analysis, TaskGapAnalysis)


def test_generate_response_includes_task_context_in_prompt():
    """Judul task harus muncul di prompt LLM."""
    llm = CapturingLLM()
    counselor_module._generate_response(
        structured_llm=llm.with_structured_output(CounselorOutput),
        user_msg="pusing",
        raw_tasks=[make_raw_task(title="Laprak Termo")],
    )
    user_content = llm.received_prompts[0][1]["content"]
    assert "Laprak Termo" in user_content


def test_generate_response_includes_additional_context():
    """additional_context harus masuk ke prompt."""
    llm = CapturingLLM()
    counselor_module._generate_response(
        structured_llm=llm.with_structured_output(CounselorOutput),
        user_msg="pusing",
        raw_tasks=[make_raw_task()],
        additional_context="ujiannya tentang algoritma sorting",
    )
    user_content = llm.received_prompts[0][1]["content"]
    assert "algoritma sorting" in user_content


def test_generate_response_fallback_on_error():
    """Fallback harus return CounselorOutput valid dengan gap_analysis."""
    llm = DummyLLMError()
    result = counselor_module._generate_response(
        structured_llm=llm.with_structured_output(CounselorOutput),
        user_msg="capek",
        raw_tasks=[make_raw_task()],
    )
    assert isinstance(result, CounselorOutput)
    assert len(result.draft) > 0
    assert isinstance(result.gap_analysis, TaskGapAnalysis)
    # Fallback harus tandai tasks sebagai incomplete
    assert result.gap_analysis.overall_complete is False


# ---------------------------------------------------------------------------
# Tests: _enrich_tasks
# ---------------------------------------------------------------------------

def test_enrich_tasks_updates_title():
    """Enrich harus update title task jika info baru tersedia."""
    raw_tasks = [make_raw_task(task_id="task_001", title="Tugas vague")]
    enriched_out = make_enriched_output(task_id="task_001", title="Ujian Kalkulus Bab 3")

    llm = DummyLLM(enriched_output=enriched_out)
    result = counselor_module._enrich_tasks(
        enrichment_llm=llm.with_structured_output(EnrichedTasksOutput),
        raw_tasks=raw_tasks,
        additional_context="ujiannya kalkulus bab 3",
        original_user_msg="pusing",
    )

    assert len(result) == 1
    assert result[0]["title"] == "Ujian Kalkulus Bab 3"


def test_enrich_tasks_preserves_untouched_fields():
    """Field yang tidak diupdate enrich harus tetap dari data lama."""
    raw_tasks = [make_raw_task(
        task_id="task_001",
        title="Tugas RPL",
        raw_input="tugas rpl deadline besok",
        category="serius",
    )]
    enriched_out = EnrichedTasksOutput(enriched_tasks=[
        EnrichedTaskItem(
            task_id="task_001",
            title="Tugas RPL",          # sama, tidak berubah
            description="Deskripsi baru.",
            raw_time=None,
            category="serius",
        )
    ])

    llm = DummyLLM(enriched_output=enriched_out)
    result = counselor_module._enrich_tasks(
        enrichment_llm=llm.with_structured_output(EnrichedTasksOutput),
        raw_tasks=raw_tasks,
        additional_context="deadline besok jam 8",
        original_user_msg="tugas rpl deadline besok",
    )

    assert result[0]["raw_input"] == "tugas rpl deadline besok"
    assert result[0]["category"] == "serius"


def test_enrich_tasks_fallback_on_error():
    """Jika enrich gagal, kembalikan raw_tasks lama tanpa error."""
    raw_tasks = [make_raw_task()]
    llm = DummyLLMError()
    result = counselor_module._enrich_tasks(
        enrichment_llm=llm.with_structured_output(EnrichedTasksOutput),
        raw_tasks=raw_tasks,
        additional_context="info baru",
        original_user_msg="pusing",
    )
    assert result == raw_tasks


def test_enrich_tasks_ignores_unknown_task_ids():
    """Jika enrich return task_id yang tidak ada, jangan crash."""
    raw_tasks = [make_raw_task(task_id="task_001")]
    enriched_out = EnrichedTasksOutput(enriched_tasks=[
        EnrichedTaskItem(
            task_id="task_999",  # tidak ada di raw_tasks
            title="Ghost Task",
            description="Tidak ada.",
            raw_time=None,
            category="biasa",
        )
    ])
    llm = DummyLLM(enriched_output=enriched_out)
    result = counselor_module._enrich_tasks(
        enrichment_llm=llm.with_structured_output(EnrichedTasksOutput),
        raw_tasks=raw_tasks,
        additional_context="info",
        original_user_msg="pusing",
    )
    # task_001 harus tetap ada, ghost task tidak masuk
    assert len(result) == 1
    assert result[0]["task_id"] == "task_001"


# ---------------------------------------------------------------------------
# Tests: make_counselor — alur utama
# ---------------------------------------------------------------------------

def test_counselor_approved_sets_done_true():
    """approved=True → counselor_done=True."""
    llm = DummyLLM(make_counselor_output(overall_complete=True))
    agent = counselor_module.make_counselor(
        llm, _interrupt=make_dummy_interrupt({"approved": True})
    )
    result = agent(make_state())
    assert result["counselor_done"] is True
    assert result["hitl_status"] == "approved"
    assert result["hitl_input"] is None


def test_counselor_rejected_sets_done_false():
    """approved=False → counselor_done=False, loop lagi."""
    llm = DummyLLM(make_counselor_output(overall_complete=False))
    hitl_response = {"approved": False, "additional_context": "ujiannya tentang sorting"}
    agent = counselor_module.make_counselor(
        llm, _interrupt=make_dummy_interrupt(hitl_response)
    )
    result = agent(make_state())
    assert result["counselor_done"] is False
    assert result["hitl_status"] == "rejected"
    assert result["hitl_input"] == hitl_response


def test_counselor_approved_response_contains_draft_and_bridge():
    """Saat approved, full_response = draft + dua newline + bridge."""
    llm = DummyLLM(make_counselor_output(draft="DRAFT_TEXT", bridge="BRIDGE_TEXT"))
    agent = counselor_module.make_counselor(
        llm, _interrupt=make_dummy_interrupt({"approved": True})
    )
    result = agent(make_state())
    full = result["counselor_response"][0]
    assert "DRAFT_TEXT\n\nBRIDGE_TEXT" == full


def test_counselor_rejected_response_no_bridge():
    """Saat rejected, bridge tidak boleh muncul."""
    llm = DummyLLM(make_counselor_output(draft="DRAFT", bridge="JANGAN_MUNCUL"))
    agent = counselor_module.make_counselor(
        llm, _interrupt=make_dummy_interrupt({"approved": False, "additional_context": ""})
    )
    result = agent(make_state())
    saved = result["counselor_response"][0]
    assert "JANGAN_MUNCUL" not in saved
    assert result["messages"][0].content != "JANGAN_MUNCUL"


def test_counselor_hitl_payload_has_required_keys():
    """HITL payload harus punya type, draft, message, has_missing_info."""
    llm = DummyLLM(make_counselor_output(overall_complete=False))
    capturing = make_capturing_interrupt({"approved": True})
    agent = counselor_module.make_counselor(llm, _interrupt=capturing)
    agent(make_state(raw_tasks=[make_raw_task()]))

    payload = capturing.captured
    assert payload.get("type") == "counselor_review"
    assert "draft" in payload
    assert "message" in payload
    assert "has_missing_info" in payload


def test_counselor_hitl_payload_has_missing_info_true_when_incomplete():
    """has_missing_info=True ketika gap_analysis.overall_complete=False."""
    llm = DummyLLM(make_counselor_output(overall_complete=False))
    capturing = make_capturing_interrupt({"approved": True})
    agent = counselor_module.make_counselor(llm, _interrupt=capturing)
    agent(make_state(raw_tasks=[make_raw_task()]))
    assert capturing.captured["has_missing_info"] is True


def test_counselor_hitl_payload_has_missing_info_false_when_complete():
    """has_missing_info=False ketika gap_analysis.overall_complete=True."""
    llm = DummyLLM(make_counselor_output(overall_complete=True))
    capturing = make_capturing_interrupt({"approved": True})
    agent = counselor_module.make_counselor(llm, _interrupt=capturing)
    agent(make_state(raw_tasks=[make_raw_task()]))
    assert capturing.captured["has_missing_info"] is False


def test_counselor_max_loop_forces_done():
    """Setelah MAX_COUNSELOR_LOOPS, paksa done tanpa interrupt."""
    llm = DummyLLM()
    agent = counselor_module.make_counselor(llm)  # tidak inject _interrupt
    existing = ["draft"] * counselor_module.MAX_COUNSELOR_LOOPS
    result = agent(make_state(counselor_response=existing))
    assert result["counselor_done"] is True
    assert result["hitl_status"] == "approved"


def test_counselor_appends_one_item_per_loop():
    """Setiap loop return list berisi 1 item."""
    llm = DummyLLM()
    agent = counselor_module.make_counselor(
        llm, _interrupt=make_dummy_interrupt({"approved": True})
    )
    result = agent(make_state())
    assert isinstance(result["counselor_response"], list)
    assert len(result["counselor_response"]) == 1


# ---------------------------------------------------------------------------
# Tests: raw_tasks enrichment di alur utama
# ---------------------------------------------------------------------------

def test_counselor_approved_returns_raw_tasks():
    """Saat approved, raw_tasks harus ada di return value."""
    raw_tasks = [make_raw_task(task_id="task_001", title="Tugas RPL")]
    llm = DummyLLM(make_counselor_output(overall_complete=True))
    agent = counselor_module.make_counselor(
        llm, _interrupt=make_dummy_interrupt({"approved": True})
    )
    result = agent(make_state(raw_tasks=raw_tasks))
    assert "raw_tasks" in result
    assert isinstance(result["raw_tasks"], list)


def test_counselor_rejected_saves_raw_tasks_progress():
    """Saat rejected, raw_tasks hasil enrich sejauh ini tetap disimpan."""
    raw_tasks = [make_raw_task(task_id="task_001")]
    llm = DummyLLM(make_counselor_output(overall_complete=False))
    agent = counselor_module.make_counselor(
        llm,
        _interrupt=make_dummy_interrupt({"approved": False, "additional_context": "info baru"}),
    )
    result = agent(make_state(raw_tasks=raw_tasks))
    assert "raw_tasks" in result
    assert len(result["raw_tasks"]) == 1


def test_counselor_enrich_called_when_additional_context_exists():
    """
    Jika additional_context ada dari loop sebelumnya,
    enrich_tasks harus dipanggil dan bisa update title.
    """
    enriched_out = make_enriched_output(task_id="task_001", title="Ujian Kalkulus Lanjut")
    llm = DummyLLM(
        counselor_output=make_counselor_output(overall_complete=True),
        enriched_output=enriched_out,
    )
    agent = counselor_module.make_counselor(
        llm, _interrupt=make_dummy_interrupt({"approved": True})
    )
    state = make_state(
        raw_tasks=[make_raw_task(task_id="task_001", title="Ujian vague")],
        hitl_input={
            "approved": False,
            "additional_context": "ujiannya kalkulus lanjut",
        },
        counselor_response=["draft loop 1"],
    )
    result = agent(state)
    # Title harus sudah diupdate dari enrich
    updated_titles = [t["title"] if isinstance(t, dict) else t.title for t in result["raw_tasks"]]
    assert "Ujian Kalkulus Lanjut" in updated_titles


def test_counselor_no_enrich_when_no_additional_context():
    """
    Jika tidak ada additional_context, enrich tidak dipanggil
    dan raw_tasks tetap seperti semula di loop pertama.
    """
    raw_tasks = [make_raw_task(task_id="task_001", title="Tugas RPL")]
    # enriched_output dengan title berbeda — seharusnya tidak dipanggil
    enriched_out = make_enriched_output(task_id="task_001", title="TIDAK SEHARUSNYA MUNCUL")
    llm = DummyLLM(
        counselor_output=make_counselor_output(overall_complete=True),
        enriched_output=enriched_out,
    )
    agent = counselor_module.make_counselor(
        llm, _interrupt=make_dummy_interrupt({"approved": True})
    )
    # Loop pertama, tidak ada hitl_input → tidak ada additional_context
    result = agent(make_state(raw_tasks=raw_tasks))
    updated_titles = [t["title"] if isinstance(t, dict) else t.title for t in result["raw_tasks"]]
    assert "TIDAK SEHARUSNYA MUNCUL" not in updated_titles
    assert "Tugas RPL" in updated_titles