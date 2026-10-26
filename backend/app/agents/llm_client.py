import json
import logging
from collections.abc import Callable
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Thin wrapper around the LLM backend used for agent reasoning steps.

    Two modes, controlled by `LLM_MODE`:
      - "ollama": calls a local Ollama server (OpenAI-ecosystem-compatible
        enough via its native /api/chat JSON-mode endpoint).
      - "mock": no network/model needed at all -- each caller supplies a
        deterministic `mock_fn` so the full pipeline still runs end-to-end
        offline, in CI, and in tests.

    If an Ollama call fails for any reason (model not pulled, server down,
    malformed JSON back), we log it and fall back to the mock output rather
    than taking the whole pipeline down -- a clinical documentation tool
    degrading to "flag everything for manual review" is a much better
    failure mode than a 500.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.mode = settings.llm_mode
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model

    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        mock_fn: Callable[[], dict[str, Any]],
    ) -> dict[str, Any]:
        if self.mode == "mock":
            return mock_fn()

        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=60.0) as client:
                resp = await client.post(
                    "/api/chat",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "format": "json",
                        "stream": False,
                    },
                )
                resp.raise_for_status()
                content = resp.json()["message"]["content"]
                return json.loads(content)
        except Exception:
            logger.exception(
                "LLM call to Ollama failed (model=%s); falling back to mock output", self.model
            )
            return mock_fn()
