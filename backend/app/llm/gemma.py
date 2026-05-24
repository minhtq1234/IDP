import json

import httpx

from app.config import settings
from app.llm.base import LLMClient


class GemmaClient(LLMClient):
    """Self-hosted Gemma via OpenAI-compatible chat completions.

    Works with vLLM (`/v1/chat/completions`) and Ollama
    (`/v1/chat/completions` since 0.1.24). Endpoint configurable.
    """

    name = "gemma"

    async def complete_json(self, system: str, user: str) -> dict:
        url = settings.gemma_base_url.rstrip("/") + "/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        if settings.gemma_api_key:
            headers["Authorization"] = f"Bearer {settings.gemma_api_key}"
        payload = {
            "model": settings.gemma_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)
