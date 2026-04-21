import json
from typing import Any

from app.graph.agents.agent1_interpreter import Task

def _parse_llm_json(raw: str) -> Any:
    """Strip markdown fence jika ada, lalu parse JSON."""
    content = raw.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        # Hapus baris pertama (```json atau ```) dan baris terakhir (```)
        content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return json.loads(content.strip())


def _all_tasks_complete(tasks: list[Task]) -> bool:
    """True jika tidak ada task yang masih butuh klarifikasi."""
    return all(len(t.needs_clarification) == 0 for t in tasks)
