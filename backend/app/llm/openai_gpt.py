import json

import httpx

from app.config import settings
from app.llm.base import LLMClient


class OpenAIClient(LLMClient):
    name = "openai"

    async def complete_json(self, system: str, user: str) -> dict:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        payload = {
            "model": settings.openai_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions", json=payload, headers=headers
            )
            resp.raise_for_status()
            data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)
