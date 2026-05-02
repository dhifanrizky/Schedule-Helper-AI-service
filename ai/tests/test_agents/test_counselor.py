import app.graph.agents.counselor as counselor_module
from app.graph.agents.counselor import CounselorOutput


# ---------------------------------------------------------------------------
# Helpers & Stubs
# ---------------------------------------------------------------------------

class DummyLLM:
    """LLM stub yang selalu return teks statis."""
    def __init__(self, draft: str = "Draft dummy.", bridge: str = "Bridge dummy."):
        self._draft = draft
        self._bridge = bridge

    def with_structured_output(self, schema):
        draft, bridge = self._draft, self._bridge
        class _Structured:
            def invoke(self, _prompt):
                return CounselorOutput(draft=draft, bridge=bridge)
        return _Structured()


class DummyLLMError:
    """LLM stub yang selalu raise Exception."""
    def with_structured_output(self, schema):
        class _Structured:
            def invoke(self, _prompt):
                raise Exception("API timeout")
        return _Structured()


class CapturingLLM:
    """LLM stub yang merekam prompt yang diterima."""
    def __init__(self, draft: str = "ok", bridge: str = "bridge ok"):
        self._draft = draft
        self._bridge = bridge
        self.received_prompts: list = []

    def with_structured_output(self, schema):
        store = self
        class _Structured:
            def invoke(self, prompt):
                store.received_prompts.append(prompt)
                return CounselorOutput(draft=store._draft, bridge=store._bridge)
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


def make_state(
    user_message: str = "aku stres banget",
    raw_tasks: list = None,
    hitl_input: dict = None,
    counselor_response: list = None,
):
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
    """Return value harus CounselorOutput dengan draft dan bridge non-empty."""
    llm = DummyLLM(
        draft="Waduh berat banget ya, wajar kamu ngerasa overwhelmed.",
        bridge="Oke, yuk kita susun jadwalnya.",
    )
    result = counselor_module._generate_response(
        structured_llm=llm.with_structured_output(CounselorOutput),
        user_msg="aku pusing tugas numpuk semua",
        raw_tasks=[],
        additional_context="",
    )
    assert isinstance(result, CounselorOutput)
    assert len(result.draft) > 0
    assert len(result.bridge) > 0


def test_generate_response_includes_additional_context_in_prompt():
    """additional_context harus masuk ke prompt yang dikirim ke LLM."""
    llm = CapturingLLM()
    counselor_module._generate_response(
        structured_llm=llm.with_structured_output(CounselorOutput),
        user_msg="aku stres",
        raw_tasks=[],
        additional_context="lagi ga enak badan juga",
    )
    assert len(llm.received_prompts) == 1
    # prompt adalah list [system_msg, user_msg] — cari di user content
    user_content = llm.received_prompts[0][1]["content"]
    assert "ga enak badan" in user_content


def test_generate_response_includes_raw_tasks_in_prompt():
    """raw_tasks harus muncul di prompt LLM."""
    llm = CapturingLLM()
    counselor_module._generate_response(
        structured_llm=llm.with_structured_output(CounselorOutput),
        user_msg="banyak tugas nih",
        raw_tasks=[{"task_id": "task_001", "title": "Tugas RPL", "raw_input": "tugas rpl"}],
        additional_context="",
    )
    user_content = llm.received_prompts[0][1]["content"]
    assert "Tugas RPL" in user_content


def test_generate_response_task_list_appears_in_bridge_prompt():
    """task_list_str (untuk bridge) harus ada di prompt."""
    llm = CapturingLLM()
    counselor_module._generate_response(
        structured_llm=llm.with_structured_output(CounselorOutput),
        user_msg="banyak tugas",
        raw_tasks=[
            {"task_id": "task_001", "title": "Laprak Termo"},
            {"task_id": "task_002", "title": "Tugas RPL"},
        ],
        additional_context="",
    )
    user_content = llm.received_prompts[0][1]["content"]
    assert "Laprak Termo" in user_content
    assert "Tugas RPL" in user_content


def test_generate_response_fallback_on_llm_error():
    """Fallback harus return CounselorOutput valid, bukan raise."""
    llm = DummyLLMError()
    result = counselor_module._generate_response(
        structured_llm=llm.with_structured_output(CounselorOutput),
        user_msg="aku capek",
        raw_tasks=[],
    )
    assert isinstance(result, CounselorOutput)
    assert len(result.draft) > 0
    assert len(result.bridge) > 0


def test_generate_response_fallback_includes_task_titles():
    """Fallback bridge harus menyebut task title jika raw_tasks ada."""
    llm = DummyLLMError()
    result = counselor_module._generate_response(
        structured_llm=llm.with_structured_output(CounselorOutput),
        user_msg="aku capek",
        raw_tasks=[{"task_id": "task_001", "title": "Ujian Kalkulus"}],
    )
    assert "Ujian Kalkulus" in result.bridge


# ---------------------------------------------------------------------------
# Tests: make_counselor — alur utama
# ---------------------------------------------------------------------------

def test_counselor_approved_sets_done_true():
    """User puas → counselor_done=True → lanjut ke Prioritizer."""
    llm = DummyLLM()
    agent = counselor_module.make_counselor(
        llm,
        _interrupt=make_dummy_interrupt({"approved": True}),
    )
    result = agent(make_state("aku stres"))

    assert result["counselor_done"] is True
    assert result["hitl_status"] == "approved"
    assert result["hitl_input"] is None


def test_counselor_not_approved_sets_done_false():
    """User mau tambahin cerita → counselor_done=False → loop lagi."""
    llm = DummyLLM()
    hitl_response = {
        "approved": False,
        "additional_context": "lagi ga enak badan juga sebenernya",
    }
    agent = counselor_module.make_counselor(
        llm,
        _interrupt=make_dummy_interrupt(hitl_response),
    )
    result = agent(make_state("aku stres"))

    assert result["counselor_done"] is False
    assert result["hitl_status"] == "rejected"
    assert result["hitl_input"] == hitl_response


def test_counselor_additional_context_used_in_next_loop():
    """Di loop ke-2, additional_context dari hitl_input harus masuk ke prompt LLM."""
    llm = CapturingLLM()
    agent = counselor_module.make_counselor(
        llm,
        _interrupt=make_dummy_interrupt({"approved": True}),
    )
    state = make_state(
        hitl_input={
            "approved": False,
            "additional_context": "aku juga lagi ga enak badan",
        },
        counselor_response=["draft loop 1"],
    )
    agent(state)

    user_content = llm.received_prompts[0][1]["content"]
    assert "ga enak badan" in user_content


def test_counselor_max_loop_forces_done_without_interrupt():
    """Setelah MAX_COUNSELOR_LOOPS, harus selesai tanpa panggil interrupt."""
    llm = DummyLLM()
    agent = counselor_module.make_counselor(llm)  # tidak inject _interrupt

    existing = ["draft"] * counselor_module.MAX_COUNSELOR_LOOPS
    result = agent(make_state(counselor_response=existing))

    assert result["counselor_done"] is True
    assert result["hitl_status"] == "approved"


def test_counselor_appends_one_item_per_loop():
    """Setiap loop return list berisi 1 item (operator.add yang gabungkan)."""
    llm = DummyLLM()
    agent = counselor_module.make_counselor(
        llm,
        _interrupt=make_dummy_interrupt({"approved": True}),
    )
    result = agent(make_state())

    assert isinstance(result["counselor_response"], list)
    assert len(result["counselor_response"]) == 1


def test_counselor_hitl_payload_has_required_keys():
    """Payload ke interrupt harus punya type, draft, dan message."""
    llm = DummyLLM()
    capturing = make_capturing_interrupt({"approved": True})
    agent = counselor_module.make_counselor(llm, _interrupt=capturing)

    agent(make_state(
        raw_tasks=[{"task_id": "task_001", "title": "Tugas RPL", "description": "..."}]
    ))

    payload = capturing.captured
    assert payload.get("type") == "counselor_review"
    assert "draft" in payload
    assert "message" in payload


# ---------------------------------------------------------------------------
# Tests: bridge — fitur baru
# ---------------------------------------------------------------------------

def test_counselor_approved_response_contains_bridge():
    """Saat approved, full_response harus mengandung draft DAN bridge."""
    llm = DummyLLM(
        draft="Aku ngerti kondisimu berat. Kesimpulan ini udah pas?",
        bridge="Oke, tarik napas dulu. Yuk kita susun jadwalnya sekarang.",
    )
    agent = counselor_module.make_counselor(
        llm,
        _interrupt=make_dummy_interrupt({"approved": True}),
    )
    result = agent(make_state())

    full = result["counselor_response"][0]
    assert "Aku ngerti kondisimu berat" in full
    assert "Yuk kita susun jadwalnya" in full


def test_counselor_rejected_response_does_not_contain_bridge():
    """Saat rejected, bridge tidak boleh muncul di response user."""
    llm = DummyLLM(
        draft="Draft empati.",
        bridge="Ini bridge yang tidak boleh muncul.",
    )
    agent = counselor_module.make_counselor(
        llm,
        _interrupt=make_dummy_interrupt({"approved": False, "additional_context": ""}),
    )
    result = agent(make_state())

    saved = result["counselor_response"][0]
    assert "bridge yang tidak boleh muncul" not in saved

    msg_content = result["messages"][0].content
    assert "bridge yang tidak boleh muncul" not in msg_content


def test_counselor_hitl_payload_draft_only_no_bridge():
    """HITL payload ke frontend hanya berisi draft, bukan bridge."""
    llm = DummyLLM(
        draft="Ini draft untuk user baca.",
        bridge="Bridge rahasia yang belum saatnya.",
    )
    capturing = make_capturing_interrupt({"approved": True})
    agent = counselor_module.make_counselor(llm, _interrupt=capturing)
    agent(make_state())

    payload = capturing.captured
    assert payload["draft"] == "Ini draft untuk user baca."
    assert "bridge" not in payload


def test_counselor_bridge_separator_in_full_response():
    """draft dan bridge harus dipisahkan dengan dua newline."""
    llm = DummyLLM(draft="DRAFT_TEXT", bridge="BRIDGE_TEXT")
    agent = counselor_module.make_counselor(
        llm,
        _interrupt=make_dummy_interrupt({"approved": True}),
    )
    result = agent(make_state())

    full = result["counselor_response"][0]
    assert "DRAFT_TEXT\n\nBRIDGE_TEXT" == full