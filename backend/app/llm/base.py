from __future__ import annotations

from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Authoring LLM used to suggest fields and assemble VLM prompts.

    Separate from the in-house VLM that runs production extraction.
    """

    name: str

    @abstractmethod
    async def complete_json(self, system: str, user: str) -> dict:
        """Return a JSON object the model produced."""
