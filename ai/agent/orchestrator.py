import instructor
import litellm

from schemas.agent_tools import AgentAction, GetWeather
from services.weather_service import fetch_weather_api


class AIAgent:
    def __init__(self, model: str = "gemini/gemini-2.5-flash"):
        self.model = model

    async def chat(self, prompt: str):
        client = instructor.from_litellm(
            litellm.completion,
            mode=instructor.Mode.JSON,  # <--- Tentukan mode secara global untuk client ini
        )
        response = client.chat.completions.create(
            model=self.model,
            response_model=AgentAction,
            messages=[
                {
                    "role": "system",
                    "content": "Kamu adalah asisten yang wajib memberikan output JSON sesuai skema.",
                },
                {"role": "user", "content": prompt},
            ],
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE",
                },
            ],
        )

        # 2. Eksekusi Logic berdasarkan pilihan LLM
        action = response.action

        if isinstance(action, GetWeather):
            data = await fetch_weather_api(action.location)
            return {"type": "tool_used", "result": data}

        return {"type": "final_answer", "result": action.answer}
